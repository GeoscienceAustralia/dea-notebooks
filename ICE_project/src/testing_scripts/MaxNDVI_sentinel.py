import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
import dask
import datacube 
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube.utils import geometry

import fiona
import rasterio.features
from osgeo import gdal, ogr
import os
from rsgislib.segmentation import segutils
from rasterstats import zonal_stats

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools, BandIndices, DEADataHandling
from load_data import load_data
from transform_tuple import transform_tuple
from imageSeg import imageSeg
from query_from_shp import query_from_shp

# where is your data and results folder?
data = 'data/'
results = 'results/'
shp_fpath = 'data/spatial/PeelR_AOI_Claire.shp'

#Input your area of interest's name, coords, and 
#the year you're interested in?
AOI = 'Peel_s2'
year = 'Summer2018-19'

time_period = ('2018-11-01', '2019-02-25')

#What thresholds should I use?
threshold = 0.8
wofs_theshold = 0.15

#Creating a folder to keep things neat
directory = results + AOI + "_" + year
if not os.path.exists(directory):
    os.mkdir(directory)

results = results + AOI + "_" + year + "/"

query = query_from_shp(shp_fpath, time_period[0], time_period[1], dask_chunks = 0)
query['resolution'] = (-10,10)
query['output_crs'] = ('epsg:3577')

dc = datacube.Datacube(app='load_clearsentinel')
#landsat
sentinel = DEADataHandling.load_clearsentinel2(dc=dc, query=query,
                        bands_of_interest=['nbart_red', 'nbart_green', 'nbart_blue', "nbart_nir_1"], 
                        masked_prop=0.5, mask_pixel_quality=True)

dc = datacube.Datacube(app='wofs')
del query['time']
wofs_alltime = dc.load(product = 'wofs_summary', **query)

print(sentinel.time.values)

#band indices calculation
def ndvi_func(nir, red):
    return ((nir - red)/(nir + red))

def ndvi_ufunc(ds):
    return xr.apply_ufunc(
        ndvi_func, ds.nbart_nir_1, ds.nbart_red,
        dask='parallelized',
        output_dtypes=[float])

NDVI_sentinel = ndvi_ufunc(sentinel)
NDVI_max = NDVI_sentinel.groupby('x','y').max('time').rename('NDVI_max')

transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
SpatialTools.array_to_geotiff(results + AOI + "_" + year + ".tif",
              NDVI_max.values, geo_transform = transform, 
              projection = projection, nodata_val=0)

# setup input filename
InputNDVIStats = results + AOI + "_" + year + ".tif"
KEAFile = results + AOI + '_' + year + '.kea'
SegmentedKEAFile = results + AOI + '_' + year + '_sheperdSEG.kea'
SegmentedTiffFile = results + AOI + '_' + year + '_sheperdSEG.tif'
SegmentedPolygons = results + AOI + '_' + year + '_SEGpolygons.shp'
print("calculating imageSegmentation")
imageSeg(InputNDVIStats, KEAFile, SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons, minPxls = 600)

gdf = gpd.read_file(results + AOI + '_' + year + '_SEGpolygons.shp')
#calculate zonal mean of NDVI
gdf['mean'] = pd.DataFrame(zonal_stats(vectors=gdf['geometry'], raster=InputNDVIStats, stats='mean'))['mean']
#calculate area of polygons
gdf['area'] = gdf['geometry'].area
#filter by area and mean NDVI
highNDVI = gdf['mean'] >= threshold
smallArea = gdf['area'] <= 5500000
gdf = gdf[highNDVI & smallArea]
#export shapefile
gdf.to_file(results + AOI + "_" + year + "_Irrigated.shp")

#get the transform and projection of our gtiff
transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
#find the width and height of the xarray dataset we want to mask
width,height = NDVI_max.shape
# rasterize vector
gdf_raster = SpatialTools.rasterize_vector(results + AOI + "_" + year + "_Irrigated.shp",
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

SpatialTools.array_to_geotiff(results + AOI + "_" + year + "_Irrigated.tif",
              NDVI_max_Irrigated.values,
              geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

