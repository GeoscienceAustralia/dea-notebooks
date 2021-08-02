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
    polyline_select
    deacoastlines_transect
    deacoastlines_histogram

Last modified: November 2020

'''

# Import required packages
import os
import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd 
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy import stats
from otps import TimePoint
from otps import predict_tide
from datacube.utils.geometry import CRS
from shapely.geometry import box, shape

# Widgets and WMS
from odc.ui import ui_poll, select_on_a_map
from ipyleaflet import (Map, WMSLayer, WidgetControl, FullScreenControl, 
                        DrawControl, basemaps, basemap_to_tiles, TileLayer)
from ipywidgets.widgets import Layout, Button, HTML
from IPython.display import display
from types import SimpleNamespace

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

        
def polyline_select(center=(-26, 135),
                    zoom=4,
                    height='600px'):
    """
    Allows the user to interactively draw a polyline on the map with a 
    DEA CoastLines overlay.
    
    This is a line drawing equivelent of `select_on_a_map` from `odc.ui`.    
    
    Parameters
    ----------
    center : tuple, optional
        An optional tuple providing the latitude and longitude over 
        which to centre the interactive map. Defaults to 
        `center=(-26, 135)`.
    zoom : integer, optional
        An optional integer giving the default zoom level for the map.
        Defaults to `zoom=4`.
    height : string, optional
        An optional string giving the height of the map in pixels. 
        Defaults to `height='600px'`.
        
    Returns
    -------
    An interactive ipyleaflet map and interactive state used as an input
    to the `deacoastlines_transect` function.
    """    
  
    def update_info(txt):
        html_info.value = '<pre style="color:grey">' + txt + '</pre>'

    def render_bounds(bounds):
        (lat1, lon1), (lat2, lon2) = bounds
        txt = 'lat: [{:.{n}f}, {:.{n}f}]\nlon: [{:.{n}f}, {:.{n}f}]'.format(
            lat1, lat2, lon1, lon2, n=4)
        update_info(txt)
        
    def on_done(btn):
        state.done = True
        btn_done.disabled = True
        m.remove_control(draw)
        for w in widgets:
            m.remove_control(w)

    def bounds_handler(event):
        bounds = event['new']
        render_bounds(bounds)
        (lat1, lon1), (lat2, lon2) = bounds
        state.bounds = dict(lat=(lat1, lat2),
                            lon=(lon1, lon2))

    def on_draw(event):
        v = event['new']
        action = event['name']
        if action == 'last_draw':
            state.selection = v['geometry']
        elif action == 'last_action' and v == 'deleted':
            state.selection = None

        btn_done.disabled = state.selection is None
        

    state = SimpleNamespace(selection=None,
                            bounds=None,
                            done=False)
    
    # Set up "Done" button
    btn_done = Button(description='done',
                      layout=Layout(width='5em'))
    btn_done.style.button_color = 'green'
    btn_done.disabled = True

    html_info = HTML(layout=Layout(flex='1 0 20em',
                                   width='20em',
                                   height='3em'))

    # Load DEACoastLines WMS
    deacl_url='https://geoserver.dea.ga.gov.au/geoserver/wms'
    deacl_layer='dea:DEACoastLines'
    wms = WMSLayer(url=deacl_url,
                   layers=deacl_layer,
                   format='image/png',
                   transparent=True,
                   attribution='DEA CoastLines © 2020 Geoscience Australia')
    
    # Plot interactive map to select area
    basemap = basemap_to_tiles(basemaps.Esri.WorldImagery)
    places = TileLayer(url=('https://server.arcgisonline.com/ArcGIS/rest/'
                            'services/Reference/World_Boundaries_and_Places'
                            '/MapServer/tile/{z}/{y}/{x}'), opacity=1)
    m = Map(layers=(basemap, wms, places, ),
            center=center, 
            zoom=zoom)
    m.scroll_wheel_zoom = True
    m.layout.height = height

    # Set up done and info widgets
    widgets = [WidgetControl(widget=btn_done, position='topright'),
               WidgetControl(widget=html_info, position='bottomleft')]
    for w in widgets:
        m.add_control(w) 
        
    # Add polyline draw control option
    draw = DrawControl(circlemarker={}, polygon={})
    m.add_control(draw)
    m.add_control(FullScreenControl())
    draw.polyline =  {'shapeOptions': {'color': 'red', 'opacity': 1.0}}

    # Set up interactivity
    draw.observe(on_draw)
    m.observe(bounds_handler, ('bounds',))
    btn_done.on_click(on_done)

    return m, state


def deacoastlines_transect(transect_mode='distance',
                           export_transect_data=True,
                           export_transect=True,
                           export_figure=True,
                           length_limit=50):
    
    """
    Function for interactively drawing a transect line on a map,
    and using this line to extract distances to each annual DEA 
    Coastlines coastline along the transect. The function can also be
    used to measure the width between two coastlines from the same year
    through time.
    
    Parameters
    ----------
    transect_mode : string, optional
        An optional string indicating whether to analyse coastlines 
        using 'distance' or 'width' mode. The "distance" mode measures the 
        distance from the start of the transect to each of the annual
        coastlines, and will ignore any coastline that intersects the 
        transect more than once. The 'width' mode will measure the 
        width between two coastlines from the same year, which can be
        useful for measuring e.g. the width of a tombolo or sandbank 
        through time. This mode will ignore any annual coastline that 
        intersections with the transect only once.
    export_transect_data : boolean, optional
        An optional boolean indicating whether to export the transect
        data as a CSV file. This file will be automatically named using 
        its centroid coordinates, and exported into the directory this 
        code is being run in. The default is True.
    export_transect : boolean, optional
        An optional boolean indicating whether to export the transect
        data as a GeoJSON and ESRI Shapefile. This file will be 
        named automatically using its centroid coordinates, and exported
        into the directory this code is being run in. Default is True.
    export_figure : boolean, optional
        An optional boolean indicating whether to export the transect
        figure as an image file. This file will be automatically named 
        using its centroid coordinates, and exported into the directory 
        this code is being run in. The default is True.
    """
    
    # Run interactive map
    m, state = polyline_select()
    display(m)
    
    def extract_geometry(state):        
        
        # Convert geometry to a GeoSeries
        profile = gpd.GeoSeries(shape(state.selection), 
                                crs='EPSG:4326')  
        
        # Test length
        transect_length = (profile.to_crs('EPSG:3577').length / 1000).sum()
        if transect_length > length_limit:
            raise ValueError(f'Your transect is {transect_length:.0f} km long. '
                             f'Please draw a transect that is less than '
                             f'{length_limit} km long.\nTo draw a shorter '
                             f'transect, re-run the cell above and draw a new '
                             f'polyline.')

        # Load data from WFS
        print('Loading DEA Coastlines data...\n')
        xmin, ymin, xmax, ymax = profile.total_bounds
        deacl_wfs = f'https://geoserver.dea.ga.gov.au/geoserver/wfs?' \
                    f'service=WFS&version=1.1.0&request=GetFeature' \
                    f'&typeName=dea:coastlines&maxFeatures=1000' \
                    f'&bbox={ymin},{xmin},{ymax},{xmax},' \
                    f'urn:ogc:def:crs:EPSG:4326'
        deacl = gpd.read_file(deacl_wfs)
        deacl.crs = 'EPSG:3577'

        # Raise exception if no coastlines are returned
        if len(deacl.index) == 0:
            raise ValueError('No annual coastlines were returned for the '
                             'supplied transect. Please select another area.')
            
        # Dissolve by year to remove duplicates, then sort by date
        deacl = deacl.dissolve(by='year', as_index=False)
        deacl['year'] = deacl.year.astype(int)
        deacl = deacl.sort_values('year')

        # Extract intersections and determine type
        profile = profile.to_crs('EPSG:3577')
        intersects = deacl.apply(
            lambda x: profile.intersection(x.geometry), axis=1)
        intersects = gpd.GeoSeries(intersects[0])   
        
        # Select geometry depending on mode
        intersects_type = (intersects.type == 'Point' if 
                           transect_mode == 'distance' else 
                           intersects.type == 'MultiPoint')

        # Remove annual data according to intersections
        deacl_filtered = deacl.loc[intersects_type]
        drop_years = ', '.join(deacl.year
                               .loc[~intersects_type]
                               .astype(str)
                               .values.tolist())

        # In 'distance' mode, analyse years with one intersection only
        if transect_mode == 'distance':  
            
            if drop_years:
                print(f'Dropping years due to multiple intersections: {drop_years}\n')

            # Add start and end coordinate
            deacl_filtered = deacl_filtered.assign(
                start=profile.interpolate(0).iloc[0])
            deacl_filtered['end'] = intersects.loc[intersects_type]

        # In 'width' mode, analyse years with multiple intersections only
        elif transect_mode == 'width':

            if drop_years:
                print(f'Dropping years due to less than two intersections: {drop_years}\n')

            # Add start and end coordinate
            deacl_filtered = deacl_filtered.assign(
                start=intersects.loc[intersects_type].apply(lambda x: x[0]))
            deacl_filtered['end'] = intersects.loc[intersects_type].apply(
                lambda x: x[1])

        # If any data was returned:
        if len(deacl_filtered.index) > 0:   

            # Compute distance
            deacl_filtered['dist'] = deacl_filtered.apply(
                lambda x: x.start.distance(x.end), axis=1)

            # Extract values
            transect_df = pd.DataFrame(deacl_filtered[['year', 'dist']])
            transect_df['dist'] = transect_df.dist.round(2)
            
            # Plot data
            fig, ax = plt.subplots(1, 1, figsize=(5, 8))
            transect_df.plot(x='dist', y='year', ax=ax, label='DEA Coastlines')
            ax.set_xlabel(f'{transect_mode.title()} (metres)')
            
            # Extract coordinates fore unique file ID
            x, y = profile.geometry.centroid.to_crs('EPSG:4326').iloc[0].xy
            
            # Create output folder if none exists
            if export_transect_data or export_transect or export_figure:
                out_dir = 'deacoastlines_outputs'
                os.makedirs(out_dir, exist_ok=True)
            
            # Optionally write output CSV data
            if export_transect_data:
                csv_path = f'{out_dir}/deacoastlines_transect_{x[0]:.3f}_{y[0]:.3f}.csv'
                
                print(f"Exporting transect data to:\n"
                      f"    {csv_path}\n")
                transect_df.to_csv(csv_path, index=False)
                
            # Optionally write vector data
            if export_transect:
                shp_path = f'{out_dir}/deacoastlines_transect_{x[0]:.3f}_{y[0]:.3f}.shp'
                geojson_path = f'{out_dir}/deacoastlines_transect_{x[0]:.3f}_{y[0]:.3f}.geojson'
                
                print(f"Exporting transect vectors to:\n"
                      f"    {shp_path}\n"
                      f"    {geojson_path}\n")
                profile.to_crs('EPSG:3577').to_file(shp_path)
                profile.to_crs('EPSG:4326').to_file(geojson_path,
                                                    driver='GeoJSON')
            
            # Optionally write image
            if export_figure:
                fig_path = f'{out_dir}/deacoastlines_transect_{x[0]:.3f}_{y[0]:.3f}.png'
                
                print(f'Exporting transect figure to:\n'
                      f'    {fig_path}\n')
                fig.savefig(fig_path, bbox_inches='tight', dpi=200)
                
            # Plot figure
            plt.show()

            return transect_df

        else:
            raise ValueError('No valid intersections found for transect')

    return ui_poll(lambda: extract_geometry(state) if state.done else None)


def deacoastlines_histogram(extent_path=None,
                            extent_id_col=None,
                            export_points_data=True,
                            export_summary_data=True,
                            export_extent=True,
                            export_figure=True,
                            cmap='RdBu',
                            hist_log=True, 
                            hist_bins=60, 
                            hist_range='auto',
                            size_limit=100000,
                            max_features=100000):
    """
    Function for interactively selecting and analysing DEACoastlines 
    statistics point data, and plotting results as histograms to 
    compare rates of change.
    
    Parameters
    ----------
    extent_path : string, optional
        An optional path to a shapefile or other vector file that will 
        be used to extract a subset of DEACoastlines statistics. The 
        default is None, which will select a subset of data using an 
        interactive map.
    extent_id_col : string, optional
        If a vector file is supplied using `extent_path`, a column name
        from the vector file must be specified using this parameter. 
        Values from this column will be used to name any output files.       
    export_points_data : boolean, optional
        An optional boolean indicating whether to export the extracted
        points data as a CSV file. This file will be automatically named 
        using either its centroid coordinates or a value from any column
        supplied using `extent_id_col`. The default is True.
    export_summary_data : boolean, optional
        An optional boolean indicating whether to export a CSV
        containing summary statistics for all extracted points in the
        selected extent. This file will contain a row for every selected
        area and five attribute fields:
             extent_id_col: A name for the selected area based either on
                            its centroid coordinates or a value from any
                            column supplied using `extent_id_col`
            'mean_rate_zeros': Mean of all rates of change (e.g. m / 
                               year) with non-significant points set to
                               a rate of 0 m / year
            'mean_rate_sigonly': Mean of all rates of change (e.g. m / 
                               year) for significant points only
            'n_zeros': Number of observations with non-significant
                       points set to a rate of 0 m / year
            'n_sigonly': Number of observations, significant points only
    export_extent : boolean, optional
        An optional boolean indicating whether to export the polygon
        extent as a GeoJSON and ESRI Shapefile. This file will be 
        automatically named using either its centroid coordinates or a 
        value from any column supplied using `extent_id_col`. The 
        default is True.
    export_figure : boolean, optional
        An optional boolean indicating whether to export the histogram
        figure as an image file. This file will be automatically named 
        using either its centroid coordinates or a value from any column
        supplied using `extent_id_col`. The default is True.
    hist_log : boolean, optional
        An optional boolean indicating whether to plot histograms with 
        a log y-axis. If True, all non-significant statistics points 
        will be assigned a rate of 0 metres / year. If False, all 
        non-significant points will be removed from the dataset, and 
        plotted with a linear y-axis. 
    hist_bins : int, optional
        Number of bins to plot on the histogram. Defaults to 60.
    hist_range : string or tuple, optional
        A tuple giving the min and max range to plot on the x-axis, e.g.
        `hist_range=(-30, 30)`. The default is 'auto', which will 
        automatically optimise the x-axis of the plot based on the 0.001
        and 0.999 percentile rates of change values. 
    size_limit : int, optional
        An optional size limit for the area selection in sq km. 
        Defaults to 100,000 sq km.
    max_features : int, optional
        The maximum number of DEACoastLines statistics points to 
        return from the WFS query. The default is 100,000.
    """
    
    #############
    # Load data #
    #############
    
    # Load polygon from file if path is provided
    if extent_path and extent_id_col:
        extents = (gpd.read_file(extent_path)
                   .to_crs('EPSG:4326')
                   .set_index(extent_id_col))
        
    # Raise error if no column
    elif extent_path and not extent_id_col:
        raise ValueError("Please supply an attribute column using " \
                         "'extent_id_col' when supplying a vector file.")         

    # Otherwise, use interactive map to select region
    else:        
        
        # Load DEACoastlines WMS
        deacl_url='https://geoserver.dea.ga.gov.au/geoserver/wms'
        deacl_layer='dea:DEACoastLines'
        wms = WMSLayer(url=deacl_url,
                       layers=deacl_layer,
                       format='image/png',
                       transparent=True,
                       attribution='DEA CoastLines © 2020 Geoscience Australia')
        
        # Plot interactive map to select area
        basemap = basemap_to_tiles(basemaps.Esri.WorldImagery)
        places = TileLayer(url=('https://server.arcgisonline.com/ArcGIS/rest/'
                               'services/Reference/World_Boundaries_and_Places'
                               '/MapServer/tile/{z}/{y}/{x}'), opacity=1)
        geopolygon = select_on_a_map(height='600px',
                                     layers=(basemap, wms, places, ),
                                     center=(-26, 135), 
                                     zoom=4) 

        # Covert extent object to geopandas.GeoDataFrame object with CRS
        extents = gpd.GeoDataFrame(geometry=[geopolygon], crs='EPSG:4326')        
       
    # List to hold summary stats
    summary_stats = []
    
    # Set up figure
    fig, ax1 = plt.subplots(1, 1, figsize=(10, 8))
    ax1.grid(True, which='both', axis='y', color='0.9')
    ax1.set_axisbelow(True)
    
    #########################
    # Load and analyse data #
    #########################
        
    # Run histogram extraction for each polygon in the extents data
    for index, row in extents.iterrows():
        
        # Pull out single extent
        extent = extents.loc[[index]]
        
        # Verify size
        area = (extent.to_crs(crs='epsg:3577').area / 1000000).sum()
        if area > size_limit:
            raise ValueError(f'Your selected area is {area:.00f} sq km. '
                             f'Please select an area of less than {size_limit} sq km.'
                             f'\nTo select a smaller area, re-run the cell '
                             f'above and draw a new polygon.')
            
        # Extract extent coordinates
        xmin, ymin, xmax, ymax = extent.to_crs('epsg:4326').total_bounds
            
        # Set up analysis ID based on either vector row or coords
        if extent_path:
            extent_id = str(index)
            file_id = os.path.splitext(extent_path)[0]
        else:
            x = (xmin + xmax) / 2
            y = (ymin + ymax) / 2
            extent_id = f'{x:.3f}_{y:.3f}'
            file_id = 'polygon'

        # Load data from WFS
        print(f'Loading DEA Coastlines data for {extent_id}...')
        deacl_wfs = f'https://geoserver.dea.ga.gov.au/geoserver/wfs?' \
                    f'service=WFS&version=1.1.0&request=GetFeature' \
                    f'&typeName=dea:coastlines_statistics' \
                    f'&maxFeatures={max_features}' \
                    f'&bbox={ymin},{xmin},{ymax},{xmax},' \
                    f'urn:ogc:def:crs:EPSG:4326'
        stats_df = gpd.read_file(deacl_wfs)
        stats_df.crs = 'EPSG:3577'

        # Clip resulting data to extent shape
        if len(stats_df.index) > 0:
            stats_df = gpd.overlay(stats_df, 
                                   extent.reset_index().to_crs('EPSG:3577'))
        else:
            raise ValueError('No statistics points were returned for the supplied '
                             'extent. Please select another area.')

        #############
        # Plot data #
        #############
        
        # Create two different methods for subsetting data
        stats_sig = stats_df.loc[stats_df.sig_time < 0.01].copy()
        stats_zeros = stats_df.copy()
        stats_zeros.loc[stats_df.sig_time > 0.01, 'rate_time'] = 0
        
        # Only generate plot if either only one polygon is being 
        # analysed or if `export_figure == True`
        if export_figure or len(extents.index) == 1:

            if hist_log:
                print('    Plotting data with log axis after setting ' \
                      'non-significant points to 0 m / year\n')
                stats_subset = stats_zeros.copy()
                
                if hist_range == 'auto':
                    hist_max = stats_subset.rate_time.quantile([0.001, 0.999]).abs().max()
                    hist_range = (-hist_max, hist_max)   
                    
                bin_offset = (hist_range[1] - hist_range[0]) / (hist_bins / 0.5)
            else:
                print('    Plotting data with linear axis after filtering ' \
                      'to significant values\n')
                stats_subset = stats_sig.copy()
                
                if hist_range == 'auto':
                    hist_max = stats_subset.rate_time.quantile([0.001, 0.999]).abs().max()
                    hist_range = (-hist_max, hist_max)   
                
                bin_offset = 0

            # Select colormap
            cm = plt.cm.get_cmap(cmap)

            # Plot histogram    
            n, bins, patches = ax1.hist(stats_subset.rate_time, 
                                        bins=hist_bins, 
                                        range=[(a + bin_offset) for a in hist_range], 
                                        log=hist_log,
                                        edgecolor='black')

            # Scale values to interval [0,1]
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            norm = colors.SymLogNorm(linthresh=0.25, 
                                     linscale=0.05,
                                     vmin=hist_range[0], 
                                     vmax=hist_range[1], 
                                     base=10)
            col = norm(bin_centers)  

            # Apply colors to bars
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))

            ax1.set_title(f'Mean rate (non-significant points set to 0 m / ' \
                          f'year): {stats_zeros.rate_time.mean():.2f} m / year\n'
                          f'Mean rate (non-significant points excluded ' \
                          f'from data): {stats_sig.rate_time.mean():.2f} m / year')
            ax1.set_xlabel('Rate of change (m / year)')
            ax1.set_ylabel('Frequency')
            
        ###############
        # Export data #
        ###############        
        
        # Create output folder if none exists
        if (export_extent or
            export_figure or 
            export_points_data or 
            export_summary_data):
            out_dir = 'deacoastlines_outputs'
            os.makedirs(out_dir, exist_ok=True)

        # Optionally write vector data
        if export_extent:
            shp_path = f'{out_dir}/deacoastlines_{file_id}_{extent_id}.shp'
            geojson_path = f'{out_dir}/deacoastlines_{file_id}_{extent_id}.geojson'

            print(f'Exporting extent vectors to:\n'
                  f'    {shp_path}\n'
                  f'    {geojson_path}\n')
            extent.to_crs('EPSG:3577').to_file(shp_path)
            extent.to_crs('EPSG:4326').to_file(geojson_path,
                                                driver='GeoJSON')

        # Optionally write image
        if export_figure:
            fig_path = f'{out_dir}/deacoastlines_{file_id}_{extent_id}.png'
            print(f'Exporting histogram figure to:\n'
                  f'    {fig_path}\n')
            plt.savefig(fig_path, bbox_inches='tight', dpi=200)
            
        # Optionally write raw data to CSV
        if export_points_data:
            csv_path = f'{out_dir}/deacoastlines_{file_id}_{extent_id}.csv'
            print(f'Exporting points data to:\n'
                      f'    {csv_path}\n')
            
            # Prepare data for export            
            stats_df = stats_df.to_crs('EPSG:4326')
            stats_df['longitude'] = stats_df.geometry.x.round(4)
            stats_df['latitude'] = stats_df.geometry.y.round(4)
            stats_df = stats_df.drop(['gml_id', 'geometry'], axis=1)
            
            # Export
            stats_df.to_csv(csv_path, index=False)
            
        # Add summary stats to list
        summary_stats.append({extent_id_col: extent_id, 
                              'mean_rate_zeros': stats_zeros.rate_time.mean(),
                              'mean_rate_sigonly': stats_sig.rate_time.mean(),
                              'n_zeros': len(stats_zeros.rate_time),
                              'n_sigonly': len(stats_sig.rate_time)})
        
        # Close axes if multiple images
        if len(extents.index) > 1:
            ax1.cla()
    
    # Close figure if multiple images
    if len(extents.index) > 1:
        plt.close(fig)
        
    # Optionally write summary data to CSV
    summary_stats_df = pd.DataFrame(summary_stats)
    if export_summary_data:
        summary_path = f'{out_dir}/deacoastlines_{file_id}_summary.csv'
        print(f'Exporting summary data to:\n'
              f'    {summary_path}\n')

        # Combine into dataframe and export        
        summary_stats_df.to_csv(summary_path, index=False)

    # Return summary data
    return summary_stats
