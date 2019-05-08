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
cpus = 4

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
results = '/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb_test/'

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
    print("exporting clipped ndvi_max geotiff")
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_NDVI_max.tif",
          NDVI_max.values,
          geo_transform = transform, 
          projection = projection, 
          nodata_val = 0)
    print("finished exporting " + tif)

maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
pool = Pool(cpus)  
pool.map(irrigated_extent, maxNDVItiffFiles)