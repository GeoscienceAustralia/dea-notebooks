############
#User Inputs
############

# where are the dcStats MaxNDVI tifs?
tiffs = 'data/datacube_stats/summer_2004_2018/mads_fun/'

#where is the shapefile of the catchemnt? used for wofs query.
shp_fpath = 'data/spatial/murrumbidgee_catchment.shp'

# where should I put the results?
results = 'results/Murrumbidgee/'

#what season are we processing?
season = 'Summer'

#Input your area of interest's name
AOI = 'Murrumbidgee_MADS'

#What thresholds should I use?
threshold = 0.8
wofs_theshold = 0.15

#-----------------------------------------

import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
import dask
import datacube 
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube.utils import geometry
import rasterio.features
from osgeo import gdal, ogr
import os
from rsgislib.segmentation import segutils
from rasterstats import zonal_stats

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools, BandIndices
from load_data import load_data
from transform_tuple import transform_tuple
from imageSeg import imageSeg
from query_from_shp import query_from_shp

#script proper------------------------------

#get the wofs summary for masking later
query = query_from_shp(shp_fpath, start_date = '2017-01-01', end_date = '2017-12-31')

dc_mads = datacube.Datacube(config='/g/data1a/u46/users/cb3058/datacube.conf', env='NCI-test')
mads = dc_mads.load(product = 'ls8_nbart_tmad_annual', **query)

del query['time']
dc = datacube.Datacube(app='wofs')
wofs_alltime = dc.load(product = 'wofs_summary', **query)

#loop through raster files and do the analysis
tiffFiles = os.listdir(tiffs)

for tif in tiffFiles:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    if season == 'Summer':
        year = tif[7:11]
        nextyear = str(int(tif[7:11]) + 1)[2:] 
        year = year + "-" + nextyear
        year = season + year
    if season == 'Winter':
        year = tiff[7:11]
        year = season + year

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)

    results_ = results_ + AOI + "_" + year + "/"

    # setup input filename
    InputNDVIStats = tiffs + tif
    KEAFile = results_ + AOI + '_' + year + '.kea'
    SegmentedKEAFile = results_ + AOI + '_' + year + '_sheperdSEG.kea'
    SegmentedTiffFile = results_ + AOI + '_' + year + '_sheperdSEG.tif'
    SegmentedPolygons = results_ + AOI + '_' + year + '_SEGpolygons.shp'
    print("calculating imageSegmentation")
    imageSeg(InputNDVIStats, KEAFile, SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons)

    gdf = gpd.read_file(results_ + AOI + '_' + year + '_SEGpolygons.shp')
    #calculate zonal mean of NDVI
    print("calculating zonal stats")
    gdf['mean'] = pd.DataFrame(zonal_stats(vectors=gdf['geometry'], raster=InputNDVIStats, stats='mean'))['mean']
    #calculate area of polygons
    gdf['area'] = gdf['geometry'].area
    #filter by area and mean NDVI
    highNDVI = gdf['mean'] >= threshold
    smallArea = gdf['area'] <= 5500000
    gdf = gdf[highNDVI & smallArea]
    #export shapefile
    gdf.to_file(results_ + AOI + "_" + year + "_Irrigated.shp")
    
    print('performing masking and raster math')
    NDVI_max = xr.open_rasterio(InputNDVIStats).squeeze()
    #get the transform and projection of our gtiff
    transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
    #find the width and height of the xarray dataset we want to mask
    width,height = NDVI_max.shape
    # rasterize vector
    gdf_raster = SpatialTools.rasterize_vector(results_ + AOI + "_" + year + "_Irrigated.shp",
                                               height, width, transform, projection, raster_path=None)
    # Mask the xarray
    NDVI_max_Irrigated = NDVI_max.where(gdf_raster)

    #remove areas below our threshold that are at the edges of the rasterized polygons
    NDVI_max_Irrigated = NDVI_max_Irrigated.where(NDVI_max_Irrigated >= threshold)
    #Use wofs to remove areas that have standing water for a significant amount of time
    NDVI_max_Irrigated = NDVI_max_Irrigated.where(wofs_alltime.frequency.drop('time').squeeze() <= wofs_theshold)

    #remove pixels that cross over the major rivers in the region
    rivers_raster = SpatialTools.rasterize_vector("data/spatial/major_rivers_aus.shp", height, width, transform, projection, raster_path=None)
    rivers_raster = rivers_raster.astype(bool)
    rivers_raster = xr.DataArray(rivers_raster, coords = [NDVI_max.y, NDVI_max.x], dims = ['y', 'x'], name='rivers')
    NDVI_max_Irrigated = NDVI_max_Irrigated.where(rivers_raster == 0)
    
    x = mads.edev.squeeze()
    y = NDVI_max_Irrigated.where(x >=0.05)
    
    print('exporting the irrigatation Gtiff')
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_Irrigated.tif",
                  y.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=0)
    print("Finished processing of " + tif)

print("Success!")

    