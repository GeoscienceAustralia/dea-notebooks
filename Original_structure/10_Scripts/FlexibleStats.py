# flexiblestats.py

"""
This code allows statistical processes from DEA stats to be calculated using non-sequential dates.

Date: September 2018
Authors: Imam Alam, Sean Chua

In this configuration it finds all the observations within the same months as the list of dates you provide,
 this can be modified.

Example: Calculate the dates where drought intensity is highest using an index such as the
Standardised Precipitation Evapotranspiration Index (SPEI) and create a geomedian from this list of dates.

Inputs:

- Netcdf (.nc) containing the list of dates you wish to process.

- Config file (.yaml) that details the input products (LS8, Sentinel 2) and output products (geomedian).
The 'date_ranges' should be the first and last times of the date list you provide above.

- Datacube conf file (.conf) that points to the database hostname, port etc.

Files for a reproducible example are available at:
https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Supplementary_data/Files/FlexibleStats

NOTE:

This script produces tiled geomedians of the input area that can be combined using the following lines.
An example is provided in the supplementary data linked above.

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
    """
    Creates a pickle file that contains the tasks of observations between the date ranges specified in the .yaml file.
    """
    # open the yaml file that specifies the datacube products
    with open('stats_config.yaml') as fl:
        config = yaml.load(fl)

    print(yaml.dump(config, indent=4))

    print('generating tasks')

    # initialise a datacube connection using the .conf file
    dc = Datacube(app='api-example', config='cambodia.conf')
    app = StatsApp(config, index=dc.index)
    # create the pickle file containing all the tasks
    pickle_stream(app.generate_tasks(dc.index), 'task.pickle')


def prune_tasks():
    """
    'Prunes' the output pickle file from save_tasks() with a netcdf that contains the dates of interest.

    Sub-functions:
    transform_task() -- iterates through each of the sensors/products in each task
    transform_sensor() -- applies transform_tile() to the data and masks within each sensor/product
    transform_tile() -- checks if each observation at a tile for a particular sensor is within the list of dates provided
    """

    # Import netcdf that contains your dates of interest
    dates = xr.open_dataset("example_dates.nc")

    def transform_task(task):
        # call transform_source() for each product/sensor in the task
        task.sources = [transform_sensor(sensor) for sensor in task.sources]
        task.sources = [sensor for sensor in task.sources if sensor is not None]

        if task.sources == []:
            return None

        return task

    def transform_sensor(sensor):
        try:
            sensor.data = transform_tile(sensor.data)
            sensor.masks = [transform_tile(mask) for mask in sensor.masks]
        except ValueError:
            return None

        return sensor

    def transform_tile(tile):
        # Create a list of the number of observations at this tile
        [num_observations] = tile.sources.time.shape

        sources = []
        # Check if task time is within list of dates and add it to list if True
        for i in range(num_observations):
            one_slice = tile.sources.isel(time=slice(i, i + 1))
            if one_slice.time.astype(
                    'datetime64[M]') in dates.time.values.astype('datetime64[M]'):
                sources.append(one_slice)

        # Add the desired observations to the tile in time order
        tile.sources = xr.concat(sources, dim='time')

        return tile

    # Call transform_tasks() for each task in the task.pickle file
    pruned = (transform_task(task)
              for task in unpickle_stream('task.pickle'))
    # Only include results if they are not None
    pruned = (task for task in pruned if task is not None)

    # Pickle the pruned output tasks
    pickle_stream(pruned, 'pruned_task.pickle')


def execute_tasks():
    """
    Uses the .yaml to call a datacube statistics function on the pickle file containing the pruned tasks.

    Processes a tile per worker using multiprocessing
    Produces tiled outputs that can be joined using code outlined in the supplementary data
    """
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
