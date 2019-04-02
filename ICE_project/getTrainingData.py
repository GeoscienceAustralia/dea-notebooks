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
import DEAPlotting, SpatialTools, BandIndices, DEADataHandling
from load_data import load_data
from transform_tuple import transform_tuple
from imageSeg import imageSeg
from query_from_shp import query_from_shp

# where is your data and results folder?
data = 'data/'
results = 'results/'
shp_fpath = shp_fpath = 'data/spatial/murrumbidgee_catchment.shp'

#Input your area of interest's name, coords, and 
#the year you're interested in?
AOI = 'training'
year = 'winter'

time_period = ('2016-04-01', '2016-05-31')

#Creating a folder to keep things neat
directory = results + AOI + "_" + year
if not os.path.exists(directory):
    os.mkdir(directory)

results = results + AOI + "_" + year + "/"


query = query_from_shp(shp_fpath, time_period[0], time_period[1], dask_chunks = 0)
query['resolution'] = (-25,25)
query['output_crs'] = ('epsg:3577')

dc = datacube.Datacube(app='load_clearsentinel')
#landsat
landsat = DEADataHandling.load_clearlandsat(dc=dc, query=query,sensors=['ls8'], 
                        bands_of_interest=['red', 'green', 'blue'],
                        masked_prop=0.2, mask_pixel_quality=True)

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

landsat = landsat.drop('data_perc') 

DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160401.tif', landsat.isel(time=0))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160409.tif', landsat.isel(time=1))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160417.tif', landsat.isel(time=2))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160423.tif', landsat.isel(time=3))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160425.tif', landsat.isel(time=4))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160503.tif', landsat.isel(time=5))
DEADataHandling.dataset_to_geotiff(results+'murrumbidgee20160527.tif', landsat.isel(time=6))