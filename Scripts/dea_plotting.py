## dea_plotting.py
'''
Description: This file contains a set of python functions for plotting 
Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, file one on 
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Functions included:
    rgb
    display_map
    map_shapefile
    xr_animation

Last modified: September 2020

'''

# Import required packages
import math
import folium
import calendar
import ipywidgets
import numpy as np
import geopandas as gpd
import matplotlib as mpl
import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
from pyproj import Proj, transform
from IPython.display import display
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1 import make_axes_locatable
from ipyleaflet import Map, Marker, Popup, GeoJSON, basemaps, Choropleth
from skimage import exposure
from branca.colormap import linear
from odc.ui import image_aspect

from matplotlib.animation import FuncAnimation
import pandas as pd
from pathlib import Path
from shapely.geometry import box
from skimage.exposure import rescale_intensity
from tqdm.auto import tqdm
import warnings


def rgb(ds,
        bands=['nbart_red', 'nbart_green', 'nbart_blue'],
        index=None,
        index_dim='time',
        robust=True,
        percentile_stretch=None,
        col_wrap=4,
        size=6,
        aspect=None,
        savefig_path=None,
        savefig_kwargs={},
        **kwargs):
    
    """
    Takes an xarray dataset and plots RGB images using three imagery 
    bands (e.g ['nbart_red', 'nbart_green', 'nbart_blue']). The `index` 
    parameter allows easily selecting individual or multiple images for 
    RGB plotting. Images can be saved to file by specifying an output 
    path using `savefig_path`.
    
    This function was designed to work as an easier-to-use wrapper 
    around xarray's `.plot.imshow()` functionality.
    
    Last modified: September 2020
    
    Parameters
    ----------  
    ds : xarray Dataset
        A two-dimensional or multi-dimensional array to plot as an RGB 
        image. If the array has more than two dimensions (e.g. multiple 
        observations along a 'time' dimension), either use `index` to 
        select one (`index=0`) or multiple observations 
        (`index=[0, 1]`), or create a custom faceted plot using e.g. 
        `col="time"`.       
    bands : list of strings, optional
        A list of three strings giving the band names to plot. Defaults 
        to '['nbart_red', 'nbart_green', 'nbart_blue']'.
    index : integer or list of integers, optional
        `index` can be used to select one (`index=0`) or multiple 
        observations (`index=[0, 1]`) from the input dataset for 
        plotting. If multiple images are requested these will be plotted
        as a faceted plot.
    index_dim : string, optional
        The dimension along which observations should be plotted if 
        multiple observations are requested using `index`. Defaults to 
        `time`.
    robust : bool, optional
        Produces an enhanced image where the colormap range is computed 
        with 2nd and 98th percentiles instead of the extreme values. 
        Defaults to True.
    percentile_stretch : tuple of floats
        An tuple of two floats (between 0.00 and 1.00) that can be used 
        to clip the colormap range to manually specified percentiles to 
        get more control over the brightness and contrast of the image. 
        The default is None; '(0.02, 0.98)' is equivelent to 
        `robust=True`. If this parameter is used, `robust` will have no 
        effect.
    col_wrap : integer, optional
        The number of columns allowed in faceted plots. Defaults to 4.
    size : integer, optional
        The height (in inches) of each plot. Defaults to 6.
    aspect : integer, optional
        Aspect ratio of each facet in the plot, so that aspect * size 
        gives width of each facet in inches. Defaults to None, which 
        will calculate the aspect based on the x and y dimensions of 
        the input data.
    savefig_path : string, optional
        Path to export image file for the RGB plot. Defaults to None, 
        which does not export an image file.
    savefig_kwargs : dict, optional
        A dict of keyword arguments to pass to 
        `matplotlib.pyplot.savefig` when exporting an image file. For 
        all available options, see: 
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.savefig.html        
    **kwargs : optional
        Additional keyword arguments to pass to `xarray.plot.imshow()`.
        For example, the function can be used to plot into an existing
        matplotlib axes object by passing an `ax` keyword argument.
        For more options, see:
        http://xarray.pydata.org/en/stable/generated/xarray.plot.imshow.html  
        
    Returns
    -------
    An RGB plot of one or multiple observations, and optionally an image
    file written to file.
    
    """

    # Get names of x and y dims
    # TODO: remove geobox and try/except once datacube 1.8 is default
    try:
        y_dim, x_dim = ds.geobox.dimensions
    except AttributeError:
        from datacube.utils import spatial_dims
        y_dim, x_dim = spatial_dims(ds)

    # If ax is supplied via kwargs, ignore aspect and size
    if 'ax' in kwargs:
        
        # Create empty aspect size kwarg that will be passed to imshow
        aspect_size_kwarg = {}    
    else:
        # Compute image aspect
        if not aspect:
            aspect = image_aspect(ds)
        
        # Populate aspect size kwarg with aspect and size data
        aspect_size_kwarg = {'aspect': aspect, 'size': size}

    # If no value is supplied for `index` (the default), plot using default 
    # values and arguments passed via `**kwargs`
    if index is None:
        
        # Select bands and convert to DataArray
        da = ds[bands].to_array().compute()

        # If percentile_stretch == True, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})        
        
        # If there are more than three dimensions and the index dimension == 1, 
        # squeeze this dimension out to remove it
        if ((len(ds.dims) > 2) and 
            ('col' not in kwargs) and 
            (len(da[index_dim]) == 1)):
        
            da = da.squeeze(dim=index_dim)
            
        # If there are more than three dimensions and the index dimension
        # is longer than 1, raise exception to tell user to use 'col'/`index`
        elif ((len(ds.dims) > 2) and 
              ('col' not in kwargs) and 
              (len(da[index_dim]) > 1)):
                
            raise Exception(
                f'The input dataset `ds` has more than two dimensions: '
                f'{list(ds.dims.keys())}. Please select a single observation '
                'using e.g. `index=0`, or enable faceted plotting by adding '
                'the arguments e.g. `col="time", col_wrap=4` to the function ' 
                'call'
            )

        img = da.plot.imshow(x=x_dim,
                             y=y_dim,
                             robust=robust,
                             col_wrap=col_wrap,
                             **aspect_size_kwarg,
                             **kwargs)

    # If values provided for `index`, extract corresponding observations and 
    # plot as either single image or facet plot
    else:

        # If a float is supplied instead of an integer index, raise exception
        if isinstance(index, float):
            raise Exception(
                f'Please supply `index` as either an integer or a list of '
                'integers'
            )

        # If col argument is supplied as well as `index`, raise exception
        if 'col' in kwargs:
            raise Exception(
                f'Cannot supply both `index` and `col`; please remove one and '
                'try again'
            )

        # Convert index to generic type list so that number of indices supplied
        # can be computed
        index = index if isinstance(index, list) else [index]

        # Select bands and observations and convert to DataArray
        da = ds[bands].isel(**{index_dim: index}).to_array().compute()

        # If percentile_stretch == True, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})

        # If multiple index values are supplied, plot as a faceted plot
        if len(index) > 1:

            img = da.plot.imshow(x=x_dim,
                                 y=y_dim,
                                 robust=robust,
                                 col=index_dim,
                                 col_wrap=col_wrap,
                                 **aspect_size_kwarg,
                                 **kwargs)

        # If only one index is supplied, squeeze out index_dim and plot as a 
        # single panel
        else:

            img = da.squeeze(dim=index_dim).plot.imshow(robust=robust,
                                                        **aspect_size_kwarg,
                                                        **kwargs)

    # If an export path is provided, save image to file. Individual and 
    # faceted plots have a different API (figure vs fig) so we get around this 
    # using a try statement:
    if savefig_path:

        print(f'Exporting image to {savefig_path}')

        try:
            img.fig.savefig(savefig_path, **savefig_kwargs)
        except:
            img.figure.savefig(savefig_path, **savefig_kwargs)

            
def display_map(x, y, crs='EPSG:4326', margin=-0.5, zoom_bias=0):
    """ 
    Given a set of x and y coordinates, this function generates an 
    interactive map with a bounded rectangle overlayed on Google Maps 
    imagery.        
    
    Last modified: September 2019
    
    Modified from function written by Otto Wagner available here: 
    https://github.com/ceos-seo/data_cube_utilities/tree/master/data_cube_utilities
    
    Parameters
    ----------  
    x : (float, float)
        A tuple of x coordinates in (min, max) format. 
    y : (float, float)
        A tuple of y coordinates in (min, max) format.
    crs : string, optional
        A string giving the EPSG CRS code of the supplied coordinates. 
        The default is 'EPSG:4326'.
    margin : float
        A numeric value giving the number of degrees lat-long to pad 
        the edges of the rectangular overlay polygon. A larger value 
        results more space between the edge of the plot and the sides 
        of the polygon. Defaults to -0.5.
    zoom_bias : float or int
        A numeric value allowing you to increase or decrease the zoom 
        level by one step. Defaults to 0; set to greater than 0 to zoom 
        in, and less than 0 to zoom out.
        
    Returns
    -------
    folium.Map : A map centered on the supplied coordinate bounds. A 
    rectangle is drawn on this map detailing the perimeter of the x, y 
    bounds.  A zoom level is calculated such that the resulting 
    viewport is the closest it can possibly get to the centered 
    bounding rectangle without clipping it. 
    """

    # Convert each corner coordinates to lat-lon
    all_x = (x[0], x[1], x[0], x[1])
    all_y = (y[0], y[0], y[1], y[1])
    all_longitude, all_latitude = transform(Proj(crs),
                                            Proj('EPSG:4326'),
                                            all_x, all_y)

    # Calculate zoom level based on coordinates
    lat_zoom_level = _degree_to_zoom_level(min(all_latitude),
                                           max(all_latitude),
                                           margin=margin) + zoom_bias
    lon_zoom_level = _degree_to_zoom_level(min(all_longitude),
                                           max(all_longitude),
                                           margin=margin) + zoom_bias
    zoom_level = min(lat_zoom_level, lon_zoom_level)

    # Identify centre point for plotting
    center = [np.mean(all_latitude), np.mean(all_longitude)]

    # Create map
    interactive_map = folium.Map(
        location=center,
        zoom_start=zoom_level,
        tiles="http://mt1.google.com/vt/lyrs=y&z={z}&x={x}&y={y}",
        attr="Google")

    # Create bounding box coordinates to overlay on map
    line_segments = [(all_latitude[0], all_longitude[0]),
                     (all_latitude[1], all_longitude[1]),
                     (all_latitude[3], all_longitude[3]),
                     (all_latitude[2], all_longitude[2]),
                     (all_latitude[0], all_longitude[0])]

    # Add bounding box as an overlay
    interactive_map.add_child(
        folium.features.PolyLine(locations=line_segments,
                                 color='red',
                                 opacity=0.8))

    # Add clickable lat-lon popup box
    interactive_map.add_child(folium.features.LatLngPopup())

    return interactive_map


def map_shapefile(gdf,
                  attribute,
                  continuous=False,
                  colormap='YlOrRd_09',
                  basemap=basemaps.Esri.WorldImagery,
                  default_zoom=None,
                  hover_col=True,
                  **style_kwargs):
    """
    Plots a geopandas GeoDataFrame over an interactive ipyleaflet 
    basemap, with features coloured based on attribute column values. 
    Optionally, can be set up to print selected data from features in 
    the GeoDataFrame. 

    Last modified: February 2020

    Parameters
    ----------  
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing the spatial features to be plotted 
        over the basemap.
    attribute: string, required
        An required string giving the name of any column in the
        GeoDataFrame you wish to have coloured on the choropleth.
    continuous: boolean, optional
        Whether to plot data as a categorical or continuous variable. 
        Defaults to remapping the attribute which is suitable for 
        categorical data. For continuous data set `continuous` to True.
    colormap : string, optional
        Either a string giving the name of a `branca.colormap.linear` 
        colormap or a `branca.colormap` object (for example, 
        `branca.colormap.linear.YlOrRd_09`) that will be used to style 
        the features in the GeoDataFrame. Features will be coloured 
        based on the selected attribute. Defaults to the 'YlOrRd_09' 
        colormap.
    basemap : ipyleaflet.basemaps object, optional
        An optional `ipyleaflet.basemaps` object used as the basemap for 
        the interactive plot. Defaults to `basemaps.Esri.WorldImagery`.
    default_zoom : int, optional
        An optional integer giving a default zoom level for the 
        interactive ipyleaflet plot. Defaults to None, which infers
        the zoom level from the extent of the data.
    hover_col : boolean or str, optional
        If True (the default), the function will print  values from the 
        GeoDataFrame's `attribute` column above the interactive map when 
        a user hovers over the features in the map. Alternatively, a 
        custom shapefile field can be specified by supplying a string
        giving the name of the field to print. Set to False to prevent 
        any attributes from being printed.
    **choropleth_kwargs :
        Optional keyword arguments to pass to the `style` paramemter of
        the `ipyleaflet.Choropleth` function. This can be used to 
        control the appearance of the shapefile, for example 'stroke' 
        and 'weight' (controlling line width), 'fillOpacity' (polygon 
        transparency) and 'dashArray' (whether to plot lines/outlines
        with dashes). For more information:
        https://ipyleaflet.readthedocs.io/en/latest/api_reference/choropleth.html

    """

    def on_hover(event, id, properties):
        with dbg:
            text = properties.get(hover_col, '???')
            lbl.value = f'{hover_col}: {text}'
            
    # Verify that attribute exists in shapefile   
    if attribute not in gdf.columns:
        raise ValueError(f"The `attribute` {attribute} does not exist "
                         f"in the geopandas.GeoDataFrame. "
                         f"Valid attributes include {gdf.columns.values}.")
        
    # If hover_col is True, use 'attribute' as the default hover attribute.
    # Otherwise, hover_col will use the supplied attribute field name
    if hover_col and (hover_col is True):
        hover_col = attribute
        
    # If a custom string if supplied to hover_col, check this exists 
    elif hover_col and (type(hover_col) == str):
        if hover_col not in gdf.columns:
                raise ValueError(f"The `hover_col` field {hover_col} does "
                                 f"not exist in the geopandas.GeoDataFrame. "
                                 f"Valid attributes include "
                                 f"{gdf.columns.values}.")

    # Convert to WGS 84 and GeoJSON format
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    data_geojson = gdf_wgs84.__geo_interface__
    
    # If continuous is False, remap categorical classes for visualisation
    if not continuous:
        
        # Zip classes data together to make a dictionary
        classes_uni = list(gdf[attribute].unique())
        classes_clean = list(range(0, len(classes_uni)))
        classes_dict = dict(zip(classes_uni, classes_clean))
        
        # Get values to colour by as a list 
        classes = gdf[attribute].map(classes_dict).tolist()  
    
    # If continuous is True then do not remap
    else: 
        
        # Get values to colour by as a list
        classes = gdf[attribute].tolist()  

    # Create the dictionary to colour map by
    keys = gdf.index
    id_class_dict = dict(zip(keys.astype(str), classes))  

    # Get centroid to focus map on
    lon1, lat1, lon2, lat2 = gdf_wgs84.total_bounds
    lon = (lon1 + lon2) / 2
    lat = (lat1 + lat2) / 2

    if default_zoom is None:

        # Calculate default zoom from latitude of features
        default_zoom = _degree_to_zoom_level(lat1, lat2, margin=-0.5)

    # Plot map
    m = Map(center=(lat, lon),
            zoom=default_zoom,
            basemap=basemap,
            layout=dict(width='800px', height='600px'))
    
    # Define default plotting parameters for the choropleth map. 
    # The nested dict structure sets default values which can be 
    # overwritten/customised by `choropleth_kwargs` values
    style_kwargs = dict({'fillOpacity': 0.8}, **style_kwargs)

    # Get colormap from either string or `branca.colormap` object
    if type(colormap) == str:
        colormap = getattr(linear, colormap)
    
    # Create the choropleth
    choropleth = Choropleth(geo_data=data_geojson,
                            choro_data=id_class_dict,
                            colormap=colormap,
                            style={**style_kwargs})
    
    # If the vector data contains line features, they will not be 
    # be coloured by default. To resolve this, we need to manually copy
    # across the 'fillColor' attribute to the 'color' attribute for each
    # feature, then plot the data as a GeoJSON layer rather than the
    # choropleth layer that we use for polygon data.
    linefeatures = any(x in ['LineString', 'MultiLineString'] 
                       for x in gdf.geometry.type.values)
    if linefeatures:
    
        # Copy colour from fill to line edge colour
        for i in keys:
            choropleth.data['features'][i]['properties']['style']['color'] = \
            choropleth.data['features'][i]['properties']['style']['fillColor']

        # Add GeoJSON layer to map
        feature_layer = GeoJSON(data=choropleth.data)
        m.add_layer(feature_layer)
        
    else:
        
        # Add Choropleth layer to map
        m.add_layer(choropleth)

    # If a column is specified by `hover_col`, print data from the
    # hovered feature above the map
    if hover_col and not linefeatures:
        
        # Use cholopleth object if data is polygon
        lbl = ipywidgets.Label()
        dbg = ipywidgets.Output()
        choropleth.on_hover(on_hover)
        display(lbl)
        
    else:
        
        lbl = ipywidgets.Label()
        dbg = ipywidgets.Output()
        feature_layer.on_hover(on_hover)
        display(lbl)

    # Display the map
    display(m)
    

def xr_animation(ds,
                 bands=None,
                 output_path='animation.mp4',
                 width_pixels=500,
                 interval=100,                 
                 percentile_stretch=(0.02, 0.98),
                 image_proc_funcs=None,
                 show_gdf=None,
                 show_date='%d %b %Y',
                 show_text=None,
                 show_colorbar=True,
                 gdf_kwargs={},
                 annotation_kwargs={},
                 imshow_kwargs={},
                 colorbar_kwargs={},
                 limit=None):
    
    """
    Takes an `xarray` timeseries and animates the data as either a 
    three-band (e.g. true or false colour) or single-band animation, 
    allowing changes in the landscape to be compared across time.
    
    Animations can be customised to include text and date annotations 
    or use specific combinations of input bands. Vector data can be 
    overlaid and animated on top of imagery, and custom image 
    processing functions can be applied to each frame.
    
    Supports .mp4 (ideal for Twitter/social media) and .gif (ideal 
    for all purposes, but can have large file sizes) format files. 
    
    Last modified: April 2020
    
    Parameters
    ----------  
    ds : xarray.Dataset
        An xarray dataset with multiple time steps (i.e. multiple 
        observations along the `time` dimension).        
    bands : list of strings
        An list of either one or three band names to be plotted, 
        all of which must exist in `ds`. 
    output_path : str, optional
        A string giving the output location and filename of the 
        resulting animation. File extensions of '.mp4' and '.gif' are 
        accepted. Defaults to 'animation.mp4'.
    width_pixels : int, optional
        An integer defining the output width in pixels for the 
        resulting animation. The height of the animation is set 
        automatically based on the dimensions/ratio of the input 
        xarray dataset. Defaults to 500 pixels wide.        
    interval : int, optional
        An integer defining the milliseconds between each animation 
        frame used to control the speed of the output animation. Higher
        values result in a slower animation. Defaults to 100 
        milliseconds between each frame.         
    percentile_stretch : tuple of floats, optional
        An optional tuple of two floats that can be used to clip one or
        three-band arrays by percentiles to produce a more vibrant, 
        visually attractive image that is not affected by outliers/
        extreme values. The default is `(0.02, 0.98)` which is 
        equivalent to xarray's `robust=True`.        
    image_proc_funcs : list of funcs, optional
        An optional list containing functions that will be applied to 
        each animation frame (timestep) prior to animating. This can 
        include image processing functions such as increasing contrast, 
        unsharp masking, saturation etc. The function should take AND 
        return a `numpy.ndarray` with shape [y, x, bands]. If your 
        function has parameters, you can pass in custom values using 
        a lambda function:
        `image_proc_funcs=[lambda x: custom_func(x, param1=10)]`.
    show_gdf: geopandas.GeoDataFrame, optional
        Vector data (e.g. ESRI shapefiles or GeoJSON) can be optionally
        plotted over the top of imagery by supplying a 
        `geopandas.GeoDataFrame` object. To customise colours used to
        plot the vector features, create a new column in the
        GeoDataFrame called 'colors' specifying the colour used to plot 
        each feature: e.g. `gdf['colors'] = 'red'`.
        To plot vector features at specific moments in time during the
        animation, create new 'start_time' and/or 'end_time' columns in
        the GeoDataFrame that define the time range used to plot each 
        feature. Dates can be provided in any string format that can be 
        converted using the `pandas.to_datetime()`. e.g.
         `gdf['end_time'] = ['2001', '2005-01', '2009-01-01']`    
    show_date : string or bool, optional
        An optional string or bool that defines how (or if) to plot 
        date annotations for each animation frame. Defaults to 
        '%d %b %Y'; can be customised to any format understood by 
        strftime (https://strftime.org/). Set to False to remove date 
        annotations completely.       
    show_text : str or list of strings, optional
        An optional string or list of strings with a length equal to 
        the number of timesteps in `ds`. This can be used to display a 
        static text annotation (using a string), or a dynamic title 
        (using a list) that displays different text for each timestep. 
        By default, no text annotation will be plotted.        
    show_colorbar : bool, optional
        An optional boolean indicating whether to include a colourbar 
        for single-band animations. Defaults to True.
    gdf_kwargs : dict, optional
        An optional dictionary of keyword arguments to customise the 
        appearance of a `geopandas.GeoDataFrame` supplied to 
        `show_gdf`. Keyword arguments are passed to `GeoSeries.plot` 
        (see http://geopandas.org/reference.html#geopandas.GeoSeries.plot). 
        For example: `gdf_kwargs = {'linewidth': 2}`. 
    annotation_kwargs : dict, optional
        An optional dict of keyword arguments for controlling the 
        appearance of  text annotations. Keyword arguments are passed 
        to `matplotlib`'s `plt.annotate` 
        (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html 
        for options). For example, `annotation_kwargs={'fontsize':20, 
        'color':'red', 'family':'serif'}.  
    imshow_kwargs : dict, optional
        An optional dict of keyword arguments for controlling the 
        appearance of arrays passed to `matplotlib`'s `plt.imshow` 
        (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html 
        for options). For example, a green colour scheme and custom
        stretch could be specified using: 
        `onebandplot_kwargs={'cmap':'Greens`, 'vmin':0.2, 'vmax':0.9}`.
        (some parameters like 'cmap' will only have an effect for 
        single-band animations, not three-band RGB animations).
    colorbar_kwargs : dict, optional
        An optional dict of keyword arguments used to control the 
        appearance of the colourbar. Keyword arguments are passed to
        `matplotlib.pyplot.tick_params` 
        (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.tick_params.html
        for options). This can be used to customise the colourbar 
        ticks, e.g. changing tick label colour depending on the 
        background of the animation: 
        `colorbar_kwargs={'colors': 'black'}`.
    limit: int, optional
        An optional integer specifying how many animation frames to 
        render (e.g. `limit=50` will render the first 50 frames). This
        can be useful for quickly testing animations without rendering 
        the entire time-series.    
            
    """

    def _start_end_times(gdf, ds):
        """
        Converts 'start_time' and 'end_time' columns in a 
        `geopandas.GeoDataFrame` to datetime objects to allow vector
        features to be plotted at specific moments in time during an
        animation, and sets default values based on the first
        and last time in `ds` if this information is missing from the
        dataset.
        """

        # Make copy of gdf so we do not modify original data
        gdf = gdf.copy()

        # Get min and max times from input dataset
        minmax_times = pd.to_datetime(ds.time.isel(time=[0, -1]).values)

        # Update both `start_time` and `end_time` columns
        for time_col, time_val in zip(['start_time', 'end_time'], minmax_times):

            # Add time_col if it does not exist
            if time_col not in gdf:
                gdf[time_col] = np.nan

            # Convert values to datetimes and fill gaps with relevant time value
            gdf[time_col] = pd.to_datetime(gdf[time_col], errors='ignore')
            gdf[time_col] = gdf[time_col].fillna(time_val)

        return gdf


    def _add_colorbar(fig, ax, vmin, vmax, imshow_defaults, colorbar_defaults):
        """
        Adds a new colorbar axis to the animation with custom minimum 
        and maximum values and styling.
        """

        # Create new axis object for colorbar
        cax = fig.add_axes([0.02, 0.02, 0.96, 0.03])

        # Initialise color bar using plot min and max values
        img = ax.imshow(np.array([[vmin, vmax]]), **imshow_defaults)
        fig.colorbar(img,
                     cax=cax,
                     orientation='horizontal',
                     ticks=np.linspace(vmin, vmax, 2))

        # Fine-tune appearance of colorbar
        cax.xaxis.set_ticks_position('top')
        cax.tick_params(axis='x', **colorbar_defaults)
        cax.get_xticklabels()[0].set_horizontalalignment('left')
        cax.get_xticklabels()[-1].set_horizontalalignment('right')


    def _frame_annotation(times, show_date, show_text):
        """
        Creates a custom annotation for the top-right of the animation
        by converting a `xarray.DataArray` of times into strings, and
        combining this with a custom text annotation. Handles cases 
        where `show_date=False/None`, `show_text=False/None`, or where
        `show_text` is a list of strings.
        """

        # Test if show_text is supplied as a list
        is_sequence = isinstance(show_text, (list, tuple, np.ndarray))

        # Raise exception if it is shorter than number of dates
        if is_sequence and (len(show_text) == 1):
            show_text, is_sequence = show_text[0], False
        elif is_sequence and (len(show_text) < len(times)):
            raise ValueError(f'Annotations supplied via `show_text` must have '
                             f'either a length of 1, or a length >= the number '
                             f'of timesteps in `ds` (n={len(times)})')

        times_list = (times.dt.strftime(show_date).values if show_date else [None] *
                      len(times))
        text_list = show_text if is_sequence else [show_text] * len(times)
        annotation_list = ['\n'.join([str(i) for i in (a, b) if i])
                           for a, b in zip(times_list, text_list)]

        return annotation_list


    def _update_frames(i, ax, extent, annotation_text, gdf, gdf_defaults,
                       annotation_defaults, imshow_defaults):
        """
        Animation called by `matplotlib.animation.FuncAnimation` to 
        animate each frame in the animation. Plots array and any text
        annotations, as well as a temporal subset of `gdf` data based
        on the times specified in 'start_time' and 'end_time' columns.
        """
        

        # Clear previous frame to optimise render speed and plot imagery
        ax.clear()
        ax.imshow(array[i, ...].clip(0.0, 1.0), extent=extent, **imshow_defaults)

        # Add annotation text
        ax.annotate(annotation_text[i], **annotation_defaults)

        # Add geodataframe annotation
        if show_gdf is not None:

            # Obtain start and end times to filter geodataframe features
            time_i = ds.time.isel(time=i).values

            # Subset geodataframe using start and end dates
            gdf_subset = show_gdf.loc[(show_gdf.start_time <= time_i) &
                                      (show_gdf.end_time >= time_i)]           

            if len(gdf_subset.index) > 0:

                # Set color to geodataframe field if supplied
                if ('color' in gdf_subset) and ('color' not in gdf_kwargs):
                    gdf_defaults.update({'color': gdf_subset['color'].tolist()})

                gdf_subset.plot(ax=ax, **gdf_defaults)

        # Remove axes to show imagery only
        ax.axis('off')
        
        # Update progress bar
        progress_bar.update(1)
        
    
    # Test if bands have been supplied, or convert to list to allow
    # iteration if a single band is provided as a string
    if bands is None:
        raise ValueError(f'Please use the `bands` parameter to supply '
                         f'a list of one or three bands that exist as '
                         f'variables in `ds`, e.g. {list(ds.data_vars)}')
    elif isinstance(bands, str):
        bands = [bands]
    
    # Test if bands exist in dataset
    missing_bands = [b for b in bands if b not in ds.data_vars]
    if missing_bands:
        raise ValueError(f'Band(s) {missing_bands} do not exist as '
                         f'variables in `ds` {list(ds.data_vars)}')
    
    # Test if time dimension exists in dataset
    if 'time' not in ds.dims:
        raise ValueError(f"`ds` does not contain a 'time' dimension "
                         f"required for generating an animation")
                
    # Set default parameters
    outline = [PathEffects.withStroke(linewidth=2.5, foreground='black')]
    annotation_defaults = {
        'xy': (1, 1),
        'xycoords': 'axes fraction',
        'xytext': (-5, -5),
        'textcoords': 'offset points',
        'horizontalalignment': 'right',
        'verticalalignment': 'top',
        'fontsize': 20,
        'color': 'white',
        'path_effects': outline
    }
    imshow_defaults = {'cmap': 'magma', 'interpolation': 'nearest'}
    colorbar_defaults = {'colors': 'white', 'labelsize': 12, 'length': 0}
    gdf_defaults = {'linewidth': 1.5}

    # Update defaults with kwargs
    annotation_defaults.update(annotation_kwargs)
    imshow_defaults.update(imshow_kwargs)
    colorbar_defaults.update(colorbar_kwargs)
    gdf_defaults.update(gdf_kwargs)

    # Get info on dataset dimensions
    height, width = ds.geobox.shape
    scale = width_pixels / width
    left, bottom, right, top = ds.geobox.extent.boundingbox

    # Prepare annotations
    annotation_list = _frame_annotation(ds.time, show_date, show_text)

    # Prepare geodataframe
    if show_gdf is not None:
        show_gdf = show_gdf.to_crs(ds.geobox.crs)
        show_gdf = gpd.clip(show_gdf, mask=box(left, bottom, right, top))
        show_gdf = _start_end_times(show_gdf, ds)

    # Convert data to 4D numpy array of shape [time, y, x, bands]
    ds = ds[bands].to_array().transpose(..., 'variable')[0:limit, ...]
    array = ds.values

    # Optionally apply image processing along axis 0 (e.g. to each timestep)
    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} ({remaining_s:.1f} ' \
                   'seconds remaining at {rate_fmt}{postfix})'
    if image_proc_funcs:
        print('Applying custom image processing functions')
        for i, array_i in tqdm(enumerate(array),
                               total=len(ds.time),
                               leave=False,
                               bar_format=bar_format,
                               unit=' frames'):
            for func in image_proc_funcs:
                array_i = func(array_i)
            array[i, ...] = array_i

    # Clip to percentiles and rescale between 0.0 and 1.0 for plotting
    vmin, vmax = np.quantile(array[np.isfinite(array)], q=percentile_stretch)
    
    # Replace with vmin and vmax if present in `imshow_defaults`
    if 'vmin' in imshow_defaults:
        vmin = imshow_defaults['vmin']
    if 'vmax' in imshow_defaults:
        vmax = imshow_defaults['vmax']
    
    array = rescale_intensity(array, in_range=(vmin, vmax), out_range=(0.0, 1.0))
    array = np.squeeze(array)  # remove final axis if only one band

    # Set up figure
    fig, ax = plt.subplots()
    fig.set_size_inches(width * scale / 72, height * scale / 72, forward=True)
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    # Optionally add colorbar
    if show_colorbar & (len(bands) == 1):
        _add_colorbar(fig, ax, vmin, vmax, imshow_defaults, colorbar_defaults)

    # Animate
    print(f'Exporting animation to {output_path}') 
    anim = FuncAnimation(
        fig=fig,
        func=_update_frames,
        fargs=(
            ax,  # axis to plot into
            [left, right, bottom, top],  # imshow extent
            annotation_list,  # list of text annotations
            show_gdf,  # geodataframe to plot over imagery
            gdf_defaults,  # any kwargs used to plot gdf
            annotation_defaults,  # kwargs for annotations
            imshow_defaults),  # kwargs for imshow
        frames=len(ds.time),
        interval=interval,
        repeat=False)
    
    # Set up progress bar
    progress_bar = tqdm(total=len(ds.time), 
                        unit=' frames', 
                        bar_format=bar_format) 

    # Export animation to file
    if Path(output_path).suffix == '.gif':
        anim.save(output_path, writer='pillow')
    else:
        anim.save(output_path, dpi=72)

    # Update progress bar to fix progress bar moving past end
    if progress_bar.n != len(ds.time):
        progress_bar.n = len(ds.time)
        progress_bar.last_print_n = len(ds.time)


def animated_timeseries(ds,
                        output_path,
                        width_pixels=500,
                        interval=200,
                        bands=['nbart_red', 'nbart_green', 'nbart_blue'],
                        percentile_stretch=(0.02, 0.98),
                        image_proc_func=None,
                        title=False,
                        show_date=True,
                        annotation_kwargs={},
                        onebandplot_cbar=True,
                        onebandplot_kwargs={},
                        shapefile_path=None,
                        shapefile_kwargs={},
                        time_dim='time',
                        x_dim='x',
                        y_dim='y'):
    """
    ------------------------------------------------------------------
    APRIL 2020 UPDATE: The `animated_timeseries` function is being 
    depreciated, and will soon be replaced with the more powerful 
    and easier-to-use `xr_animation` function from 
    `Scripts/dea_plotting`. Please update your code to use 
    `xr_animation` instead.
    ------------------------------------------------------------------
    
    Takes an xarray time series and animates the data as either a 
    three-band (e.g. true or false colour) or single-band animation, 
    allowing changes in the landscape to be compared across time.
    
    Animations can be exported as .mp4 (ideal for Twitter/social media)
    and .gif (ideal for all purposes, but can have large file sizes) 
    format files, and customised to include titles and date annotations 
    or use specific combinations of input bands.
    
    A shapefile boundary can be added to the output animation by 
    providing a path to the shapefile.
    
    This function can be used to produce visually appealing 
    cloud-free animations when used in combination with the `load_ard` 
    function from `dea-notebooks/Scripts/dea_datahandling`.
    
    Last modified: October 2019
    
    Parameters
    ----------  
    ds : xarray.Dataset
        An xarray dataset with multiple time steps (i.e. multiple 
        observations along the `time` dimension).        
    output_path : str
        A string giving the output location and filename of the 
        resulting animation. File extensions of '.mp4' and '.gif' are 
        accepted.    
    width_pixels : int, optional
        An integer defining the output width in pixels for the resulting 
        animation. The height of the animation is set automatically 
        based on the dimensions/ratio of the input xarray dataset. 
        Defaults to 500 pixels wide.        
    interval : int, optional
        An integer defining the milliseconds between each animation 
        frame used to control the speed of the output animation. Higher 
        values result in a slower animation. Defaults to 200 
        milliseconds between each frame.         
    bands : list of strings, optional
        An optional list of either one or three bands to be plotted, 
        all of which must exist in `ds`. Defaults to 
        `['nbart_red', 'nbart_green', 'nbart_blue']`.         
    percentile_stretch : tuple of floats, optional
        An optional tuple of two floats that can be used to clip one or 
        three-band arrays by percentiles to produce a more vibrant, 
        visually attractive image that is not affected by outliers/
        extreme values. The default is `(0.02, 0.98)` which is 
        equivalent to xarray's `robust=True`.        
    image_proc_func : func, optional
        An optional function can be passed to modify three-band arrays 
        for each timestep prior to animating. This could include image 
        processing functions such as increasing contrast, unsharp 
        masking, saturation etc. The function should take AND return a 
        three-band numpy array with shape [:, :, 3]. If your function 
        has parameters, you can pass in custom values using `partial` 
        from `functools`: 
        `image_proc_func=partial(custom_func, param1=10)`.
    title : str or list of strings, optional
        An optional string or list of strings with a length equal to the
        number of timesteps in ds. This can be used to display a static 
        title (using a string), or a dynamic title (using a list) that 
        displays different text for each timestep. Defaults to False, 
        which plots no title.        
    show_date : bool, optional
        An optional boolean that defines whether or not to plot date 
        annotations for each animation frame. Defaults to True, which 
        plots date annotations based on ds.        
    annotation_kwargs : dict, optional
        An optional dict of kwargs for controlling the appearance of 
        text annotations to pass to the matplotlib `plt.annotate` 
        function (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html 
        for options). For example, `annotation_kwargs={'fontsize':20, 
        'color':'red', 'family':'serif'}. By default, text annotations 
        are plotted as white, size 20 mono-spaced font with a 2.5pt 
        black outline in the top-right of the animation.         
    onebandplot_cbar : bool, iptional
        An optional boolean indicating whether to include a colourbar 
        for one-band arrays. Defaults to True.        
    onebandplot_kwargs : dict, optional
        An optional dict of kwargs for controlling the appearance of 
        one-band image arrays to pass to matplotlib `plt.imshow` 
        (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html 
        for options). This only applies if an xarray with a single band 
        is passed to `ds`. For example, a green colour scheme and custom 
        stretch could be specified using: 
        `onebandplot_kwargs={'cmap':'Greens`, 'vmin':0.2, 'vmax':0.9}`. 
        By default, one-band arrays are plotted using the 'Greys' cmap 
        with bilinear interpolation.
        
        Two special kwargs (`tick_fontsize`, `tick_colour`) can also be 
        passed to control the tick labels on the colourbar. This can be 
        useful for example when the tick labels are difficult to see 
        against a dark background.       
    shapefile_path : str or list of strings, optional
        An optional string or list of strings giving the file paths of 
        one or multiple shapefiles to overlay on the output animation. 
        The shapefiles must be in the same projection as the input 
        xarray dataset.        
    shapefile_kwargs : dict or list of dicts, optional
        An optional dictionary of kwargs or list of dictionaries to 
        specify the appearance of the shapefile overlay by passing to 
        `GeoSeries.plot` (see http://geopandas.org/reference.html#geopandas.GeoSeries.plot). 
        For example: `shapefile_kwargs = {'linewidth':2, 
        'edgecolor':'black', 'facecolor':"#00000000"}`. If multiple 
        shapefiles were provided to `shapefile_path`, each shapefile can 
        be plotted with a different colour style by passing in a list of
        kwarg dicts of the same length as `shapefile_path`.        
    time_dim : str, optional
        An optional string allowing you to override the xarray dimension 
        used for time. Defaults to 'time'.
    x_dim : str, optional
        An optional string allowing you to override the xarray dimension 
        used for x coordinates. Defaults to 'x'.    
    y_dim : str, optional
        An optional string allowing you to override the xarray dimension 
        used for y coordinates. Defaults to 'y'.
        
    """
    
    warnings.warn("The `animated_timeseries` function is being depreciated, "
                  "and will soon be replaced with the more powerful and "
                  "easier-to-use `xr_animation` function from "
                  "`Scripts/dea_plotting`. Please update your code to use "
                  "`xr_animation` instead.", 
                  DeprecationWarning, stacklevel=2)

    ###############
    # Setup steps #
    ###############

    # Test if all dimensions exist in dataset
    if time_dim in ds and x_dim in ds and y_dim in ds:

        # First test if there are three bands, and that all exist in both datasets:
        if ((len(bands) == 3) |
            (len(bands) == 1)) & all([(b in ds.data_vars) for b in bands]):

            # Import xarrays as lists of three band numpy arrays
            imagelist, vmin, vmax = _ds_to_arrraylist(
                ds,
                bands=bands,
                time_dim=time_dim,
                x_dim=x_dim,
                y_dim=y_dim,
                percentile_stretch=percentile_stretch,
                image_proc_func=image_proc_func)

            # Get time, x and y dimensions of dataset and calculate 
            # width vs height of plot
            timesteps = len(ds[time_dim])
            width = len(ds[x_dim])
            height = len(ds[y_dim])
            scale = (width_pixels / width)

            # If title is supplied as a string, multiply out to a list 
            # with one string per timestep. Otherwise, use supplied list
            # for plot titles.
            if isinstance(title, str) or isinstance(title, bool):
                title_list = [title] * timesteps
            else:
                title_list = title

            # Set up annotation parameters that plt.imshow plotting for 
            # single band array images. The nested dict structure sets 
            # default values which can be overwritten/customised by the
            # manually specified `onebandplot_kwargs`
            onebandplot_kwargs = dict({'cmap': 'Greys',
                                       'interpolation': 'bilinear',
                                       'vmin': vmin,
                                       'vmax': vmax,
                                       'tick_colour': 'black',
                                       'tick_fontsize': 12}, 
                                      **onebandplot_kwargs)

            # Use pop to remove the two special tick kwargs from the 
            # onebandplot_kwargs dict, and save individually
            onebandplot_tick_colour = onebandplot_kwargs.pop('tick_colour')
            onebandplot_tick_fontsize = onebandplot_kwargs.pop('tick_fontsize')

            # Set up annotation parameters that control font etc. The 
            # nested dict structure sets default values which can be 
            # overwritten/customised by the manually specified 
            #`annotation_kwargs`
            annotation_kwargs = dict(
                {
                    'xy': (1, 1),
                    'xycoords': 'axes fraction',
                    'xytext': (-5, -5),
                    'textcoords': 'offset points',
                    'horizontalalignment': 'right',
                    'verticalalignment': 'top',
                    'fontsize': 20,
                    'color': 'white',
                    'path_effects': [PathEffects.withStroke(linewidth=2.5, 
                                                            foreground='black')]
                }, **annotation_kwargs)

            ###################
            # Initialise plot #
            ###################

            # Set up figure
            fig, ax1 = plt.subplots(ncols=1)
            fig.subplots_adjust(left=0,
                                bottom=0,
                                right=1,
                                top=1,
                                wspace=0,
                                hspace=0)
            
            fig.set_size_inches(width * scale / 72, 
                                height * scale / 72, 
                                forward=True)
            ax1.axis('off')

            # Initialise axesimage objects to be updated during 
            # animation, setting extent from dims
            extents = [float(ds[x_dim].min()),
                       float(ds[x_dim].max()),
                       float(ds[y_dim].min()),
                       float(ds[y_dim].max())]
            
            im = ax1.imshow(imagelist[0], 
                            extent=extents, 
                            **onebandplot_kwargs)

            # Initialise annotation objects to be updated during 
            # animation
            t = ax1.annotate('', **annotation_kwargs)

            #########################
            # Add optional overlays #
            #########################

            # Optionally add shapefile overlay(s) from either string 
            # path or list of string paths
            if isinstance(shapefile_path, str):

                # Define default plotting parameters for the overlaying 
                # shapefile(s). The nested dict structure sets default 
                # values which can be overwritten/customised by the 
                # manually specified `shapefile_kwargs`
                shapefile_kwargs = dict({'linewidth': 2,
                                         'edgecolor': 'black',
                                         'facecolor': "#00000000"}, 
                                        **shapefile_kwargs)

                shapefile = gpd.read_file(shapefile_path)
                shapefile.plot(**shapefile_kwargs, ax=ax1)

            elif isinstance(shapefile_path, list):

                # Iterate through list of string paths
                for i, shapefile in enumerate(shapefile_path):

                    if isinstance(shapefile_kwargs, list):

                        # If a list of shapefile_kwargs is supplied, use
                        # one for each shapefile
                        shapefile_kwargs_i = dict({'linewidth': 2,
                                                   'edgecolor': 'black',
                                                   'facecolor': "#00000000"}, 
                                                  **shapefile_kwargs[i])

                        shapefile = gpd.read_file(shapefile)
                        shapefile.plot(**shapefile_kwargs_i, ax=ax1)

                    else:

                        # If one shapefile_kwargs is provided, use for 
                        # all shapefiles
                        shapefile_kwargs = dict({'linewidth': 2,
                                                 'edgecolor': 'black',
                                                 'facecolor': "#00000000"}, 
                                                **shapefile_kwargs)

                        shapefile = gpd.read_file(shapefile)
                        shapefile.plot(**shapefile_kwargs, ax=ax1)

            # After adding shapefile, fix extents of plot
            ax1.set_xlim(extents[0], extents[1])
            ax1.set_ylim(extents[2], extents[3])

            # Optionally add colourbar for one band images
            if (len(bands) == 1) & onebandplot_cbar:

                _add_colourbar(ax1,
                               im,
                               tick_fontsize=onebandplot_tick_fontsize,
                               tick_colour=onebandplot_tick_colour,
                               vmin=onebandplot_kwargs['vmin'],
                               vmax=onebandplot_kwargs['vmax'],
                               cmap=onebandplot_kwargs['cmap'])

            ########################################
            # Create function to update each frame #
            ########################################

            # Function to update figure
            def update_figure(frame_i):

                # If possible, extract dates from time dimension
                try:

                    # Get human-readable date info (e.g. "16 May 1990")
                    ts = ds[time_dim][{time_dim: frame_i}].dt
                    year = ts.year.item()
                    month = ts.month.item()
                    day = ts.day.item()
                    date_string = '{} {} {}'.format(day,
                                                    calendar.month_abbr[month],
                                                    year)

                except:

                    date_string = ds[time_dim][{time_dim: frame_i}].values.item()

                # Create annotation string based on title and date 
                # specifications:
                title = title_list[frame_i]
                if title and show_date:
                    title_date = '{}\n{}'.format(date_string, title)
                elif title and not show_date:
                    title_date = '{}'.format(title)
                elif show_date and not title:
                    title_date = '{}'.format(date_string)
                else:
                    title_date = ''

                # Update figure for frame
                im.set_array(imagelist[frame_i])
                t.set_text(title_date)

                # Return the artists set
                return [im, t]

            ##############################
            # Generate and run animation #
            ##############################

            # Generate animation
            print('Generating {} frame animation'.format(timesteps))
            ani = animation.FuncAnimation(fig,
                                          update_figure,
                                          frames=timesteps,
                                          interval=interval,
                                          blit=True)

            # Export as either MP4 or GIF
            if output_path[-3:] == 'mp4':
                print('    Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=72)

            elif output_path[-3:] == 'gif':
                print('    Exporting animation to {}'.format(output_path))
                ani.save(output_path,
                         writer='pillow') 

            else:
                print('    Output file type must be either .mp4 or .gif')

        else:
            print(
                'Please select either one or three bands that all exist in the input dataset'
            )

    else:
        print('At least one x, y or time dimension does not exist in the input dataset. Please use the `time_dim`,' \
              '`x_dim` or `y_dim` parameters to override the default dimension names used for plotting')


# Define function to convert xarray dataset to list of one or three band numpy arrays
def _ds_to_arrraylist(ds, bands, time_dim, x_dim, y_dim, percentile_stretch, image_proc_func=None): 

    """
    Converts an xarray dataset to a list of numpy arrays for plt.imshow plotting
    """

    # Compute percents
    p_low, p_high = ds[bands].to_array().quantile(percentile_stretch).values

    array_list = []
    for i, timestep in enumerate(ds[time_dim]):

        # Select single timestep from the data array
        ds_i = ds[{time_dim: i}]

        # Get shape of array
        x = len(ds[x_dim])
        y = len(ds[y_dim])

        if len(bands) == 1:    

            # Create new one band array
            img_toshow = exposure.rescale_intensity(ds_i[bands[0]].values, 
                                                    in_range=(p_low, p_high),
                                                    out_range='image')

        else:

            # Create new three band array                
            rawimg = np.zeros((y, x, 3), dtype=np.float32)

            # Add xarray bands into three dimensional numpy array
            for band, colour in enumerate(bands):

                rawimg[:, :, band] = ds_i[colour].values

            # Stretch contrast using percentile values
            img_toshow = exposure.rescale_intensity(rawimg, 
                                                    in_range=(p_low, p_high),
                                                    out_range=(0, 1.0))

            # Optionally image processing
            if image_proc_func:
                
                img_toshow = image_proc_func(img_toshow).clip(0, 1)

        array_list.append(img_toshow)

    return array_list, p_low, p_high


def _add_colourbar(ax, im, vmin, vmax, cmap='Greys', tick_fontsize=15, tick_colour='black'):

    """
    Add a nicely formatted colourbar to an animation panel
    """

    # Add colourbar
    axins2 = inset_axes(ax, width='97%', height='4%', loc=8, borderpad=1) 
    plt.gcf().colorbar(im, cax=axins2, orientation='horizontal', ticks=np.linspace(vmin, vmax, 3)) 
    axins2.xaxis.set_ticks_position('top')
    axins2.tick_params(axis='x', colors=tick_colour, labelsize=tick_fontsize) 
    
    # Justify left and right labels to edge of plot
    axins2.get_xticklabels()[0].set_horizontalalignment('left')
    axins2.get_xticklabels()[-1].set_horizontalalignment('right')
    labels = [item.get_text() for item in axins2.get_xticklabels()]
    labels[0] = '  ' + labels[0]
    labels[-1] = labels[-1] + '  '
    
        
def _degree_to_zoom_level(l1, l2, margin=0.0):
    
    """
    Helper function to set zoom level for `display_map`
    """
    
    degree = abs(l1 - l2) * (1 + margin)
    zoom_level_int = 0
    if degree != 0:
        zoom_level_float = math.log(360 / degree) / math.log(2)
        zoom_level_int = int(zoom_level_float)
    else:
        zoom_level_int = 18
    return zoom_level_int
