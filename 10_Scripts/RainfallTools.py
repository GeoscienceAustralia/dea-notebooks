## RainfallTools.py

'''RainfallTools contains a set of python functions for working with rainfall data.
Available functions:
    load_rainfall
    
Last modified: October 2018
Authors: Bex Dunn, Vanessa Newey 
    
'''
import datacube
import numpy as np
import xarray as xr

def load_rainfall(query):
    ''' Loads the rainfall grids from 1901 to the most recent from the staging database,
    pending the official publication of gridded rainfall data by BoM. 
    Last modified: Oct 2018
    Author: Vanessa Newey'''
    
    dc_rf =datacube.Datacube(config='/g/data/r78/bom_grids/rainfall.conf')
    
    rf_data = dc_rf.load(product = 'rainfall_grids_1901_2017',align=(0.025,0.027), **query)
    print('These rainfall grids have been realigned by the load_rainfall function - if you think this ',
          ' may be incorrect then check your data and metadata then contact BDunn or VNewey'
    return rf_data