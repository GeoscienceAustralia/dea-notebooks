# notebookapp_changefilmstrips.py
'''
This file contains functions for loading and interacting with data in the
change filmstrips notebook, inside the Real_world_examples folder.

Available functions:
    run_filmstrips_app

Last modified: January 2020
'''

# Load modules
import os
import sys
import dask
import datacube
import numpy as np
import matplotlib.pyplot as plt
from odc.ui import select_on_a_map
from dask.utils import parse_bytes
from datacube.utils.geometry import CRS
from datacube.utils.rio import configure_s3_access
from datacube.utils.dask import start_local_dask
from odc.algo import xr_geomedian 

# Load utility functions
sys.path.append('../Scripts')
from dea_datahandling import load_ard
from dea_coastaltools import tidal_tag


def run_filmstrip_app(time_range,
                      time_step,
                      tide_range=(0.0, 1.0),
                      max_cloud=50,
                      resolution=(-30, 30),
                      size_limit=100):
    
    dc = datacube.Datacube(app='DEA_notebooks_template')
    
    # Configure dashboard link to go over proxy
    dask.config.set({"distributed.dashboard.link":
                     os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')+"proxy/{port}/status"});

    # Figure out how much memory/cpu we really have (those are set by jupyterhub)
    mem_limit = int(os.environ.get('MEM_LIMIT', '0'))
    cpu_limit = float(os.environ.get('CPU_LIMIT', '0'))
    cpu_limit = int(cpu_limit) if cpu_limit > 0 else 4
    mem_limit = mem_limit if mem_limit > 0 else parse_bytes('8Gb')

    # Leave 4Gb for notebook itself
    mem_limit -= parse_bytes('4Gb')

    # Close previous client if any, so that one can re-run this cell without issues
    client = locals().get('client', None)
    if client is not None:
        client.close()
        del client

    # Start dask client
    client = start_local_dask(n_workers=1,
                              threads_per_worker=cpu_limit, 
                              memory_limit=mem_limit)
    display(client)

    # Configure GDAL for s3 access 
    configure_s3_access(aws_unsigned=True,  # works only when reading public resources
                        client=client);

    
    # Plot interactive map to select area
    geopolygon = select_on_a_map(height='600px', 
                                 center=(-33.9719, 151.1934), zoom=12)

    # Test size
    area = (geopolygon.to_crs(crs = CRS('epsg:3577')).area / 
            (size_limit * 1000000))
    radius = np.round(np.sqrt(size_limit), 1)
    if area > size_limit: 
        print(f'Warning: Your selected area is {area:.00f} square kilometers. \n'
              f'Please select an area of less than {size_limit} square kilometers (e.g. '
              f'{radius} x {radius} km) . \nTo select a smaller area, re-run the cell above '
              f'and draw a new polygon.')
        
    else:
        
        query = {'time': time_range,
                 'geopolygon': geopolygon,
                 'output_crs': 'epsg:3577',
#                  'resampling': {'*': 'average', 'fmask': 'nearest'},
                 'gqa_iterative_mean_xy': [0, 1],
                 'cloud_cover': [0, max_cloud],
                 'resolution': resolution}

        ds = load_ard(dc=dc, 
                      measurements=['nbart_red', 'nbart_green', 'nbart_blue'],  
                      products=['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'], 
                      min_gooddata=0.0,
                      lazy_load=True,
                      **query)
        
        # Calculate tides for each timestep in the satellite dataset
        if tide_range != (0.0, 1.0):
            ds = tidal_tag(ds=ds, tidepost_lat=None, tidepost_lon=None)
            min_tide, max_tide = ds.tide_height.quantile(tide_range).values
            ds = ds.sel(time = (ds.tide_height >= min_tide) & 
                               (ds.tide_height <= max_tide))
            ds = ds.drop('tide_height')
            print(f'    Keeping {len(ds.time)} observations with tides '
                  f'between {min_tide:.2f} and {max_tide:.2f} m')

        ds_geomedian = (ds.resample(time=time_step, closed='left', label='left')
                        .apply(lambda ds_subset: 
                               xr_geomedian(ds_subset, 
                                  num_threads=1,  # disable internal threading, dask will run several concurrently
                                  eps=0.2 * (1 / 10_000),  # 1/5 pixel value resolution
                                  nocheck=True)))  # disable some checks inside geomedian library that use too much ram

        print('\nGenerating filmstrip plot... (this may take several minutes)')
        ds_geomedian = ds_geomedian.compute()

        # Reset CRS
        ds_geomedian.attrs['crs'] = ds.crs
        

        ############
        # Plotting #
        ############
        
        # Convert to array and extract vmin/vmax
        output_array = ds_geomedian[['nbart_red', 'nbart_green',
                                    'nbart_blue']].to_array()
        percentiles = output_array.quantile(q=(0.02, 0.98)).values

        # Create the plot with one subplot more than timesteps in the dataset
        # Figure width is set based on the number of subplots
        n_obs = len(output_array.time)
        fig, axes = plt.subplots(1, n_obs + 1, figsize=(5.05 * (n_obs + 1), 5))
        fig.subplots_adjust(wspace=0.05, hspace=0.05)

        # Add each timestep to the plot and set aspect to equal to preserve shape
        for i, ax_i in enumerate(axes.flatten()[:n_obs]):
            output_array.isel(time=i).plot.imshow(ax=ax_i,
                                                  vmin=percentiles[0],
                                                  vmax=percentiles[1])
            ax_i.get_xaxis().set_visible(False)
            ax_i.get_yaxis().set_visible(False)
            ax_i.set_aspect('equal')

        # Add standard deviation panel to final subplot
        output_array.std(dim=['time']).mean(dim='variable').plot.imshow(
            ax=axes.flatten()[-1], robust=True, cmap='magma', add_colorbar=False)
        axes.flatten()[-1].get_xaxis().set_visible(False)
        axes.flatten()[-1].get_yaxis().set_visible(False)
        axes.flatten()[-1].set_aspect('equal')
        axes.flatten()[-1].set_title('Standard deviation')

        # Export to file
        date_string = '_'.join(time_range)
        fig.savefig(f'filmstrip_{date_string}_{time_step}.png',
                    dpi=150,
                    bbox_inches='tight',
                    pad_inches=0.1)

        return ds_geomedian

