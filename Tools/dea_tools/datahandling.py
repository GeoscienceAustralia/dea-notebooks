## dea_datahandling.py
'''
Loading and manipulating Digital Earth Australia products and data
using the Open Data Cube and xarray.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one
on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: August 2022
'''

# Import required packages
import os
import zipfile
import numexpr
import datetime
import requests
import warnings
import odc.algo
import dask
import numpy as np
import pandas as pd
import dask.array as da
import xarray as xr
import skimage.transform
import sklearn.decomposition
from skimage.exposure import match_histograms
from skimage.color import rgb2hsv, hsv2rgb
from osgeo import gdal
from random import randint
from collections import Counter
from odc.algo import mask_cleanup
from datacube.utils import masking
from scipy.ndimage import binary_dilation
from datacube.utils.dates import normalise_dt


def _dc_query_only(**kw):
    """
    Remove load-only parameters, the rest can be passed to Query

    Returns
    -------
    dict of query parameters
    """

    def _impl(measurements=None,
              output_crs=None,
              resolution=None,
              resampling=None,
              skip_broken_datasets=None,
              dask_chunks=None,
              fuse_func=None,
              align=None,
              datasets=None,
              progress_cbk=None,
              group_by=None,
              **query):
        return query

    return _impl(**kw)


def _common_bands(dc, products):
    """
    Takes a list of products and returns a list of measurements/bands
    that are present in all products

    Returns
    -------
    List of band names
    """
    common = None
    bands = None

    for p in products:
        p = dc.index.products.get_by_name(p)
        if common is None:
            common = set(p.measurements)
            bands = list(p.measurements)
        else:
            common = common.intersection(set(p.measurements))
    return [band for band in bands if band in common]


def load_ard(dc,
             products=None,
             min_gooddata=0.0,
             fmask_categories=['valid', 'snow', 'water'],
             mask_pixel_quality=True,
             mask_filters=None,
             mask_contiguity=False,
             ls7_slc_off=True,
             predicate=None,
             dtype='auto',
             **kwargs):

    """
    Loads and combines Landsat Collection 3 or Sentinel 2 Definitive
    and Near Real Time data for multiple sensors (i.e. ls5t, ls7e and
    ls8c for Landsat; s2a and s2b for Sentinel 2), optionally applies
    pixel quality and contiguity masks, and drops time steps that
    contain greater than a minimum proportion of good quality (e.g. non-
    cloudy or shadowed) pixels.

    The function supports loading the following DEA products:
        * ga_ls5t_ard_3
        * ga_ls7e_ard_3
        * ga_ls8c_ard_3
        * ga_s2am_ard_3
        * ga_s2bm_ard_3

    Last modified: November 2022

    Parameters
    ----------
    dc : datacube Datacube object
        The Datacube to connect to, i.e. `dc = datacube.Datacube()`.
        This allows you to also use development datacubes if required.
    products : list
        A list of product names to load data from. Valid options are
        ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'] for Landsat,
        ['ga_s2am_ard_3', 'ga_s2bm_ard_3'] for Sentinel 2.
    min_gooddata : float, optional
        An optional float giving the minimum percentage of good quality
        pixels required for a satellite observation to be loaded.
        Defaults to 0.0 which will return all observations regardless of
        pixel quality (set to e.g. 0.99 to return only observations with
        more than 99% good quality pixels).
    fmask_categories : list, optional
        An optional list of fmask category names to treat as good
        quality pixels in the above `min_gooddata` calculation, and for
        masking data by pixel quality (if `mask_pixel_quality=True`).
        The default is `['valid', 'snow', 'water']` which will return
        non-cloudy or shadowed land, snow and water pixels. Choose from:
        'nodata', 'valid', 'cloud', 'shadow', 'snow', and 'water'.
    mask_pixel_quality : bool, optional
        An optional boolean indicating whether to mask out poor quality
        pixels using fmask based on the `fmask_categories` provided
        above. The default is True, which will set poor quality pixels
        to NaN if `dtype='auto'` (which will convert the data to
        'float32'), or set poor quality pixels to the data's native
        nodata value if `dtype='native' (which can be useful for
        reducing memory).
    mask_filters : iterable of tuples, optional
        Iterable tuples of morphological operations - ("<operation>", <radius>)
        to apply to the pixel quality mask, where:
        operation: string, can be one of these morphological operations:
            * ``'closing'``  = remove small holes in cloud - morphological closing
            * ``'opening'``  = shrinks away small areas of the mask
            * ``'dilation'`` = adds padding to the mask
            * ``'erosion'``  = shrinks bright regions and enlarges dark regions
        radius: int
        e.g. ``mask_filters=[('erosion', 5),("opening", 2),("dilation", 2)]``
    mask_contiguity : str or bool, optional
        An optional string or boolean indicating whether to mask out
        pixels missing data in any band (i.e. "non-contiguous" values).
        This can be important for generating clean composite datasets.
        The default is False, which will ignore non-contiguous values
        completely. If loading NBART data, set the parameter to:
        `mask_contiguity='nbart_contiguity'`. If loading NBAR data,
        specify `mask_contiguity='nbar_contiguity'` instead.
        Non-contiguous pixels will be set to NaN if `dtype='auto'`, or
        set to the data's native nodata value if `dtype='native'`
        (which can be useful for reducing memory).
    dtype : string, optional
        An optional parameter that controls the data type/dtype that
        layers are coerced to after loading. Valid values: 'native',
        'auto', 'float{16|32|64}'. When 'auto' is used, the data will be
        converted to `float32` if masking is used, otherwise data will
        be returned in the native data type of the data. Be aware that
        if data is loaded in its native dtype, nodata and masked
        pixels will be returned with the data's native nodata value
        (typically -999), not NaN.
    ls7_slc_off : bool, optional
        An optional boolean indicating whether to include data from
        after the Landsat 7 SLC failure (i.e. SLC-off). Defaults to
        True, which keeps all Landsat 7 observations > May 31 2003.
    predicate : function, optional
        An optional function that can be passed in to restrict the
        datasets that are loaded by the function. A predicate function
        should take a `datacube.model.Dataset` object as an input (i.e.
        as returned from `dc.find_datasets`), and return a boolean.
        For example, a predicate function could be used to return True
        for only datasets acquired in January:
        `dataset.time.begin.month == 1`
    **kwargs :
        A set of keyword arguments to `dc.load` that define the
        spatiotemporal query and load parameters used to extract data.
        Keyword arguments can either be listed directly in the
        `load_ard` call like any other parameter (e.g.
        `measurements=['nbart_red']`), or by passing in a query kwarg
        dictionary (e.g. `**query`). Keywords can include `measurements`,
        `x`, `y`, `time`, `resolution`, `resampling`, `group_by`, `crs`;
        see the `dc.load` documentation for all possible options:
        https://datacube-core.readthedocs.io/en/latest/dev/api/generate/datacube.Datacube.load.html

    Returns
    -------
    combined_ds : xarray Dataset
        An xarray dataset containing only satellite observations that
        contains greater than `min_gooddata` proportion of good quality
        pixels.

    """

    #########
    # Setup #
    #########

    # Use 'nbart_contiguity' by default if mask_contiguity is true
    if mask_contiguity is True:
        mask_contiguity = 'nbart_contiguity'

    # We deal with `dask_chunks` separately
    dask_chunks = kwargs.pop('dask_chunks', None)
    requested_measurements = kwargs.pop('measurements', None)

    # Warn user if they combine lazy load with min_gooddata
    if (min_gooddata > 0.0) and dask_chunks is not None:
        warnings.warn("Setting 'min_gooddata' percentage to > 0.0 "
                      "will cause dask arrays to compute when "
                      "loading pixel-quality data to calculate "
                      "'good pixel' percentage. This can "
                      "slow the return of your dataset.")

    # Verify that products were provided, and determine if Sentinel-2
    # or Landsat data is being loaded
    if not products:
        raise ValueError("Please provide a list of product names "
                         "to load data from. Valid options are: \n"
                         "['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'] "
                         "for Landsat, ['ga_s2am_ard_3', "
                         "'ga_s2bm_ard_3'] \nfor Sentinel 2.")
    elif all(['ls' in product for product in products]):
        product_type = 'ls'
    elif all(['s2' in product for product in products]):
        product_type = 's2'

    fmask_band = 'fmask'
    measurements = (requested_measurements.copy() if
                    requested_measurements else None)

    if measurements is None:

        # Deal with "load all" case: pick a set of bands common across
        # all products
        measurements = _common_bands(dc, products)

        # If no `measurements` are specified, Landsat ancillary bands are
        # loaded with a 'oa_' prefix, but Sentinel-2 bands are not. As a
        # work-around, we need to rename the default contiguity and fmask
        # bands if loading Landsat data without specifying `measurements`
        if product_type == 'ls':
            mask_contiguity = (f'oa_{mask_contiguity}' if
                               mask_contiguity else False)
            fmask_band = f'oa_{fmask_band}'

    # If `measurements` are specified but do not include fmask or
    # contiguity variables, add these to `measurements`
    if fmask_band not in measurements:
        measurements.append(fmask_band)
    if mask_contiguity and mask_contiguity not in measurements:
        measurements.append(mask_contiguity)

    # Get list of data and mask bands so that we can later exclude
    # mask bands from being masked themselves
    data_bands = [band for band in measurements if
                  band not in (fmask_band, mask_contiguity)]
    mask_bands = [band for band in measurements if band not in data_bands]

    #################
    # Find datasets #
    #################

    # Pull out query params only to pass to dc.find_datasets
    query = _dc_query_only(**kwargs)

    # Extract datasets for each product using subset of dcload_kwargs
    dataset_list = []

    # Get list of datasets for each product
    print('Finding datasets')
    for product in products:

        # Obtain list of datasets for product
        print(f'    {product} (ignoring SLC-off observations)'
              if not ls7_slc_off and product == 'ga_ls7e_ard_3'
              else f'    {product}')
        datasets = dc.find_datasets(product=product, **query)

        # Remove Landsat 7 SLC-off observations if ls7_slc_off=False
        if not ls7_slc_off and product == 'ga_ls7e_ard_3':
            datasets = [i for i in datasets if
                        normalise_dt(i.time.begin) <
                        datetime.datetime(2003, 5, 31)]

        # Add any returned datasets to list
        dataset_list.extend(datasets)

    # Raise exception if no datasets are returned
    if len(dataset_list) == 0:
        raise ValueError("No data available for query: ensure that "
                         "the products specified have data for the "
                         "time and location requested")

    # If predicate is specified, use this function to filter the list
    # of datasets prior to load
    if predicate:
        print(f'Filtering datasets using predicate function')
        dataset_list = [ds for ds in dataset_list if predicate(ds)]

    # Raise exception if filtering removes all datasets
    if len(dataset_list) == 0:
        raise ValueError("No data available after filtering with "
                         "predicate function")

    #############
    # Load data #
    #############

    # Note we always load using dask here so that we can lazy load data
    # before filtering by good data
    ds = dc.load(datasets=dataset_list,
                 measurements=measurements,
                 dask_chunks={} if dask_chunks is None else dask_chunks,
                 **kwargs)

    ####################
    # Filter good data #
    ####################

    # Calculate pixel quality mask
    pq_mask = odc.algo.fmask_to_bool(ds[fmask_band],
                                     categories=fmask_categories)

    # The good data percentage calculation has to load in all `fmask`
    # data, which can be slow. If the user has chosen no filtering
    # by using the default `min_gooddata = 0`, we can skip this step
    # completely to save processing time
    if min_gooddata > 0.0:

        # Compute good data for each observation as % of total pixels
        print('Counting good quality pixels for each time step')
        data_perc = (pq_mask.sum(axis=[1, 2], dtype='int32') /
                     (pq_mask.shape[1] * pq_mask.shape[2]))
        keep = (data_perc >= min_gooddata).persist()

        # Filter by `min_gooddata` to drop low quality observations
        total_obs = len(ds.time)
        ds = ds.sel(time=keep)
        pq_mask = pq_mask.sel(time=keep)

        print(f'Filtering to {len(ds.time)} out of {total_obs} '
              f'time steps with at least {min_gooddata:.1%} '
              f'good quality pixels')
    
    # Morphological filtering on cloud masks
    if (mask_filters is not None) & (mask_pixel_quality):
        print(f"Applying morphological filters to pixel quality mask: {mask_filters}")
        pq_mask = mask_cleanup(pq_mask, mask_filters=mask_filters)
    
    ###############
    # Apply masks #
    ###############

    # Create an overall mask to hold both pixel quality and contiguity
    mask = None

    # Add pixel quality mask to overall mask
    if mask_pixel_quality:
        print('Applying pixel quality/cloud mask')
        mask = pq_mask

    # Add contiguity mask to overall mask
    if mask_contiguity:
        print('Applying contiguity mask')
        cont_mask = ds[mask_contiguity] == 1

        # If mask already has data if mask_pixel_quality == True,
        # multiply with cont_mask to perform a logical 'or' operation
        # (keeping only pixels good in both)
        mask = cont_mask if mask is None else mask * cont_mask

    # Split into data/masks bands, as conversion to float and masking
    # should only be applied to data bands
    ds_data = ds[data_bands]
    ds_masks = ds[mask_bands]

    # Mask data if either of the above masks were generated
    if mask is not None:
        ds_data = odc.algo.keep_good_only(ds_data, where=mask)

    # Automatically set dtype to either native or float32 depending
    # on whether masking was requested
    if dtype == 'auto':
        dtype = 'native' if mask is None else 'float32'

    # Set nodata values using odc.algo tools to reduce peak memory
    # use when converting data dtype
    if dtype != 'native':
        ds_data = odc.algo.to_float(ds_data, dtype=dtype)

    # Put data and mask bands back together
    attrs = ds.attrs
    ds = xr.merge([ds_data, ds_masks])
    ds.attrs.update(attrs)

    ###############
    # Return data #
    ###############

    # Drop bands not originally requested by user
    if requested_measurements:
        ds = ds[requested_measurements]

    # If user supplied dask_chunks, return data as a dask array without
    # actually loading it in
    if dask_chunks is not None:
        print(f'Returning {len(ds.time)} time steps as a dask array')
        return ds
    else:
        print(f'Loading {len(ds.time)} time steps')
        return ds.compute()


def array_to_geotiff(fname, data, geo_transform, projection,
                     nodata_val=0, dtype=gdal.GDT_Float32):
    """
    Create a single band GeoTIFF file with data from an array.

    Because this works with simple arrays rather than xarray datasets
    from DEA, it requires geotransform info ("(upleft_x, x_size,
    x_rotation, upleft_y, y_rotation, y_size)") and projection data
    (in "WKT" format) for the output raster. These are typically
    obtained from an existing raster using the following GDAL calls:

        import gdal
        gdal_dataset = gdal.Open(raster_path)
        geotrans = gdal_dataset.GetGeoTransform()
        prj = gdal_dataset.GetProjection()

    ...or alternatively, directly from an xarray dataset:

        geotrans = xarraydataset.geobox.transform.to_gdal()
        prj = xarraydataset.geobox.crs.wkt

    Parameters
    ----------
    fname : str
        Output geotiff file path including extension
    data : numpy array
        Input array to export as a geotiff
    geo_transform : tuple
        Geotransform for output raster; e.g. "(upleft_x, x_size,
        x_rotation, upleft_y, y_rotation, y_size)"
    projection : str
        Projection for output raster (in "WKT" format)
    nodata_val : int, optional
        Value to convert to nodata in the output raster; default 0
    dtype : gdal dtype object, optional
        Optionally set the dtype of the output raster; can be
        useful when exporting an array of float or integer values.
        Defaults to gdal.GDT_Float32

    """
    warnings.warn(
        "The `array_to_geotiff` function is deprecated, and will "
        "be removed from future versions of `dea-tools`.",
        FutureWarning)

    # Set up driver
    driver = gdal.GetDriverByName('GTiff')

    # Create raster of given size and projection
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, dtype)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)

    # Write data to array and set nodata values
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(nodata_val)

    # Close file
    dataset = None


def mostcommon_crs(dc, product, query):
    """
    Takes a given query and returns the most common CRS for observations
    returned for that spatial extent. This can be useful when your study
    area lies on the boundary of two UTM zones, forcing you to decide
    which CRS to use for your `output_crs` in `dc.load`.

    Parameters
    ----------
    dc : datacube Datacube object
        The Datacube to connect to, i.e. `dc = datacube.Datacube()`.
        This allows you to also use development datacubes if required.
    product : str
        A product name (or list of product names) to load CRSs from.
    query : dict
        A datacube query including x, y and time range to assess for the
        most common CRS

    Returns
    -------
    epsg_string : str
        An EPSG string giving the most common CRS from all datasets returned
        by the query above

    """
    
    # Find list of datasets matching query for either product or 
    # list of products
    if isinstance(product, list):
        matching_datasets = []
        for i in product:
            matching_datasets.extend(dc.find_datasets(product=i, 
                                                      **query))        
    else:
        matching_datasets = dc.find_datasets(product=product, **query)

    # Extract all CRSs
    crs_list = [str(i.crs) for i in matching_datasets]
    
    # If CRSs are returned
    if len(crs_list) > 0:

        # Identify most common CRS
        crs_counts = Counter(crs_list)
        crs_mostcommon = crs_counts.most_common(1)[0][0]

        # Warn user if multiple CRSs are encountered
        if len(crs_counts.keys()) > 1:

            warnings.warn(f'Multiple UTM zones {list(crs_counts.keys())} '
                          f'were returned for this query. Defaulting to '
                          f'the most common zone: {crs_mostcommon}',
                          UserWarning)

        return crs_mostcommon
    
    else:
        
        raise ValueError(f'No CRS was returned as no data was found for '
                         f'the supplied product ({product}) and query. '
                         f'Please ensure that data is available for '
                         f'{product} for the spatial extents and time '
                         f'period specified in the query (e.g. by using '
                         f'the Data Cube Explorer for this datacube '
                         f'instance).')


def download_unzip(url,
                   output_dir=None,
                   remove_zip=True):
    """
    Downloads and unzips a .zip file from an external URL to a local
    directory.

    Parameters
    ----------
    url : str
        A string giving a URL path to the zip file you wish to download
        and unzip
    output_dir : str, optional
        An optional string giving the directory to unzip files into.
        Defaults to None, which will unzip files in the current working
        directory
    remove_zip : bool, optional
        An optional boolean indicating whether to remove the downloaded
        .zip file after files are unzipped. Defaults to True, which will
        delete the .zip file.

    """

    # Get basename for zip file
    zip_name = os.path.basename(url)

    # Raise exception if the file is not of type .zip
    if not zip_name.endswith('.zip'):
        raise ValueError(f'The URL provided does not point to a .zip '
                         f'file (e.g. {zip_name}). Please specify a '
                         f'URL path to a valid .zip file')

    # Download zip file
    print(f'Downloading {zip_name}')
    r = requests.get(url)
    with open(zip_name, 'wb') as f:
        f.write(r.content)

    # Extract into output_dir
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
        print(f'Unzipping output files to: '
              f'{output_dir if output_dir else os.getcwd()}')

    # Optionally cleanup
    if remove_zip:
        os.remove(zip_name)


def wofs_fuser(dest, src):
    """
    Fuse two WOfS water measurements represented as ``ndarray``s.

    Note: this is a copy of the function located here:
    https://github.com/GeoscienceAustralia/digitalearthau/blob/develop/digitalearthau/utils.py
    """
    empty = (dest & 1).astype(np.bool)
    both = ~empty & ~((src & 1).astype(np.bool))
    dest[empty] = src[empty]
    dest[both] |= src[both]


def dilate(array, dilation=10, invert=True):
    """
    Dilate a binary array by a specified nummber of pixels using a
    disk-like radial dilation.

    By default, invalid (e.g. False or 0) values are dilated. This is
    suitable for applications such as cloud masking (e.g. creating a
    buffer around cloudy or shadowed pixels). This functionality can
    be reversed by specifying `invert=False`.

    Parameters
    ----------
    array : array
        The binary array to dilate.
    dilation : int, optional
        An optional integer specifying the number of pixels to dilate
        by. Defaults to 10, which will dilate `array` by 10 pixels.
    invert : bool, optional
        An optional boolean specifying whether to invert the binary
        array prior to dilation. The default is True, which dilates the
        invalid values in the array (e.g. False or 0 values).

    Returns
    -------
    An array of the same shape as `array`, with valid data pixels
    dilated by the number of pixels specified by `dilation`.
    """

    y, x = np.ogrid[
        -dilation: (dilation + 1),
        -dilation: (dilation + 1),
    ]

    # disk-like radial dilation
    kernel = (x * x) + (y * y) <= (dilation + 0.5) ** 2

    # If invert=True, invert True values to False etc
    if invert:
        array = ~array

    return ~binary_dilation(array.astype(np.bool),
                            structure=kernel.reshape((1,) + kernel.shape))


def paths_to_datetimeindex(paths, string_slice=(0, 10)):
    """
    Helper function to generate a Pandas datetimeindex object
    from dates contained in a file path string.

    Parameters
    ----------
    paths : list of strings
        A list of file path strings that will be used to extract times
    string_slice : tuple
        An optional tuple giving the start and stop position that
        contains the time information in the provided paths. These are
        applied to the basename (i.e. file name) in each path, not the
        path itself. Defaults to (0, 10).

    Returns
    -------
    datetime : pandas.DatetimeIndex
        A pandas.DatetimeIndex object containing a 'datetime64[ns]' derived
        from the file paths provided by `paths`.
    """

    date_strings = [os.path.basename(i)[slice(*string_slice)]
                    for i in paths]
    return pd.to_datetime(date_strings)


def _select_along_axis(values, idx, axis):
    other_ind = np.ix_(*[np.arange(s) for s in idx.shape])
    sl = other_ind[:axis] + (idx,) + other_ind[axis:]
    return values[sl]


def first(array: xr.DataArray,
          dim: str,
          index_name: str = None) -> xr.DataArray:
    """
    Finds the first occuring non-null value along the given dimension.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to reduce by finding the first
        non-null value.

    Returns
    -------
    reduced : xr.DataArray
        An array of the first non-null values.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension where
        the last value was found.
    """

    axis = array.get_axis_num(dim)
    idx_first = np.argmax(~pd.isnull(array), axis=axis)
    reduced = array.reduce(_select_along_axis, idx=idx_first, axis=axis)
    reduced[dim] = array[dim].isel({dim: xr.DataArray(idx_first,
                                                      dims=reduced.dims)})
    if index_name is not None:
        reduced[index_name] = xr.DataArray(idx_first, dims=reduced.dims)
    return reduced


def last(array: xr.DataArray,
         dim: str,
         index_name: str = None) -> xr.DataArray:
    """
    Finds the last occuring non-null value along the given dimension.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to reduce by finding the last non-null
        value.
    index_name : str, optional
        If given, the name of a coordinate to be added containing the
        index of where on the dimension the nearest value was found.

    Returns
    -------
    reduced : xr.DataArray
        An array of the last non-null values.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension where
        the last value was found.
    """

    axis = array.get_axis_num(dim)
    rev = (slice(None),) * axis + (slice(None, None, -1),)
    idx_last = -1 - np.argmax(~pd.isnull(array)[rev], axis=axis)
    reduced = array.reduce(_select_along_axis, idx=idx_last, axis=axis)
    reduced[dim] = array[dim].isel({dim: xr.DataArray(idx_last,
                                                      dims=reduced.dims)})
    if index_name is not None:
        reduced[index_name] = xr.DataArray(idx_last, dims=reduced.dims)
    return reduced


def nearest(array: xr.DataArray,
            dim: str, target,
            index_name: str = None) -> xr.DataArray:
    """
    Finds the nearest values to a target label along the given
    dimension, for all other dimensions.

    E.g. For a DataArray with dimensions ('time', 'x', 'y')

        nearest_array = nearest(array, 'time', '2017-03-12')

    will return an array with the dimensions ('x', 'y'), with non-null
    values found closest for each (x, y) pixel to that location along
    the time dimension.

    The returned array will include the 'time' coordinate for each x,y
    pixel that the nearest value was found.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to look for the target label.
    target : same type as array[dim]
        The value to look up along the given dimension.
    index_name : str, optional
        If given, the name of a coordinate to be added containing the
        index of where on the dimension the nearest value was found.

    Returns
    -------
    nearest_array : xr.DataArray
        An array of the nearest non-null values to the target label.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension closest
        to the given target label.
    """

    before_target = slice(None, target)
    after_target = slice(target, None)

    da_before = array.sel({dim: before_target})
    da_after = array.sel({dim: after_target})

    da_before = (last(da_before, dim, index_name) if
                 da_before[dim].shape[0] else None)
    da_after = (first(da_after, dim, index_name) if
                da_after[dim].shape[0] else None)

    if da_before is None and da_after is not None:
        return da_after
    if da_after is None and da_before is not None:
        return da_before

    target = array[dim].dtype.type(target)
    is_before_closer = (abs(target - da_before[dim]) <
                        abs(target - da_after[dim]))
    nearest_array = xr.where(is_before_closer, da_before, da_after)
    nearest_array[dim] = xr.where(is_before_closer,
                                  da_before[dim],
                                  da_after[dim])

    if index_name is not None:
        nearest_array[index_name] = xr.where(is_before_closer,
                                             da_before[index_name],
                                             da_after[index_name])
    return nearest_array


def parallel_apply(ds, dim, func, *args):
    """
    Applies a custom function in parallel along the dimension of an 
    xarray.Dataset or xarray.DataArray.
    
    The function can be any function that can be applied to an
    individual xarray.Dataset or xarray.DataArray (e.g. data for a 
    single timestep). The function should also return data in 
    xarray.Dataset or xarray.DataArray format.
    
    This function is useful as a simple method for parallising code
    that cannot easily be parallised using Dask.
    
    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        xarray data with a dimension `dim` to apply the custom function
        along.
    dim : string
        The dimension along which the custom function will be applied.
    func : function
        The function that will be applied in parallel to each array
        along dimension `dim`. The first argument passed to this
        function should be the array along `dim`.
    *args :
        Any number of arguments that will be passed to `func`.
        
    Returns
    -------
    xarray.Dataset
        A concatenated dataset containing an output for each array
        along the input `dim` dimension.
    """

    from concurrent.futures import ProcessPoolExecutor
    from tqdm import tqdm
    from itertools import repeat

    with ProcessPoolExecutor() as executor:

        # Apply func in parallel
        groups = [group for (i, group) in ds.groupby(dim)]
        to_iterate = (groups, *(repeat(i, len(groups)) for i in args))
        out_list = list(tqdm(executor.map(func, *to_iterate), total=len(groups)))

    # Combine to match the original dataset
    return xr.concat(out_list, dim=ds[dim])


def _apply_weights(da, band_weights):
    """
    Apply weights from a dictionary to the bands of a
    multispectral xarray.DataArray.  Raises a ValueError if any
    bands in `da` are not present in the `band_weights` dictionary.

    Parameters
    ----------
    da : xarray.DataArray object
        DataArray containing multispectral data. The dataarray
        should contain a "variable" dimension that corresponds
        to the different bands of the data.
    band_weights : dict
        Mapping of band names to weights to be applied. The keys
        of the dictionary should be the names of the bands in the
        "variable" dimension of `da`, and the values should be
        the weights to be applied to each band.

    Returns
    -------
    xarray.DataArray object
        DataArray with weights applied to the bands.
    """

    # Identify any bands without weights, and raise an
    # error if they exist
    bands_without_weights = set(da["variable"].values) - set(band_weights.keys())
    if len(bands_without_weights) > 0:
        raise ValueError(
            f"The following multispectral bands are missing from the "
            f"`band_weights` dictionary: {bands_without_weights}.\n"
            f"Ensure that weights are supplied for all multispectral "
            f"bands in `ds`, or set `band_weights=None`."
        )

    # Create xr.DataArray with weights for each variable
    # along the "variable" dimension
    weights_da = xr.DataArray(
        data=list(band_weights.values()),
        coords={"variable": list(band_weights.keys())},
        dims="variable",
    )

    # Apply weights
    return da.weighted(weights_da)


def _brovey_pansharpen(ds, pan_band, band_weights=None):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the Brovey transform (with optional per-band weights).

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    band_weights : dict, optional
        Mapping of band names to weights to be applied to each band when
        calculating the sum of all multispectral bands. The keys of
        the dictionary should be the names of the bands, and the values
        should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting `band_weights=None`
        will use a simple unweighted sum.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Create new dataarrays with and without pan band
    da_nopan = ds.drop(pan_band).to_array()
    da_pan = ds[pan_band]

    # Calculate weighted sum
    if band_weights is not None:
        da_total = _apply_weights(da_nopan, band_weights).sum(dim="variable")
    else:
        da_total = da_nopan.sum(dim="variable")

    # Perform Brovey Transform in form of: band / total * panchromatic
    da_pansharpened = da_nopan / da_total * da_pan
    ds_pansharpened = da_pansharpened.to_dataset("variable")

    return ds_pansharpened


def _esri_pansharpen(ds, pan_band, band_weights=None):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the ESRI transform (with optional per-band weights).

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    band_weights : dict, optional
        Mapping of band names to weights to be applied to each band when
        calculating the mean of all multispectral bands. The keys of
        the dictionary should be the names of the bands, and the values
        should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting `band_weights=None`
        will use a simple unweighted mean.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Create new dataarrays with and without pan band
    da_nopan = ds.drop(pan_band).to_array()
    da_pan = ds[pan_band]

    # Calculate weighted sum
    if band_weights is not None:
        da_mean = _apply_weights(da_nopan, band_weights).mean(dim="variable")
    else:
        da_mean = da_nopan.mean(dim="variable")

    # Calculate adjustment and apply to multispectral bands
    adj = da_pan - da_mean
    da_pansharpened = da_nopan + adj
    ds_pansharpened = da_pansharpened.to_dataset("variable")

    return ds_pansharpened


def _simple_mean_pansharpen(ds, pan_band):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the Simple Mean transform.

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Create new dataarrays with and without pan band
    ds_nopan = ds.drop(pan_band)
    da_pan = ds[pan_band]

    # Take mean of pan band and RGBs
    ds_pansharpened = (ds_nopan + da_pan) / 2.0

    return ds_pansharpened


def _hsv_timestep_pansharpen(ds_i, pan_band):
    """
    Perform pansharpening on a single timestep of a multispectral
    dataset using the Hue Saturation Value (HSV) transform.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Convert to an xr.DataArray and move "variable" to end
    da_i = ds_i.to_array().transpose(..., "variable")

    # Create new dataarrays with and without pan band
    da_i_nopan = da_i.drop(pan_band, dim="variable")
    da_i_pan = da_i.sel(variable=pan_band)

    # Convert to HSV colour space
    hsv = rgb2hsv(da_i_nopan)

    # Replace value (lightness) channel with pan band data
    hsv[:, :, 2] = da_i_pan.values

    # Convert back to RGB colour space
    pansharped_array = hsv2rgb(hsv)

    # Add back into original array, reshape and return dataframe
    da_i_nopan[:] = pansharped_array
    ds_pansharpened = da_i_nopan.to_dataset("variable")

    return ds_pansharpened


def _pca_timestep_pansharpen(ds_i, pan_band, pca_rescaling="histogram"):
    """
    Perform pansharpening on a single timestep of a multispectral
    dataset using the principal component analysis (PCA) transform.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    pca_rescaling : str, optional
        Method to use for rescaling pan band to more closely match the
        distribution of values in the first PCA component. "simple"
        scales the pan band values to more closely match the first PCA
        component by subtracting the mean of the pan band values from
        each value, scaling the resulting values by the ratio of the
        standard deviations of the first PCA component and the pan band,
        and adding back the mean of the first PCA component.
        "histogram" uses a histogram matching technique to adjust the
        pan band values so that the resulting histogram more closely
        matches the histogram of the first PCA component.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Reshape to 2D by stacking x and y dimensions to prepare it
    # as an input to PCA. Drop NA rows as these are not supported
    # by `pca.fit_transform`.
    da_2d = (
        ds_i.to_array()
        .stack(pixel=("y", "x"))
        .transpose("pixel", "variable")
        .dropna(dim="pixel")
    )

    # Create new dataarrays with and without pan band
    da_2d_nopan = da_2d.drop(pan_band, dim="variable")
    da_2d_pan = da_2d.sel(variable=pan_band)

    # Apply PCA transformation
    pca = sklearn.decomposition.PCA()
    pca_array = pca.fit_transform(da_2d_nopan)

    # Rescale pan band to more closely match the first PCA component
    if pca_rescaling == "simple":
        pca_array[:, 0] = (da_2d_pan.values - da_2d_pan.values.mean()) * (
            pca_array[:, 0].std() / da_2d_pan.values.std()
        ) + pca_array[:, 0].mean()
    elif pca_rescaling == "histogram":
        pca_array[:, 0] = match_histograms(da_2d_pan.values, pca_array[:, 0])

    # Apply reverse PCA transform to restore multispectral array
    pansharped_array = pca.inverse_transform(pca_array)

    # Add back into original array, reshape and return dataframe
    da_2d_nopan[:] = pansharped_array
    ds_pansharpened = da_2d_nopan.unstack("pixel").to_dataset("variable")

    return ds_pansharpened


def xr_pansharpen(
    ds,
    transform,
    pan_band="nbart_panchromatic",
    return_pan=False,
    output_dtype=None,
    parallelise=False,
    band_weights={"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2},
    pca_rescaling="histogram",
):

    """
    Apply pan-sharpening to multispectral satellite data with one
    or more timesteps. The following pansharpening transforms are
    currently supported:

        - Brovey ("brovey"), with optional band weighting
        - ESRI ("esri"), with optional band weighting
        - Simple mean ("simple mean")
        - PCA ("pca")
        - HSV ("hsv"), similar to IHS

    Note: Pan-sharpening transforms do not necessarily maintain
    the spectral integrity of the input satellite data, and may
    be more suitable for visualisation than quantitative work.

    Parameters
    ----------
    ds : xarray.Dataset
        An xarrray dataset containing the three input multispectral
        bands, and a panchromatic band. This dataset should have
        already been resampled to the spatial resolution of the
        panchromatic band (15 m for Landsat). Due to differences in
        the electromagnetic spectrum covered by the panchromatic band,
        Landsat 8 and 9 data should be supplied with 'blue', 'green',
        and 'red' multispectral bands, while Landsat 7 should be
        supplied with 'green', 'red' and 'NIR'.
    transform : string
        The pansharpening transform to apply to the data. Valid options
        include "brovey", "esri", "simple mean", "pca", "hsv".
    pan_band : string, optional
        The name of the panchromatic band that will be used to
        pansharpen the multispectral data.
    return_pan : bool, optional
        Whether to return the panchromatic band in the output dataset.
        Defaults to False.
    output_dtype : string or numpy.dtype, optional
        The dtype used for the output values. Defaults to the input
        dtype of the multispectral bands in `ds`.
    parallelise: bool, optional
        Whether to parallelise transformations across multiple cores.
        Used for PCA and HSV transforms that are applied to each
        timestep in `ds` individually; defaults to False.
    band_weights : dict, optional
        Used for the Brovey and ESRI transforms. Mapping of band
        names to weights to be applied to each band when calculating
        the sum (Brovey) or mean (ESRI) of all multispectral bands.
        The keys of the dictionary should be the names of the bands,
        and the values should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting `band_weights=None`
        will use a simple unweighted sum (for the Brovey transform)
        or unweighted mean (for the ESRI transform).
    pca_rescaling : str, optional
        Used for the PCA transform. The method to use for rescaling
        pan band to more closely match the distribution of values
        in the first PCA component. "simple" scales the pan band
        values to more closely match the first PCA component by
        subtracting the mean of the pan band values from each value,
        scaling the resulting values by the ratio of the standard
        deviations of the first PCA component and the pan band, and
        adding back the mean of the first PCA component.
        "histogram" uses a histogram matching technique to adjust the
        pan band values so that the resulting histogram more closely
        matches the histogram of the first PCA component.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        An xarrray dataset containing the three pansharpened input
        multispectral bands and optionally the panchromatic band
        (if `return_pan=True`).
    """

    # Assert whether pan band exists in the dataset
    if pan_band not in ds.data_vars:
        raise ValueError(
            f"The specified panchromatic band '{pan_band}' cannot be found in `ds`. "
            f"Specify a panchromatic band name that exists in the dataset using `pan_band=...`."
        )

    # Assert whether exactly three multispectral bands are included in `ds`
    n_multi = len(ds.drop(pan_band).data_vars)
    if n_multi != 3:
        raise ValueError(
            f"`ds` should contain exactly three multispectral bands (not "
            f"including the panchromatic band). However, {n_multi} "
            f"multispectral bands were found: {list(ds.drop(pan_band).data_vars)}. "
        )

    # Define dict linking functions to each transform
    transform_dict = {
        "brovey": _brovey_pansharpen,
        "esri": _esri_pansharpen,
        "simple mean": _simple_mean_pansharpen,
        "pca": _pca_timestep_pansharpen,
        "hsv": _hsv_timestep_pansharpen,
    }

    # If Brovey, ESRI or Simple Mean pansharpening is specified, apply to
    # entire `xr.Dataset` in one go (with optional weights for Brovey, ESRI)
    if transform in ("brovey", "esri", "simple mean"):
        print(f"Applying {transform.capitalize()} pansharpening")
        extra_params = (
            {"band_weights": band_weights} if transform in ("brovey", "esri") else {}
        )
        ds_pansharpened = transform_dict[transform](
            ds,
            pan_band=pan_band,
            **extra_params,
        )

    # Otherwise, apply PCA or HSV pansharpening to each
    # timestep in the `xr.Dataset` using `.apply`
    elif transform in ("pca", "hsv"):

        extra_params = {"pca_rescaling": pca_rescaling} if transform == "pca" else {}

        # Apply pansharpening to all timesteps in data in parallel
        if ("time" in ds.dims) and parallelise:
            print(
                f"Applying {transform.upper()} pansharpening to each timestep in parallel"
            )
            ds_pansharpened = parallel_apply(
                ds,
                "time",
                transform_dict[transform],
                pan_band,
                *extra_params.values(),  # TODO: Update once `parallel_apply` supports kwargs
            )

        # Apply pansharpening to all timesteps in data sequentially
        elif ("time" in ds.dims) and not parallelise:
            print(f"Applying {transform.upper()} pansharpening to each timestep")
            ds_pansharpened = ds.groupby("time").apply(
                transform_dict[transform],
                pan_band=pan_band,
                **extra_params,
            )

        # Otherwise, apply func directly if only one timestep
        else:
            print(f"Applying {transform.upper()} pansharpening")
            ds_pansharpened = transform_dict[transform](
                ds, pan_band=pan_band, **extra_params
            )

    else:
        raise ValueError(
            f"Unsupported value '{transform}' passed to `method`. Please "
            f"provide one of {list(transform_dict.keys())}."
        )

    # Optionally insert pan band back into dataset
    if return_pan:
        ds_pansharpened[pan_band] = ds[pan_band]

    # Return data in original or requested dtype
    return ds_pansharpened.astype(
        ds.to_array().dtype if output_dtype is None else output_dtype
    )