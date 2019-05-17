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

############
#User Inputs
############

# where are the dcStats MaxNDVI tifs?
MaxNDVItiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/previous_run/testing_mosaics/ndvi_max/"

# where are the dcStats NDVIArgMaxMin tifs?
NDVIArgMaxMintiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/previous_run/testing_mosaics/NDVIArgMaxMin/"

#Is there an irrigatable area shapefile we're using for masking?
irrigatable_area = False
irrigatable_area_shp_fpath = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/NSW_OEH_irrigated_2013.shp"

#is there a shapefile we're using for clipping the extent? e.g. just the northern basins
clip_extent = True
northernBasins_shp = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/northern_basins.shp"

# where should I put the results?
results = '/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/previous_run/testing_mosaics/results/'

#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'

#Input your area of interest's name
AOI = 'largetest'

#What thresholds should I use for NDVI?
threshold = 0.8

#-----------------------------------------

#script proper------------------------------

#loop through raster files and do the analysis
maxNDVItiffFiles = os.listdir(MaxNDVItiffs)
# NDVIArgMaxMintiffFiles = os.listdir(NDVIArgMaxMintiffs)

for tif in maxNDVItiffFiles:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    if season == 'Summer':
        year = tif[9:13]
        nextyear = str(int(year) + 1)[2:] 
        year = year + "_" + nextyear
        year = season + year
        argmaxminyear = "NDVIArgMaxMin_" + year[6:10] + "1101_mosaic.tif" 
    if season == 'Winter':
        year = tif[7:11]
        year = season + year
        argmaxminyear = "NDVIArgMaxMin_" + year[6:10] + "0501_mosaic.tif" 

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)

    results_ = results_ + AOI + "_" + year + "/"

    # set up input filename
    InputNDVIStats = MaxNDVItiffs + tif
    KEAFile = results_ + AOI + '_' + year + '.kea'
    SegmentedKEAFile = results_ + AOI + '_' + year + '_sheperdSEG.kea'
    SegmentedTiffFile = results_ + AOI + '_' + year + '_sheperdSEG.tif'
    SegmentedPolygons = results_ + AOI + '_' + year + '_SEGpolygons.shp'
    
    print("calculating imageSegmentation")
    imageSeg(InputNDVIStats, KEAFile, SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons, minPxls=100, epsg = '3577')

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
    
    print('exporting the irrigatation Gtiff')
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_Irrigated.tif",
                  NDVI_max_Irrigated.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=-9999)
    
    # import timeofmax and timeofmin rasters
    argmaxmin = xr.open_rasterio(NDVIArgMaxMintiffs+argmaxminyear)
    timeofmax = argmaxmin[0] 
    timeofmin = argmaxmin[1]

    # mask timeof layers by irrigated extent
    timeofmax = timeofmax.where(~np.isnan(NDVI_max_Irrigated))
    timeofmin = timeofmin.where(~np.isnan(NDVI_max_Irrigated))

    # export masked timeof layers.
    print('exporting the timeofmaxmin Gtiffs')
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_timeofmaxNDVI.tif",
                  timeofmax.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=-9999)

    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_timeofminNDVI.tif",
                  timeofmin.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=-9999)
    
    if irrigatable_area == True:
        print('limiting analysis to the irrigatable area polygon')
        # rasterize Irrigatable vector file
        oeh_raster = SpatialTools.rasterize_vector(irrigatable_area_shp_fpath,height, width, 
                                                   transform, projection, raster_path=None)
        #mask
        NDVI_max_Irrigated_oeh = NDVI_max_Irrigated.where(oeh_raster)

        #export as GTiff
        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_OEHMasked_Irrigated.tif",
                  NDVI_max_Irrigated_oeh.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=-9999)
    
        # mask timeof layers by irrigated extent
        timeofmax_oeh = timeofmax.where(~np.isnan(NDVI_max_Irrigated_oeh))
        timeofmin_oeh = timeofmin.where(~np.isnan(NDVI_max_Irrigated_oeh))

        # export masked timeof layers.
        print('exporting the timeofmaxmin Gtiff')
        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_OEHMasked_timeofmaxNDVI.tif",
                      timeofmax_oeh.values,
                      geo_transform = transform, 
                      projection = projection, 
                      nodata_val=-9999)

        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_OEHMasked_timeofminNDVI.tif",
                      timeofmin_oeh.values,
                      geo_transform = transform, 
                      projection = projection, 
                      nodata_val=-9999)
        
    if clip_extent == True:
        print('clipping extent to provided polygon')
        clip_raster = SpatialTools.rasterize_vector(northernBasins_shp,
                                               height, width, transform, projection, raster_path=None)
        #mask all outputs to the clip extent
        NDVI_max_Irrigated_clipped  = NDVI_max_Irrigated.where(clip_raster)
        timeofmax_clipped = timeofmax.where(~np.isnan(NDVI_max_Irrigated_clipped))
        timeofmin_clipped = timeofmin.where(~np.isnan(NDVI_max_Irrigated_clipped))
        
        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_Irrigated_clipped.tif",
              NDVI_max_Irrigated_clipped.values,
              geo_transform = transform, 
              projection = projection, 
              nodata_val=-9999)
        
        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_timeofmaxNDVI_clipped.tif",
                      timeofmax_clipped.values,
                      geo_transform = transform, 
                      projection = projection, 
                      nodata_val=-9999)

        SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_timeofminNDVI_clipped.tif",
                      timeofmin_clipped.values,
                      geo_transform = transform, 
                      projection = projection, 
                      nodata_val=-9999)
    
    print("Finished processing of " + tif)
    
print("Success!")


    