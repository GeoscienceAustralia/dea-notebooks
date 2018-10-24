# flexiblestats.py

"""
This code allows statistical processes from DEA stats to be calculated using non-sequential dates.

Date: September 2018
Authors: Imam Alam, Sean Chua

In this configuration it finds all the observations within the same months as the list of dates you provide, this can be modified.

Example: Calculate the dates where drought intensity is highest using an index such as the Standardised Precipitation Evapotranspiration Index (SPEI) and create a geomedian from this list of dates.

Inputs: 

- Netcdf (.nc) containing the list of dates you wish to process.

- Config file (.yaml) that details the input products (LS8, Sentinel 2) and output products (geomedian). The 'date_ranges' should be the first and last times of the date list you provide above.

- Datacube conf file (.conf) that points to the database hostname, port etc.


NOTE:

This script produces tiled geomedians of the input area that can be combined using the following lines in your pbs script.

# Combine tiles into a single tif for each band
for BAND in blue green red nir swir1 swir2; do
   for i in *.nc; do echo NETCDF:$i:$BAND; done | xargs -n 1000 -x gdalbuildvrt $BAND.vrt
   gdal_translate -of GTiff $BAND.vrt $BAND.tif
 done

# Merge bands together to make the final Geomedian
gdal_merge.py -init 255 -o geomedian.tif blue.tif green.tif red.tif nir.tif swir1.tif swir2.tif -separate

""" 

from datacube_stats import StatsApp
from datacube_stats.statistics import GeoMedian
from datacube import Datacube
from datacube_stats.utils import pickle_stream, unpickle_stream
import yaml
import multiprocessing
import xarray as xr

def save_tasks():
    # Creates a pickle file with the locations of every datacube observation specified in the yaml file 
    with open('stats_config.yaml') as fl:
        config = yaml.load(fl)

    print(yaml.dump(config, indent=4))

    print('generating tasks')
    dc = Datacube(app='api-example', config='cambodia.conf')
    app = StatsApp(config, index = dc.index)
    pickle_stream(app.generate_tasks(dc.index), 'task.pickle')
    
def prune_tasks():
    # 'prunes' the output pickle file from save_tasks() with a list of dates to create a new pickle file
    
    # Import netcdf with the list of dates
    dates = xr.open_dataset("/g/data/u46/users/sc0554/drought_indices_cambodia/spei_quartile_dates/spei_q1_dates_hard.nc")

    pruned = (transform_task(task, dates)
              for task in unpickle_stream('task.pickle'))
    pruned = (task for task in pruned if task is not None)

    pickle_stream(pruned, 'pruned_task.pickle')

def transform_task(task, q_dates):
    new_path = 'nbart_geomedian_{x}_{y}.nc'
    task.output_products['ls_level2_geomedian_annual'].file_path_template = new_path

    task.sources = [transform_source(source, q_dates) for source in task.sources]
    task.sources = [source for source in task.sources if source is not None]

    if task.sources == []:
        return None

    return task

def transform_source(source, q_dates):
    try:
        source.data = transform_tile(source.data, q_dates)
        source.masks = [transform_tile(mask, q_dates) for mask in source.masks]
    except ValueError:
        return None

    return source

def transform_tile(tile, q_dates):
    [num_observations] = tile.sources.time.shape

    sources = []
    
    # Check if task time is within list of dates and add it to list if True
    for i in range(num_observations):
        one_slice = tile.sources.isel(time=slice(i, i + 1))
        if one_slice.time.astype('datetime64[M]') in q_dates.time.values.astype('datetime64[M]'):
            sources.append(one_slice)

    tile.sources = xr.concat(sources, dim='time')

    return tile

def execute_tasks():
    # using the stats_config.yaml call a datacube statistics function on the pickle file containing the tasks / dates previously pruned
    with open('stats_config.yaml') as fl:
        config = yaml.load(fl)

    print(yaml.dump(config, indent=4))

    task_file = 'pruned_task.pickle'

    print('executing tasks')
    app = StatsApp(config)

    p = multiprocessing.Pool()
    p.map(app.execute_task, list(unpickle_stream(task_file)))

if __name__ == '__main__':
    save_tasks()            
    prune_tasks()
    execute_tasks()

