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
# **Author** Claire Krause, Jono Mettes, Vanessa Newey


from datacube import Datacube
from datacube.utils import geometry
from datacube.storage import masking
import fiona
import rasterio.features
import csv
import sys
from math import ceil
import os
from shapely import geometry as shapely_geom
from datetime import datetime
import xarray as xr
import configparser

config = configparser.ConfigParser()


config_file = sys.argv[1]
config.read(config_file)
shape_file = config['DEFAULT']['SHAPEFILE']
print(f'Reading in {shape_file}')


global output_dir
output_dir = config['DEFAULT']['OUTPUTDIR']
print()

part = sys.argv[2]
part = int(part)
print(f'Working on chunk {part}')

numChunks = sys.argv[3]
numChunks = int(numChunks)
print(f'Splitting into {numChunks} chunks')

# not used if using huge mem
size = 'small'
if len(sys.argv) > 4:
    size = sys.argv[4]

missing_only =False
if len(sys.argv) > 5:
    if str(sys.argv[5])=='missing':
        missing_only = True
        print('only processing missing')
processed_file = ''
if len(sys.argv) > 6:
    processed_file = str(sys.argv[6])
    print(f'only processing not in {processed_file}')


# ## Loop through the polygons and write out a csv of waterbody percentage area full and wet pixel count
import time
time.sleep(5*part)

# Get the shapefile's crs
with fiona.open(shape_file) as shapes:
    crs = geometry.CRS(shapes.crs_wkt)
    ShapesList = list(shapes)

# not used if using huge mem
if size == 'small':
    newlist = []
    for shapes in ShapesList:
        if shapely_geom.shape(shapes['geometry']).envelope.area <= 150000:
            newlist.append(shapes)
    ShapesList = newlist
    print(f'{len(newlist)} small polygons')

# not used if using huge mem
if size == 'huge':
    newlist = []
    for shapes in ShapesList:
        if shapely_geom.shape(shapes['geometry']).envelope.area > 150000:
            newlist.append(shapes)
    ShapesList = newlist
    print(f'{len(newlist)} huge polygons')

if missing_only & len(processed_file)<2:
    missingList =[]
    for shapes in ShapesList:
        polyName = shapes['properties']['FID']
        strPolyName = str(polyName).zfill(6)
        fpath = os.path.join(output_dir, f'{strPolyName[0:4]}/{strPolyName}.csv')
        if not os.path.exists(fpath):
            missingList.append(shapes)
    ShapesList = missingList
    print(f'{len(missingList)} missing polygons')

if len(processed_file)>1:
    missingList = []
    files = open(processed_file, 'r').readlines()
    for shapes in ShapesList:
        polyName = shapes['properties']['FID']
        strPolyName = str(polyName).zfill(6)
        fpath = os.path.join(output_dir, f'{strPolyName[0:4]}/{strPolyName}.csv\n')
        if not fpath in files:
            missingList.append(shapes)
    ShapesList = missingList
    print(f'{len(missingList)} missing polygons')


ChunkSize = ceil(len(ShapesList)/numChunks) + 1
shapessubset = ShapesList[(part - 1) * ChunkSize: part * ChunkSize]

print(f'The index we will use is {(part - 1) * ChunkSize, part * ChunkSize}')


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
    Nothing is returned from the function, but a csv file is written out to disk   
    """
    dc = Datacube(app='Polygon drill')
    first_geometry = shapes['geometry']
    polyName = shapes['properties']['FID']
    geom = geometry.Geometry(first_geometry, crs=crs)
    current_year = datetime.now().year

    if shapely_geom.shape(first_geometry).envelope.area > 200000:
        years = range(1986, current_year + 1, 5)
        time_periods = [(str(year),str(year+4)) for year in years]
    else:
        time_periods =[('1986',str(current_year))]
        ## Set up the query, and load in all of the WOFS layers
    query = {'geopolygon': geom}

    ## Work out how full the dam is at every time step
    DamCapacityPc = []
    DamCapacityCt = []
    DryObserved = []
    InvalidObservations = []
    time_obs = []
    for time in time_periods:
        query['time'] = time
        WOFL = dc.load(product='wofs_albers', **query)

        # Make a mask based on the polygon (to remove extra data outside of the polygon)
        mask = rasterio.features.geometry_mask([geom.to_crs(WOFL.geobox.crs) for geoms in [geom]],
                                               out_shape=WOFL.geobox.shape,
                                               transform=WOFL.geobox.affine,
                                               all_touched=False,
                                               invert=True)

        if len(mask[mask])<1:
            mask =~mask
        time_obs.append(WOFL.time)
        for ix, times in enumerate(WOFL.time):
            # Grab the data for our timestep
            AllTheBitFlags = WOFL.water.isel(time = ix)
            # Find all the wet/dry pixels for that timestep
            WetPixels = masking.make_mask(AllTheBitFlags, wet=True)
            DryPixels = masking.make_mask(AllTheBitFlags, dry=True)
            # Apply the mask and count the number of observations
            MaskedAll = AllTheBitFlags.where(mask).count().values.item()
            MaskedWet = WetPixels.where(mask).sum().values.item()
            MaskedDry = DryPixels.where(mask).sum().values.item()
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
    time_obs = xr.concat(time_obs, dim='time')
    ## Filter out timesteps with less than 90% valid observations 

    try:
        ValidMask = [i for i, x in enumerate(InvalidObservations) if x < 10]
        if len(ValidMask) >0:
            ValidObs = time_obs.time[ValidMask].dropna(dim='time')
            ValidCapacityPc = [DamCapacityPc[i] for i in ValidMask]
            ValidCapacityCt = [DamCapacityCt[i] for i in ValidMask]

            DateList = ValidObs.to_dataframe().to_csv(None, header=False, index=False,date_format="%Y-%m-%dT%H:%M:%SZ").split('\n')
            rows = zip(DateList,ValidCapacityPc,ValidCapacityCt)

            if DateList:
                strPolyName = str(polyName).zfill(6)
                fpath = os.path.join(output_dir, f'{strPolyName[0:4]}/{strPolyName}.csv')
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, 'w') as f:
                    writer = csv.writer(f)
                    Headings = ['Observation Date', 'Wet pixel percentage', 'Wet pixel count (n = {0})'.format(MaskedAll)]
                    writer.writerow(Headings)
                    for row in rows:
                        writer.writerow(row)
        else:
            print(f'{str(polyName).zfill(6)} is an invalid polygon')
        return True
    except:
        print(f'This polygon isn\'t working...: {polyName}')
        return False


#-----------------------------------------------------------------------#


#process each polygon. attempt each polygon 3 times
for shapes in shapessubset:
    result = FindOutHowFullTheDamIs(shapes, crs)
    if not result:
        result = FindOutHowFullTheDamIs(shapes, crs)

