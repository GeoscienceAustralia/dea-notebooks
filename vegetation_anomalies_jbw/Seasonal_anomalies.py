#!/usr/bin/env python
# coding: utf-8

# # Seasonal Vegetation Anomalies
# 
# 

# ## Background
# 
# Understanding how the vegetated landscape responds to longer-term environmental drivers such as the El Nino Southern Oscillation (ENSO) or climate change, requires the calculation of seasonal anomalies. Seasonal anomalies subtract the long-term seasonal mean from a time-series, thus removing seasonal variability and highlighting change related to longer-term drivers. 

# ## Description
# 
# This notebook will calculate the seasonal anomaly for any given season and year. The long-term seasonal climatologies (both mean and standard deviation) for the vegetation index `NDVI` have been pre-calculated and are stored on disk. Given an AOI, season, and year, the script will calculate the seasonal mean for one of these indices and subtract the seasonal mean from the long-term climatology, resulting in a map of standardised vegetation anomalies for your AOI.  Optionally, the script will output a geotiff of the result. 
# 
# **IMPORTANT NOTES:** 
# 
# * It is a convention to establish climatologies based on a 30-year time range to account for inter-annual and inter-decadal modes of climate variability (often 1980-2010). As the landsat archive only goes back to 1987, the climatologies here have been calculated using the date-range `1988 - 2010` (inclusive).  While this is not ideal, a 22-year climatology should suffice to capture the bulk of inter-annual and inter-decadal variability, for example, both a major El Nino (1998) and a major La Nina (2010) are captured by this time-range.
# 
# * Files & scripts for running datacube stats to calculate vegetation climatologies are located here: `'/g/data/r78/cb3058/dea-notebooks/vegetation_anomlies/dcstats'`. 
# 
# * The pre-computed climatologies are stored here: `/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/results/NSW_NDVI_climatologies_<mean>`.  The script below will use this string location to grab the data, so shifting the climatology mosaics to another location will require editing the `anomalies.py` script.
# 
# * So far, NDVI climatolgies have been produced for the full extent of NSW only. 

# ## Technical details
# 
# * **Products used:** 'ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'
# 

# ## Getting Started
# 
# To run this analysis, go to the `Analysis Parameters` section and enter the relevant details, then run all the cells in the notebook. If running the analysis multiple times, only run the `Set up dask cluster` and `import libraries` cells once.

# ## Import libraries

# In[ ]:


import xarray as xr
from datacube.helpers import write_geotiff
from datacube.utils.cog import write_cog
import matplotlib.pyplot as plt
import geopandas as gpd
import sys
import os
import datacube


sys.path.append('../Scripts')
from dea_plotting import display_map, map_shapefile
from anomalies import calculate_anomalies
from dea_datahandling import load_ard
from dea_dask import create_local_dask_cluster

# get_ipython().run_line_magic('load_ext', 'autoreload')
# get_ipython().run_line_magic('autoreload', '2')
print('Running NDVI anomaly')


# ### Set up local dask cluster
# 
# Dask will create a local cluster of cpus for running this analysis in parallel. If you'd like to see what the dask cluster is doing, click on the hyperlink that prints after you run the cell and you can watch the cluster run.

# In[ ]:

print('Creating Dask Cluster')
create_local_dask_cluster()


# ## Analysis Parameters
# 
# The following cell sets the parameters, which define the area of interest and the season to conduct the analysis over. The parameters are:
# 
# * `shp_fpath`: Provide a filepath to a shapefile that defines your AOI, if not using a shapefile then put `None` here.
# * `lat`, `lon`, `buffer`: If not using a shapefile to define the AOI, then use a latitide, longitude, and buffer to define a query 'box'.
# * `collection`: The landsat collection to load data from. either `'c3'` or `'c2'`
# * `year`: The year of interest, e.g. `'2018'`
# * `season`:  The season of interest, e.g `'DJF'`,`'JFM'`, `'FMA'` etc
# * `name` : A string value used to name the output geotiff, e.g 'NSW'
# * `dask_chunks` : dictionary of values to chunk the data using dask e.g. `{'x':3000, 'y':3000}`

# In[ ]:


shp_fpath = "data/NSW_and_ACT.shp" 
# shp_fpath="/home/156/jbw156/goFARM property boundaries for NSW DPI/goFARM property boundaries for NSW DPI/Petro Station.shp"
lat, lon, buff = -34.958, 149.281, 1
collection =  'c2'
year = '2020'
season = 'SON'
name='NSW'
dask_chunks = {'x':3000, 'y':3000}


# ## Calculate the anomaly for the AOI
# 
# For large queries (e.g > 10,000 x 10,000 pixels), the code will take several minutes to run.  Queries larger than ~25,000 x 25,000 pixels may start to fail due to memory limitations (several (42,000 x 35,000 x 52) runs covering all of NSW has been successfully run on the VDI). Check the x,y dimensions in the lazily loaded output to get idea of how big your result will be before you run  the `.compute()` cell.

print('Lazy Load...')
anomalies,obs = calculate_anomalies(shp_fpath=shp_fpath,
                                    query_box=(lat,lon,buff),
                                    collection=collection,
                                    year=year,
                                    season=season,
                                    dask_chunks=dask_chunks)


print('Computing anomalies...')
anomalies = anomalies.compute()


# write_geotiff('results/computed_anomalies/ndvi_' +year+season+'_'+name+'_standardised_anomalies.tif', anomalies)
print('Writing anomalies to tif')
anomaliesA=anomalies.to_array()
if collection == 'c2':
    write_cog(geo_im=anomaliesA,fname='results/computed_anomalies/ndvi_c2_' +year+season+'_'+name+'_standardised_anomalies.tif', overwrite=True)
if collection == 'c3':
    write_cog(geo_im=anomaliesA,fname='results/computed_anomalies/ndvi_c3_' +year+season+'_'+name+'_standardised_anomalies.tif', overwrite=True)
    
print('writing last observation')  
lastobs=obs.to_dataframe()
lastobs.to_csv('results/computed_anomalies/'+year+season+'_NDVIanom_timestamps.csv',index=False)




