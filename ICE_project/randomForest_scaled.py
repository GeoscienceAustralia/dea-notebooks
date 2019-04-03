
# coding: utf-8

# In[1]:


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

#USER INPUTS

# where is your data and results folder?
results = "results/"
data = "/g/data1a/r78/cb3058/dea-notebooks/ICE_project/data/datacube_stats/Murrumbidgee/stats/winter_1990_2018/"

#Input your area of interest's name
#the year you're interested in?
AOI = 'Murrum_RF_scaled'
year = "20170501"

ncpus=32

#-----------------------------------------

#Creating a folder to keep things neat
directory = results + AOI + "_" + year
if not os.path.exists(directory):
    os.mkdir(directory)

results = results + AOI + "_" + year + "/"


#Bring in GTiffs generated using datacube stats
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
             NDMI_max, NDMI_mean, NDMI_std, NDMI_min, NDVI_range, timeofmax, timeofmin, rate,
             brightness_max, brightness_mean, brightness_std, brightness_std]
names = ['NDVI_max', 'NDVI_mean', 'NDVI_std', 'NDVI_min', 'NDVI_range',
         'NDMI_max', 'NDMI_mean', 'NDMI_std', 'NDMI_min','NDMI_range',
         'timeofmax', 'timeofmin','rate', 'brightness_max', 'brightness_mean', 'brightness_std', 'brightness_std']


# ### Image segmentation for use in masking AFTER the RF classifier

#export Gtiff for use in Image segmentation
transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
SpatialTools.array_to_geotiff(results + AOI + "_" + year + "_NDVI_max.tif",
              green_max.values, geo_transform = transform, 
              projection = projection, nodata_val=np.nan)


InputNDVIStats = results + AOI + "_" + year + "_NDVI_max.tif"
KEAFile = results + AOI + '_' + year + '.kea'
SegmentedKEAFile = results + AOI + '_' + year + '_sheperdSEG.kea'
SegmentedTiffFile = results + AOI + '_' + year + '_sheperdSEG.tif'
SegmentedPolygons = results + AOI + '_' + year + '_SEGpolygons.shp'
imageSeg(InputNDVIStats, KEAFile, SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons, minPxls = 100)

#grab the training data and prepare it
trainingSet = gpd.read_file("/g/data1a/r78/cb3058/dea-notebooks/ICE_project/data/spatial/murrumbidgee_randomTraining_samples.shp")
trainingSet = trainingSet.to_crs(epsg=3577)
trainingSet = trainingSet[['Id', 'geometry']]
trainingSet = trainingSet.replace([330,133,541], 10) #reclasss so we can do a binary classification
trainingSet.to_file(results + "trainingset_ready.shp")

#get the transform and projection of our gtiff
transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
#find the width and height of the xarray dataset we want to mask
width,height = NDVI_max.shape
# rasterize vector
training_set = SpatialTools.rasterize_vector(results + "trainingset_ready.shp",
               height, width, transform, projection, field='Id',raster_path= results + AOI + "_" + year +'training_raster.tif')

k = xr.open_rasterio(results + AOI + "_" + year +'training_raster.tif')
k = k.squeeze()
classes = np.unique(k)
for c in classes:
    print('Class {c} contains {n} pixels'.format(c=c,n=(training_set == c).sum()))

# Read in our training data
roi_ds = gdal.Open(results + AOI + "_" + year +'training_raster.tif', gdal.GA_ReadOnly)
roi = roi_ds.GetRasterBand(1).ReadAsArray().astype(np.uint16)

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

# use this cell if importing .npy file
# img = np.load(results + 'img.npy')

# Find how many non-zero entries we have
n_samples = (roi > 0).sum()
print('We have {n} samples'.format(n=n_samples))

# What are our classification labels?
labels = np.unique(roi[roi > 0])
print('The training data include {n} classes: {classes}'.format(n=labels.size, 
                                                                classes=labels))
x = img[roi > 0,:]
y = roi[roi > 0]

print('Our x matrix is sized: {sz}'.format(sz=x.shape))
print('Our y array is sized: {sz}'.format(sz=y.shape))

from sklearn.ensemble import RandomForestClassifier
# Initialize our model with 300 trees
rf = RandomForestClassifier(n_estimators=400, oob_score=True, verbose=True,
                            n_jobs=ncpus, max_features="auto") #auto = sqrt(n_features)

# Fit our model to training data
rf = rf.fit(x, y)

#save the model
from joblib import dump, load
dump(rf, results + 'murrumbidgee_rfModel_binary.joblib')

print('Our OOB prediction of accuracy is: {oob}%'.format(oob=rf.oob_score_ * 100))

#display the importance of the individual bands
for b, imp in zip(names, rf.feature_importances_):
    print('Band {b} importance: {imp}'.format(b=b, imp=imp))

# Create a cross-tabulation dataframe to check out how each class performs
df = pd.DataFrame()
df['truth'] = y
df['predict'] = rf.predict(x)

# Cross-tabulate predictions
print(pd.crosstab(df['truth'], df['predict'], margins=True))


