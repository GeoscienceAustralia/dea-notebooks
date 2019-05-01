import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from osgeo import gdal, ogr
import os
from multiprocessing import Pool, cpu_count
from rsgislib.segmentation import segutils

import datacube 
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube.utils import geometry

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools
from transform_tuple import transform_tuple

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
cpus = 14

# where are the dcStats MaxNDVI tifs?
MaxNDVItiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/ndvi_max/mosaics/"

# where are the dcStats NDVIArgMaxMin tifs?
NDVIArgMaxMintiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/ndviArgMaxMin/mosaics"

#Is there an irrigatable area shapefile we're using for masking?
# irrigatable_area = False
# irrigatable_area_shp_fpath = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/NSW_OEH_irrigated_2013.shp"

#Shapefile we're using for clipping the extent? e.g. just the northern basins
northernBasins_shp = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/northern_basins.shp"

# where should I put the results?
results = '/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/'

#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'

#Input your area of interest's name
AOI = 'nmdb'

# script proper-----------------------------

def irrigated_extent(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    
    if season == 'Summer':
        year = tif[9:13]
        nextyear = str(int(year) + 1)[2:] 
        year = year + "_" + nextyear
        year = season + year
        argmaxminyear = "ndviArgMaxMin_" + year[6:10] + "1101_mosaic.tif" 
    if season == 'Winter':
        year = tif[7:11]
        year = season + year
        argmaxminyear = "ndviArgMaxMin_" + year[6:10] + "0501_mosaic.tif" 

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)

    results_ = results_ + AOI + "_" + year + "/"
    
    #limiting the extent to the northern basins
    print('clipping extent to provided polygon')
    NDVI_max = xr.open_rasterio(MaxNDVItiffs + tif).squeeze()

    transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
    width,height = NDVI_max.shape

    clip_raster = SpatialTools.rasterize_vector(northernBasins_shp, height, width,
                                                transform, projection, raster_path=None)

    NDVI_max = NDVI_max.where(clip_raster)

    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_NDVI_max.tif",
          NDVI_max.values,
          geo_transform = transform, 
          projection = projection, 
          nodata_val = 0)
          
    #inputs to GDAL and RSGISlib
    InputNDVIStats = results_ + AOI + "_" + year + "_NDVI_max.tif"
    KEAFile = results_ + AOI + '_' + year + '.kea'
    SegmentedKEAFile = results_ + AOI + '_' + year + '_sheperdSEG.kea'
    meanImage = results_ + AOI + '_' + year + "_ClumpMean.kea"
     
    # Change the tiff to a kea file
    print("converting tiff to kea")
    gdal.Translate(KEAFile, InputNDVIStats, format='KEA', outputSRS='EPSG:3577')
    
    # Run segmentation, with creation of clump means
    print('running image seg')
    segutils.runShepherdSegmentation(KEAFile, SegmentedKEAFile, meanImage,
                        numClusters=20, minPxls=100)

    segment_means = xr.open_rasterio(meanImage).squeeze()
    
    #reclassify and threshold by different values
    a = np.where(segment_means.values>=0.8, 80, segment_means)
    b = np.where((a>=0.75) & (a<0.8), 75, a)
    c = np.where((b>=0.70) & (b<0.75), 70, b)
    d = np.where(c>=70, c, np.nan)
    
    print('exporting the multithreshold as Gtiff')
    transform, projection = transform_tuple(segment_means, (segment_means.x, segment_means.y), epsg=3577)
    #find the width and height of the xarray dataset we want to mask
    width,height = segment_means.shape
    
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_multithreshold.tif",
                  d, geo_transform = transform, 
                  projection = projection, 
                  nodata_val=np.nan)
    
    #converting irrigated areas results to polygons
    print('converting multithreshold tiff to polygons...')
    multithresholdTIFF = results_ + AOI + "_" + year + "_multithreshold.tif"
    multithresholdPolygons = results_ + AOI + '_' + year + '_multithreshold.shp'
    
    os.system('gdal_polygonize.py ' + multithresholdTIFF + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + multithresholdPolygons)
    
    #filter by the area of the polygons to get rid of any forests etc
    print('filtering polygons by size, exporting, then rasterizing')
    gdf = gpd.read_file(multithresholdPolygons)
    gdf['area'] = gdf['geometry'].area
    smallArea = gdf['area'] <= 10000000
    gdf = gdf[smallArea]
    #export shapefile
    gdf.to_file(results_ + AOI + "_" + year + "_Irrigated.shp")
    
    gdf_raster = SpatialTools.rasterize_vector(results_ + AOI + "_" + year + "_Irrigated.shp",
                                               height, width, transform, projection, raster_path=None)
    
    print('loading, then masking timeof rasters')
    argmaxmin = xr.open_rasterio(NDVIArgMaxMintiffs+argmaxminyear)
    timeofmax = argmaxmin[0] 
    timeofmin = argmaxmin[1]

    # mask timeof layers by irrigated extent
    timeofmax = timeofmax.where(gdf_raster)
    timeofmin = timeofmin.where(gdf_raster)

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

maxNDVItiffFiles = os.listdir(MaxNDVItiffs)

if __name__ == '__main__':
    pool = Pool(cpus)  
    pool.map(irrigated_extent, maxNDVItiffFiles)

