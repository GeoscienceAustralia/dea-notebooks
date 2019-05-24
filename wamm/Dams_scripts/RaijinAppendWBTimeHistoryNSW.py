# # Get dam time history - parallel workflow
# 
# **What this notebook does** This notebook uses the python module `multiprocessing` to simply parallelise a workflow. Here we have a shapefile containing polygons we wish to explore. Each polygon is independant from the other, and so lends itself to simple parallelisation of the workflow. 
# 
# This code was parallelised by moving all of the processing into a single function (here called `FindOutHowFullTheDamIs`). This function is called by the `multiprocessing` module inside a loop. The code loops through each polygon in the shapefile, and assigns it to an available CPU for processing. Once that polygon has been processed, the CPU moves on to the next one until all of the polygons have been processed. This all runs as a background process, so the notebook appears to not be doing anything when the code is running.
# 
# **Required inputs** Shapefile containing the polygon set of water bodies to be interrogated.
# 
# **Date** August 2018
# 
# **Author** Claire Krause, Jono Mettes

# In[1]:


from datacube import Datacube
from datacube.utils import geometry
from datacube.storage import masking
import fiona
import rasterio.features
import numpy as np
import csv
import multiprocessing
import sys
from math import ceil
import os
from datetime import datetime
from dateutil import relativedelta, parser

# ## Set up some file paths

shape_file = '/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/AllNSW2000to201810pcMinMaxRiverCleanedNoSea.shp'
print(f'Reading in {shape_file}')
numChunks = sys.argv[2]
numChunks = int(numChunks)
print(f'Splitting into {numChunks} chunks')


part = sys.argv[1]
part = int(part)
print(f'Working on chunk {part}')


global Output_dir
Output_dir = '/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/Timeseries'

# ## Loop through the polygons and write out a csv of dam capacity
current_time = datetime.now()
# Get the shapefile's crs
with fiona.open(shape_file) as shapes:
    crs = geometry.CRS(shapes.crs_wkt) 
    ShapesList = list(shapes)
    ChunkSize = ceil(len(ShapesList)/numChunks) + 1
    shapessubset = shapes[(part - 1) * ChunkSize: part * ChunkSize]


print(f'The index we will use is {(part - 1) * ChunkSize, part * ChunkSize}')


def get_last_date(fpath):
    try:
        with open(fpath, 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            last_date = last_line.split(',')[0]
            start_date = parser.parse(last_date)
            start_date = start_date + relativedelta.relativedelta(days=1)
            start_date = start_date.strftime('%Y-%m-%d')
            return start_date
    except:
        return None

# Define a function that does all of the work    
def FindOutHowFullTheDamIs(shapes, crs):
    """
    This is where the code processing is actually done. This code takes in a polygon, and the
    shapefile's crs and performs a polygon drill into the wofs_albers product. The resulting 
    xarray, which contains the water classified pixels for that polygon over every available 
    timestep, is used to calculate the percentage of the water body that is wet at each time step. 
    The outputs are written to a csv file named using the polygon ID. 
    
    Inputs:
    shapes - polygon to be interrogated
    crs - crs of the shapefile
    
    Outputs:
    True or False - False if something unexpected happened, so the function can be run again.
    a csv file on disk is appended for every valid polygon.
    """
    dc = Datacube(app='Polygon drill')
    first_geometry = shapes['geometry']
    polyName = shapes['properties']['ID']
    strPolyName = str(polyName).zfill(5)
    fpath = os.path.join(Output_dir, f'{strPolyName[0:3]}/{strPolyName}.csv')

    start_date = get_last_date(fpath)

    if start_date is None:
        print(f'There is no csv for {strPolyName}')
        return 1
    else:
        time_period = (start_date, current_time.strftime('%Y-%m-%d'))

        #print(polyName)
    #    polyArea = shapes['properties']['area']
        geom = geometry.Geometry(first_geometry, crs=crs)

        ## Set up the query, and load in all of the WOFS layers
        query = {'geopolygon': geom, 'time': time_period}
        WOFL = dc.load(product='wofs_albers', **query)

        if len(WOFL.attrs)==0:
            print(f'There is no new data for {strPolyName}')
            return 2
        # Make a mask based on the polygon (to remove extra data outside of the polygon)
        mask = rasterio.features.geometry_mask([geom.to_crs(WOFL.geobox.crs) for geoms in [geom]],
                                               out_shape=WOFL.geobox.shape,
                                               transform=WOFL.geobox.affine,
                                               all_touched=False,
                                               invert=True)
        ## Work out how full the dam is at every time step
        DamCapacityPc = []
        DamCapacityCt = []
        DryObserved = []
        InvalidObservations = []
        for ix, times in enumerate(WOFL.time):
            # Grab the data for our timestep
            AllTheBitFlags = WOFL.water.isel(time = ix)
            # Find all the wet/dry pixels for that timestep
            WetPixels = masking.make_mask(AllTheBitFlags, wet=True)
            DryPixels = masking.make_mask(AllTheBitFlags, dry=True)
            # Apply the mask and count the number of observations
            MaskedAll = AllTheBitFlags.where(mask).count().item()
            MaskedWet = WetPixels.where(mask).sum().item()
            MaskedDry = DryPixels.where(mask).sum().item()
            # Turn our counts into percents
            try:
                WaterPercent = MaskedWet / MaskedAll * 100
                DryPercent = MaskedDry / MaskedAll * 100
                UnknownPercent = (MaskedAll - (MaskedWet + MaskedDry)) / MaskedAll *100
            except ZeroDivisionError:
                WaterPercent = 0.0
                DryPercent = 0.0
                UnknownPercent = 100.0
            # Append the percentages to a list for each timestep
            DamCapacityPc.append(WaterPercent)
            InvalidObservations.append(UnknownPercent)
            DryObserved.append(DryPercent)
            DamCapacityCt.append(MaskedWet)

        ## Filter out timesteps with less than 90% valid observations
        try:
            ValidMask = [i for i, x in enumerate(InvalidObservations) if x < 10]
            if len(ValidMask) >0:
                ValidObs = WOFL.time[ValidMask].dropna(dim='time')
                ValidCapacityPc = [DamCapacityPc[i] for i in ValidMask]
                ValidCapacityCt = [DamCapacityCt[i] for i in ValidMask]

                DateList = ValidObs.to_dataframe().to_csv(None, header=False, index=False,
                                                          date_format="%Y-%m-%dT%H:%M:%SZ").split('\n')
                rows = zip(DateList,ValidCapacityPc,ValidCapacityCt)

                if DateList:
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, 'a') as f:
                        writer = csv.writer(f)
                        for row in rows:
                            writer.writerow(row)
            else:
                print(f'{polyName} has no new good (90percent) valid data')
            return 1
        except:
            print(f'This polygon isn\'t working...: {polyName}')
            return 3


#-----------------------------------------------------------------------#

noNewDataCount =0
#process each polygon. attempt each polygon 3 times
for shapes in shapessubset:
    result = FindOutHowFullTheDamIs(shapes, crs)
    if result == 3:
        result = FindOutHowFullTheDamIs(shapes, crs)
    elif result ==2:
        noNewDataCount+= 1
        # if noNewDataCount >300:
        #     print('Over 300 polygons with no new data')
        #     exit
print(f'No new data count is {noNewDataCount}')

