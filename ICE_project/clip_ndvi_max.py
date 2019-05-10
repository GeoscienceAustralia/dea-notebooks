import numpy as np
import xarray as xr
import os
from multiprocessing import Pool, cpu_count

#import custom functions
import sys
sys.path.append('src')
import SpatialTools
from transform_tuple import transform_tuple

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
cpus = 4

# where are the dcStats MaxNDVI tifs?
MaxNDVItiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/ndvi_max/mosaics/"

#Shapefile we're using for clipping the extent? e.g. just the northern basins
clip_shp = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/renmark.shp"

# where should I put the results?
results = '/g/data/r78/cb3058/dea-notebooks/dcStats/results/renmark_test/'

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
        year = tif[9:13]
        nextyear = str(int(year) + 1)[2:] 
        year = year + "_" + nextyear
        year = season + year

    if season == 'Winter':
        year = tif[7:11]
        year = season + year

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

    clip_raster = SpatialTools.rasterize_vector(clip_shp, height, width,
                                                transform, projection, raster_path=None)
    #mask and remove nans
    NDVI_max = NDVI_max.where(clip_raster)
    NDVI_max = NDVI_max.dropna(dim='x', how='all').dropna(dim='y', how='all') #get rid of all-nan row,cols
    #get new transform info
    transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
    width,height = NDVI_max.shape
    
    print("exporting clipped ndvi_max geotiff")
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_NDVI_max.tif",
          NDVI_max.values,
          geo_transform = transform, 
          projection = projection, 
          nodata_val = np.nan)
    print("finished exporting " + tif)

maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
pool = Pool(cpus)  
pool.map(irrigated_extent, maxNDVItiffFiles)