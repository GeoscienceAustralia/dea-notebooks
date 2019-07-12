# WetlandsTools.py
"""
This file contains a set of python functions used for processing existing shapefile types for the Wetlands Insight Tool.  In future these will be turned into a wetlands insight tool module, with options to select a polygon type or a default setting getting the name off the OBJECTID of the polygon.
Available functions:

    get_RAMSAR_polyName
    get_LRA_polyName

Last modified: July 2019
Author: Bex Dunn

"""
from datacube.utils import geometry
import fiona
import geopandas




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

def get_WetMAP_polyName(shapefile):
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