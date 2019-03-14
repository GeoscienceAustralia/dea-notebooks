
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

# In[2]:


# where is your data and results folder?
data = 'data/'
results = 'results/'

#do I need to load in new data from the datacube
#or have you already saved it previously?
load_fresh_data = True

sensors = ['ls5', 'ls7', 'ls8']

#are we using a polygon to mask the AOI?
polygon_mask = True
shp_fpath = 'data/spatial/murrumbidgee_catchment.shp'

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


# ## load data

# In[3]:


#load landsat data    
if load_fresh_data == True:
    if polygon_mask == True:
        #set up query
        query = query_from_shp(shp_fpath, time_period[0], time_period[1], dask_chunks = 1000)
        print("I'm using a shapefile for dc.load")
        #landsat
        landsat = load_data(dc_name = 'irrigated_areas', sensors=sensors, 
                  export_name = data + AOI + "_" + year + '.nc', query=query)
        #wofs
        dc = datacube.Datacube(app='wofs')
        del query['time'] 
        wofs_alltime = dc.load(product = 'wofs_summary', **query)
        
        #masking the returned array to the polygon area
        with fiona.open(shp_fpath) as shapes:
                crs = geometry.CRS(shapes.crs_wkt)
                first_geometry = next(iter(shapes))['geometry']
                geom = geometry.Geometry(first_geometry, crs=crs)

        mask = rasterio.features.geometry_mask([geom.to_crs(landsat.geobox.crs) for geoms in [geom]],
                                                   out_shape=landsat.geobox.shape,
                                                   transform=landsat.geobox.affine,
                                                   all_touched=False,
                                                   invert=True)
        # Mask the xarrays
        landsat = landsat.where(mask)
        wofs_alltime = wofs_alltime.where(mask)
    else:
        # Set up query
        query = {'lon': (lon - latLon_adjust, lon + latLon_adjust),
                 'lat': (lat - latLon_adjust, lat + latLon_adjust),
                 'time': time_period}
        #landsat
        landsat = load_data(dc_name = 'irrigated_areas', sensors=sensors,
                  export_name = data + AOI + "_" + year + '.nc', query=query)
        #wofs
        dc = datacube.Datacube(app='wofs')
        del query['time'] 
        wofs_alltime = dc.load(product = 'wofs_summary', **query)
        
else:
    #load in data from saved netcdf file
    landsat = xr.open_dataset("data/wagga_Summer2017-18.nc")
    
    #landsat = xr.open_dataset('data/' + AOI +  "_" + year + '.nc')
    #load wofs for masking
    query_wofs = {'lon': (lon - latLon_adjust, lon + latLon_adjust),
                 'lat': (lat - latLon_adjust, lat + latLon_adjust)} 
    dc = datacube.Datacube(app='wofs')
    wofs_alltime = dc.load(product = 'wofs_summary', **query_wofs)


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


# ## Masking

#get the transform and projection of our gtiff
transform, projection = transform_tuple(NDVI_max, (NDVI_max.x, NDVI_max.y), epsg=3577)
#find the width and height of the xarray dataset we want to mask
width,height = NDVI_max.shape
# rasterize vector
gdf_raster = SpatialTools.rasterize_vector(results + AOI + "_" + year + "_Irrigated.shp",
                                           height, width, transform, projection, raster_path=None)
# Mask the xarray
NDVI_max_Irrigated = NDVI_max.where(gdf_raster)


# ## Reclassify & raster math

# In[ ]:


#remove areas below our threshold that are at the edges of the rasterized polygons
NDVI_max_Irrigated = NDVI_max_Irrigated.where(NDVI_max_Irrigated >= threshold)
#Use wofs to remove areas that have standing water for a significant amount of time
NDVI_max_Irrigated = NDVI_max_Irrigated.where(wofs_alltime.frequency.drop('time').squeeze() <= wofs_theshold)

#remove pixels that cross over the major rivers in the region
rivers_raster = SpatialTools.rasterize_vector("data/spatial/major_rivers_aus.shp", height, width, transform, projection, raster_path=None)
rivers_raster = rivers_raster.astype(bool)
rivers_raster = xr.DataArray(rivers_raster, coords = [NDVI_max.y, NDVI_max.x], dims = ['y', 'x'], name='rivers')
NDVI_max_Irrigated = NDVI_max_Irrigated.where(rivers_raster == 0)


#What is the area of irrigation?
ones = np.count_nonzero(~np.isnan(NDVI_max_Irrigated.values))
area = (ones*(25*25)) / 1000000
print("Around " + AOI + " during " + str(year) + ", " + str(area) + " km2 was under irrigated cultivation")

# ## export results as GTiff

SpatialTools.array_to_geotiff(results + AOI + "_" + year + "_Irrigated.tif",
              NDVI_max_Irrigated.values,
              geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

