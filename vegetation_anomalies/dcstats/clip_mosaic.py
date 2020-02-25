

import numpy as np
import xarray as xr
import os
from multiprocessing import Pool, cpu_count
from osgeo import gdal, ogr
import geopandas as gpd
from datacube.helpers import write_geotiff

#import custom functions
import sys
sys.path.append("../Scripts")
from dea_spatialtools import xr_rasterize

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
cpus = 4

# where are the dcStats mosaics tifs?
tiffs = "/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/results/NSW_NDVI_Climatologies_std/mosaics/"

#Shapefile we're using for clipping the extent? e.g.NSW state polygon
clip_shp = "/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/data/NSW_and_ACT.shp"

# where should I put the results?
results = "/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/results/NSW_NDVI_Climatologies_std/mosaics/"

# script proper-----------------------------

def clip_extent(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    #limiting the extent to the shapefile
    print('clipping extent to provided polygon')
    ds = xr.open_rasterio(tiffs + tif).squeeze()
    
    #load shapefile
    gdf = gpd.read_file(clip_shp)
    gdf = gdf.to_crs({'init': 'epsg:3577'})
    
    #rasterize shapeile
    mask = xr_rasterize(gdf=gdf,
                         da=ds)
    
    #clip to shapeile extent
    clipped_ds = ds.where(mask)
    
    #export results
    clipped_ds = clipped_ds.to_dataset(name = 'data')
    clipped_ds['data'].attrs = ds.attrs 
    clipped_ds.attrs = ds.attrs
    
    write_geotiff(results+tif[:-11]+'.tif', clipped_ds) 
    
list_of_tifs = os.listdir(tiffs)    
list_of_tifs.sort()

pool = Pool(cpus)  
pool.map(clip_extent, list_of_tifs)