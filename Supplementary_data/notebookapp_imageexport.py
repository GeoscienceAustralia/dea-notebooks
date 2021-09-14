# notebookapp_changefilmstrips.py
'''
This file contains functions for loading and interacting with data in the
change filmstrips notebook, inside the Real_world_examples folder.

Available functions:
    run_filmstrip_app

Last modified: September 2021
'''

# Load modules
import os
import dask
import datacube
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from odc.ui import select_on_a_map
from dask.utils import parse_bytes
from datacube.utils.geometry import CRS
from datacube.utils.rio import configure_s3_access
from datacube.utils.dask import start_local_dask
from ipyleaflet import basemaps, basemap_to_tiles
from datacube.storage import masking
from skimage import exposure

from ipyleaflet import (Map, WMSLayer, WidgetControl, FullScreenControl,
                        DrawControl, basemaps, basemap_to_tiles, TileLayer)
from traitlets import Unicode

# Load utility functions
import sys

sys.path.insert(1, '../Tools/')
from dea_tools.datahandling import load_ard, mostcommon_crs
from dea_tools.dask import create_local_dask_cluster


def run_imageexport_app(output_name,
                        satellites,
                        date,
                        style,
                        vmin, 
                        vmax,
                        percentile_stretch=None,
                        resolution=(-30, 30),
                        size_limit=30000):
    '''
    An interactive app that allows the user to select a region from a
    map, then export Digital Earth Australia satellite data as an image
    file.
    
    Last modified: September 2021

    Parameters
    ----------  
    output_name : str
        A name that will be used to name the output filmstrip plot file.
    date : tuple
        A string giving a date to extract imagery (e.g. 
        `date='1988-01-01'`). This is used to extract the nearest image
        to the specified date.
    resolution : tuple, optional
        The spatial resolution to load data. The default is 
        `resolution = (-30, 30)`, which will load data at 30 m pixel 
        resolution. Increasing this (e.g. to `resolution = (-100, 100)`) 
        can be useful for loading large spatial extents.
    size_limit : int, optional
        An optional size limit for the area selection in sq km.
        Defaults to 200 sq km.
        
    Returns
    -------
    ds_geomedian : xarray Dataset
        An xarray dataset containing geomedian composites for each 
        timestep in the analysis.
        
    '''

    ###########################
    # Set up satellite params #
    ###########################

    sat_params = {
        'landsat': {
            'layer': 'ga_ls_ard_3',
            'products': ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'],
            'styles': {
                'true colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'false colour': ['nbart_swir_1', 'nbart_nir', 'nbart_green']
            }
        },
        'sentinel2': {
            'layer': 's2_ard_granule_nbar_t',
            'products': ['s2a_ard_granule', 's2b_ard_granule'],
            'styles': {
                'true colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'false colour': ['nbart_swir_2', 'nbart_nir_1', 'nbart_green']
            }
        },
        'sentinel2_nrt': {
            'layer': 's2_nrt_granule_nbar_t',
            'products': ['s2a_nrt_granule', 's2b_nrt_granule'],
            'styles': {
                'true colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'false colour': ['nbart_swir_2', 'nbart_nir_1', 'nbart_green']
            }
        }
    }

    ########################
    # Select and load data #
    ########################

    # Define centre_coords as a global variable
    global centre_coords

    # Test if centre_coords is in the global namespace;
    # use default value if it isn't
    if 'centre_coords' not in globals():
        centre_coords = (-25.18, 134.18)

    # Load DEA WMS
    class TimeWMSLayer(WMSLayer):
        time = Unicode('').tag(sync=True, o=True)

    time_wms = TimeWMSLayer(url='https://ows.dea.ga.gov.au/',
                            layers=sat_params[satellites]['layer'],
                            time=date,
                            format='image/png',
                            transparent=True,
                            attribution='Digital Earth Australia')

    # Plot interactive map to select area
    #     basemap = basemap_to_tiles(basemaps.Esri.WorldImagery)
    basemap = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
    geopolygon = select_on_a_map(height='600px',
                                 layers=(
                                     basemap,
                                     time_wms,
                                 ),
                                 center=centre_coords,
                                 zoom=4)

    # Set centre coords based on most recent selection to re-focus
    # subsequent data selections
    centre_coords = geopolygon.centroid.points[0][::-1]

    # Test size of selected area
    area = geopolygon.to_crs(crs=CRS('epsg:3577')).area / 1000000
    if area > size_limit:
        print(f'Warning: Your selected area is {area:.00f} sq km. '
              f'Please select an area of less than {size_limit} sq km.'
              f'\nTo select a smaller area, re-run the cell '
              f'above and draw a new polygon.')

    else:

        print('Starting analysis...')

        # Connect to datacube database
        dc = datacube.Datacube(app='Change_filmstrips')

        # Configure local dask cluster
        create_local_dask_cluster()

        # Run time buffer
        from dea_tools.temporal import time_buffer
        date_range = time_buffer(date,
                                 buffer='20 days',
                                 output_format='%Y-%m-%d')

        # Create query based on time range, area selected, custom params
        query = {'time': date_range, 'geopolygon': geopolygon}

        # Obtain native CRS
        crs = mostcommon_crs(dc=dc, product='ga_ls8c_ard_3', query=query)

        # Load data from all three Landsats
        ds = load_ard(dc=dc,
                      measurements=sat_params[satellites]['styles'][style],
                      products=sat_params[satellites]['products'],
                      mask_pixel_quality=False,
                      output_crs=crs,
                      resolution=resolution,
                      group_by='solar_day',
                      dask_chunks={
                          'time': 1,
                          'x': 3000,
                          'y': 3000
                      },
                      **query)
        
        ds = masking.mask_invalid_data(ds)

        ############
        # Plotting #
        ############

        # Keep nearest timestep only
        nearest_time = np.argmin(abs(ds.time.values - np.datetime64(date)))

        # Convert to numpy array
        rgb_array = np.transpose(ds.isel(time=nearest_time).to_array().values,
                                 axes=[1, 2, 0])

        # Apply a log transform to improve colours
        power = None
        if power:
            rgb_array = rgb_array**power

        # Contrast stretching
        if percentile_stretch:    
            vmin, vmax = np.nanpercentile(rgb_array, percentile_stretch)
        rgb_rescaled = exposure.rescale_intensity(rgb_array.astype(np.float),
                                                  in_range=(vmin, vmax),
                                                  out_range=(0.0, 1.0))

        # Create unique file name
        fname = f'{satellites}_{date}_{centre_coords[0]:+.2f}_{centre_coords[1]:.2f}.png'

        # Export to file
        print('Exporting image to file...')
        plt.imsave(fname=fname, arr=rgb_rescaled, format="png")
