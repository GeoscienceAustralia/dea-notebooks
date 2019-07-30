from datacube.storage import masking
from datacube.helpers import write_geotiff
from datacube import Datacube
from datetime import datetime
from skimage import exposure
import numpy as np

import datacube
import datetime
import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio.mask
import rasterio.features
from shapely import geometry
import seaborn as sns
import sys
import xarray as xr

import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from datacube.storage import masking
from datacube.utils import geometry
from datacube.helpers import ga_pq_fuser, write_geotiff

import sys
import os

###FIXME: this is for getting s2 to write to geotiff
import rasterio

# Point this to where you have the algorithms from the dea-notebooks/algorithms saved
sys.path.append('../../10_Scripts')
import DEADataHandling, DEAPlotting, TasseledCapTools

dc = Datacube(app='Sentinel2')

#change the path here if you want a different polygon
#poly_path = '/g/data/r78/rjd547/shapefiles/EnvironmentalFlowMonitoringPolygon.shp'
poly_path = '/g/data/r78/rjd547/shapefiles/FarmScaleWaterBalancePolygon.shp'

#open the polygon
with fiona.open(poly_path) as shapes:
        crs = geometry.CRS(shapes.crs_wkt)
        first_geometry = next(iter(shapes))['geometry']
        geom = geometry.Geometry(first_geometry, crs=crs)

shape_file = poly_path
GEOM, SHAPE_NAME = DEADataHandling.open_polygon_from_shapefile(shape_file)
#start_of_epoch, end_of_epoch=('2018-05-01', '2018-07-31')

query = {
   'time': ('2016-10-01', '2017-04-30'), 
  # 'time': (start_of_epoch, end_of_epoch), 
    'geopolygon': GEOM,
    'output_crs': 'EPSG:3577',
    'resolution': (-10, 10)
}
#load in data
s2= dc.load(product='s2b_ard_granule', group_by='solar_day', 
                   measurements=['fmask', 
                             'nbart_blue', 
                             'nbart_green', 
                             'nbart_red', 
                             'nbart_red_edge_1',
                             'nbart_red_edge_2',
                             'nbart_red_edge_3',
                             'nbart_nir_1',
                             'nbart_nir_2',
                             'nbart_swir_2',
                             'nbart_swir_3'], **query)
#### See what came back from the extraction
s2
ds=s2
#get polygon name from the polygon path
polyname = poly_path.split('/')[-1].split('.')[0]
savefilepath = '/g/data/r78/rjd547/WaterCompHackFeb2019/Sentinel2Data/'+polyname
filename=savefilepath
#### this is a really annoying kludge to deal with the fact that new sentinel data has multiple data types and the functions were not written to cope
ds
## Sneakily force fmask layer to int16 type
#ds['fmask']=ds['fmask'].astype(np.int16)
ds
###Note: I munged this to change the datatype for S2
def dataset_to_geotiff2(filename, data):
    # Depreciation warning for write_geotiff
    print("This function will be superceded by the 'write_geotiff' function from 'datacube.helpers'. "
          "Please revise your notebooks to use this function instead")
    kwargs = {'driver': 'GTiff',
              'count': len(data.data_vars),  # geomedian no time dim
              'width': data.sizes['x'], 'height': data.sizes['y'],
              'crs': data.crs.crs_str,
              'transform': data.affine,
              'dtype': list(data.data_vars.values())[0].values.dtype,
              'nodata': 0,
              'compress': 'deflate', 'zlevel': 4, 'predictor': 2}
    # for ints use 2 for floats use 3}
    with rasterio.open(filename, 'w', **kwargs) as src:
        for i, band in enumerate(data.data_vars):
            src.write(data[band].data, i + 1)
### write the list of bands to a textfile
band_list =[]
with open(filename+'band_list_s2.txt','w') as outfile: 
    for i, band in enumerate(ds.data_vars):
        #print(str(f'{i+1} {band} \n'))
        outfile.write(str(f'{i+1} {band} \n'))
        #band_list.append([i+1,band])
    #print(band_list)    
### Write each date to a separate geotiff
print(filename)
#print the dates for which we have imagery and write to file
for i in range(len(ds.time)):
    date_s2 = str(ds.isel(time=i).time.data)[:-19]
    filename2='{}s2b_{}.tif'.format(filename,date_s2)
    print(date_s2)
    dataset_to_geotiff2(filename2, ds.isel(time=i))
