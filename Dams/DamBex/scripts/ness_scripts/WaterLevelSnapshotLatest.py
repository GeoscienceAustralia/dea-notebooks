
import subprocess
import glob
import geopandas as gp
import re

Timeseries_dir = '/g/data/r78/vmn547/Dams/Timeseries_new2/'
Shapefile_to_append = '/g/data/r78/cek156/dea-notebooks/Dams/Dams2000to2018/AllNSW2000to201810LatestSnapshot.shp'


## Get a list of all of the files in the folder to loop through
TimeSeriesFiles = glob.glob(f'{Timeseries_dir}*.txt')
SnapshotShp = gp.read_file(Shapefile_to_append)

def find_lastline(fname, linenum = -1):
    with open(fname, 'r') as f:
        lines = f.read().splitlines()
        last_line = lines[linenum]
        return last_line

lastDateLog = '/g/data/r78/vmmn547/Dams/lastTimeLog.txt'
lastTime = find_lastline(lastDateLog)

for file in TimeSeriesFiles:
    # Get the ID
    NameComponents = re.split('\.|/', file) # Splitting on '.' and '/'
    PolyID = NameComponents[-2]
    PolyID = int(PolyID)
    lastline = find_lastline(file)
    try:
        ObsDate, x, Pct = lastline.split(',')
    except ValueError:
        try:
            lastline = find_lastline(file, -2)
        except ValueError:
            print(f'Something is dodgy with {PolyID}\'s text file')
            continue
    Pct = float(Pct)
    FindPolyIndex = SnapshotShp.where(SnapshotShp['ID'] == PolyID).dropna(how='all').index.values[0]
    SnapshotShp.loc[(FindPolyIndex,'LatestObs')] = ObsDate
    SnapshotShp.loc[(FindPolyIndex,'PctArea')] = Pct
    


SnapshotShp.to_file(Shapefile_to_append)

