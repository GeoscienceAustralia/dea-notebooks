
# coding: utf-8

# # WOfS Count Catchment Extraction
# 
# **What does this notebook do?**
# 
# **Required inputs** Shapefile containing the polygon set of catchments to be interrogated. This code assumes that each polygon has a unique identifier attribute called `BASIN_NAME`.
# 
# **Date** November 2018
# 
# **Author** Claire Krause

# In[1]:


from datacube import Datacube
from datacube.utils import geometry
from datacube.storage import masking
dc = Datacube(app = 'Catchment Polygon drill')

import fiona
import rasterio.features
import numpy as np
import csv
import pandas as pd
from dateutil.relativedelta import relativedelta
import os.path
import sys
from math import ceil

# ## Set up some file paths

# In[2]:


shape_file = '/g/data/r78/cek156/ShapeFiles/QLDFisheries/LeahyROIWhole2/StratifiedEditedBasins10km.shp'
Output_dir = '/g/data/r78/vmn547/Dams/Catchments'


# ## Set up the dates for the analysis

# In[3]:


start_date = '01-07-1995'
end_date = '30-06-2020'
end_date = pd.to_datetime(end_date, format='%d-%m-%Y')


part = sys.argv[1]
part = int(part)
print(f'Working on chunk {part}')


# In[ ]:

print(f'Reading in {shape_file}')
# ## Loop through the polygons and write out a csv of dam capacity
import time
time.sleep(5*part)
# Get the shapefile's crs
with fiona.open(shape_file) as shapes:
    crs = geometry.CRS(shapes.crs_wkt)
    ShapesList = list(shapes)
    ChunkSize = ceil(len(ShapesList)/32) + 1
    shapessubset = shapes[(part - 1) * ChunkSize: part * ChunkSize]
print(f'The index we will use is {(part - 1) * ChunkSize, part * ChunkSize}')


print(f'Reading in {shape_file}')

# ## Loop through each polygon and extract WOfS info

def FindOutHowWet(shapes, crs):
    StartDate = pd.to_datetime(start_date, format='%d-%m-%Y')
    EndDate = pd.to_datetime(StartDate + relativedelta(years=2), format='%d-%m-%Y')
    polyName = shapes['properties']['FID']
    if int(polyName) > 0:
        while EndDate < end_date:
            print(f'Working on {StartDate} to {EndDate}')
            first_geometry = shapes['geometry']
            polyName = shapes['properties']['FID']
            print(polyName)
            geom = geometry.Geometry(first_geometry, crs=crs)

            ## Set up the query, and load in all of the WOFS layers
            query = {'geopolygon': geom,
                     'time': (f'{StartDate}', f'{EndDate}')}
            WOFL = dc.load(product='wofs_albers', group_by='solar_day', **query)

            # Make a mask based on the polygon (to remove extra data outside of the polygon)
            mask = rasterio.features.geometry_mask([geom.to_crs(WOFL.geobox.crs) for geoms in [geom]],
                                                   out_shape=WOFL.geobox.shape,
                                                   transform=WOFL.geobox.affine,
                                                   all_touched=False,
                                                   invert=True)

            ## Work out how full the dam is at every time step
            AllObservations = []
            WetObserved = []
            DryObserved = []
            InvalidObservations = []
            for ix, times in enumerate(WOFL.time):
                # Grab the data for our timestep
                AllTheBitFlags = WOFL.water.isel(time = ix)
                # Find all the wet/dry pixels for that timestep
                WetPixels = masking.make_mask(AllTheBitFlags, wet=True)
                DryPixels = masking.make_mask(AllTheBitFlags, dry=True)
                # Apply the mask and count the number of observations
                MaskedAll = AllTheBitFlags.where(mask).count().item() # count all pixels
                MaskedWet = WetPixels.where(mask).sum().item() # count wet pixels
                MaskedDry = DryPixels.where(mask).sum().item() # count dry pixels
                InvalidObs = MaskedAll - (MaskedWet + MaskedDry) # all pixels - (wet + dry) = invalid pixels

                # Append the counts to a list for each timestep
                WetObserved.append(MaskedWet)
                InvalidObservations.append(InvalidObs)
                DryObserved.append(MaskedDry)
                AllObservations.append(MaskedAll)

            # write out to a csv
            AllTimesteps = WOFL.time

            DateList = AllTimesteps.to_dataframe().to_csv(None, header=False, index=False).split('\n')
            rows = zip(DateList,WetObserved,DryObserved,InvalidObservations,AllObservations)

            if DateList:

                if os.path.exists(f'{Output_dir}/{polyName}.txt'):
                    with open('{0}/{1}.txt'.format(Output_dir, polyName), 'a') as f:
                        writer = csv.writer(f)
                        for row in rows:
                            writer.writerow(row)
                else:
                    with open('{0}/{1}.txt'.format(Output_dir, polyName), 'w') as f:
                        writer = csv.writer(f)
                        Headings = ['Observation Date', 'Wet pixel count', 'Dry pixel count',
                                    'Invalid pixel count', 'Total observed pixel count']
                        writer.writerow(Headings)
                        for row in rows:
                            writer.writerow(row)
            StartDate = pd.to_datetime(EndDate + relativedelta(days=1), format='%d-%m-%Y')
            EndDate = pd.to_datetime(StartDate + relativedelta(years=2), format='%d-%m-%Y')
            WOFL =None
            mask = None
            AllObservations = None
            WetObserved = None
            DryObserved = None
            InvalidObservations = None
            rows =None

for shapes in shapessubset:
    result = FindOutHowWet(shapes, crs)
    if not result:
        result = FindOutHowWet(shapes, crs)
    if not result:
        result = FindOutHowWet(shapes, crs)
