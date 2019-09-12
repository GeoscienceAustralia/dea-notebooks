## dea_datahandling.py
'''
Description: This file contains a set of python functions for handling Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

'''

# Import required packages
import numpy as np
import xarray as xr
from datacube.storage import masking


def load_ard(dc,
             products=None,
             min_gooddata=0.0,
             fmask_gooddata=[1, 4, 5],
             mask_pixel_quality=True,
             mask_invalid_data=True,
             ls7_slc_off=True,
             product_metadata=False,
             dask_chunks={'time': 1},
             lazy_load=False,
             **dcload_kwargs):
    '''
    Loads Landsat Collection 3 or Sentinel 2 Definitive and Near Real 
    Time data for multiple sensors (i.e. ls5t, ls7e and ls8c for 
    Landsat; s2a and s2b for Sentinel 2), and returns a single masked 
    xarray dataset containing only observations that contain greater 
    than a given proportion of good quality pixels. This can be used 
    to extract clean time series of observations that are not affected 
    by cloud, for example as an input to the `animated_timeseries` 
    function from `dea_plotting`.
    
    The proportion of good quality pixels is calculated by summing the 
    pixels flagged as good quality in `fmask`. By default non-cloudy or 
    shadowed land, snow and water pixels are treated as good quality, 
    but this can be customised using the `fmask_gooddata` parameter.
    
    MEMORY ISSUES: For large data extractions, it can be advisable to 
    set both `mask_pixel_quality=False` and `mask_invalid_data=False`. 
    These operations coerce all numeric values to float64 when NaN 
    values are inserted into the array, potentially causing your data 
    to use 4x as much memory. Be aware that the resulting arrays will 
    contain invalid -999 values which may affect future analyses.
    
    Last modified: September 2019
    
    Parameters
    ----------  
    dc : datacube Datacube object
        The Datacube to connect to, i.e. `dc = datacube.Datacube()`.
        This allows you to also use development datacubes if required.    
    products : list
        A list of product names to load data from. Valid options are 
        ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'] for Landsat,
        ['s2a_ard_granule', 's2b_ard_granule'] for Sentinel 2 Definitive, 
        and ['s2a_nrt_granule', 's2b_nrt_granule'] for Sentinel 2 Near 
        Real Time.
    min_gooddata : float, optional
        An optional float giving the minimum percentage of good quality 
        pixels required for a satellite observation to be loaded. 
        Defaults to 0.0 which will return all observations regardless of
        pixel quality (set to e.g. 0.99 to return only observations with
        more than 99% good quality pixels).
    fmask_gooddata : list, optional
        An optional list of fmask values to treat as good quality 
        observations in the above `min_gooddata` calculation. The 
        default is `[1, 4, 5]` which will return non-cloudy or shadowed 
        land, snow and water pixels. Choose from: 
        `{'0': 'nodata', '1': 'valid', '2': 'cloud', 
          '3': 'shadow', '4': 'snow', '5': 'water'}`.
    mask_pixel_quality : bool, optional
        An optional boolean indicating whether to apply the good data 
        mask to all observations that were not filtered out for having 
        less good quality pixels than `min_gooddata`. E.g. if 
        `min_gooddata=0.99`, the filtered observations may still contain 
        up to 1% poor quality pixels. The default of False simply 
        returns the resulting observations without masking out these 
        pixels; True masks them out and sets them to NaN using the good 
        data mask. This will convert numeric values to float64 which can 
        cause memory issues, set to False to prevent this.
    mask_invalid_data : bool, optional
        An optional boolean indicating whether invalid -999 nodata 
        values should be replaced with NaN. Defaults to True. This will 
        convert all numeric values to float64 which can cause memory 
        issues, set to False to prevent this.
    ls7_slc_off : bool, optional
        An optional boolean indicating whether to include data from 
        after the Landsat 7 SLC failure (i.e. SLC-off). Defaults to 
        True, which keeps all Landsat 7 observations > May 31 2003. 
    product_metadata : bool, optional
        An optional boolean indicating whether to return the dataset 
        with a `product` variable that gives the name of the product 
        that each observation in the time series came from (e.g. 
        'ga_ls5t_ard_3'). Defaults to False.
    dask_chunks : dict, optional
        An optional dictionary containing the coords and sizes you wish 
        to create dask chunks over. Usually used in combination with 
        `lazy_load=True` (see below). For example: 
        `dask_chunks = {'x': 500, 'y': 500}`
    lazy_load : boolean, optional
        Setting this variable to True will delay the computation of the 
        function until you explicitly run `ds.compute()`. If used in 
        conjuction with `dask.distributed.Client()` this will allow for 
        automatic parallel computation.
    **dcload_kwargs : 
        A set of keyword arguments to `dc.load` that define the 
        spatiotemporal query used to extract data. This can include `x`,
        `y`, `time`, `resolution`, `resampling`, `group_by`, `crs`
        etc, and can either be listed directly in the `load_ard` call 
        (e.g. `x=(150, 151)`), or by passing in a query kwarg 
        (e.g. `**query`). For a full list of possible options, see: 
        https://datacube-core.readthedocs.io/en/latest/dev/api/generate/datacube.Datacube.load.html          
        
    Returns
    -------
    combined_ds : xarray Dataset
        An xarray dataset containing only satellite observations that 
        contains greater than `min_gooddata` proportion of good quality 
        pixels.   
        
    '''
    
    # Verify that products were provided
    if not products:
        raise ValueError("Please provide a list of product names "
                         "to load data from. Valid options are: \n"
                         "['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'] " 
                         "for Landsat, ['s2a_ard_granule', "
                         "'s2b_ard_granule'] \nfor Sentinel 2 Definitive, or "
                         "['s2a_nrt_granule', 's2b_nrt_granule'] for Sentinel 2 "
                         "Near Real Time")

    # If `measurements` are specified but do not include fmask, add it
    if (('measurements' in dcload_kwargs) and 
        ('fmask' not in dcload_kwargs['measurements'])):
        dcload_kwargs['measurements'].append('fmask')

    # Create a list to hold data for each product
    product_data = []

    # Iterate through each requested product
    for product in products:

        try:

            # Load data including fmask band
            print(f'Loading {product} data')
            try:
                ds = dc.load(product=f'{product}',
                             dask_chunks=dask_chunks,
                             **dcload_kwargs)
            except KeyError as e:
                raise ValueError(f'Band {e} does not exist in this product. '
                                 f'Verify all requested `measurements` exist '
                                 f'in {products}')
            
            # Keep a record of the original number of observations
            total_obs = len(ds.time)

            # Remove Landsat 7 SLC-off observations if ls7_slc_off=False
            if not ls7_slc_off and product == 'ga_ls7e_ard_3':
                print('    Ignoring SLC-off observations for ls7')
                ds = ds.sel(time=ds.time < np.datetime64('2003-05-30'))
                
            # If no measurements are specified, `fmask` is given a 
            # different name. If necessary, rename it:
            if 'oa_fmask' in ds:
                ds = ds.rename({'oa_fmask': 'fmask'})

            # Identify all pixels not affected by cloud/shadow/invalid
            good_quality = np.isin(ds.fmask,
                                   test_elements=fmask_gooddata)
            good_quality = ds.fmask.where(good_quality).notnull()

            # Compute good data for each observation as % of total pixels
            data_perc = good_quality.sum(axis=1).sum(
                axis=1) / (good_quality.shape[1] * good_quality.shape[2])

            # Filter by data_perc to drop low quality observations
            filtered = ds.sel(time=data_perc >= min_gooddata)
            print(f'    Filtering to {len(filtered.time)} '
                  f'out of {total_obs} observations')

            # Optionally apply pixel quality mask to all observations that
            # were not dropped in previous step
            if mask_pixel_quality & (len(filtered.time) > 0):
                print('    Applying pixel quality mask')
                filtered = filtered.where(good_quality)

            # Optionally add satellite name
            if product_metadata:
                filtered['product'] = xr.DataArray(
                    [product] * len(filtered.time), [('time', filtered.time)])

            # If any data was returned, add result to list
            if len(filtered.time) > 0:
                product_data.append(filtered.drop('fmask'))

        # If  AttributeError due to there being no `fmask` variable in
        # the dataset, skip this product and move on to the next
        except AttributeError:
            print(f'    No data for {product}')

    # If any data was returned above, combine into one xarray
    if (len(product_data) > 0):

        # Concatenate results and sort by time
        print(f'Combining and sorting data')
        combined_ds = xr.concat(product_data, dim='time').sortby('time')

        # Optionally filter to replace no data values with nans
        if mask_invalid_data:
            print('    Masking out invalid values')
            combined_ds = masking.mask_invalid_data(combined_ds)

        # If `lazy_load` is True, return data as a dask array without
        # actually loading it in
        if lazy_load:
            print(f'    Returning {len(combined_ds.time)} observations'
                  ' as a dask array')
            return combined_ds

        else:
            print(f'    Returning {len(combined_ds.time)} observations ')
            return combined_ds.compute()

    # If no data was returned:
    else:
        print('No data returned for query')
        return None
