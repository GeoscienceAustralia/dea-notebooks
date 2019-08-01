import sys
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr

import sys
sys.path.append('src')
import DEAPlotting, SpatialTools

results = "results/nmdb_plots/frequency/"

#bring in data
irr_alltime = xr.open_dataset(results+'NMDB_irrigation.nc').astype(bool)
# irr_alltime = xr.open_dataset(results+'NMDB_irrigation.nc').isel(x=range(26000,28000)).isel(y=range(18500,20000)).astype(bool)

#create parallized function for calculting sum and nanargmax
def count_irrigation(x, dim):
    return xr.apply_ufunc(np.sum, x, dask='parallelized',
                          input_core_dims=[[dim]],
                          kwargs={'axis': -1})

def IrrigationFirstOccurs(x, dim):
    """
    Calculating the time (indice) at which the first occurence of 
    Irrigation occurs (per-pixel). This works because np.nanargmax:
    "In cases of multiple occurrences of the maximum values,
    the indices corresponding to the first occurrence are returned."
    """
    return xr.apply_ufunc(np.nanargmax, x, dask='parallelized',
                          input_core_dims=[[dim]],
                          kwargs={'axis': -1})

count = count_irrigation(irr_alltime.Irrigated_Area, dim='time')
frequency = count / len(irr_alltime.time)
firstOccured = IrrigationFirstOccurs(irr_alltime.Irrigated_Area, dim='time')
yearsIrrigated = len(irr_alltime.time)-firstOccured 
normalisedFrequency = count / yearsIrrigated

#covert first observed to an array with the date (year)
dates = [t for t in range(1987,2019,1)]
dates =  [e for e in dates if e not in (2011, 2012)]
dates = np.asarray(dates)

def timey(ind, time):
    func = time[ind]
    return func

firstOccuredDates = timey(firstOccured, dates)

#mask out areas that return non-sensical values using the normalised frequency xarray
firstOccuredDates = np.where(normalisedFrequency.values > 0, firstOccuredDates, np.nan)
yearsIrrigated = yearsIrrigated.where(normalisedFrequency.values >0)

#export geotiffs
transform, projection = SpatialTools.geotransform(irr_alltime, (irr_alltime.x, irr_alltime.y), epsg=3577)

SpatialTools.array_to_geotiff(results+'rawFrequency_alltime.tif',
              frequency.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'count_alltime.tif',
              count.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'firstOccured_alltime.tif',
              firstOccured.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'firstOccuredDates_alltime.tif',
              firstOccuredDates, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'yearsIrrigated_alltime.tif',
              yearsIrrigated.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'normalisedFrequency_alltime.tif',
              normalisedFrequency.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

#NOW DO THE 90'S
irr_90s = irr_alltime.isel(time=range(0,13))
count_90s = count_irrigation(irr_90s.Irrigated_Area, dim='time')
firstOccured_90s = IrrigationFirstOccurs(irr_90s.Irrigated_Area, dim='time')
yearsIrrigated_90s = len(irr_90s.time)-firstOccured_90s 
normalisedFrequency_90s = count_90s / yearsIrrigated_90s

SpatialTools.array_to_geotiff(results+'normalisedfrequency_90s.tif',
              normalisedFrequency_90s.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

#NOW DO THE 00'S
irr_00s = irr_alltime.isel(time=range(13,23))
count_00s = count_irrigation(irr_00s.Irrigated_Area, dim='time')
firstOccured_00s = IrrigationFirstOccurs(irr_00s.Irrigated_Area, dim='time')
yearsIrrigated_00s = len(irr_00s.time)-firstOccured_00s 
normalisedFrequency_00s = count_00s / yearsIrrigated_00s

SpatialTools.array_to_geotiff(results+'normalisedfrequency_00s.tif',
              normalisedFrequency_00s.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

#NOW DO THE 10'S
irr_10s = irr_alltime.isel(time=range(23,30))
count_10s = count_irrigation(irr_10s.Irrigated_Area, dim='time')
firstOccured_10s = IrrigationFirstOccurs(irr_10s.Irrigated_Area, dim='time')
yearsIrrigated_10s = len(irr_10s.time)-firstOccured_10s 
normalisedFrequency_10s = count_10s / yearsIrrigated_10s

SpatialTools.array_to_geotiff(results+'normalisedfrequency_10s.tif',
              normalisedFrequency_10s.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

