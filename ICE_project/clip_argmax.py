import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from osgeo import gdal, ogr
import os
#from multiprocessing import Pool, cpu_count
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
MaxNDVItiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/renmark/"

# where are the dcStats NDVIArgMaxMin tifs?
NDVIArgMaxMintiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/ndviArgMaxMin/mosaics"

# where should I put the results?
results ='/g/data/r78/cb3058/dea-notebooks/ICE_project/results/renmark/'

#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'

#Input your area of interest's name
AOI = 'renmark'

# script proper-----------------------------

def irrigated_extent(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    
    if season == 'Summer':
        year = tif[14:19]
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
    
    #grab a tiff to get the transform tuple from
    multithresholdTIFF = results_ + AOI + "_" + year + "_multithreshold.tif"
    t = xr.open_rasterio(multithresholdTIFF).squeeze()
#     t = t.dropna(dim='x', how='all').dropna(dim='y', how='all') #get rid of all nans row,cols
       
    #find the transform etc of the xarray dataarray
    transform, projection = transform_tuple(t, (t.x, t.y), epsg=3577)
    width,height = t.shape

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

# if __name__ == '__main__':
#     irrigated_extent(sys.argv[1])
    
maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
pool = Pool(cpus)  
pool.map(irrigated_extent, maxNDVItiffFiles)