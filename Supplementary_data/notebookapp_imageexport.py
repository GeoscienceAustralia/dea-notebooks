# notebookapp_imageexport.py
'''
This file contains functions for creating an interactive map for 
selecting satellite imagery and exporting image files.

Available functions:
    run_imageexport_app

Last modified: September 2021
'''

# Load modules
import datacube
import itertools
import numpy as np
import matplotlib.pyplot as plt
from odc.ui import select_on_a_map
from datacube.utils.geometry import CRS
from datacube.utils import masking
from skimage import exposure
from ipyleaflet import (WMSLayer, basemaps, basemap_to_tiles)
from traitlets import Unicode

import sys

sys.path.insert(1, '../Tools/')
from dea_tools.spatial import reverse_geocode
from dea_tools.dask import create_local_dask_cluster
from dea_tools.datahandling import pan_sharpen_brovey


def run_imageexport_app(date,
                        satellites,
                        style,
                        pansharpen=True,
                        resolution=None,
                        vmin=0,
                        vmax=2000,
                        percentile_stretch=None,
                        power=None,
                        standardise_name=False,
                        image_proc_funcs=None,
                        size_limit=10000):
    '''
    An interactive app that allows the user to select a region from a
    map, then export Digital Earth Australia satellite data as an image
    file. The function supports Sentinel-2 and Landsat data, creating
    True and False colour images, and applying pansharpening to increase
    the resolution of Landsat 7 and 8 imagery.
        
    By default, files are named to match the DEA Imagery and Animations 
    folder naming convention:
    
        "<product> - <YYYY-MM-DD> - <site, state> - <description>.png" 
        
    Set `standardise_name=True` for a machine-readable name:
    
        "<product>_<YYYY-MM-DD>_<site-state>_<description>.png" 
    
    Last modified: September 2021

    Parameters
    ----------
    date : str
        The exact date used to extract imagery (e.g. `date='1988-01-01'`). 
        This is also used to plot imagery from the same date over the 
        interactive map.
    satellites : str
        The satellite data to be used to extract the image. Three 
        options are currently supported:
            "Landsat": data from the Landsat 5, 7 and 8 satellites
            "Sentinel-2": data from Sentinel-2A and Sentinel-2B
            "Sentinel-2 NRT": most recent 'near real time' data from 
            Sentinel-2A and Sentinel-2B (use this to obtain imagery 
            acquired in the past three months).
    style : str
        The style used to produce the image. Two options are currently
        supported:
            "True colour": Creates a true colour image using the red, 
            green and blue satellite bands
            "False colour": Creates a false colour image using 
            short-wave infrared, infrared and green satellite bands.
            The specific bands used vary between Landsat and Sentinel-2.  
    pansharpen: bool, optional
        Whether to apply pansharpening (using the Brovey Transform) to 
        increase the resolution of Landsat imagery from 30 m to 15 m 
        pixels. This will only be applied if all the following are 
        true: 
            - Landsat 7 or 8 data (with panchromatic band)
            - `style` is set to "True colour"
            - `resolution` is set to `None` (see below).
    resolution : tuple, optional
        The spatial resolution to load data. By default, the tool will 
        automatically set the best possible resolution depending on the 
        satellites selected (i.e 30 m for Landsat, 10 m for Sentinel-2). 
        Increasing this (e.g. to resolution = (-100, 100)) can be useful
        for loading large spatial extents.
    vmin, vmax : int or float
        The minimum and maximum surface reflectance values used to 
        clip the resulting imagery to enhance contrast. 
    percentile_stretch : tuple of floats, optional
        An tuple of two floats (between 0.00 and 1.00) that can be used 
        to clip the imagery to based on percentiles to get more control 
        over the brightness and contrast of the image. The default is 
        None; '(0.02, 0.98)' is equivelent to `robust=True`. If this 
        parameter is used, `vmin` and `vmax` will have no effect.
    power : float, optional
        Raises imagery by a power to reduce bright features and 
        enhance dark features. This can add extra definition over areas
        with extremely bright features like snow, beaches or salt pans.
    size_limit : int, optional
        An optional size limit for the area selection in sq km.
        Defaults to 10000 sq km.        
    '''

    ###########################
    # Set up satellite params #
    ###########################

    sat_params = {
        'Landsat': {
            'layer': 'ga_ls_ard_3',
            'products': ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'],
            'resolution': [-30, 30],
            'styles': {
                'True colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'False colour': ['nbart_swir_1', 'nbart_nir', 'nbart_green']
            }
        },
        'Sentinel-2': {
            'layer': 's2_ard_granule_nbar_t',
            'products': ['s2a_ard_granule', 's2b_ard_granule'],
            'resolution': [-10, 10],
            'styles': {
                'True colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'False colour': ['nbart_swir_2', 'nbart_nir_1', 'nbart_green']
            }
        },
        'Sentinel-2 NRT': {
            'layer': 's2_nrt_granule_nbar_t',
            'products': ['s2a_nrt_granule', 's2b_nrt_granule'],
            'resolution': [-10, 10],
            'styles': {
                'True colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'False colour': ['nbart_swir_2', 'nbart_nir_1', 'nbart_green']
            }
        }
    }

    ########################
    # Select and load data #
    ########################

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
    basemap = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
    geopolygon = select_on_a_map(height='600px',
                                 layers=(
                                     basemap,
                                     time_wms,
                                 ),
                                 center=(-25.18, 134.18),
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

        # Connect to datacube database
        dc = datacube.Datacube(app='Exporting_satellite_images')

        # Configure local dask cluster
        create_local_dask_cluster()

        # Create query after adjusting interval time to UTC by
        # adding a UTC offset of -10 hours. This results issues
        # on the east coast of Australia where satelite overpasses
        # can occur on either side of 24:00 hours UTC
        start_date = np.datetime64(date) - np.timedelta64(10, 'h')
        end_date = np.datetime64(date) + np.timedelta64(14, 'h')
        query_params = {
            'time': (str(start_date), str(end_date)),
            'geopolygon': geopolygon
        }

        # Find matching datasets
        dss = [
            dc.find_datasets(product=i, **query_params)
            for i in sat_params[satellites]['products']
        ]
        dss = list(itertools.chain.from_iterable(dss))

        # Get CRS and sensor
        crs = str(dss[0].crs)
        sensor = dss[0].metadata_doc['properties']['eo:platform'].capitalize()
        sensor = sensor[0:-1].replace('_', '-') + sensor[-1].capitalize()

        # Meets pansharpening requirements
        can_pansharpen = style == 'True colour' and not resolution and sensor in [
            'Landsat-7', 'Landsat-8'
        ]

        # Set up load params
        if pansharpen and can_pansharpen:
            load_params = {
                'output_crs': crs,
                'resolution': (-15, 15),
                'align': (7.5, 7.5),
                'resampling': 'bilinear'
            }

            # Add panchromatic to list of true colour bands
            sat_params[satellites]['styles']['True colour'] += [
                'nbart_panchromatic'
            ]

        else:

            # Use resolution if provided, otherwise use default
            if resolution:
                sat_params[satellites]['resolution'] = resolution

            load_params = {
                'output_crs': crs,
                'resolution': sat_params[satellites]['resolution'],
                'resampling': 'bilinear'
            }

        # Load data from datasets
        ds = dc.load(datasets=dss,
                     measurements=sat_params[satellites]['styles'][style],
                     group_by='solar_day',
                     dask_chunks={
                         'time': 1,
                         'x': 3000,
                         'y': 3000
                     },
                     **load_params,
                     **query_params)
        ds = masking.mask_invalid_data(ds)

        # Create plain numpy array, optionally after pansharpening
        if pansharpen and can_pansharpen:

            # Perform Brovey pan-sharpening and return three numpy.arrays
            print(f'Pansharpening {sensor} image to 15 m resolution')
            red_sharpen, green_sharpen, blue_sharpen = pan_sharpen_brovey(
                band_1=ds.nbart_red,
                band_2=ds.nbart_green,
                band_3=ds.nbart_blue,
                pan_band=ds.nbart_panchromatic)
            rgb_array = np.vstack([red_sharpen, green_sharpen, blue_sharpen])

        else:
            rgb_array = ds.isel(time=0).to_array().values

        ############
        # Plotting #
        ############

        # Create unique file name
        site = reverse_geocode(coords=centre_coords)
        fname = (f"{sensor} - {date} - {site} - {style}, "
                 f"{load_params['resolution'][1]} m resolution.png")

        # Remove spaces and commas if requested
        if standardise_name:
            fname = fname.replace(' - ', '_').replace(', ',
                                                      '-').replace(' ',
                                                                   '-').lower()

        print(
            f'\nExporting image to {fname}.\nThis may take several minutes to complete...'
        )

        # Convert to numpy array
        rgb_array = np.transpose(rgb_array, axes=[1, 2, 0])

        # If percentile stretch is supplied, calculate vmin and vmax
        # from percentiles
        if percentile_stretch:
            vmin, vmax = np.nanpercentile(rgb_array, percentile_stretch)

        # Raise by power to dampen bright features and enhance dark.
        # Raise vmin and vmax by same amount to ensure proper stretch
        if power:
            rgb_array = rgb_array**power
            vmin, vmax = vmin**power, vmax**power

        # Rescale/stretch imagery between vmin and vmax
        rgb_rescaled = exposure.rescale_intensity(rgb_array.astype(float),
                                                  in_range=(vmin, vmax),
                                                  out_range=(0.0, 1.0))
        
        # Apply image processing funcs
        if image_proc_funcs:
            for i, func in enumerate(image_proc_funcs):
                print(f'Applying custom function {i + 1}')
                rgb_rescaled = func(rgb_rescaled)
    
        # Plot RGB
        plt.imshow(rgb_rescaled)

        # Export to file
        plt.imsave(fname=fname, arr=rgb_rescaled, format="png")
        print('Finished exporting image.')
