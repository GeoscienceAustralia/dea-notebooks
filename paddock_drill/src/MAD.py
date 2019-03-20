from statsmodels import robust
import numpy as np
import xarray as xr

def MAD(xarray, coords_label = ('x', 'y') , c=0.6745):
    """
    Calculate the per pixel median absolute deviation 
    see statsmodel.robust.mad for more info
    
    xarray =  dataArray
    c =  the normalisation constant
    coords_label = tuple. the labels of the georeferencing coordinate data 
    
    """
    y  = xarray.coords[coords_label[1]]
    x  = xarray.coords[coords_label[0]]
    arr_1 = xarray.values
    t1, x1, y1 = arr_1.shape
    mads = np.zeros((x1, y1))
    #loop through each cell of arr1 to conduct the stat
    print('Starting for loops...this could take a while')
    for x in range(x1):
        for y in range(y1):
            arr_2 = arr_1[:, x, y] #for each x,y position, create a 1D array of the timeseries
            arr_2 = arr_2[~np.isnan(arr_2)] #deal with the nans
            mads[x,y] = robust.mad(arr_2, c=c) #run the test 
    return mads