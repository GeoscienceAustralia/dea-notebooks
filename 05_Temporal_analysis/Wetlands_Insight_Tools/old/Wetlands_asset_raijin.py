# #!/usr/bin/python


# | Authors:  | Bex Dunn|
# |----------|----------------|
# | Created: | Jan 7, 2019 |
# | Last edited: | March 15,2019 |


#  Before running this script load these modules:
# `module use /g/data/v10/public/modules/modulefiles` 
# `module load dea`
# This code is designed to run on raijin, on the Australian NCI. 
# The shell script to run this code has a *.sh extension


# If you find an error in this code, please raise an issue at https://github.com/GeoscienceAustralia/dea-notebooks
# 
# This code takes a supplied shapefile of a polygon and queries Digital Earth
# Australia http://geoscienceaustralia.github.io/digitalearthau/
# for WOfS, Fractional Cover and NBART. It calculates thresholded tasselled cap wetness. The dominant result for
# each pixel is calculated and the percentage area of the polygon covered by water, wet vegetation, 
# photosynthetic vegetation, non-photosynthetic vegetation and bare soil is output into a jpg stacked plot and to
# csv. The resulting data can be used to monitor changes in wetland behaviour spatiotemporally. 

# - Input Datasets:
# - Landsat 5
# - Landsat 7
# - Landsat 8

# -- Fractional Cover --
# - PV - Photosythetic vegetation
# - NPV - Non-Photosythetic vegetation
# - BS - Bare Soil

# - WOfS Feature Layers (WOFLs)

# __Future Work:__ 
# - do this by max extent of wetness        

### Import Statements: import the modules we need ------------------------------

import csv
import multiprocessing as mp

#$#$#$#$#$

import datacube
import datetime
import fiona
import geopandas as gpd
from math import ceil
import numpy as np
import pandas as pd
import rasterio.mask
import rasterio.features
from shapely import geometry
import seaborn as sns
import sys
import time
import xarray as xr

#keep the plotting modules in here as we want to output the stackplots to *.jpg
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from datacube.storage import masking
from datacube.utils import geometry

#append path to dea notebooks scripts to the system so we can access it
sys.path.append('/g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/10_Scripts')
import DEADataHandling, DEAPlotting, TasseledCapTools

# setup the datacube 
dc = datacube.Datacube(app='asset drill')

### Set up polygon
poly_path='/g/data/r78/rjd547/Ramsar_Wetlands/ExplodedRAMSAR.shp'
print(f'Shape file is {poly_path}')

#3333333part = sys.argv[1] #take an argument from the command line (our parallelish scripte)
part = 2
part = int(part)
print(f'system argument received is {part}')

global Output_dir
Output_dir = '/g/data/r78/rjd547/Ramsar_Wetlands/Ramsar_Outputs_1/'

# add in a delay between dc.load calls to avoid overloading the database - 5 seconds in this case
time.sleep(5*part)
#open the polygon

#this code tells us which polygon ids will be running on this particular (node?). Shapessubset will be the subset of polygons that our function
#will run over. 
with fiona.open(poly_path) as allshapes:
        #get the crs of the polygon file to use when processing each polygon
        crs = geometry.CRS(allshapes.crs_wkt)
        #get the list of all the shapes in the shapefile
        ShapesList = list(allshapes)
        #Desired number of chunks
        #Set this to 64 because we want megamem to use 4x8x2 cpus (64)
        DesiredChunks = 64
        ChunkSize = ceil(len(ShapesList)/DesiredChunks) #this was set due to Claire having 64000 polygons in her code
        print(f'chunk size is {ChunkSize}')
        print(f'There are {int(len(ShapesList)/ChunkSize)} generated chunks')
        shapessubset = allshapes[(part - 1) * ChunkSize: part * ChunkSize]
        print(f'Running for polygon IDs in the range {(part - 1) * ChunkSize} to {part * ChunkSize}')  

### define functions that are run in the mainline here

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

def get_masked_ls578_data(query, geom):
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

def BigFunkyFunction(lilshape,crs):
    '''This is a function that does lots of things. It takes a single polygon and does all the things #FIXME '''
    ### This is set up to be shapefile-specific. I'm not sure this can be avoided, as often shapefiles are pretty specific..
    first_geometry = lilshape['geometry']
    polyName = get_RAMSAR_polyName(lilshape)
    geom = geometry.Geometry(first_geometry, crs=crs)
    query = {'geopolygon': geom}# this should run for all time, if there is no time set?
    
    #load and mask data. selecting data with more than 90% clear for the geobox around the polygon... #FIXME
    ls578_ds, mask_xr= get_masked_ls578_data(query,geom)
    
    print('run tasselled cap transform')
    #transform the nbart into tci
    tci = TasseledCapTools.thresholded_tasseled_cap(ls578_ds,wetness_threshold=-350, drop=True , drop_tc_bands=True)

    ### create a masked version of the extent of overthreshold wetness

    #select only finite values (over threshold values)
    tcw = xr.ufuncs.isfinite(tci.wetness_thresholded)

    # #reapply the polygon mask
    tcw = tcw.where(mask_xr==False)

    ### load wofls and select only wet pixels
    print('load wofls')
    #load wofs
    wofls = dc.load(product = 'wofs_albers', like=ls578_ds)

    #only get wet obs
    wetwofl = masking.make_mask(wofls, wet=True)

    #match the wofs observations to the nbart
    wetwofl=wetwofl.where(wofls.time==ls578_ds.time)

    ### mask the wofs obs

    #mask the wofs obs with the polygon mask
    wetwofl = wetwofl.where(mask_xr==False)

    ### load in fractional cover data
    print('load fractional cover data')
    #load the data according to our query
    #choose a mask proportion to look for a clear timestep
    fc_ds = DEADataHandling.load_clearlandsat(dc, query,product='fc',masked_prop=0.90)

    ### mask FC with polygon

    fc_ds = fc_ds.where(mask_xr==False)

    ### mask FC with wetness

    fc_ds_noTCW=fc_ds.where(tcw==False)

    ### Calculate number of pixels in area of interest

    #number of pixels in area of interest
    pixels = (mask_xr==0).sum(dim=['x','y'])

    mask_xr==0
    mask_xr.count(dim=['x','y'])

    #count number of wofs pixels
    wofs_pixels = wetwofl.water.sum(dim=['x','y'])

    #count percentage of area of wofs
    wofs_area_percent = (wofs_pixels/pixels)*100

    #count number of tcw pixels
    tcw_pixel_count = tcw.sum(dim=['x','y'])

    #calculate percentage area wet
    tcw_area_percent = (tcw_pixel_count/pixels)*100

    #calculate wet not wofs
    tcw_less_wofs = tcw_area_percent-wofs_area_percent

    ### Calculate the dominant fraction for each pixel in Fractional Cover

    #drop data percentage and Unmixing Error
    fc_tester = fc_ds_noTCW.drop(['data_perc','UE'])

    #following robbi's advice, cast the dataset to a dataarray
    maxFC = fc_tester.to_array(dim='variable', name='maxFC')

    #turn FC array into integer only as nanargmax doesn't seem to handle floats the way we want it to
    FC_int = maxFC.astype('int8')

    #use numpy.nanargmax to get the index of the maximum value along the variable dimension
    #BSPVNPV=np.nanargmax(FC_int, axis=0)
    BSPVNPV=FC_int.argmax(dim='variable')

    FC_mask=xr.ufuncs.isfinite(maxFC).all(dim='variable')

    # #re-mask with nans to remove no-data
    BSPVNPV=BSPVNPV.where(FC_mask)


    FC_dominant = xr.Dataset({
        'BS': (BSPVNPV==0).where(FC_mask),
        'PV': (BSPVNPV==1).where(FC_mask),
        'NPV': (BSPVNPV==2).where(FC_mask),
    })

    FC_count = FC_dominant.sum(dim=['x','y'])

    #Fractional cover pixel count method
    #Get number of FC pixels, divide by total number of pixels per polygon

    Bare_soil_percent=(FC_count.BS/pixels)*100

    Photosynthetic_veg_percent=(FC_count.PV/pixels)*100

    NonPhotosynthetic_veg_percent=(FC_count.NPV/pixels)*100

    NoData = 100 - wofs_area_percent- tcw_less_wofs - Photosynthetic_veg_percent - NonPhotosynthetic_veg_percent - Bare_soil_percent

    #set up color palette
    pal = [sns.xkcd_rgb["grey"],
           sns.xkcd_rgb["cobalt blue"],
           sns.xkcd_rgb["neon blue"],
           sns.xkcd_rgb["grass"],
           sns.xkcd_rgb["beige"],
           sns.xkcd_rgb["brown"]]       
    #try and figure out what the error is on one of the plots
    try:
        #make a stacked area plot
        plt.clf()
        plt.figure(figsize = (26,6))
        plt.stackplot(wofs_area_percent.time.values, 
                      NoData,
                      wofs_area_percent, 
                      tcw_less_wofs, 
                      Photosynthetic_veg_percent, 
                      NonPhotosynthetic_veg_percent,
                      Bare_soil_percent,
                      labels=['cloud',
                              'open water',
                              'wet',
                              'PV',
                              'NPV',
                              'BS',
                             ], colors=pal, alpha = 0.6)

        plt.title(f'Percentage of area WOfS, Wetness, Fractional Cover for {polyName}')


        #set date ticks every year

        years = mdates.YearLocator(1)
        yearsFmt = mdates.DateFormatter('%Y')

        #set axis limits to the min and max
        plt.axis(xmin = wofs_area_percent.time[0].data, xmax = wofs_area_percent.time[-1].data, ymin = 0, ymax = 100)
        ax = plt.gca()
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        #add a legend and a tight plot box
        plt.legend(loc='lower right')
        #plt.tight_layout()

        #create rectangle borders for no-data times (SLC-off only)
        LS5_8_gap_start = datetime(2011,11,1)
        LS5_8_gap_end = datetime(2013,4,1)

        # convert to matplotlib date representation
        gap_start = mdates.date2num(LS5_8_gap_start)
        gap_end = mdates.date2num(LS5_8_gap_end)
        gap = gap_end - gap_start

        #set up rectangle
        slc_rectangle= Rectangle((gap_start,0), gap, 100,alpha = 0.5, facecolor=sns.xkcd_rgb['white'],
                     edgecolor=sns.xkcd_rgb['white'], hatch="////",linewidth=2)
        ax.add_patch(slc_rectangle)


        #save the figure
        plt.savefig(f'{Output_dir}{polyName}.png')#, transparent=True)
        plt.show()
        print(f'plot created for {polyName}')
    except:
        print("Unexpected error:",sys.exc_info()[0])
    
    #make a new dataframe using the data from the xarray of wofs area for the polygon

    ### start setup of dataframe by adding only one dataset
    WOFS_df = pd.DataFrame(data=wofs_area_percent.data, index=wofs_area_percent.time.values,columns=['wofs_area_percent'])

    #add data into pandas dataframe for export
    WOFS_df['tcw_area_percent']=tcw_less_wofs.data
    WOFS_df['PV_percent']=Photosynthetic_veg_percent.data
    WOFS_df['NPV_percent']=NonPhotosynthetic_veg_percent.data
    WOFS_df['BS_percent']=Bare_soil_percent.data
    WOFS_df['Cloud_percent']=NoData.data

    #call the composite dataframe something sensible, like PolyDrill
    PolyDrill_df = WOFS_df.round(2)

    #save the csv of the output data used to create the stacked plot for the polygon drill
    PolyDrill_df.to_csv(f'{Output_dir}{polyName}.csv')
    print(f'wrote output data to file {Output_dir}{polyName}.csv')
    return 1

## __Mainline__

  #-----------------------------------------------------------------------#

# Launch a process for each polygon.

### for each shapefile in our subset of shapefiles:
for shapes in shapessubset:
    ### try to run the function once, for the shapefile and given crs
    result = BigFunkyFunction(shapes, crs)
    ### if result is False ie. doesn't run
    if not result: 
        print('first go did not succeed')
        ### Try to run the function again
        result = BigFunkyFunction(shapes, crs)
        ### if that didn't work:    
        if not result:
            print('second go did not succeed, running for last time')
            ### try for a third and last time
            result = BigFunkyFunction(shapes, crs)   
