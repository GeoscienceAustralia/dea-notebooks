## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA.
Available functions:
load_nbarx
load_sentinel

Last modified: March 2018
Author: Claire Krause

'''

from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube import Datacube

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
    bands_of_interest - List of strings containing the bands to be read in.

    optional
    product - 'nbar' or 'nbart'. Defaults to nbart unless otherwise specified

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
    bands_of_interest - List of strings containing the bands to be read in. Options
                       'red', 'green', 'blue', 'nir', 'swir1', 'swir2'

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
