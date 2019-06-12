import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from osgeo import gdal, ogr
import os
from multiprocessing import Pool, cpu_count

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools
from transform_tuple import transform_tuple

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
cpus = 5

# where are the dcStats NDVIArgMaxMin tifs?
NDVIArgMaxMintiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/nmdb/ndvi_argmax/"
# where should I put the results?
results ='/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/'
#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'
#Input your area of interest's name
AOI = 'nmdb'
#suffix of the 'irrigation polygons'
input_suffix = "_Irrigated_OEHandLS_masked"

#-------------------------------------------------------------

def maskArgMax(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    
    year = tif[11:15]
    nextyear = str(int(year) + 1)[2:] 
    year = year + "_" + nextyear
    year = season + year
    argmaxminyear = AOI+"_"+ year + "_ndviArgMax.tif" 

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)

    results_ = results_ + AOI + "_" + year + "/"
    
    timeofmax = xr.open_rasterio(NDVIArgMaxMintiffs+argmaxminyear).squeeze()
    transform, projection = transform_tuple(timeofmax, (timeofmax.x, timeofmax.y), epsg=3577)
    width,height = timeofmax.shape
    print("creating mask from shapefile...")
    mask_shp = results_ + AOI + "_" + year + input_suffix +".shp"
    mask = SpatialTools.rasterize_vector(mask_shp,height, width,
                                         transform, projection, raster_path=None)

    # mask timeof layers by irrigated extent
    timeofmax = timeofmax.where(mask)

    # export masked timeof layers.
    print('exporting the timeofmaxmin Gtiffs')
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_Irrigated_timeofMaxNDVI.tif",
                  timeofmax.values,
                  geo_transform = transform, 
                  projection = projection, 
                  nodata_val=-9999)

NDVIArgMaxMintiffFiles = os.listdir(NDVIArgMaxMintiffs) 
NDVIArgMaxMintiffFiles.sort()
pool = Pool(cpus)  
pool.map(maskArgMax, NDVIArgMaxMintiffFiles)
