
# coding: utf-8

# This is a complete but still being tested workflow for generating irrigated cropping extents
# 
# Go to the user inputs section and input the required info, then run the rest of the cells.
# Results will be in your results folder

# ### Libraries

# In[1]:


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
import DEAPlotting, SpatialTools, BandIndices
from load_data import load_data
from transform_tuple import transform_tuple
from imageSeg import imageSeg
from query_from_shp import query_from_shp


# ## User Inputs

# where is your data and results folder?
data = 'data/'
results = 'results/'


#If not using a polygon then enter your AOI coords
#below:
lat, lon = -35.105587, 147.354434
latLon_adjust = 0.05

#Input your area of interest's name, coords, and 
#the year you're interested in?
AOI = 'Murrumbidgee'
year = 'Summer2017-18'

time_period = ('2017-10-15', '2018-03-31')

#What thresholds should I use?
threshold = 0.8
wofs_theshold = 0.15
#-----------------------------------------


#Creating a folder to keep things neat
directory = results + AOI + "_" + year
if not os.path.exists(directory):
    os.mkdir(directory)

results = results + AOI + "_" + year + "/"


# Band Indices and Stats

#band indices calculation
def ndvi_func(nir, red):
    return ((nir - red)/(nir + red))

def ndvi_ufunc(ds):
    return xr.apply_ufunc(
        ndvi_func, ds.nir, ds.red,
        dask='parallelized',
        output_dtypes=[float])
print("calculating NDVI")
NDVI_landsat = ndvi_ufunc(landsat)

#calculate per pixel summary stats
print("calculating summary stats")
NDVI_max = NDVI_landsat.groupby('x','y').max('time').rename('NDVI_max')
NDVI_max = NDVI_max.chunk({'x':1000, 'y':1000})

transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
print("exporting MaxNDVI GTiff")
SpatialTools.array_to_geotiff(results + AOI + "_" + year + ".tif",
              NDVI_max.values, geo_transform = transform, 
              projection = projection, nodata_val=0)

# ## Image Segmentation

# setup input filename
InputNDVIStats = results + AOI + "_" + year + ".tif"
KEAFile = results + AOI + '_' + year + '.kea'
SegmentedKEAFile = results + AOI + '_' + year + '_sheperdSEG.kea'
SegmentedTiffFile = results + AOI + '_' + year + '_sheperdSEG.tif'
SegmentedPolygons = results + AOI + '_' + year + '_SEGpolygons.shp'
print("calculating imageSegmentation")
imageSeg(InputNDVIStats, KEAFile, SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons)

# ### Zonal Statistics & filtering

gdf = gpd.read_file(results + AOI + '_' + year + '_SEGpolygons.shp')
#calculate zonal mean of NDVI
print("Calculating zonal stats over the polygons")
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

#What is the area of irrigation?
ones = np.count_nonzero(~np.isnan(NDVI_max_Irrigated.values))
area = (ones*(25*25)) / 1000000
print("Around " + AOI + " during " + str(year) + ", " + str(area) + " km2 was under irrigated cultivation")

