import datacube 
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import xarray as xr

def load_data(dc_name, sensors, export_name, query):

    #load data
    xarray_dict = {}
    dc = datacube.Datacube(app=dc_name)
    for sensor in sensors:
        print(f'{sensor}_loading...')
        # Load data 
        landsat_ds = dc.load(product = f'{sensor}_nbart_albers', 
                             group_by = 'solar_day', 
                             **query)

        # Load PQ data 
        landsat_pq = dc.load(product = f'{sensor}_pq_albers', 
                             measurements = ['pixelquality'],
                             group_by = 'solar_day', 
                             **query)                       
        print(f'{sensor}_loaded')
        if not landsat_ds:
            del landsat_ds
            continue
        else:
            # Filter to subset of Landsat observations that have matching PQ data 
            time = (landsat_ds.time - landsat_pq.time).time
            landsat_ds = landsat_ds.sel(time=time)
            landsat_pq = landsat_pq.sel(time=time)

            # Create PQ mask
            good_quality = masking.make_mask(landsat_pq.pixelquality,
                                             cloud_acca='no_cloud',
                                             cloud_shadow_acca='no_cloud_shadow',
                                             cloud_shadow_fmask='no_cloud_shadow',
                                             cloud_fmask='no_cloud',
                                             blue_saturated=False,
                                             green_saturated=False,
                                             red_saturated=False,
                                             nir_saturated=False,
                                             contiguous=True) 

            # Apply mask to set all PQ-affected pixels to NaN and set nodata to NaN
            landsat_ds = landsat_ds.where(good_quality)

            # Add result to dict
            xarray_dict[sensor] = landsat_ds
            
            
    # Concatenate multiple sensors into one dataset
    landsat = xr.concat(xarray_dict.values(), dim='time')
    landsat = landsat.sortby('time')

    #export out data so we dont need to reload everytime we need to clear the kernel
    #datacube.storage.storage.write_dataset_to_netcdf(landsat, export_name)
    
    return landsat