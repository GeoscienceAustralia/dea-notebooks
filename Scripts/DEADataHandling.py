## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA. If a function does not use 
DEA functionality (for example, dc.load or xarrays), it may be better suited for inclusion in SpatialTools.py.
Available functions:

    load_nbarx
    load_sentinel
    tasseled_cap
    dataset_to_geotiff
    open_polygon_from_shapefile
    write_your_netcdf

Last modified: May 2018
Author: Claire Krause
Modified by: Robbi Bishop-Taylor, Bex Dunn

'''

# Load modules
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import gdal
import numpy as np
import xarray as xr
import rasterio

from datacube.utils import geometry
import fiona
import shapely.geometry
from datacube.storage.storage import write_dataset_to_netcdf

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

        # If product is NBAR-T, also correct terrain by replacing -999.0 with nan
        if product == 'nbart':

            print('Masked {} with {} and filtered terrain'.format(product_name,
                                                                  mask_product))
            ds = ds.where(ds != -999.0)

        # If NBAR, simply print successful run
        elif product == 'nbar':

            print('Masked {} with {}'.format(product_name, mask_product))

        else:

            print('Failed to mask {} with {}'.format(product_name, mask_product))

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
            clear_pixels = np.logical_and(ds.pixel_quality != 2, ds.pixel_quality != 3)
            ds = ds.where(clear_pixels)
        ds.attrs['crs'] = crs
        ds.attrs['affine'] = affine
    else:
        print('did not load {}'.format(product))

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None


def tasseled_cap(sensor_data, sensor, tc_bands=['greenness', 'brightness', 'wetness'],
                 drop=True):
    """
    Computes tasseled cap wetness, greenness and brightness bands from a six
    band xarray dataset, and returns a new xarray dataset with old bands
    optionally dropped.

    Coefficients for demonstration purposes only; sourced from:
    Landsat 5: https://doi.org/10.1016/0034-4257(85)90102-6
    Landsat 7: https://doi.org/10.1080/01431160110106113
    Landsat 8: https://doi.org/10.1080/2150704X.2014.915434

    :attr sensor_data: input xarray dataset with six Landsat bands
    :attr tc_bands: list of tasseled cap bands to compute
    (valid options: 'wetness', 'greenness','brightness'
    :attr sensor: Landsat sensor used for coefficient values
    (valid options: 'ls5', 'ls7', 'ls8')
    :attr drop: if 'drop = False', return all original Landsat bands

    :returns: xarray dataset with newly computed tasseled cap bands
    """

    # Copy input dataset
    output_array = sensor_data.copy(deep=True)

    # Coefficients for each tasseled cap band
    wetness_coeff = {'ls5': {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102,
                             'nir': 0.1594, 'swir1': -0.6806, 'swir2': -0.6109},
                     'ls7': {'blue': 0.2626, 'green': 0.2141, 'red': 0.0926,
                             'nir': 0.0656, 'swir1': -0.7629, 'swir2': -0.5388},
                     'ls8': {'blue': 0.1511, 'green': 0.1973, 'red': 0.3283,
                             'nir': 0.3407, 'swir1': -0.7117, 'swir2': -0.4559}}

    greenness_coeff = {'ls5': {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934,
                               'nir': 0.7940, 'swir1': -0.0002, 'swir2': -0.1446},
                       'ls7': {'blue': -0.3344, 'green': -0.3544, 'red': -0.4556,
                               'nir': 0.6966, 'swir1': -0.0242, 'swir2': -0.2630},
                       'ls8': {'blue': -0.2941, 'green': -0.2430, 'red': -0.5424,
                               'nir': 0.7276, 'swir1': -0.0713, 'swir2': -0.1608}}

    brightness_coeff = {'ls5': {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524,
                                'nir': 0.5741, 'swir1': 0.3124, 'swir2': 0.2303},
                        'ls7': {'blue': 0.3561, 'green': 0.3972, 'red': 0.3904,
                                'nir': 0.6966, 'swir1': 0.2286, 'swir2': 0.1596},
                        'ls8': {'blue': 0.3029, 'green': 0.2786, 'red': 0.4733,
                                'nir': 0.5599, 'swir1': 0.508, 'swir2': 0.1872}}

    # Dict to use correct coefficients for each tasseled cap band
    analysis_coefficient = {'wetness': wetness_coeff,
                            'greenness': greenness_coeff,
                            'brightness': brightness_coeff}

    # For each band, compute tasseled cap band and add to output dataset
    for tc_band in tc_bands:
        # Create xarray of coefficient values used to multiply each band of input
        coeff = xr.Dataset(analysis_coefficient[tc_band][sensor])
        sensor_coeff = sensor_data * coeff

        # Sum all bands
        output_array[tc_band] = sensor_coeff.blue + sensor_coeff.green + \
                                sensor_coeff.red + sensor_coeff.nir + \
                                sensor_coeff.swir1 + sensor_coeff.swir2

    # If drop = True, remove original bands
    if drop:
        bands_to_drop = list(sensor_data.data_vars)
        output_array = output_array.drop(bands_to_drop)

    return output_array


def dataset_to_geotiff(filename, data):
    '''
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
    '''

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
    get the geom for the datacube query . It will also make sure you have the correct crs object for the    DEA
    Last modified May 2018
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
    '''this function turns an xarray dataarray into a dataset so we can write it to netcdf. It adds on a crs definition
    from the original array. data = your xarray dataset, dataset_name is a string describing your variable'''    
    #turn array into dataset so we can write the netcdf
    if isinstance(data,xr.DataArray):
        dataset= data.to_dataset(name=dataset_name)
    elif isinstance(data,xr.Dataset):
        dataset = data
    else:
        print('your data might be the wrong type, it is: '+type(data))
    #grab our crs attributes to write a spatially-referenced netcdf
    dataset.attrs['crs'] = crs
    #dataset.attrs['affine'] =affine

    #dataset.dataset_name.attrs['crs'] = crs
    try:
        write_dataset_to_netcdf(dataset, filename)
    except RuntimeError as err:
        print("RuntimeError: {0}".format(err))    
