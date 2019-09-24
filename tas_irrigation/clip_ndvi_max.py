
"""
This script will clip a list of geotiffs to the extent of a shapefile
Code is multiprocessed so will conduct the analysis across n number of
specified cpus. Adjust the user inputs, and then run the script
through the terminal:
 
 python3 clip_ndvi_map.py
 
NOTE: Look out for the string slicing on line 59, this can throw
    errors if the filenames are different from those I've specified.

"""


import numpy as np
import xarray as xr
import os
from multiprocessing import Pool, cpu_count
from osgeo import gdal, ogr

#import custom functions
import sys
sys.path.append('src')
import SpatialTools

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
cpus = 4

# where are the MaxNDVI tifs?
MaxNDVItiffs = "data/ndvi_max/""

#Shapefile we're using for clipping the extent?
clip_shp = "data/IrrigableLand.shp"

# where should I put the results?
results = "data/ndvi_max_NE/"

#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'

#Input your area of interest's name
AOI = 'tasNE'

# script proper-----------------------------

def clip_extent(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    #reset the results string
    results_ = results
    
    year = tif[9:13]
    nextyear = str(int(year) + 1)[2:] 
    year = year + "_" + nextyear
    year = season + year

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)

    results_ = results_ + AOI + "_" + year + "/"
    
    #open the geotiff
    NDVI_max = xr.open_rasterio(MaxNDVItiffs + tif).squeeze()
    #get the projection info and coords
    transform, projection = SpatialTools.geotransform(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
    width,height = NDVI_max.shape
    #rasterize the vector
    clip_raster = SpatialTools.rasterize_vector(clip_shp, height, width,
                                                transform, projection, raster_path=None)
    #mask and remove nans
    NDVI_max = NDVI_max.where(clip_raster)
    NDVI_max = NDVI_max.dropna(dim='x', how='all').dropna(dim='y', how='all') #get rid of all-nans
    
    #get new transform info
    transform, projection = SpatialTools.geotransform(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
    
    #exoprt clipped geotiff
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_NDVI_max.tif",
          NDVI_max.values,
          geo_transform = transform, 
          projection = projection, 
          nodata_val = np.nan)
    print("finished exporting " + tif)

maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
maxNDVItiffFiles.sort()

#multithread function
pool = Pool(cpus)  
pool.map(clip_extent, maxNDVItiffFiles)