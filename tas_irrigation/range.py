

#import libraries
import xarray as xr
import datacube
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import numpy as np
import dask
import geopandas as gpd
from datacube.drivers.netcdf import write_dataset_to_netcdf
from datacube.helpers import write_geotiff
from dask.distributed import Client
from src import DEADataHandling
from multiprocessing import Pool

import warnings
warnings.filterwarnings("ignore")

#!!!!!!!!!!!!!!
# USER INPUTS
#!!!!!!!!!!!!!
start = 2000
end = 2004
shp_fpath = "/g/data/r78/cb3058/dea-notebooks/tas_irrigation/data/IrrigationDistrict.shp"
ncpus = 2


#---functions-------------------------------------------------------------------------------

def query_from_shp(shp_fpath, start_date, end_date, dask_chunks = 0):
    """
    Uses the extent of a polygon to create a bounding
    box, then generates a query object for the datcube
    """
    #import project area shapefiles
    project_area = gpd.read_file(shp_fpath)

    #convert the shapefile to GDA94 lat-long coords so we can query dc_load using lat long
    project_area['geometry'] = project_area['geometry'].to_crs(epsg=4283)

    #find the bounding box that contains all the queried projects
    x = project_area.total_bounds
    #longitude
    ind = [0,2]
    extent_long = x[ind]  
    extent_long = tuple(extent_long)
    #latitude
    ind1 = [1,3]
    extent_lat = x[ind1] 
    extent_lat = tuple(extent_lat)

    #datacube query is created
    query = {'time': (start_date, end_date),}
    query['x'] = extent_long
    query['y'] = extent_lat
    if dask_chunks != 0:
        query['dask_chunks']= {'x': dask_chunks, 'y': dask_chunks} 
        return query
    return query

def compute_range(time):
    print("working on "+ time[0][:-3])
    query = query_from_shp(shp_fpath, time[0], time[1])

    ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, sensors=['ls5','ls7','ls8'],  product='nbart',
                                       bands_of_interest=['nir', 'red'],mask_pixel_quality=True,
                                       mask_invalid_data=True)

    ndvi = ((ds.nir - ds.red)/(ds.nir + ds.red))
    min_ndvi = ndvi.min('time')
    max_ndvi = ndvi.max('time')
    range_ndvi = max_ndvi - min_ndvi

    range_ndvi = range_ndvi.rename('ndvi_range').to_dataset()
    range_ndvi.attrs = ds.attrs
    range_ndvi.attrs['units'] = 1
    range_ndvi.ndvi_range.attrs = ds.attrs
    range_ndvi.ndvi_range.attrs['units'] = 1

    write_geotiff("data/ndvi_range/ndvi_range_" + time[0][:-3] +'.tif', range_ndvi)
    
    ds = None
    ndvi=None
    min_ndvi=None
    max_ndvi=None
    range_ndvi=None
    

#---------run code-------------------------------------------------------------------------

dc = datacube.Datacube(app='ndvi_range')

x = []
for i in range(start, end):
    x.append((str(i)+'-01', str(i)+'-12'))

for i in x:
    compute_range(i)    
# p = Pool(ncpus)
# p.map(compute_range, x) # MULTIPROCESS
