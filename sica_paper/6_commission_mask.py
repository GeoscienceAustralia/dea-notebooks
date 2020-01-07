"""
Generate commission error mask

Commission masking using per-pixel frequency maps:
-	If normalised frequency (all_time) is <=0.125 (1 in 8 years) == commision error

-	Relax that threshold to account for recent commission errors (whose normalised frequency will look like higher frequency cropping.) If the count is equal to 1 and the normalised frequency is between 0.125 and 0.25, count as commission error.

-	Commission errors occurring for the first time in the last 3 years (since 2016) will be missed by this analysis. Regions converted to irrigation between 2010 and 2015 that were only irrigated once will be erroneously recorded as commission errors. 

-	Regions that were irrigated for a short period of time (low count) at the start of the time-series, but then underwent land use change and were no longer irrigated, will be erroneously removed by the commission masks. Eg. Imagine a paddock first irrigated in 1988 and irrigated for 3 years before ceasing being irrigatedits normalised frequency will be 3/29=0.103 and thus it will be removed by the commission error mask (set at 0.125)

"""

import numpy as np
import xarray as xr
from datacube.helpers import write_geotiff

results = "results/"

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


#-----------SCRIPT-----------------

#bring in data
irr_alltime = xr.open_dataset(results+'NMDB_irrigation.nc')

#generate various summary tiffs
print('calculating count, freq, first occured, normalised freq')
count = count_irrigation(irr_alltime.Irrigated_Area, dim='time')
frequency = count / len(irr_alltime.time)
firstOccured = IrrigationFirstOccurs(irr_alltime.Irrigated_Area, dim='time')
yearsIrrigated = len(irr_alltime.time)-firstOccured 
normalisedFrequency = count / yearsIrrigated

# Now actually create the commission mask
print('creating and exporting commission error mask')

freq_mask = np.where((normalisedFrequency <= 0.125) & (normalisedFrequency > 0), 1, 0)
count_mask = np.where((count.values == 1) & ((normalisedFrequency > 0.125) & (normalisedFrequency<= 0.25)), 1, 0)
combined_mask = np.where((freq_mask==1) | (count_mask==1), 1, 0)

combined_mask = xr.DataArray(combined_mask,
                          coords=[irr_alltime.y,irr_alltime.x],
                          dims=['y', 'x'],
                          name='commission_mask',
                          attrs=irr_alltime.attrs)

combined_mask = combined_mask.to_dataset()
combined_mask = combined_mask.astype('int16')
combined_mask.attrs = irr_alltime.attrs

write_geotiff(results+ "commission_mask.tif", combined_mask)

#clean up irrigation netcdf with the new mask and export
print('masking and exporting irrigation netcdf')
irr_clean = irr_alltime.where(combined_mask.commission_mask == 0, 0)

irr_clean.attrs = irr_alltime.attrs
irr_clean.to_netcdf('results/NMDB_irrigation_commission_cleaned.nc')
