import sys
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
import rasterio.features

results = "results/"
directory = "results/nmdb/"
suffix = "_LSandOEH_masked"

#FUNCTIONS for SCRIPT
def convertIrrShpToTiff(shp, year):  
    #open a tif and get transform info
    tif = directory+'/nmdb_'+year+"/nmdb_Summer"+year+"_multithreshold_65Thres.tif"
    ds = xr.open_rasterio(tif).squeeze()
    
    #convert to tif
    gdf = gpd.read_file(shp)
    shapes = zip(gdf['geometry'], gdf['DN'])
    transform = ds.transform
    y, x = ds.values.shape

    # Now convert the polgons into a numpy array
    shp_arr = rasterio.features.rasterize(shapes=shapes,
                                         out_shape=(y, x),
                                         all_touched=False,
                                         fill=np.nan,
                                         transform=transform)

    #convert numpy array into xarray
    shp_xr = xr.DataArray(shp_arr, coords = [ds.y, ds.x], dims = ['y', 'x'])
    #append xarray to list
    print('appending '+year)
    da_list.append(shp_xr)

#-----------SCRIPT-----------------
#list of years to help for-loop iterate through folders
x = range(1987,2019,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
# removing years that didn't work
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()

#list of folders to help with loop
folders = os.listdir(directory)
folders.sort()

da_list = []
for year, folder in zip(years, folders): 
    print("\r", "working on year: " + year, end = '')
    convertIrrShpToTiff(directory+folder+"/"+"nmdb_Summer"+ year + "_Irrigated"+suffix+".shp", year)

#generate date ranges to use as coordinates in xrray dataset
dates = pd.date_range(start='1/1/1987', end='1/01/2019', freq='Y')
dates = dates.drop([pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31')])
#concatenate all xarrays into a single multi-dim xarray with time ('dates') as coords.
da = xr.concat(da_list, dim=dates).rename({'concat_dim':'time'}).rename('Irrigated_Area')

#now convert to dataset and reclassify as boolean array to keep filesize down
#get some attributes
a = xr.open_rasterio('results/nmdb/nmdb_1994_95/nmdb_Summer1994_95_multithreshold_65Thres.tif')
attrs = a.attrs
#reclassify
ds = xr.DataArray(np.where(np.isfinite(da.Irrigated_Area.data), 1, 0),
                                  coords=[da.time, da.y, da.x],
                                  dims=['time', 'y', 'x'],
                                  name='Irrigated_Area',
                                  attrs=attrs)

ds = ds.to_dataset()
ds = ds.astype('int16')
ds.attrs = attrs
ds.to_netcdf('results/NMDB_irrigation.nc')
