
"""
 This script produces an MSAVI seasonal anomaly timeseries for an area equal to the total
 bounds of a specified shapefile.  The anomaly is based on the seasonal mean of all input time 
 steps.  The job is parallized with Dask. Go to the user inputs section and enter the relevant
 info.

"""


#import libraries
import numpy as np
import xarray as xr
import datacube 
import dask
from dask.distributed import Client, LocalCluster
import logging
import sys
sys.path.append('src')
# import lazily_load_clearlandsat as llcLS
import DEADataHandling
import query_from_shp

#!!!!!!!!!!!!!!
# USER INPUTS
#!!!!!!!!!!!!!
start = '1987-12-01'
end = '2019-05-31'
shp_fpath = "/g/data/r78/cb3058/dea-notebooks/dcStats/data/spatial/griffith_MSAVI_test.shp"
chunk_size = 500
cpus = 12
memory_per_cpu = '30GB'
results = 'results/test_standardised_anomaly_big.nc'

lat, lon = -34.294, 146.037
latLon_adjust = 0.5

#-------------------------------------------------------------------------
#Functions for script

def compute_seasonal(data, output_dir):
    #Scale reflectance values to 0-1
    nir = data.nir / 10000
    red = data.red / 10000
    #calculate msavi
    msavi = (2*nir+1-((2*nir+1)**2 - 8*(nir-red))**0.5)/2
    msavi = msavi.astype('float32') #convert to reduce memory
    #resample to quarterly and groupby seasons
    msavi_seasonalMeans = msavi.resample(time='QS-DEC').mean('time')
    msavi_seasonalMeans = msavi_seasonalMeans.groupby('time.season')
    #calculate climatologies
    climatology_mean = msavi.groupby('time.season').mean('time')
    climatology_std = msavi.groupby('time.season').std('time')
    #calculate standardised anomalies
    msavi_stand_anomalies = xr.apply_ufunc(lambda x, m, s: (x - m) / s,
                                 msavi_seasonalMeans, climatology_mean, climatology_std,
                                 dask='allowed')
    #write out results (will compute now)
    msavi_stand_anomalies.to_netcdf(output_dir, format='netCDF4')

#-------------------------------------------------------------------------------------
print('starting')

if __name__ == '__main__':
    
    with LocalCluster(n_workers=cpus, threads_per_worker=1) as cluster:
        with Client(cluster, memory_limit=memory_per_cpu) as client:
            
            # trying to suppress 'garbage collector' warnings from distributed
            # and 'divide' warnings from numpy
            logger = logging.getLogger("distributed.utils_perf")
            logger.setLevel(logging.ERROR)
            np.seterr(divide='ignore', invalid='ignore')
            
            # create query and load data
            query = {'lon': (lon - latLon_adjust, lon + latLon_adjust),
                     'lat': (lat - latLon_adjust, lat + latLon_adjust),
                     'time': (start, end)}
            dc = datacube.Datacube(app='load_clearlandsat')
            ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, sensors=['ls5','ls7','ls8'], 
                                                   bands_of_interest=['nir', 'red'], lazy_load=True,
                                                   dask_chunks = {'x': chunk_size, 'y': chunk_size}, 
                                                   masked_prop=0.25, mask_pixel_quality=True,
                                                   mask_invalid_data=False)
            #lazily compute anomalies
            compute_seasonal(ds, results)
            

            
