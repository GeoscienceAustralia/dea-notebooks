import numpy as np
import xarray as xr
from datacube.helpers import write_geotiff

results = "results/"
irr_netcdf = 'results/NMDB_irrigation_commission_cleaned.nc'

#create parallized function for calculting sum and nanargmax
def count_irrigation(x, dim):
    return xr.apply_ufunc(np.sum, x, dask='parallelized',
                          output_dtypes=[float],
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
                          output_dtypes=[float],
                          input_core_dims=[[dim]],
                          kwargs={'axis': -1})


#-----------SCRIPT-----------------

#bring in data and get spatial info
irr_alltime = xr.open_dataset(irr_netcdf)
print(irr_alltime)
xcoords = irr_alltime.x
ycoords = irr_alltime.y
attrs = irr_alltime.attrs

#generate various summary tiffs
print('calculating count, freq, first occured, normalised freq')
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

#use the combined LS-OEH and Commissio error mask

print('exporting year first observed')
firstOccuredDates = xr.DataArray(firstOccuredDates,
                          coords=[ycoords,xcoords],
                          dims=['y', 'x'],
                          name='yearfirstoccurred',
                          attrs=attrs)

firstOccuredDates = firstOccuredDates.to_dataset()
firstOccuredDates.attrs = attrs
write_geotiff(results + "yearfirstoccurred.tif", firstOccuredDates)

print('exporting normalised frequency')
normalisedFrequency = normalisedFrequency.rename('normalisedfrequency').to_dataset()
normalisedFrequency.attrs = attrs
write_geotiff(results + "normalisedFrequency.tif", normalisedFrequency)

