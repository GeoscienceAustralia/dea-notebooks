
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import xarray as xr
import dask

def lazily_load_clearlandsat(dc, query, sensors=('ls5', 'ls7', 'ls8'), product='nbart', dask_chunks = {'time': 1},
                      bands_of_interest=None, masked_prop=0.99, mask_dict=None,
                      mask_pixel_quality=False, mask_invalid_data=True, ls7_slc_off=False, satellite_metadata=False):
    
    """
    Function is the same as DEADataHandling.load_clearlandsat, except it accepts spatial chunking using dask and
    will return a chunked dataset with none of the functions computed until you explicitly run ds.compute()
    """    

    # List to save results from each sensor and list to keep names of successfully processed sensors
    filtered_sensors = []
    successfully_returned = []

    # Iterate through all sensors, returning only observations with > mask_prop clear pixels
    for sensor in sensors:
        print("\r", 'loading sensor ' + sensor, end='')
        try:
            
            # If bands of interest are given, assign measurements in dc.load call. This is
            # for compatibility with the existing dea-notebooks load_nbarx function.
            if bands_of_interest:
                
                # Lazily load Landsat data using dask              
                data = dc.load(product=f'{sensor}_{product}_albers',
                               measurements=bands_of_interest,
                               group_by='solar_day', 
                               dask_chunks=dask_chunks,
                               **query)

            # If no bands of interest given, run without specifying measurements, and 
            # therefore return all available bands
            else:
                
                # Lazily load Landsat data using dask  
                data = dc.load(product=f'{sensor}_{product}_albers',
                               group_by='solar_day', 
                               dask_chunks=dask_chunks,
                               **query)             

            # Load PQ data
            pq = dc.load(product=f'{sensor}_pq_albers',
                         group_by='solar_day',
                         fuse_func=ga_pq_fuser,
                         dask_chunks=dask_chunks,
                         **query)

            # Remove Landsat 7 SLC-off from PQ layer if ls7_slc_off=False
            if not ls7_slc_off and sensor == 'ls7':
                data = data.sel(time=data.time < np.datetime64('2003-05-30'))

            # Return only Landsat observations that have matching PQ data 
            time = (data.time - pq.time).time
            data = data.sel(time=time)
            pq = pq.sel(time=time)
            
            # If a custom dict is provided for mask_dict, use these values to make mask from PQ
            if mask_dict:
                
                # Mask PQ using custom values by unpacking mask_dict **kwarg
                good_quality = masking.make_mask(pq.pixelquality, **mask_dict)
                
            else:

                # Identify pixels with no clouds in either ACCA for Fmask
                good_quality = masking.make_mask(pq.pixelquality,
                                                 cloud_acca='no_cloud',
                                                 cloud_fmask='no_cloud',
                                                 contiguous=True)

            # Compute good data for each observation as a percentage of total array pixels
            data_perc = good_quality.sum(axis=1).sum(axis=1) / (good_quality.shape[1] * good_quality.shape[2])
            
            # Add data_perc data to Landsat dataset as a new xarray variable
            data['data_perc'] = xr.DataArray(data_perc, [('time', data.time)])

            # Filter by data_perc to drop low quality observations and finally import data using dask
            filtered = data.sel(time=data.data_perc >= masked_prop)
            
            # Optionally apply pixel quality mask to all observations that were not dropped in previous step
            if mask_pixel_quality:
                filtered = filtered.where(good_quality)

            # Optionally add satellite name variable
            if satellite_metadata:
                filtered['satellite'] = xr.DataArray([sensor] * len(filtered.time), [('time', filtered.time)])

            # Append result to list and add sensor name to list of successfully sensors
            filtered_sensors.append(filtered)
            successfully_returned.append(sensor)
            
            # Close datasets
            filtered = None
            good_quality = None
            data = None
            pq = None            
                        
        except:
            pass
  
    print(', concatenating & sorting sensors')
    # Concatenate all sensors into one big xarray dataset, and then sort by time 
    combined_ds = xr.concat(filtered_sensors, dim='time')
    combined_ds = combined_ds.sortby('time')                                                               

    # Optionally filter to replace no data values with nans
    if mask_invalid_data:
        combined_ds = masking.mask_invalid_data(combined_ds)

    # Return combined dataset
    return combined_ds