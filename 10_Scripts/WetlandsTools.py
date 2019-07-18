# WetlandsTools.py
"""
This file contains a set of python functions used in the Wetlands Insight Toolkit.  In future these will be turned into a wetlands insight tool module, with options to select a polygon type or a default setting getting the name off the OBJECTID of the polygon.
Available functions:

    get_RAMSAR_polyName
    get_LRA_polyName
    get_polyname
    get_WetMAP_polyname
    get_masked_tcw
    get_masked_ls578_data

Last modified: July 2019
Author: Bex Dunn

"""

import fiona
from datetime import datetime, timedelta
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio.mask
import rasterio.features
from shapely import geometry
import seaborn as sns
import sys
import xarray as xr

import datacube as dc
from datacube.storage import masking
from datacube.utils import geometry
from digitalearthau.utils import wofs_fuser

sys.path.append('/g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/10_Scripts')
import DEADataHandling, TasseledCapTools


def get_RAMSAR_polyName(shapefile):
    ''' function designed specifically for the RAMSAR wetlands australia shapefile. Takes the shapefile and extracts
    the ramsar name, wetland name and objectID from the ESRI shapefile format and turns it into a useful string for our output.
    :Inputs: shapefile with RAMSAR_NAM, WETLAND_NA, and OBJECTID as properties. 
    Author: Bex Dunn Last Edited: March 2019'''
    # get the ramsar name from the shapes 
    RAMSAR_NAME = '_'.join(shapefile['properties']['RAMSAR_NAM'].split(' '))
    WETLAND_NAME = '_'.join(shapefile['properties']['WETLAND_NA'].split(' '))
    STATE = '_'.join(shapefile['properties']['STATE'].split(' ')) 
    ID = shapefile['id']
    polyName = f'{RAMSAR_NAME}-{WETLAND_NAME}-{STATE}-{ID}'
    print(f'processing polygon {polyName}')
    return(polyName)

def get_LRA_polyName(feature):
    ''' function designed specifically for the LRA australia geojson. Takes the geojson file  and extracts
    the polygon name and objectID andturns it into a useful string for our output.
    :Inputs: geojson with OBJECTID and NAME as properties. 
    Author: Bex Dunn Last Edited: May 2019'''
    # get name shapes 
    #NAME = '_'.join(shpfile['properties']['NAME'].split(' '))
    LOTPLANSEGPAR = f"{feature['properties']['LOTPLAN']}_{feature['properties']['SEGPAR']}"
    OBJECTID = feature['properties']['OBJECTID']
    LOCALITY = feature['properties']['LOCALITY']
    polyName = f'{LOTPLANSEGPAR}-{LOCALITY}-{OBJECTID}'
    print(f'processing polygon {polyName}')
    return(polyName)

def get_polyName(shapefile):
    'function just for the peatlands'
    ID = feature['properties']['OBJECTID']
    polyName = f'peat-{ID}'
    print(f'processing polygon {polyName}')
    return(polyName)

def get_WetMAP_polyName(feature):
    'function just for the WetMAP polygons'
    ID = feature['properties']['FID_1']
    if feature['properties']['LU_NAME']is not None:
        NAME = '_'.join(feature['properties']['LU_NAME'].split(' ')).replace("'","_").replace("/","_") 
        print(NAME)
    elif feature['properties']['NAME_MAIN'] is not None:
        NAME = f'_'.join(feature['properties']['NAME_MAIN'].split(' ')).replace("'","_").replace("/","_") 
    else:     
        NAME = 'WetMAP_polygon'  
    polyName = f'{ID}_{NAME}'
    print(f'processing polygon {polyName}')
    return(polyName)

def get_masked_tcw(sr_data, mask, threshold=-350):
    '''uses TasseledCapTools and an input threshold (defaults to -350) to create masked over-threshold tasseled cap '''

    #transform the nbart into tci
    tci = TasseledCapTools.thresholded_tasseled_cap(sr_data,wetness_threshold=-350, drop=True , drop_tc_bands=True)

    #select only finite values (over threshold values)
    tcw = xr.ufuncs.isfinite(tci.wetness_thresholded)

    # #reapply the polygon mask
    tcw = tcw.where(mask==False)

    return tcw

def get_masked_ls578_data(query, geom, dc=dc):
    '''create a function that takes in the masked proportion, query and geometry and returns the fully masked surface reflectance data'''
    ## Set up datasets
    #set cloudmasking threshold and load landsat nbart data
    landsat_masked_prop = 0.90
    ls578_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, product='nbart',
            masked_prop=landsat_masked_prop)

    ### mask the data with our original polygon to remove extra data 

    data = ls578_ds
    mask = rasterio.features.geometry_mask([geom.to_crs(data.geobox.crs)for geoms in [geom]],
                                               out_shape=data.geobox.shape,
                                               transform=data.geobox.affine,
                                               all_touched=False,
                                               invert=False)

    #for some reason xarray is not playing nicely with our old masking function
    mask_xr = xr.DataArray(mask, dims = ('y','x'))
    ls578_ds = data.where(mask_xr==False)
    return ls578_ds, mask_xr
