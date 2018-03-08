## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA.
Available functions:
load_nbarx

Last modified: March 2018
Author: Claire Krause

'''

from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube import Datacube
dc = Datacube(app = 'test')

def load_nbarx(sensor, query, bands_of_interest, product = 'nbart'): 
    '''loads nbar or nbart data for a sensor, masks using pq, then filters 
    out terrain -999s
    Last modified: March 2018
    Author: Bex Dunn
    Modified by: Claire Krause
    
    This function requires the following be loaded:
    from datacube.helpers import ga_pq_fuser
    from datacube.storage import masking
    from datacube import Datacube
    dc = Datacube(app = 'test')
    
    inputs
    sensor - Options are 'ls5', 'ls7', 'ls8'
    query - A dict containing the query bounds. Can include lat/lon, time etc
    bands_of_interest - List of strings containing the bands to be read in. Options
                       'red', 'green', 'blue', 'nir', 'swir1', 'swir2'

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
    ds = dc.load(product = product_name, measurements = bands_of_interest,
                 group_by = 'solar_day', **query)
    #grab crs defs from loaded ds if ds exists
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
            print('masked {} with {} and filtered terrain'.format(product_name, 
                                                                  mask_product))
            # nbarT is correctly used to correct terrain by replacing -999.0 with nan
            ds = ds.where(ds!=-999.0)
        else: 
            print('did not mask {} with {}'.format(product_name, mask_product))
    else:
        print ('did not load {}'.format(product_name)) 

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None
