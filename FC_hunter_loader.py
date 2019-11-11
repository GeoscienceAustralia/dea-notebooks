"""
Load fractional cover product over the Hunter region (with soil carbon site data)
and save the resulting pixel timeseries using Pandas.

Author: Richard Taylor

Last edited: November 2019

"""

#imports
import datacube
import fiona
from datacube.utils import geometry

import numpy as np
import pandas as pd

import sys
sys.path.append('10_Scripts/')
import DEADataHandling

from multiprocessing import Pool

#open the shapefile containing the extent of the sampling region
with fiona.open('HV_big_shp/HV_big.shp','r') as hunter2:
    crs = geometry.CRS(hunter2.crs_wkt)
    print(hunter2)
    poly = geometry.Geometry(hunter2[0]['geometry'],crs=crs)

    
#load the FC product across all 30 years of Landsat for this region (big mem req'd - over 32 GB)

dc = datacube.Datacube(app='dc-FC')

#construct query for the region with soil samples available
query = {
    
    'geopolygon': poly,
#     'time' : ('2013-01-01','2019-01-01'),
}

print("loading FC product...")
FC = DEADataHandling.load_clearlandsat(dc,query,product='fc',masked_prop=0.0,ls7_slc_off=True,lazy_load=False)
print("done.")
#open the site data file

TC_df = pd.read_csv('filtered_data.csv')

#convert points to same CRS as the FC dataset
TC_crs = geometry.CRS('EPSG:32756') #WGS84 UTM zone 56S
TC_df['points'] = TC_df.apply(lambda row: geometry.point(row.Easting,row.Northing,crs=TC_crs).to_crs(FC.crs),axis=1)

#define function to select a pixel nearest each point and interpolate it to 'seasonal' (three-month) observations 
def pxts(loc):
    x = loc.coords[0][0]
    y = loc.coords[0][1]
    
    print('Getting FC timeseries for pixel near x = '+str(x)+', y = '+str(y))
    
    #one-pixel tolerance distance
    timeseries = FC.sel(x=x,y=y,method='nearest',tolerance=25)
    timeseries = timeseries.dropna(dim='time')
    if len(timeseries.time)>30:
        resamp = timeseries.resample(time='3M').interpolate('cubic').to_array()
    else:
        resamp = None
    
    return resamp

#hopefully use all available CPUs
p = Pool()

print("getting timeseries data for every sampling site")
res = p.map(pxts,TC_df['points'])
p.close()
p.join()

TC_df['FC_timeseries'] = res

print("saving results as pickle")
TC_df.to_pickle("FC_TC_ts.pkl")

print("success.")