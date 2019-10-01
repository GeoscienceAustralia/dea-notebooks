## dea_coastaltools.py
'''
Description: This file contains a set of python functions for conducting coastal analyses on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

'''

# Import required packages
import xarray as xr
from otps import TimePoint
from otps import predict_tide
from datacube.utils.geometry import CRS


def tidal_tag(ds, tidepost_lat=None, tidepost_lon=None, swap_dims=False):
    """
    Takes an xarray.Dataset and returns the same dataset with a new 
    `tide_height` variable giving the height of the tide at the exact
    moment of each satellite acquisition. 
    
    By default, the function models tides for the centroid of the 
    dataset, but a custom tidal modelling location can be specified 
    using `tidepost_lat` and `tidepost_lon`.
    
    Tides are modelled using the OTPS tidal modelling software based on
    the TPXO8 tidal model: http://volkov.oce.orst.edu/tides/tpxo8_atlas.html
    
    Parameters
    ----------     
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions  
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling 
        location.
    swap_dims : bool, optional
        An optional boolean indicating whether to swap the `time` 
        dimension in the original xarray.Dataset to the new 
        `tide_height` variable. 
        
    Returns
    -------
    The original xarray.Dataset with a new `tide_height` variable giving
    the height of the tide at the exact moment of each satellite 
    acquisition.  
    
    """

    # If custom tide modelling locations are not provided, use the
    # dataset centroid
    if not tidepost_lat or not tidepost_lon:

        tidepost_lon, tidepost_lat = ds.extent.centroid.to_crs(
            crs=CRS('EPSG:4326')).coords[0]
        print(f'Setting tide modelling location from dataset centroid: '
              f'{tidepost_lon}, {tidepost_lat}')

    else:
        print(f'Using user-supplied tide modelling location: '
              f'{tidepost_lon}, {tidepost_lat}')

    # Use the tidal model to compute tide heights for each observation:
    obs_datetimes = ds.time.data.astype('M8[s]').astype('O').tolist()
    obs_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) 
                      for dt in obs_datetimes]
    obs_predictedtides = predict_tide(obs_timepoints)

    # If tides cannot be successfully modeled (e.g. if the centre of the 
    # xarray dataset is located is over land), raise an exception
    if len(obs_predictedtides) == 0:

        raise ValueError(
            f'Tides could not be modelled for dataset centroid located '
            f'at {tidepost_lon}, {tidepost_lat}. This can happen if '
            f'this coordinate occurs over land. Please manually specify '
            f'a tide modelling location located over water using the '
            f'`tidepost_lat` and `tidepost_lon` parameters.'
        )

    else:

        # Extract tide heights
        obs_tideheights = [predictedtide.tide_m for predictedtide 
                           in obs_predictedtides]

        # Assign tide heights to the dataset as a new variable
        ds['tide_height'] = xr.DataArray(obs_tideheights, [('time', ds.time)])

        # If swap_dims = True, make tide height the primary dimension 
        # instead of time
        if swap_dims:

            # Swap dimensions and sort by tide height
            ds = ds.swap_dims({'time': 'tide_height'})
            ds = ds.sortby('tide_height')

        return ds
