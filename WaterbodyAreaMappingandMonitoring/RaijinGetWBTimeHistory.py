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
import fiona
import rasterio.features
import csv
import sys
from math import ceil
import os
from shapely import geometry as shapely_geom
from datetime import datetime, timezone
import xarray as xr
import configparser
from dateutil import relativedelta, parser

global output_dir
global start_date
global end_date
global time_span
global id_field

config = configparser.ConfigParser()

config_file = sys.argv[1]

config.read(config_file)
start_date = '1986'
if 'SHAPEFILE' in config['DEFAULT'].keys():
    shape_file = config['DEFAULT']['SHAPEFILE']
if 'START_DATE' in config['DEFAULT'].keys():
    start_date = config['DEFAULT']['START_DATE']
if 'END_DATE' in config['DEFAULT'].keys():
    end_date = config['DEFAULT']['END_DATE']
if 'SIZE' in config['DEFAULT'].keys():
    size = config['DEFAULT']['SIZE'].upper()
else:
    size = 'ALL'
if 'MISSING_ONLY' in config['DEFAULT'].keys():
    if config['DEFAULT']['MISSING_ONLY'].upper() == 'TRUE':
        missing_only = True
    else:
        missing_only = False
else:
    missing_only = False

if 'PROCESSED_FILE' in config['DEFAULT'].keys():
    if len(config['DEFAULT']['PROCESSED_FILE']) > 2:
        processed_file = config['DEFAULT']['PROCESSED_FILE']
    else:
        processed_file = ''
else:
    processed_file = ''
if 'TIME_SPAN' in config['DEFAULT'].keys():
    time_span = config['DEFAULT']['TIME_SPAN'].upper()
else:
    time_span = 'ALL'


if 'OUTPUTDIR' in config['DEFAULT'].keys():
    output_dir = config['DEFAULT']['OUTPUTDIR']


print(f'Reading in {shape_file}')
part = sys.argv[2]
part = int(part)
print(f'Working on chunk {part}')

numChunks = sys.argv[3]
numChunks = int(numChunks)
print(f'Splitting into {numChunks} chunks')

# not used if using huge mem

if len(sys.argv) > 4:
    size = sys.argv[4].upper()
print(size)

if len(sys.argv) > 5:
    if str(sys.argv[5])=='missing':
        missing_only = True
        print('only processing missing')

if len(sys.argv) > 6:
    processed_file = str(sys.argv[6])
    print(f'only processing not in {processed_file}')

# ## Loop through the polygons and write out a csv of waterbody percentage area full and wet pixel count
import time
time.sleep(5*part)

# Get the shapefile's crs
with fiona.open(shape_file) as shapes:
    source_driver = shapes.driver
    source_crs = shapes.crs
    source_schema = shapes.schema
    crs = geometry.CRS(shapes.crs_wkt)
    ShapesList = list(shapes)

if 'FID' in ShapesList[0]['properties'].keys():
    id_field = 'FID'
else:
    id_field = 'ID'

# not used if using huge mem
if size == 'SMALL':
    newlist = []
    for shapes in ShapesList:
        if shapely_geom.shape(shapes['geometry']).envelope.area <= 2000000:
            newlist.append(shapes)
    ShapesList = newlist
    print(f'{len(newlist)} small polygons')

# not used if using huge mem
if size == 'HUGE':
    newlist = []
    for shapes in ShapesList:
        if shapely_geom.shape(shapes['geometry']).envelope.area > 2000000:
            newlist.append(shapes)
    ShapesList = newlist
    print(f'{len(newlist)} huge polygons')

print('missing_only', missing_only)
if missing_only:
    print('missing_only', missing_only)
    if len(processed_file) < 2:
        print('processed_file',processed_file)
        missingList =[]
        for shapes in ShapesList:
            polyName = shapes['properties'][id_field]
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
        polyName = shapes['properties'][id_field]
        strPolyName = str(polyName).zfill(6)
        fpath = os.path.join(output_dir, f'{strPolyName[0:4]}/{strPolyName}.csv\n')
        if not fpath in files:
            missingList.append(shapes)
    ShapesList = missingList
    print(f'{len(missingList)} missing polygons from {processed_file}')


ChunkSize = ceil(len(ShapesList)/numChunks) + 1
shapessubset = ShapesList[(part - 1) * ChunkSize: part * ChunkSize]

print(f'The index we will use is {(part - 1) * ChunkSize, part * ChunkSize}')

def get_last_date(fpath, max_days=None):
    try:
        current_time = datetime.now(timezone.utc)
        with open(fpath, 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            last_date = last_line.split(',')[0]
            start_date = parser.parse(last_date)
            start_date = start_date + relativedelta.relativedelta(days=1)
            if max_days:
                if (current_time - start_date).days > max_days:
                    start_date = current_time - relativedelta.relativedelta(days=max_days)
            str_start_date = start_date.strftime('%Y-%m-%d')
            return str_start_date
    except:
        return None

# Define a function that does all of the work    
def FindOutHowFullTheDamIs(shapes, crs, start_date=None, end_date = None):
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

    polyName = shapes['properties'][id_field]

    strPolyName = str(polyName).zfill(6)
    fpath = os.path.join(output_dir, f'{strPolyName[0:4]}/{strPolyName}.csv')
    geom = geometry.Geometry(first_geometry, crs=crs)
    current_year = datetime.now().year

    #print(shapely_geom.shape(first_geometry).envelope.area)

    if time_span == 'ALL':
        if shapely_geom.shape(first_geometry).envelope.area > 2000000:
            years = range(1986, current_year + 1, 5)
            time_periods = [(str(year),str(year+4)) for year in years]
        else:
            time_periods =[('1986',str(current_year))]
    elif time_span == 'APPEND':
        start_date = get_last_date(fpath)
        if start_date is None:
            print(f'There is no csv for {strPolyName}')
            return 1
        time_periods =[(start_date,str(current_year))]
    elif time_span == 'CUSTOM':
        time_periods = [(start_date, end_date)]
    ## Set up the query, and load in all of the WOFS layers

    #print('time_periods',time_periods)
    ## Work out how full the dam is at every time step


    ValidCapacityPc = []
    ValidCapacityCt = []
    ValidLSApc = []
    DateList = []
    for time in time_periods:
        DamCapacityPc = []
        DamCapacityCt = []
        LSA_WetPc = []
        DryObserved = []
        InvalidObservations = []

        ## Set up the query, and load in all of the WOFS layers
        query = {'geopolygon': geom, 'time': time}
        WOFL = dc.load(product='wofs_albers', group_by='solar_day', **query)

        if len(WOFL.attrs) == 0:
            print(f'There is no new data for {strPolyName}')
            return 2
        # Make a mask based on the polygon (to remove extra data outside of the polygon)
        mask = rasterio.features.geometry_mask([geom.to_crs(WOFL.geobox.crs) for geoms in [geom]],
                                               out_shape=WOFL.geobox.shape,
                                               transform=WOFL.geobox.affine,
                                               all_touched=False,
                                               invert=True)
        #mask the data to the shape of the polygon
        if geom.boundingbox.width > 25.1 and geom.boundingbox.height > 25.1:
            wofl_masked = WOFL.water.where(mask)
        else:
            wofl_masked = WOFL.water

        ## Work out how full the dam is at every time step
        for ix, times in enumerate(WOFL.time):

            # Grab the data for our timestep
            AllTheBitFlags = wofl_masked.isel(time=ix)

            # Find all the wet/dry pixels for that timestep
            LSA_Wet = AllTheBitFlags.where(AllTheBitFlags == 136).count().item()
            LSA_Dry = AllTheBitFlags.where(AllTheBitFlags == 8).count().item()
            WetPixels = AllTheBitFlags.where(AllTheBitFlags == 128).count().item() + LSA_Wet
            DryPixels = AllTheBitFlags.where(AllTheBitFlags == 0).count().item() + LSA_Dry

            # Apply the mask and count the number of observations
            MaskedAll = AllTheBitFlags.count().item()
            # Turn our counts into percents
            try:
                WaterPercent = WetPixels / MaskedAll * 100
                DryPercent = DryPixels / MaskedAll * 100
                UnknownPercent = (MaskedAll - (WetPixels + DryPixels)) / MaskedAll * 100
                LSA_WetPercent = LSA_Wet / MaskedAll * 100
            except ZeroDivisionError:
                WaterPercent = 0.0
                DryPercent = 0.0
                UnknownPercent = 100.0
                LSA_WetPercent = 0.0
                print(f'{polyName} has divide by zero error')

            # Append the percentages to a list for each timestep
            DamCapacityPc.append(WaterPercent)
            InvalidObservations.append(UnknownPercent)
            DryObserved.append(DryPercent)
            DamCapacityCt.append(WetPixels)
            LSA_WetPc.append(LSA_WetPercent)

        ## Filter out timesteps with less than 90% valid observations
        if True:
            ValidMask = [i for i, x in enumerate(InvalidObservations) if x < 10]
            if len(ValidMask) > 0:
                ValidObs=WOFL.time[ValidMask].dropna(dim='time')
                ValidCapacityPc += [DamCapacityPc[i] for i in ValidMask]
                ValidCapacityCt += [DamCapacityCt[i] for i in ValidMask]
                ValidLSApc += [LSA_WetPc[i] for i in ValidMask]
                DateList += ValidObs.to_dataframe().to_csv(None, header=False, index=False,
                                                          date_format="%Y-%m-%dT%H:%M:%SZ").split('\n')
                DateList.pop()

    if DateList:
        rows = zip(DateList, ValidCapacityPc, ValidCapacityCt, ValidLSApc)
        os.makedirs(os.path.dirname
                    (fpath), exist_ok=True)
        if time_span == 'APPEND':
            with open(fpath, 'a') as f:
                writer = csv.writer(f)
                for row in rows:
                    writer.writerow(row)
        else:
            with open(fpath, 'w') as f:
                writer = csv.writer(f)
                headings = ['Observation Date', 'Wet pixel percentage',
                            'Wet pixel count (n = {0})'.format(MaskedAll), 'LSA Wet Pixel Pct']
                writer.writerow(headings)
                for row in rows:
                    writer.writerow(row)
    else:
        print(f'{polyName} has no new good (90percent) valid data')
    return True



#-----------------------------------------------------------------------#


#process each polygon. attempt each polygon 3 times
for shapes in shapessubset:
    result = FindOutHowFullTheDamIs(shapes, crs)
    if not result:
        result = FindOutHowFullTheDamIs(shapes, crs)

