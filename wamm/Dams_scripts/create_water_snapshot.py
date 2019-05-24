
# coding: utf-8

# # Create Water Level Snapshot - pick time
# 
# **What this notebook does** This notebook creates a snapshot of latest water body conditions, appending the dam fill level as an attribute in a shapefile. This code needs to be run manually after new data has been ingested into DEA, and after the .txt files for each water bosy have been updated.
# 
# **Required inputs** 
# - A shapefile to be appended with the latest data (`Shapefile_to_append`)
# - A folder where all the `.txt files` are located from which the snapshot will be created (`Timeseries_dir`)
# - The date for analysis needs to be updated below (`DateToExtractStr`)
# 
# **Date** December 2018
# 
# **Author** Claire Krause


import glob
import geopandas as gp
import re
import pandas as pd
import sys
from dateutil.relativedelta import relativedelta
import warnings

import datacube
from datetime import datetime
import os
current_time = datetime.now()
dc = datacube.Datacube()

time_period = ('2019-03-01', current_time.strftime('%m-%d-%Y'))
query = {'time': time_period}
datasets= dc.find_datasets(product='wofs_albers', **query)
#datasets= dc.find_datasets(product='ls8_nbart_albers', **query)
dataset_times = [dataset.center_time for dataset in datasets]
dataset_times.sort()
print(f'Latest wofls in datacube is {dataset_times[-1]}')


# ### Choose when you want the snapshot for
# 
# Note that there is a filter built in here that excludes observations that are more than 45 days from the chosen date.

if len(sys.argv) >1:
    DateToExtractStr =  sys.argv[1] #'20190304'
    DateToExtract = pd.to_datetime(DateToExtractStr, format='%Y%m%d', utc=True)
else:
   DateToExtract = dataset_times[-1]
   DateToExtractStr = DateToExtract.strftime('%Y%m%d')
   DateToExtract = pd.to_datetime(DateToExtractStr, format='%Y%m%d', utc=True)

print(f'Appending shapefile with nearest values to {DateToExtractStr}')

# Create filter range which only includes observations of +/- 45 days
DateFilterA = DateToExtract + relativedelta(days=-45)
DateFilterB = DateToExtract + relativedelta(days=45)


# ## Set up the file paths, date to be extracted and output file names
# 
# `Timeseries_dir` is the folder where all the .txt files are located from which the snapshot will be created
# 
# `Shapefile_to_append` is the shapefile which the snapshot will be added to as an attribute



Timeseries_dir = '/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/Timeseries/'


season_dict={1:'summer', 2:'summer', 3:'spring', 4:'spring', 5:'spring', 6:'summer', 7:'summer', 8:'summer', 9:'autumn',
             10:'autumn', 11:'autumn', 12:'summer'}
season = season_dict[DateToExtract.month]

Shapefile_to_append = '/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/AllNSW2000to201901LatestSnapshot2/AllNSW2000to201901LatestSnapshotPar2.shp'
output_shapefile = f'/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/AllNSW_Snapshots/AllNSW_{DateToExtract.year}_{season}_Snapshot.shp'

if os.path.isfile(output_shapefile):
    print('file exists')
    Shapefile_to_append = output_shapefile


SnapshotShp = gp.read_file(Shapefile_to_append)


# ## Get a list of all of the files in the folder to loop through

TimeSeriesFiles = glob.glob(f'{Timeseries_dir}/**/*.csv',recursive=True)


# ## Loop through and extract the relevant date from all the .txt files

for file in TimeSeriesFiles:
    # Get the ID
    NameComponents = re.split('\.|/', file)  # Splitting on '.' and '/'
    PolyID = NameComponents[-2]
    PolyID = int(PolyID)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            AllObs = pd.read_csv(file, parse_dates=[
                                 'Observation Date'], index_col='Observation Date')
            x = AllObs.iloc[AllObs.index.get_loc(DateToExtract, method='nearest')]
        if(x.name > DateFilterA and x.name < DateFilterB):
            ObsDate = str(x.name)
            Pct = float(x['Wet pixel percentage'])
            FindPolyIndex = SnapshotShp.where(
                SnapshotShp['ID'] == PolyID).dropna(how='all').index.values[0]
            SnapshotShp.loc[(FindPolyIndex, f'{DateToExtractStr}')] = ObsDate
            SnapshotShp.loc[(FindPolyIndex, f'Pc{DateToExtractStr}')] = Pct
        else:
            print(x.name, f'is out of snapshot range for polyid: {PolyID}')
    except:
        print(f'Bad {PolyID}')


# ## Write out the appended shapefile

schema = gp.io.file.infer_schema(SnapshotShp)
schema['properties'][f'{DateToExtractStr}'] = 'str'
schema['properties'][f'Pc{DateToExtractStr}'] = 'float' 
SnapshotShp.to_file(output_shapefile, schema = schema)

Snapshot = gp.read_file(output_shapefile)

#import subprocess
#subprocess.call(['chmod', 'g+rw', f'{output_shapefile.split(".")[0]}.*'])



