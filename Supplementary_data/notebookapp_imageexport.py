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
import numpy as np
import matplotlib.pyplot as plt
from odc.ui import select_on_a_map
from datacube.utils.geometry import CRS
from datacube.storage import masking
from skimage import exposure
from ipyleaflet import (WMSLayer, basemaps, basemap_to_tiles)
from traitlets import Unicode

import sys
sys.path.insert(1, '../Tools/')
from dea_tools.spatial import reverse_geocode
from dea_tools.datahandling import load_ard, mostcommon_crs
from dea_tools.dask import create_local_dask_cluster


def run_imageexport_app(date,
                        satellites,                        
                        style,
                        resolution=(-30, 30),
                        vmin=0, 
                        vmax=2000,
                        percentile_stretch=None,
                        power=None,
                        size_limit=30000):
    '''
    An interactive app that allows the user to select a region from a
    map, then export Digital Earth Australia satellite data as an image
    file. Files are named to match the DEA Imagery and Animations folder
    naming convention:
    
        "<product> - <YYYY-MM-DD> - <location> - <description>.png" 
    
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
    resolution : tuple, optional
        The spatial resolution to load data. The default is 
        `resolution = (-30, 30)`, which will load data at 30 m pixel 
        resolution. Increasing this (e.g. to `resolution = (-100, 100)`) 
        can be useful for loading large spatial extents.
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
        Defaults to 30000 sq km.        
    '''

    ###########################
    # Set up satellite params #
    ###########################

    sat_params = {
        'Landsat': {
            'layer': 'ga_ls_ard_3',
            'products': ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'],
            'styles': {
                'True colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'False colour': ['nbart_swir_1', 'nbart_nir', 'nbart_green']
            }
        },
        'Sentinel-2': {
            'layer': 's2_ard_granule_nbar_t',
            'products': ['s2a_ard_granule', 's2b_ard_granule'],
            'styles': {
                'True colour': ['nbart_red', 'nbart_green', 'nbart_blue'],
                'False colour': ['nbart_swir_2', 'nbart_nir_1', 'nbart_green']
            }
        },
        'Sentinel-2 NRT': {
            'layer': 's2_nrt_granule_nbar_t',
            'products': ['s2a_nrt_granule', 's2b_nrt_granule'],
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
                                 layers=(basemap, time_wms, ),
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

        # Create query based on time range, area selected, custom params
        date = '2021-03-31'
        query = {'time': date, 'geopolygon': geopolygon}

        # Obtain native CRS
        print('Loading imagery...\n')
        crs = mostcommon_crs(dc=dc, 
                             product=sat_params[satellites]['products'], 
                             query=query)

        # Load data from all three Landsats
        ds = load_ard(dc=dc,
                      measurements=sat_params[satellites]['styles'][style],
                      products=sat_params[satellites]['products'],
                      mask_pixel_quality=False,
                      output_crs=crs,
                      resolution=resolution,
                      group_by='solar_day',
                      dask_chunks={'time': 1, 'x': 3000, 'y': 3000},
                      **query)
        
        # Set nodata to nan
        ds = masking.mask_invalid_data(ds)

        ############
        # Plotting #
        ############

        # Create unique file name
        site = reverse_geocode(coords=centre_coords)
        fname = f'{satellites} - {date} - {site} - {style}.png'
        print(f'\nExporting image to {fname}')
        
        # Convert to numpy array
        rgb_array = np.transpose(ds.isel(time=0).to_array().values,
                                 axes=[1, 2, 0])

        # If percentile stretch is supplied, calculate vmin and vmax
        # from percentiles
        if percentile_stretch:    
            vmin, vmax = np.nanpercentile(rgb_array, percentile_stretch)
            
        # Raise by power to dampen bright features and enhance dark.
        # Raise vmin and vmax by same amount to ensure proper stretch
        if power:
            rgb_array = rgb_array ** power
            vmin, vmax = vmin ** power, vmax ** power            
        
        # Rescale/stretch imagery between vmin and vmax
        rgb_rescaled = exposure.rescale_intensity(rgb_array.astype(np.float),
                                                  in_range=(vmin, vmax),
                                                  out_range=(0.0, 1.0))
        # Plot RGB
        plt.imshow(rgb_rescaled)

        # Export to file
        plt.imsave(fname=fname, arr=rgb_rescaled, format="png")
