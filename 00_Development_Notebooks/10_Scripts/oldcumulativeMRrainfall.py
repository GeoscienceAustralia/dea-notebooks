## RainfallTools.py

'''RainfallTools contains a set of python functions for working with rainfall data.
Available functions:
    load_rainfall
    calculate_residual_mass_curve
    
Last modified: October 2018
Authors: Bex Dunn, Vanessa Newey, Neil Symington, Claire Krause  
    
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

def calculate_residual_mass_curve(a):
    '''This function calculates the residual mass rainfall curve
    :param a:  '''
    
    #resample rainfall data to month start
    a = a.resample('MS', dim='time', how='sum', keep_attrs=True) 
    # find the number of time steps (ie. years)
    n = len(a.rainfall.time)/12
    
    # First calculate a cumulative rainfall xarray from the rainfall data
    
    arr = a.rainfall.values
    
    cum_rf = np.cumsum(arr, axis = 0)
    
    cum_rf_xr = xr.DataArray(cum_rf, dims = ('time', 'latitude', 'longitude'),
                            coords = [a.time, a.latitude, a.longitude])
    
    # NOw we will calculate a cumulative rainfall assuming average rainfall on a month by month basis
    # Find the average of all months
    ave_months = a.rainfall.groupby('time.month').mean('time').values
   
    # In the case that we are not starting from January we will need to reorder the array
    
    start_month = a.time[0].dt.month.values - 1
    
    ave_month = np.concatenate((ave_months[start_month:,:,:], ave_months[0:start_month,:,:]), axis = 0)

    
    # Tile an array so that we can run a cumulative sum on it
    tiled_ave = np.tile(ave_months, (round(n), 1, 1))
    
    # In the case that we have residual months remove them from the tiled array
    if (n).is_integer() == False:
        month_remainder = int(round((n%1) * 12))

        tiled_ave = tiled_ave[:int(-month_remainder),:,:]
        
    # Generate the cumulative sum of rainfall one would get assuming average rainfall every month
    cum_ave = np.cumsum(tiled_ave, axis = 0)
    
    cum_ave_xr = xr.DataArray(cum_ave, dims = ('time', 'latitude', 'longitude'),
                              coords = [a.time, a.latitude, a.longitude])
    
    # The mass residual curve is the difference between the cumulative rainfall data and the cumulative
    # rainfall one would get iff the average always occured
    mass_res_curve = cum_rf_xr - cum_ave_xr
    
    return mass_res_curve
