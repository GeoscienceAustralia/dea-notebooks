

import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
from osgeo import gdal, ogr, gdal_array
import dask
import datacube 
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube.utils import geometry
import os
#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools, BandIndices, DEADataHandling
from load_data import load_data
from transform_tuple import transform_tuple
from query_from_shp import query_from_shp
from rsgislib.segmentation import segutils
from rasterstats import zonal_stats
from imageSeg import imageSeg
import fiona
import rasterio.features

import warnings
warnings.filterwarnings('ignore')


# where is your data and results folder?
results = "results/"
data = "/g/data1a/r78/cb3058/dea-notebooks/ICE_project/data/datacube_stats/Murrumbidgee/stats/winter_1990_2018/"

#Input your area of interest's name, coords, and 
#the year you're interested in?
AOI = 'Murrum_RF_scaled'
year = '20170501'

rfmodel = "murrumbidgee_rfModel_binary.joblib"
#-----------------------------------------


#Creating a folder to keep things neat
directory = results + AOI + "_" + year
if not os.path.exists(directory):
    os.mkdir(directory)

results = results + AOI + "_" + year + "/"


#Bring in Gtiff from datcube stats results
ndmi_stats = xr.open_rasterio(data + "ndmi_stats_" + year + ".tif")
ndmi_stats = ndmi_stats.where(ndmi_stats>0, np.nan) #change nodata value to np.nan to be consistent
ndvi_stats = xr.open_rasterio(data + "ndvi_stats_" + year + ".tif")
ndvi_stats = ndmi_stats.where(ndvi_stats>0, np.nan) 

brightness_stats = xr.open_rasterio(data + "brightness_stats_" + year + ".tif")
brightness_stats = brightness_stats.where(brightness_stats>0, np.nan)

rate_stats = xr.open_rasterio(data + "rate_" + year + ".tif")
rate_stats = rate_stats.where(rate_stats!= -9999.0, np.nan)

NDMI_min = ndmi_stats[0]
NDMI_max = ndmi_stats[1]
NDMI_mean = ndmi_stats[2]
NDMI_std = ndmi_stats[3]
NDMI_range = NDMI_max - NDMI_min

NDVI_min = ndvi_stats[0]
NDVI_max = ndvi_stats[1]
NDVI_mean = ndvi_stats[2]
NDVI_std = ndvi_stats[3]
NDMI_range = NDVI_max - NDVI_min

brightness_min = brightness_stats[0]
brightness_max = brightness_stats[1]
brightness_mean = brightness_stats[2]
brightness_std = brightness_stats[3]

rate = rate_stats[0]
timeofmax = rate_stats[1]
timeofmin = rate_stats[2]

#add to a list 
xray_list = [NDVI_max, NDVI_mean, NDVI_std, NDVI_min, NDVI_range,
             NDMI_max, NDMI_mean, NDMI_std, NDMI_min,timeofmax, timeofmin, rate,
             brightness_max, brightness_mean, brightness_std, brightness_std]
names = ['NDVI_max', 'NDVI_mean', 'NDVI_std', 'NDVI_min', 'NDVI_range',
         'NDMI_max', 'NDMI_mean', 'NDMI_std', 'NDMI_min','timeofmax', 'timeofmin','rate',
            'brightness_max', 'brightness_mean', 'brightness_std', 'brightness_std']


#convert to numpy arrays
x,y = NDVI_max.shape
z = len(xray_list)
img = np.zeros((x,y,z))
count=0
for b,c in zip(xray_list, range(img.shape[2])):
    count += 1
    progress = round((count/z) * 100, 3)
    print("\r", "adding slice: " + str(count) + ", " + str(progress) + "%" + " complete. ", end = '')
    img[:, :, c] = b.values 
    
img[np.isnan(img)]=-999. #remove nans as they f/w classifier
np.save(results + 'img.npy', img) #save it as binary file

# load back in the trained RF model:
from joblib import load
rf = load(results + rf_model)

# Take our full image, and reshape into long 2d array (nrow * ncol, nband) for classification
new_shape = (img.shape[0] * img.shape[1], img.shape[2])

img_as_array = img[:, :, :z].reshape(new_shape)
print('Reshaped from {o} to {n}'.format(o=img.shape,
                                        n=img.shape))

# Now predict for each pixel
print('generating prediction')
class_prediction = rf.predict(img_as_array)

# Reshape our classification map
class_prediction = class_prediction.reshape(img[:, :, 0].shape)
# class_prediction=np.where(class_prediction==10, 0, 1) #turn into a binary

#export out the results
print('exporting class_predict GTiff')
transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
SpatialTools.array_to_geotiff(results + AOI + "_" + year + "classpredict.tif",
              class_prediction, geo_transform = transform, 
              projection = projection, nodata_val=0)

#export eroded classified image
from scipy.ndimage import morphology
x=np.where(class_prediction==10, 0, 1)
y = morphology.binary_erosion(x)
SpatialTools.array_to_geotiff(results + AOI + "_" + year + "classpredict_binaryeroded.tif",
              y, geo_transform = transform, 
              projection = projection, nodata_val=0)

#using image seg to mask
class_predict = xr.open_rasterio(results + AOI + "_" + year + "classpredict.tif")
class_predict = class_predict.squeeze()

gdf = gpd.read_file(results + AOI + '_' + year + '_SEGpolygons.shp')
gdf['majority'] = pd.DataFrame(zonal_stats(vectors=gdf['geometry'], raster=results + AOI + "_" + year + "classpredict.tif", stats='majority'))['majority']
gdf['area'] = gdf['geometry'].area
smallArea = gdf['area'] <= 5500000
irrigated = gdf['majority'] == 430.0 #filtering for irrigated areas only
gdf = gdf[smallArea&irrigated]
#export shapefile
gdf.to_file(results + AOI + "_" + year + "_Irrigated.shp")

# #get the transform and projection of our gtiff
# transform, projection = transform_tuple(class_predict, (class_predict.x, class_predict.y), epsg=3577)
# #find the width and height of the xarray dataset we want to mask
# width,height = class_predict.shape
# # rasterize vector
# gdf_raster = SpatialTools.rasterize_vector(results + AOI + "_" + year + "_Irrigated.shp",
#                                            height, width, transform, projection, raster_path=results + AOI + "_" + year + "_Irrigated.tif")

print('success')