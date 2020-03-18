## dea_coastaltools.py
'''
Description: This file contains a set of python functions for conducting 
coastal analyses on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, post a question on the Open Data Cube 
Slack channel (http://slack.opendatacube.org/) or the GIS Stack Exchange 
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using 
the `open-data-cube` tag (you can view previously asked questions here: 
https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one 
on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Functions included:
    tidal_tag
    tidal_stats

Last modified: February 2020

'''

# Import required packages
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from otps import TimePoint
from otps import predict_tide
from datacube.utils.geometry import CRS

# Fix converters for tidal plot
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def tidal_tag(ds,
              tidepost_lat=None, 
              tidepost_lon=None, 
              ebb_flow=False, 
              swap_dims=False,
              return_tideposts=False):
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
    ebb_flow : bool, optional
        An optional boolean indicating whether to compute if the 
        tide phase was ebbing (falling) or flowing (rising) for each 
        observation. The default is False; if set to True, a new 
        `ebb_flow` variable will be added to the dataset with each 
        observation labelled with 'Ebb' or 'Flow'.
    swap_dims : bool, optional
        An optional boolean indicating whether to swap the `time` 
        dimension in the original xarray.Dataset to the new 
        `tide_height` variable. Defaults to False.
    return_tideposts : bool, optional
        An optional boolean indicating whether to return the `tidepost_lat`
        and `tidepost_lon` location used to model tides in addition to the
        xarray.Dataset. Defaults to False.
        
    Returns
    -------
    The original xarray.Dataset with a new `tide_height` variable giving
    the height of the tide (and optionally, its ebb-flow phase) at the 
    exact moment of each satellite acquisition.  
    
    (if `return_tideposts=True`, the function will also return the 
    `tidepost_lon` and `tidepost_lat` location used in the analysis)
    
    """

    # If custom tide modelling locations are not provided, use the
    # dataset centroid
    if not tidepost_lat or not tidepost_lon:

        tidepost_lon, tidepost_lat = ds.extent.centroid.to_crs(
            crs=CRS('EPSG:4326')).coords[0]
        print(f'Setting tide modelling location from dataset centroid: '
              f'{tidepost_lon:.2f}, {tidepost_lat:.2f}')

    else:
        print(f'Using user-supplied tide modelling location: '
              f'{tidepost_lon:.2f}, {tidepost_lat:.2f}')

    # Use the tidal model to compute tide heights for each observation:
    obs_datetimes = ds.time.data.astype('M8[s]').astype('O').tolist()    
    obs_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) 
                      for dt in obs_datetimes]
    obs_predictedtides = predict_tide(obs_timepoints)   

    # If tides cannot be successfully modeled (e.g. if the centre of the 
    # xarray dataset is located is over land), raise an exception
    if len(obs_predictedtides) > 0:

        # Extract tide heights
        obs_tideheights = [predictedtide.tide_m for predictedtide 
                           in obs_predictedtides]

        # Assign tide heights to the dataset as a new variable
        ds['tide_height'] = xr.DataArray(obs_tideheights, [('time', ds.time)])

        # Optionally calculate the tide phase for each observation
        if ebb_flow:
            
            # Model tides for a time 15 minutes prior to each previously
            # modelled satellite acquisition time. This allows us to compare
            # tide heights to see if they are rising or falling.
            print('Modelling tidal phase (e.g. ebb or flow)')
            pre_times = (ds.time - pd.Timedelta('15 min'))
            pre_datetimes = pre_times.data.astype('M8[s]').astype('O').tolist()   
            pre_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) 
                              for dt in pre_datetimes]
            pre_predictedtides = predict_tide(pre_timepoints)
            
            # Compare tides computed for each timestep. If the previous tide 
            # was higher than the current tide, the tide is 'ebbing'. If the
            # previous tide was lower, the tide is 'flowing'
            tidal_phase = ['Ebb' if pre.tide_m > obs.tide_m else 'Flow'
                           for pre, obs in zip(pre_predictedtides, 
                                               obs_predictedtides)]
            
            # Assign tide phase to the dataset as a new variable
            ds['ebb_flow'] = xr.DataArray(tidal_phase, [('time', ds.time)]) 
            
        # If swap_dims = True, make tide height the primary dimension 
        # instead of time
        if swap_dims:

            # Swap dimensions and sort by tide height
            ds = ds.swap_dims({'time': 'tide_height'})          
            ds = ds.sortby('tide_height')  
            ds = ds.drop('time')
            
        if return_tideposts:
            return ds, tidepost_lon, tidepost_lat
        else:
            return ds
    
    else:
        
        raise ValueError(
            f'Tides could not be modelled for dataset centroid located '
            f'at {tidepost_lon:.2f}, {tidepost_lat:.2f}. This can occur if '
            f'this coordinate occurs over land. Please manually specify '
            f'a tide modelling location located over water using the '
            f'`tidepost_lat` and `tidepost_lon` parameters.'
        )


def tidal_stats(ds, 
                tidepost_lat=None,
                tidepost_lon=None,
                plain_english=True, 
                plot=True,
                modelled_freq='2h',
                round_stats=3): 
    """
    Takes an xarray.Dataset and statistically compares the tides 
    modelled for each satellite observation against the full modelled 
    tidal range. This comparison can be used to evaluate whether the 
    tides observed by satellites (e.g. Landsat) are biased compared to 
    the natural tidal range (e.g. fail to observe either the highest or 
    lowest tides etc).    
       
    By default, the function models tides for the centroid of the 
    dataset, but a custom tidal modelling location can be specified 
    using `tidepost_lat` and `tidepost_lon`.
    
    Tides are modelled using the OTPS tidal modelling software based on
    the TPXO8 tidal model: http://volkov.oce.orst.edu/tides/tpxo8_atlas.html
    
    For more information about the tidal statistics computed by this 
    function, refer to Figure 8 in Bishop-Taylor et al. 2018:
    https://www.sciencedirect.com/science/article/pii/S0272771418308783#fig8
    
    Parameters
    ----------     
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions  
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling 
        location.
    plain_english : bool, optional
        An optional boolean indicating whether to print a plain english 
        version of the tidal statistics to the screen. Defaults to True.
    plot : bool, optional
        An optional boolean indicating whether to plot how satellite-
        observed tide heights compare against the full tidal range. 
        Defaults to True.
    modelled_freq : str, optional
        An optional string giving the frequency at which to model tides 
        when computing the full modelled tidal range. Defaults to '2h', 
        which computes a tide height for every two hours across the
        temporal extent of `ds`.        
    round_stats : int, optional
        The number of decimal places used to round the output statistics.
        Defaults to 3.
        
    Returns
    -------
    A pandas.Series object containing the following statistics:
    
        tidepost_lat: latitude used for modelling tide heights
        tidepost_lon: longitude used for modelling tide heights
        observed_min_m: minimum tide height observed by the satellite
        all_min_m: minimum tide height from full modelled tidal range
        observed_max_m: maximum tide height observed by the satellite
        all_max_m: maximum tide height from full modelled tidal range
        observed_range_m: tidal range observed by the satellite
        all_range_m: full modelled tidal range 
        spread_m: proportion of the full modelled tidal range observed 
                  by the satellite (see Bishop-Taylor et al. 2018)
        low_tide_offset: proportion of the lowest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        high_tide_offset: proportion of the highest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        observed_slope: slope of any relationship between observed tide 
                  heights and time
        all_slope: slope of any relationship between all modelled tide 
                  heights and time
        observed_pval: significance/p-value of any relationship between 
                  observed tide heights and time
        all_pval: significance/p-value of any relationship between 
                  all modelled tide heights and time
    
    """
    
    # Model tides for each observation in the supplied xarray object
    ds_tides, tidepost_lon, tidepost_lat = tidal_tag(ds,
                                                     tidepost_lat=tidepost_lat,
                                                     tidepost_lon=tidepost_lon,
                                                     return_tideposts=True)

    # Generate range of times covering entire period of satellite record
    all_timerange = pd.date_range(start=ds_tides.time.min().item(),
                                  end=ds_tides.time.max().item(),
                                  freq=modelled_freq)
    all_datetimes = all_timerange.values.astype('M8[s]').astype('O').tolist()  

    # Use the tidal model to compute tide heights for each observation:  
    all_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) 
                      for dt in all_datetimes]
    all_predictedtides = predict_tide(all_timepoints)   
    all_tideheights = [predictedtide.tide_m for predictedtide 
                        in all_predictedtides]

    # Get coarse statistics on all and observed tidal ranges
    obs_mean = ds_tides.tide_height.mean().item()
    all_mean = np.mean(all_tideheights)
    obs_min, obs_max = ds_tides.tide_height.quantile([0.0, 1.0]).values
    all_min, all_max = np.quantile(all_tideheights, [0.0, 1.0])

    # Calculate tidal range
    obs_range = (obs_max - obs_min)
    all_range = (all_max - all_min)

    # Calculate Bishop-Taylor et al. 2018 tidal metrics
    spread = obs_range / all_range
    low_tide_offset = abs(all_min - obs_min) / all_range
    high_tide_offset = abs(all_max - obs_max) / all_range  
    
    # Extract x (time in decimal years) and y (distance) values
    all_x = (all_timerange.year + 
             ((all_timerange.dayofyear - 1) / 365) +
             ((all_timerange.hour - 1) / 24))
    all_y = all_tideheights
    time_period = all_x.max() - all_x.min()

    # Extract x (time in decimal years) and y (distance) values
    obs_x = (ds_tides.time.dt.year + 
             ((ds_tides.time.dt.dayofyear - 1) / 365) + 
             ((ds_tides.time.dt.hour - 1) / 24))
    obs_y = ds_tides.tide_height.values.astype(np.float)           

    # Compute linear regression
    obs_linreg = stats.linregress(x=obs_x, y=obs_y)  
    all_linreg = stats.linregress(x=all_x, y=all_y)
    
    if plain_english:
        
        print(f'\n{spread:.0%} of the full {all_range:.2f} m modelled tidal '
              f'range is observed at this location.\nThe lowest '
              f'{low_tide_offset:.0%} and highest {high_tide_offset:.0%} '
              f'of tides are never observed.\n')
        
        # Plain english
        if obs_linreg.pvalue > 0.05:
            print(f'Observed tides do not increase or decrease significantly '
                  f'over the ~{time_period:.0f} year period.')
        else:
            obs_slope_desc = 'decrease' if obs_linreg.slope < 0 else 'increase'
            print(f'Observed tides {obs_slope_desc} significantly '
                  f'(p={obs_linreg.pvalue:.3f}) over time by '
                  f'{obs_linreg.slope:.03f} m per year (i.e. a '
                  f'~{time_period * obs_linreg.slope:.2f} m '
                  f'{obs_slope_desc} over the ~{time_period:.0f} year period).')

        if all_linreg.pvalue > 0.05:
            print(f'All tides do not increase or decrease significantly over '
                  f'the ~{time_period:.0f} year period.')
        else:
            all_slope_desc = 'decrease' if all_linreg.slope < 0 else 'increase'
            print(f'All tides {all_slope_desc} significantly '
                  f'(p={all_linreg.pvalue:.3f}) over time by '
                  f'{all_linreg.slope:.03f} m per year (i.e. a '
                  f'~{time_period * all_linreg.slope:.2f} m '
                  f'{all_slope_desc} over the ~{time_period:.0f} year period).')

    if plot:
        
        # Create plot and add all time and observed tide data
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(all_timerange, all_tideheights, alpha=0.4)
        ds_tides.tide_height.plot.line(ax=ax, 
                                       marker='o',
                                       linewidth=0.0, 
                                       color='black',
                                       markersize=2)

        # Add horizontal lines for spread/offsets
        ax.axhline(obs_min, color='black', linestyle=':', linewidth=1)
        ax.axhline(obs_max, color='black', linestyle=':', linewidth=1)
        ax.axhline(all_min, color='black', linestyle=':', linewidth=1)
        ax.axhline(all_max, color='black', linestyle=':', linewidth=1)

        # Add text annotations for spread/offsets
        ax.annotate('    High tide\n    offset', 
                     xy=(all_timerange.max(), 
                         np.mean([all_max, obs_max])), 
                     va='center')
        ax.annotate('    Spread', 
                     xy=(all_timerange.max(), 
                         np.mean([obs_min, obs_max])), 
                     va='center')
        ax.annotate('    Low tide\n    offset', 
                     xy=(all_timerange.max(), 
                         np.mean([all_min, obs_min])))

        # Remove top right axes and add labels
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_ylabel('Tide height (m)')
        ax.set_xlabel('');
        ax.margins(x=0.015)
        
    # Export pandas.Series containing tidal stats
    return pd.Series({'tidepost_lat': tidepost_lat,
                      'tidepost_lon': tidepost_lon,
                      'observed_mean_m': obs_mean,
                      'all_mean_m': all_mean,
                      'observed_min_m': obs_min,
                      'all_min_m': all_min,
                      'observed_max_m': obs_max,
                      'all_max_m': all_max,
                      'observed_range_m': obs_range,
                      'all_range_m': all_range,
                      'spread': spread,
                      'low_tide_offset': low_tide_offset,
                      'high_tide_offset': high_tide_offset,
                      'observed_slope': obs_linreg.slope,
                      'all_slope': all_linreg.slope,
                      'observed_pval': obs_linreg.pvalue,
                      'all_pval': all_linreg.pvalue}).round(round_stats)
