## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA.
Available functions:

    load_nbarx
    load_sentinel
    dataset_to_geotiff
    array_to_geotiff

Last modified: March 2018
Author: Claire Krause
Modified by: Robbi Bishop-Taylor

'''

# Load modules
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import gdal


def load_nbarx(dc, sensor, query, product = 'nbart', **bands_of_interest): 
    '''loads nbar or nbart data for a sensor, masks using pq, then filters 
    out terrain -999s

    Last modified: March 2018
    Author: Bex Dunn
    Modified by: Claire Krause
    
    This function requires the following be loaded:
    from datacube.helpers import ga_pq_fuser
    from datacube.storage import masking
    from datacube import Datacube
    
    inputs
    dc - handle for the Datacube to import from. This allows you to also use dev environments
	 if that have been imported into the environment.
    sensor - Options are 'ls5', 'ls7', 'ls8'
    query - A dict containing the query bounds. Can include lat/lon, time etc

    optional
    product - 'nbar' or 'nbart'. Defaults to nbart unless otherwise specified
    bands_of_interest - List of strings containing the bands to be read in. Options
                       'red', 'green', 'blue', 'nir', 'swir1', 'swir2'

    outputs
    ds - Extracted and pq filtered dataset
    crs - ds coordinate reference system
    affine - ds affine
    '''  
    dataset = []
    product_name = '{}_{}_albers'.format(sensor, product)
    print('loading {}'.format(product_name))
    if bands_of_interest:
    	ds = dc.load(product = product_name, measurements = bands_of_interest,
                     group_by = 'solar_day', **query)
    else:
        ds = dc.load(product = product_name, group_by = 'solar_day', **query)  
    if ds.variables:
        crs = ds.crs
        affine = ds.affine
        print('loaded {}'.format(product_name))
        mask_product = '{}_{}_albers'.format(sensor, 'pq')
        sensor_pq = dc.load(product = mask_product, fuse_func = ga_pq_fuser,
                            group_by = 'solar_day', **query)
        if sensor_pq.variables:
            print('making mask {}'.format(mask_product))
            cloud_free = masking.make_mask(sensor_pq.pixelquality,
                                           cloud_acca ='no_cloud',
                                           cloud_shadow_acca = 'no_cloud_shadow',                           
                                           cloud_shadow_fmask = 'no_cloud_shadow',
                                           cloud_fmask = 'no_cloud',
                                           blue_saturated = False,
                                           green_saturated = False,
                                           red_saturated = False,
                                           nir_saturated = False,
                                           swir1_saturated = False,
                                           swir2_saturated = False,
                                           contiguous = True)
            ds = ds.where(cloud_free)
            ds.attrs['crs'] = crs
            ds.attrs['affine'] = affine

        if product=='nbart':
            print('masked {} with {} and filtered terrain'.format(product_name,
                                                                  mask_product))
            # nbarT is correctly used to correct terrain by replacing -999.0 with nan
            ds = ds.where(ds!=-999.0)
        elif product=='nbar':
             print('masked {} with {}'.format(product_name, mask_product))
        else: 
            print('did not mask {} with {}'.format(product_name, mask_product))
    else:
        print ('did not load {}'.format(product_name)) 

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None

def load_sentinel(dc, product, query, **bands_of_interest): 
    '''loads a sentinel granule product and masks using pq

    Last modified: March 2018
    Claire Krause: Bex Dunn
    
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
    	ds = dc.load(product = product, measurements = bands_of_interest,
                     group_by = 'solar_day', **query)
    else:
        ds = dc.load(product = product, group_by = 'solar_day', **query)  
    if ds.variables:
        crs = ds.crs
        affine = ds.affine
        print('loaded {}'.format(product))
        print('making mask')
        clear_pixels = ds.pixel_quality == 1
        ds = ds.where(clear_pixels)
        ds.attrs['crs'] = crs
        ds.attrs['affine'] = affine
    else:
        print ('did not load {}'.format(product)) 

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None


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

    Note: this function cuurrently requires the data have lat/lon only, i.e. no
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



def array_to_geotiff(fname, data, geo_transform, projection, nodata_val):
    """
    Create a single band GeoTIFF file with data from array. Because this
    works with simple arrays rather than xarray datasets from DEA, it requires
    the use to pass in geotransform and projection data for the output raster

    Last modified: March 2018
    Author: Robbi Bishop-Taylor

    :attr fname: output file path
    :attr data: input array
    :attr geo_transform: geotransform for output raster
    :attr projection: projection for output raster
    :attr nodata_val: value to convert to nodata in output raster
    """

    # Set up driver
    driver = gdal.GetDriverByName('GTiff')

    # Create raster of given size and projection
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, gdal.GDT_Byte)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)

    # Write data to array and set nodata values
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(nodata_val)

    # Close file
    dataset = None
