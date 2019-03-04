## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA. If a function does not use 
DEA functionality (for example, dc.load or xarrays), it may be better suited for inclusion in SpatialTools.py.
Available functions:

    load_nbarx
    load_sentinel
    load_clearlandsat (also does fractional cover)
    load_clearsentinel2
    dataset_to_geotiff
    open_polygon_from_shapefile
    write_your_netcdf
    zonal_timeseries

Last modified: March 2019
Authors: Claire Krause, Robbi Bishop-Taylor, Bex Dunn, Chad Burton

'''

# Load modules
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import gdal
import numpy as np
import xarray as xr
import rasterio
import geopandas as gpd
import dask
import rasterstats as rs

from datacube.utils import geometry
import fiona
import shapely.geometry

try:   
    from datacube.storage.storage import write_dataset_to_netcdf
except ImportError:
    from datacube.drivers.netcdf import write_dataset_to_netcdf
    
import warnings
warnings.simplefilter('ignore', FutureWarning)

    
def load_nbarx(dc, sensor, query, product='nbart', bands_of_interest='', filter_pq=True):
    """
    Loads NBAR (Nadir BRDF Adjusted Reflectance) or NBAR-T (terrain corrected NBAR) data for a
    sensor, masks using pixel quality (PQ), then optionally filters out terrain -999s (for NBAR-T).
    Returns an xarray dataset and CRS and Affine objects defining map projection and geotransform

    Last modified: May 2018
    Author: Bex Dunn
    Modified by: Claire Krause, Robbi Bishop-Taylor, Bex Dunn

    inputs
    dc - Handle for the Datacube to import from. This allows you to also use dev environments
    if that have been imported into the environment.
    sensor - Options are 'ls5', 'ls7', 'ls8'
    query - A dict containing the query bounds. Can include lat/lon, time etc. 

    optional
    product - 'nbar' or 'nbart'. Defaults to nbart unless otherwise specified
    bands_of_interest - List of strings containing the bands to be read in; defaults to all bands,
                        options include 'red', 'green', 'blue', 'nir', 'swir1', 'swir2'
    filter_pq - boolean. Will filter clouds and saturated pixels using PQ unless set to False


    outputs
    ds - Extracted and optionally PQ filtered dataset
    crs - CRS object defining dataset coordinate reference system
    affine - Affine object defining dataset affine transformation
    """

    product_name = '{}_{}_albers'.format(sensor, product)
    mask_product = '{}_{}_albers'.format(sensor, 'pq')
    print('Loading {}'.format(product_name))

    # If bands of interest are given, assign measurements in dc.load call
    if bands_of_interest:

        ds = dc.load(product=product_name, measurements=bands_of_interest,
                     group_by='solar_day', **query)

    # If no bands of interest given, run without specifying measurements
    else:

        ds = dc.load(product=product_name, group_by='solar_day', **query)

    # Proceed if the resulting call returns data
    if ds.variables:

        crs = ds.crs
        affine = ds.affine
        print('Loaded {}'.format(product_name))

        # If pixel quality filtering is enabled, extract PQ data to use as mask
        if filter_pq:

            sensor_pq = dc.load(product=mask_product, fuse_func=ga_pq_fuser,
                                group_by='solar_day', **query)

            # If PQ call returns data, use to mask input data
            if sensor_pq.variables:
                print('Generating mask {}'.format(mask_product))
                good_quality = masking.make_mask(sensor_pq.pixelquality,
                                                 cloud_acca='no_cloud',
                                                 cloud_shadow_acca='no_cloud_shadow',
                                                 cloud_shadow_fmask='no_cloud_shadow',
                                                 cloud_fmask='no_cloud',
                                                 blue_saturated=False,
                                                 green_saturated=False,
                                                 red_saturated=False,
                                                 nir_saturated=False,
                                                 swir1_saturated=False,
                                                 swir2_saturated=False,
                                                 contiguous=True)

                # Apply mask to preserve only good data
                ds = ds.where(good_quality)

            ds.attrs['crs'] = crs
            ds.attrs['affine'] = affine

        # Replace nodata values with nans

            ds = masking.mask_invalid_data(ds)

        return ds, crs, affine

    else:

        print('Failed to load {}'.format(product_name))
        return None, None, None


def load_sentinel(dc, product, query, filter_cloud=True, **bands_of_interest):
    '''loads a sentinel granule product and masks using pq

    Last modified: March 2018
    Authors: Claire Krause, Bex Dunn

    This function requires the following be loaded:
    from datacube.helpers import ga_pq_fuser
    from datacube.storage import masking
    from datacube import Datacube

    inputs
    dc - handle for the Datacube to import from. This allows you to also use dev environments
	 if that have been imported into the environment.
    product - string containing the name of the sentinel product to load
    query - A dict containing the query bounds. Can include lat/lon, time etc

    optional:
    bands_of_interest - List of strings containing the bands to be read in.

    outputs
    ds - Extracted and pq filtered dataset
    crs - ds coordinate reference system
    affine - ds affine
    '''
    dataset = []
    print('loading {}'.format(product))
    if bands_of_interest:
        ds = dc.load(product=product, measurements=bands_of_interest,
                     group_by='solar_day', **query)
    else:
        ds = dc.load(product=product, group_by='solar_day', **query)
    if ds.variables:
        crs = ds.crs
        affine = ds.affine
        print('loaded {}'.format(product))
        if filter_cloud:
            print('making mask')
            clear_pixels = np.logical_and(np.logical_and(ds.fmask != 0, ds.fmask != 2),
                              ds.fmask != 3)
            ds = ds.where(clear_pixels)
        ds.attrs['crs'] = crs
        ds.attrs['affine'] = affine
    else:
        print('did not load {}'.format(product))

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None


def load_clearlandsat(dc, query, sensors=('ls5', 'ls7', 'ls8'), product='nbart',
                      bands_of_interest=None, masked_prop=0.0, mask_dict=None,
                      mask_pixel_quality=True, mask_invalid_data=True, 
                      ls7_slc_off=False, satellite_metadata=False):

    
    """Loads Landsat NBAR, NBART or FC25 and PQ data for multiple sensors (i.e. ls5, ls7, ls8) and returns a single 
    xarray dataset containing only observations that contain greater than a given proportion of good quality pixels.
    
    This function can be used to extract visually appealing time series of observations that are not affected by cloud,
    for example as an input to the `animated_timeseries` function from `DEAPlotting`.
    
    The proportion of clear pixels is calculated by summing the pixels that are marked as being good quality
    in the Landsat PQ25 layer. By default cloud, cloud shadow, saturated pixels and pixels missing data for any band 
    are considered poor quality data, but this can be customised using the `mask_dict` parameter.
    
    Last modified: March 2019
    Author: Robbi Bishop-Taylor, Bex Dunn    
    
    Parameters
    ----------    
    dc : datacube Datacube object
        A specific Datacube to import from, i.e. `dc = datacube.Datacube(app='Clear Landsat')`. This allows you to 
        also use development datacubes if they have been imported into the environment.    
    query : dict
        A dict containing the query bounds. Can include lat/lon, time etc. If no `time` query is given, the 
        function defaults to all timesteps available to all sensors (e.g. 1987-2018)
    sensors : list, optional
        An optional list of Landsat sensor names to load data for. Options are 'ls5', 'ls7', 'ls8'; defaults to all.
    product : str, optional
        An optional string specifying 'nbar', 'nbart' or 'fc'. Defaults to 'nbart'. For information on the difference, 
        see the '02_DEA_datasets/Introduction_to_Landsat' or '02_DEA_datasets/Introduction_to_Fractional_Cover'
        notebooks from DEA-notebooks.
    bands_of_interest : list, optional
        An optional list of strings containing the bands to be read in; options include 'red', 'green', 'blue', 
        'nir', 'swir1', 'swir2'; defaults to all available bands if no bands are specified.
    masked_prop : float, optional
        An optional float giving the minimum percentage of good quality pixels required for a Landsat observation to 
        be loaded. Defaults to 0.0 which will return all observations regardless of pixel quality (set to e.g. 0.99 
        to return only observations with more than 99% good quality pixels).
    mask_dict : dict, optional
        An optional dict of arguments to the `masking.make_mask` function that can be used to identify poor
        quality pixels from the PQ layer using alternative masking criteria. The default value of None masks
        out pixels flagged as cloud or cloud shadow by either the ACCA or Fmask algorithms, any saturated pixels, 
        or any pixels that are missing data in any band (equivalent to: `mask_dict={'cloud_acca': 'no_cloud', 
        'cloud_shadow_acca': 'no_cloud_shadow', 'cloud_shadow_fmask': 'no_cloud_shadow', 'cloud_fmask': 'no_cloud', 
        'blue_saturated': False, 'green_saturated': False, 'red_saturated': False, 'nir_saturated': False, 
        'swir1_saturated': False, 'swir2_saturated': False, 'contiguous': True}`. See the 
        `02_DEA_datasets/Introduction_to_LandsatPQ.ipynb` notebook on DEA Notebooks for a list of all possible options.
    mask_pixel_quality : bool, optional
        An optional boolean indicating whether to apply the pixel quality mask to all observations that were not
        filtered out for having less good quality pixels that `masked_prop`. For example, if `masked_prop=0.99`, the
        filtered images may still contain up to 1% poor quality pixels. The default of False simply returns the
        resulting observations without masking out these pixels; True masks them out and sets them to NaN using the
        pixel quality mask, but has the side effect of changing the data type of the output arrays from int16 to
        float64 which can cause memory issues. To reduce memory usage, set to False.
    mask_invalid_data : bool, optional
        An optional boolean indicating whether invalid -999 nodata values should be replaced with NaN. Defaults to
        True; this has the side effect of changing the data type of the output arrays from int16 to float64 which
        can cause memory issues. To reduce memory usage, set to False.
    ls7_slc_off : bool, optional
        An optional boolean indicating whether to include data from after the Landsat 7 SLC failure (i.e. SLC-off).
        Defaults to False, which removes all Landsat 7 observations after May 31 2003. 
    satellite_metadata : bool, optional
        An optional boolean indicating whether to return the dataset with a `satellite` variable that gives the name 
        of the satellite that made each observation in the timeseries (i.e. ls5, ls7, ls8). Defaults to False. 
    
    Returns
    -------
    combined_ds : xarray Dataset
        An xarray dataset containing only Landsat observations that contain greater than `masked_prop`
        proportion of clear pixels.   
        
    Notes
    -----
    Memory issues: For large data extractions, it is recommended that you set both `mask_pixel_quality=False` and 
    `mask_invalid_data=False`. Otherwise, all output variables will be coerced to float64 when NaN values are 
    inserted into the array, potentially causing your data to use 4x as much memory. Be aware that the resulting
    arrays will contain invalid -999 values which should be considered in analyses.
        
    Example
    -------    
    >>> # Import modules
    >>> import datacube
    >>> import sys
    >>> # Import dea-notebooks functions using relative link to 10_Scripts directory
    >>> sys.path.append('../10_Scripts')
    >>> import DEADataHandling
    >>> # Connect to a datacube containing Landsat data
    >>> dc = datacube.Datacube(app='load_clearlandsat')
    >>> # Set up spatial and temporal query
    >>> query = {'x': (954163, 972163),
    ...          'y': (-3573891, -3555891),
    ...          'time': ('2011-06-01', '2013-06-01'),
    ...          'crs': 'EPSG:3577'}   
    >>> # Load observations with more than 75% good quality pixels from ls5, ls7 and ls8 as a combined dataset
    >>> landsat_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, sensors=['ls5', 'ls7', 'ls8'], 
    ...                                    bands_of_interest=['red', 'green', 'blue'], 
    ...                                    masked_prop=0.75, mask_pixel_quality=True, ls7_slc_off=True)
    Loading ls5
        Loading 4 filtered ls5 timesteps
    Loading ls7
        Loading 29 filtered ls7 timesteps
    Loading ls8
        Loading 3 filtered ls8 timesteps
    Combining and sorting ls5, ls7, ls8 data
        Replacing invalid -999 values with NaN (data will be coerced to float64)
    >>> # Test that function returned data
    >>> len(landsat_ds.time) > 0
    True
                
    """    

    #######################
    # Process each sensor #
    #######################    
    
    # Dictionary to save results from each sensor 
    filtered_sensors = {}

    # Iterate through all sensors, returning only observations with > mask_prop clear pixels
    for sensor in sensors:     
        
            # Load PQ data using dask
            print(f'Loading {sensor}')
            
            # If bands of interest are given, assign measurements in dc.load call. This is
            # for compatibility with the existing dea-notebooks load_nbarx function.
            if bands_of_interest:
                
                # Lazily load Landsat data using dask              
                data = dc.load(product=f'{sensor}_{product}_albers',
                               measurements=bands_of_interest,
                               group_by='solar_day', 
                               dask_chunks={'time': 1},
                               **query)

            # If no bands of interest given, run without specifying measurements, and 
            # therefore return all available bands
            else:
                
                # Lazily load Landsat data using dask  
                data = dc.load(product=f'{sensor}_{product}_albers',
                               group_by='solar_day', 
                               dask_chunks={'time': 1},
                               **query)             

            # Load PQ data
            pq = dc.load(product=f'{sensor}_pq_albers',
                         group_by='solar_day',
                         fuse_func=ga_pq_fuser,
                         dask_chunks={'time': 1},
                         **query)            
            
            # If resulting dataset has data, continue:
            if data.variables:
                
                # Remove Landsat 7 SLC-off from PQ layer if ls7_slc_off=False
                if not ls7_slc_off and sensor == 'ls7':

                    print('    Ignoring SLC-off observations for ls7')
                    data = data.sel(time=data.time < np.datetime64('2003-05-30')) 
                
                # If more than 0 timesteps
                if len(data.time) > 0:                       

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
                                                         cloud_shadow_acca='no_cloud_shadow',
                                                         cloud_shadow_fmask='no_cloud_shadow',
                                                         cloud_fmask='no_cloud',
                                                         blue_saturated=False,
                                                         green_saturated=False,
                                                         red_saturated=False,
                                                         nir_saturated=False,
                                                         swir1_saturated=False,
                                                         swir2_saturated=False,
                                                         contiguous=True)
                   
                    # Compute good data for each observation as a percentage of total array pixels. Need to
                    # sum over x and y axes individually so that the function works with lat-lon dimensions,
                    # and because it isn't currently possible to pass a list of axes (bug with xarray?) 
                    data_perc = good_quality.sum(axis=1).sum(axis=1) / (good_quality.shape[1] * good_quality.shape[2])

                    # Add data_perc data to Landsat dataset as a new xarray variable
                    data['data_perc'] = xr.DataArray(data_perc, [('time', data.time)])

                    # Filter by data_perc to drop low quality observations and finally import data using dask
                    filtered = data.sel(time=data.data_perc >= masked_prop)
                    print(f'    Loading {len(filtered.time)} filtered {sensor} timesteps')

                    # Optionally apply pixel quality mask to all observations that were not dropped in previous step
                    if mask_pixel_quality:
                        filtered = filtered.where(good_quality)

                    # Optionally add satellite name variable
                    if satellite_metadata:
                        filtered['satellite'] = xr.DataArray([sensor] * len(filtered.time), [('time', filtered.time)])

                    # Add result to dictionary
                    filtered_sensors[sensor] = filtered.compute()

                    # Close datasets
                    filtered = None
                    good_quality = None
                    data = None
                    pq = None            

                else:

                    # If there is no data for sensor or if another error occurs:
                    print(f'    Skipping {sensor}; no valid data for query')
                    
            else:

                # If there is no data for sensor or if another error occurs:
                print(f'    Skipping {sensor}; no valid data for query')
                
                
    ############################
    # Combine multiple sensors #
    ############################
                
    # Proceed with concatenating only if there is more than 1 sensor processed
    if len(filtered_sensors) > 1:

        # Concatenate all sensors into one big xarray dataset, and then sort by time 
        sensor_string = ", ".join(filtered_sensors.keys())
        print(f'Combining and sorting {sensor_string} data')
        combined_ds = xr.concat(filtered_sensors.values(), dim='time')
        combined_ds = combined_ds.sortby('time')                                                               

        # Optionally filter to replace no data values with nans
        if mask_invalid_data:

            print('    Replacing invalid -999 values with NaN (data will be coerced to float64)')
            combined_ds = masking.mask_invalid_data(combined_ds)

        # Return combined dataset
        return combined_ds
    
    # Return the single dataset if only one sensor was processed
    elif len(filtered_sensors) == 1:
        
        sensor_string = ", ".join(filtered_sensors.keys())
        print(f'Returning {sensor_string} data')
        sensor_ds = list(filtered_sensors.values())[0]
        
        # Optionally filter to replace no data values with nans
        if mask_invalid_data:

            print('    Replacing invalid -999 values with NaN (data will be coerced to float64)')
            sensor_ds = masking.mask_invalid_data(sensor_ds)       
        
        return sensor_ds
    
    else:
        
        print(f'No data returned for query for any sensor in {", ".join(sensors)} '
              f'and time range {"-".join(query["time"])}')


def load_clearsentinel2(dc, query, sensors=('s2a', 's2b'), product='ard',
                        bands_of_interest=('nbart_red', 'nbart_green', 'nbart_blue', 'nbart_nir_1', 'nbart_swir_2', 'nbart_swir_3'),
                        masked_prop=0.0, mask_values=(0, 2, 3), pixel_quality_band='fmask',
                        mask_pixel_quality=True, mask_invalid_data=True, satellite_metadata=False):
    
    """
    Loads Sentinel 2 data for multiple sensors (i.e. s2a, s2b), and returns a single xarray dataset containing 
    only observations that contain greater than a given proportion of good quality pixels. This can be used to extract
    visually appealing time series of observations that are not affected by cloud, for example as an input to the
    `animated_timeseries` function from `DEAPlotting`.
    
    The proportion of good quality pixels is calculated by summing the pixels flagged as good quality
    in the Sentinel pixel quality array. By default pixels flagged as nodata, cloud or shadow are used to 
    calculate the number of good quality quality pixels, but this can be customised using the `mask_values` parameter.
    
    MEMORY ISSUES: For large data extractions, it is recommended that you set both `mask_pixel_quality=False` and 
    `mask_invalid_data=False`. Otherwise, all output variables will be coerced to float64 when NaN values are 
    inserted into the array, potentially causing your data to use 4x as much memory. Be aware that the resulting
    arrays will contain invalid -999 values which should be considered in analyses.
    
    Last modified: March 2019
    Author: Robbi Bishop-Taylor
    
    :param dc: 
        A specific Datacube to import from, i.e. `dc = datacube.Datacube(app='Sentinel datacube')`. This allows you 
        to also use development datacubes if they have been imported into the environment.
    
    :param query: 
        A dict containing the query bounds. Can include lat/lon, time etc. If no `time` query is given, the 
        function defaults to all time steps available to all sensors (e.g. 2015 onward)

    :param sensors:
        An optional list of Sentinel 2 sensors to load data for. Options are 's2a', and 's2b'; defaults to both.

    :param product:
        An optional string specifying the product to load. Defaults to 'ard', which is equivalent to loading
        e.g. `s2a_ard_granule`. 
        
    :param bands_of_interest:
        An optional list of strings containing the bands to be read in; to view full list run the following:
        `dc.list_measurements().loc['s2b_ard_granule']`. Defaults to `('nbart_red', 'nbart_green', 'nbart_blue', 
        'nbart_nir_1', 'nbart_swir_2', 'nbart_swir_3')`.

    :param masked_prop:
        An optional float giving the minimum percentage of good quality pixels required for a Sentinel 2 observation
        to be loaded. Defaults to 0.0 which will return all observations regardless of pixel quality (set to e.g. 0.99 
        to return only observations with more than 99% good quality pixels).
    
    :param mask_values:
        An optional list of pixel quality values to treat as poor quality observations in the above `masked_prop`
        calculation. The default is `[0, 2, 3]` which treats nodata, cloud and cloud shadow as poor quality.
        Choose from: `{'0': 'nodata', '1': 'valid', '2': 'cloud', '3': 'shadow', '4': 'snow', '5': 'water'}`.
        
    :param pixel_quality_band:
        An optional string giving the name of the pixel quality band contained in the Sentinel 2 dataset. The default
        value is 'fmask'.
      
    :param mask_pixel_quality:
        An optional boolean indicating whether to apply the pixel quality mask to all observations that were not
        filtered out for having less good quality pixels that `masked_prop`. For example, if `masked_prop=0.99`, the
        filtered images may still contain up to 1% poor quality pixels. The default of True masks poor quality pixeks 
        out and sets them to NaN using the pixel quality mask. This has the side effect of changing the data type of 
        the output arrays from int16 to float64 which can cause memory issues. To reduce memory usage, set to False.
        
    :param mask_invalid_data:
        An optional boolean indicating whether invalid -999 nodata values should be replaced with NaN. Defaults to
        True; this has the side effect of changing the data type of the output arrays from int16 to float64 which can
        cause memory issues. To reduce memory usage, set to False.
        
    :param satellite_metadata:
        An optional boolean indicating whether to return the dataset with a `satellite` variable that gives the name
        of the satellite that made each observation in the time series (i.e. s2a, s2b). Defaults to False.
        
    :returns:
        An xarray dataset containing only Sentinel 2 observations that contain greater than `masked_prop`
        proportion of clear pixels.  
        
    :example:
    
    >>> # Import modules
    >>> import datacube
    >>> import sys

    >>> # Import dea-notebooks functions using relative link to 10_Scripts directory
    >>> sys.path.append('../10_Scripts')
    >>> import DEADataHandling

    >>> # Connect to a datacube containing Sentinel data
    >>> dc = datacube.Datacube(app='load_clearsentinel')

    >>> # Set up spatial and temporal query; note that 'output_crs' and 'resolution' need to be set
    >>> query = {'x': (-191400.0, -183400.0),
    ...          'y': (-1423460.0, -1415460.0),
    ...          'time': ('2018-01-01', '2018-03-01'),
    ...          'crs': 'EPSG:3577',
    ...          'output_crs': 'EPSG:3577',
    ...          'resolution': (10, 10)}   

    >>> # Load observations with less than 70% cloud from both S2A and S2B as a single combined dataset
    >>> sentinel_ds = DEADataHandling.load_clearsentinel2(dc=dc, query=query, sensors=['s2a', 's2b'], 
    ...                                    bands_of_interest=['nbart_red', 'nbart_green', 'nbart_blue'], 
    ...                                    masked_prop=0.3, mask_pixel_quality=True)
    Loading s2a pixel quality
        Loading 3 filtered s2a timesteps
    Loading s2b pixel quality
        Loading 2 filtered s2b timesteps
    Combining and sorting s2a, s2b data
        Replacing invalid -999 values with NaN (data will be coerced to float64)

    >>> # Test that function returned data
    >>> len(sentinel_ds.time) > 0
    True
      
    """

    # Dictionary to save results from each sensor 
    filtered_sensors = {}

    # Iterate through all sensors, returning only observations with > mask_prop clear pixels
    for sensor in sensors:
       
        # If bands of interest are given, assign measurements in dc.load call. This is
        # for compatibility with the existing dea-notebooks load_nbarx function.
        if bands_of_interest:

            # Lazily load Sentinel 2 data using dask
            data = dc.load(product=f'{sensor}_{product}_granule',
                            measurements=bands_of_interest,
                            group_by='solar_day',
                            dask_chunks={'time': 1},
                            **query)

        # If no bands of interest given, run without specifying measurements, and
        # therefore return all available bands
        else:

            # Lazily load Sentinel 2 data using dask
            data = dc.load(product=f'{sensor}_{product}_granule',
                            group_by='solar_day',
                            dask_chunks={'time': 1},
                            **query)

        # Load PQ data
        print(f'Loading {sensor} pixel quality')
        pq = dc.load(product=f'{sensor}_{product}_granule',
                     measurements=[pixel_quality_band],
                     group_by='solar_day',
                     dask_chunks={'time': 1},
                     **query)
              
        # If resulting dataset has data, continue:
        if data.variables:
              
            # If more than 0 timesteps
            if len(data.time) > 0:  

                # Identify pixels with valid data
                good_quality = np.isin(pq[pixel_quality_band], test_elements=mask_values, invert=True)
                good_quality = pq[pixel_quality_band].where(good_quality).notnull()

                # Compute good data for each observation as a percentage of total array pixels
                data_perc = good_quality.sum(axis=1).sum(axis=1) / (good_quality.shape[1] * good_quality.shape[2])

                # Add data_perc data to Sentinel 2 dataset as a new xarray variable
                data['data_perc'] = xr.DataArray(data_perc, [('time', data.time)])

                # Filter by data_perc to drop low quality observations and finally import data using dask
                filtered = data.sel(time=data.data_perc >= masked_prop)
                print(f'    Loading {len(filtered.time)} filtered {sensor} timesteps')

                # Optionally apply pixel quality mask to all observations that were not dropped in previous step
                if mask_pixel_quality:
                    filtered = filtered.where(good_quality)

                # Optionally add satellite name
                if satellite_metadata:
                    filtered['satellite'] = xr.DataArray([sensor] * len(filtered.time), [('time', filtered.time)])

                # Add result to dictionary
                filtered_sensors[sensor] = filtered.compute()

                # Close datasets
                filtered = None
                good_quality = None
                data = None
     
            else:

                # If there is no data for sensor or if another error occurs:
                print(f'    Skipping {sensor}; no valid data for query')
                    
        else:

            # If there is no data for sensor or if another error occurs:
            print(f'    Skipping {sensor}; no valid data for query')
            
              
    ############################
    # Combine multiple sensors #
    ############################
              
    # Proceed with concatenating only if there is more than 1 sensor processed
    if len(filtered_sensors) > 1:

        # Concatenate all sensors into one big xarray dataset, and then sort by time 
        sensor_string = ", ".join(filtered_sensors.keys())
        print(f'Combining and sorting {sensor_string} data')
        combined_ds = xr.concat(filtered_sensors.values(), dim='time')
        combined_ds = combined_ds.sortby('time')  

        # Optionally filter to replace invalid data values with nans
        if mask_invalid_data:
              
            print('    Replacing invalid -999 values with NaN (data will be coerced to float64)')
            combined_ds = masking.mask_invalid_data(combined_ds)

        # Return combined dataset
        return combined_ds
              
    # Return the single dataset if only one sensor was processed
    elif len(filtered_sensors) == 1:
        
        sensor_string = ", ".join(filtered_sensors.keys())
        print(f'Combining and sorting {sensor_string} data')
        sensor_ds = list(filtered_sensors.values())[0]
        
        # Optionally filter to replace no data values with nans
        if mask_invalid_data:

            print('    Replacing invalid -999 values with NaN (data will be coerced to float64)')
            sensor_ds = masking.mask_invalid_data(sensor_ds)       
        
        return sensor_ds
    
    else:
        
        print(f'No data returned for query for any sensor in {", ".join(sensors)} '
              f'and time range {"-".join(query["time"])}')


def dataset_to_geotiff(filename, data):

    """
    this function uses rasterio and numpy to write a multi-band geotiff for one
    timeslice, or for a single composite image. It assumes the input data is an
    xarray dataset (note, dataset not dataarray) and that you have crs and affine
    objects attached, and that you are using float data. future users
    may wish to assert that these assumptions are correct.

    Last modified: March 2018
    Authors: Bex Dunn and Josh Sixsmith
    Modified by: Claire Krause, Robbi Bishop-Taylor

    inputs
    filename - string containing filename to write out to
    data - dataset to write out
    Note: this function currently requires the data have lat/lon only, i.e. no
    time dimension
    """

    # Depreciation warning for write_geotiff
    print("This function will be superceded by the 'write_geotiff' function from 'datacube.helpers'. "
          "Please revise your notebooks to use this function instead")

    kwargs = {'driver': 'GTiff',
              'count': len(data.data_vars),  # geomedian no time dim
              'width': data.sizes['x'], 'height': data.sizes['y'],
              'crs': data.crs.crs_str,
              'transform': data.affine,
              'dtype': list(data.data_vars.values())[0].values.dtype,
              'nodata': 0,
              'compress': 'deflate', 'zlevel': 4, 'predictor': 3}
    # for ints use 2 for floats use 3}

    with rasterio.open(filename, 'w', **kwargs) as src:
        for i, band in enumerate(data.data_vars):
            src.write(data[band].data, i + 1)
 

def open_polygon_from_shapefile(shapefile, index_of_polygon_within_shapefile=0):

    '''This function takes a shapefile, selects a polygon as per your selection, 
    uses the datacube geometry object, along with shapely.geometry and fiona to 
    get the geom for the datacube query. It will also make sure you have the correct 
    crs object for the DEA

    Last modified: May 2018
    Author: Bex Dunn'''

    # open all the shapes within the shape file
    shapes = fiona.open(shapefile)
    i =index_of_polygon_within_shapefile
    #print('shapefile index is '+str(i))
    if i > len(shapes):
        print('index not in the range for the shapefile'+str(i)+' not in '+str(len(shapes)))
        sys.exit(0)
    #copy attributes from shapefile and define shape_name
    geom_crs = geometry.CRS(shapes.crs_wkt)
    geo = shapes[i]['geometry']
    geom = geometry.Geometry(geo, crs=geom_crs)
    geom_bs = shapely.geometry.shape(shapes[i]['geometry'])
    shape_name = shapefile.split('/')[-1].split('.')[0]+'_'+str(i)
    #print('the name of your shape is '+shape_name)
    #get your polygon out as a geom to go into the query, and the shape name for file names later
    return geom, shape_name          


def write_your_netcdf(data, dataset_name, filename, crs):

    """
    This function turns an xarray dataarray into a dataset so we can write it to netcdf. 
    It adds on a crs definition from the original array. data = your xarray dataset, dataset_name 
    is a string describing your variable
    
    Last modified: May 2018
    Author: Bex Dunn    
    """ 
   
    #turn array into dataset so we can write the netcdf
    if isinstance(data,xr.DataArray):
        dataset= data.to_dataset(name=dataset_name)
    elif isinstance(data,xr.Dataset):
        dataset = data
    else:
        print('your data might be the wrong type, it is: '+type(data))
    #grab our crs attributes to write a spatially-referenced netcdf
    dataset.attrs['crs'] = crs

    try:
        write_dataset_to_netcdf(dataset, filename)
    except RuntimeError as err:
        print("RuntimeError: {0}".format(err))    

	
def zonal_timeseries(dataArray, shp_loc, results_loc, feature_name, stat='mean', csv=False, netcdf=False, plot=False):

    """
    Given an xarray dataArray and a shapefile, generates a timeseries of zonal statistics across n number of 
    uniquely labelled polygons. The function exports a .csv of the stats, a netcdf containing the stats, and .pdf plots.
    Requires the installation of the rasterstats module: https://pythonhosted.org/rasterstats/installation.html
    
    Inputs:
    data = xarray dataarray (note dataarray, not dataset - it is a requirement the data only have a single variable).
    shp_loc = string. Location of the shapefile used to extract the zonal timseries.
    results_loc = string. Location of the directory where results should export.
    feature_name = string. Name of attribute column in the shapefile that is of interest - used to label dataframe, plots etc.
    stat = string.  The statistic you want to extract. Options include 'count', 'max', 'median', 'min', 'std', 'mean'.
    plot = Boolean. If True, function will produce pdfs of timeseries for each polygon in the shapefile.
    csv = Boolean. If True, function will export results as a .csv.
    netcdf = Boolean. If True, function will export results as a netcdf.
    
    Last modified: May 2018
    Author: Chad Burton    
    """

    #use dask to chunk the data along the time axis in case its a very large dataset
    dataArray = dataArray.chunk(chunks = {'time':20})
    
    #create 'transform' tuple to provide ndarray with geo-referencing data. 
    one = float(dataArray.x[0])
    two = float(dataArray.y[0] - dataArray.y[1])
    three = 0.0
    four = float(dataArray.y[0])
    five = 0.0
    six = float(dataArray.x[0] - dataArray.x[1])

    transform_zonal = (one, two, three, four, five, six)

    #import shapefile, make sure its in the right projection to match the dataArray
    #and set index to the feature_name
    project_area = gpd.read_file(shp_loc)               #get the shapefile
    reproj=int(str(dataArray.crs)[5:])                  #do a little hack to get EPSG from the dataArray 
    project_area = project_area.to_crs(epsg=reproj)     #reproject shapefile to match dataArray
    project_area = project_area.set_index(feature_name) #set the index
    
    #define the general function
    def zonalStats(dataArray, stat=stat): 
        """extract the zonal statistics of all
        pixel values within each polygon"""
        stats = [] 
        for i in dataArray:
            x = rs.zonal_stats(project_area, i, transform=transform_zonal, stats=stat)    
            stats.append(x)
        #extract just the values from the results, and convert 'None' values to nan
        stats = [[t[stat] if t[stat] is not None else np.nan for t in feature] for feature in stats]
        stats = np.array(stats)
        return stats

    #use the zonal_stats functions to extract the stats:
    n = len(project_area) #number of polygons in the shapefile (defines the dimesions of the output)
    statistics = dataArray.data.map_blocks(zonalStats, chunks=(-1,n), drop_axis=1, dtype=np.float64).compute()

    #get unique identifier and timeseries data from the inputs 
    colnames = pd.Series(project_area.index.values)
    time = pd.Series(dataArray['time'].values)

    #define functions for cleaning up the results of the rasterstats operation
    def tidyresults(results):
        x = pd.DataFrame(results).T #transpose
        x = x.rename(colnames, axis='index') #rename the columns to the timestamp
        x = x.rename(columns = time)
        return x

    #place results into indexed dataframes using tidyresults function
    statistics_df = tidyresults(statistics)
    
    #convert into xarray for merging into a dataset
    stat_xr = xr.DataArray(statistics_df, dims=[feature_name, 'time'], coords={feature_name: statistics_df.index, 'time': time}, name= stat)
    
    #options for exporting results as csv, netcdf, pdf plots
    #export results as a .csv
    if csv:
        statistics_df.to_csv('{0}{1}.csv'.format(results_loc, stat))
                             
    if netcdf:
        #export out results as netcdf
        stat_xr.to_netcdf('{0}zonalstats_{1}.nc'.format(results_loc, stat), mode='w',format='NETCDF4') 

    if plot:     
        #place the data from the xarray into a list
        plot_data = []
        for i in range(0,len(stat_xr[feature_name])):
            x = stat_xr.isel([stat], **{feature_name: i})
            plot_data.append(x)

        #extract the unique names of each polygon
        feature_names = list(stat_xr[feature_name].values)

        #zip the both the data and names together as a dictionary 
        monthly_dict = dict(zip(feature_names,plot_data))

        #create a function for generating the plots
        def plotResults(dataArray, title):
            """a function for plotting up the results of the
            fractional cover change and exporting it out as pdf """
            x = dataArray.time.values
            y = dataArray.data          

            plt.figure(figsize=(15,5))
            plt.plot(x, y,'k', color='#228b22', linewidth = 1)
            plt.grid(True, linestyle ='--')
            plt.title(title)
            plt.savefig('{0}{1}.pdf'.format(results_loc, title), bbox_inches='tight')

        #loop over the dictionaries and create the plots
        {key: plotResults(monthly_dict[key], key + "_"+ stat) for key in monthly_dict} 
    
    #return the results as a dataframe
    return statistics_df


# The following tests are run if the module is called directly (not when being imported).
# To do this, run the following: `python {modulename}.py`

if __name__=='__main__':
   
    # Import doctest to test our module for documentation
    import doctest
    
    # Run all reproducible examples in the module and test against expected outputs
    print('Testing...')
    doctest.testmod(optionflags=doctest.ELLIPSIS)
    print('Testing complete')
