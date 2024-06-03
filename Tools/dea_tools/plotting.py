## dea_plotting.py
'''
Plotting and animating Digital Earth Australia products and data.

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
GitHub: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Last modified: April 2023

'''

# Import required packages
import math
import folium
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import xarray as xr
from matplotlib import colors as mcolours
from matplotlib.animation import FuncAnimation
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import box
from skimage.exposure import rescale_intensity
from tqdm.auto import tqdm

import odc.geo.xr
from odc.ui import image_aspect
from dea_tools.spatial import add_geobox


def rgb(ds,
        bands=['nbart_red', 'nbart_green', 'nbart_blue'],
        index=None,
        index_dim='time',
        robust=True,
        percentile_stretch=None,
        col_wrap=4,
        size=6,
        aspect=None,
        titles=None,
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
    titles : string or list of strings, optional
        Replace the xarray 'time' dimension on plot titles with a string
        or list of string titles, when a list of index values are
        provided, of your choice. Defaults to None.
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
    y_dim, x_dim = ds.odc.spatial_dims

    # If ax is supplied via kwargs, ignore aspect and size
    if 'ax' in kwargs:

        # Create empty aspect size kwarg that will be passed to imshow
        aspect_size_kwarg = {}
    else:
        # Compute image aspect
        if not aspect:
            aspect = ds.odc.geobox.aspect

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
        if ((len(ds.dims) > 2) and ('col' not in kwargs) and
            (len(da[index_dim]) == 1)):

            da = da.squeeze(dim=index_dim)

        # If there are more than three dimensions and the index dimension
        # is longer than 1, raise exception to tell user to use 'col'/`index`
        elif ((len(ds.dims) > 2) and ('col' not in kwargs) and
              (len(da[index_dim]) > 1)):

            raise Exception(
                f'The input dataset `ds` has more than two dimensions: '
                f'{list(ds.dims.keys())}. Please select a single observation '
                'using e.g. `index=0`, or enable faceted plotting by adding '
                'the arguments e.g. `col="time", col_wrap=4` to the function '
                'call')

        img = da.plot.imshow(x=x_dim,
                             y=y_dim,
                             robust=robust,
                             col_wrap=col_wrap,
                             **aspect_size_kwarg,
                             **kwargs)
        if titles is not None:
            for ax, title in zip(img.axs.flat, titles):
                ax.set_title(title)

    # If values provided for `index`, extract corresponding observations and
    # plot as either single image or facet plot
    else:

        # If a float is supplied instead of an integer index, raise exception
        if isinstance(index, float):
            raise Exception(
                f'Please supply `index` as either an integer or a list of '
                'integers')

        # If col argument is supplied as well as `index`, raise exception
        if 'col' in kwargs:
            raise Exception(
                f'Cannot supply both `index` and `col`; please remove one and '
                'try again')

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
            if titles is not None:
                for ax, title in zip(img.axs.flat, titles):
                    ax.set_title(title)

        # If only one index is supplied, squeeze out index_dim and plot as a
        # single panel
        else:

            img = da.squeeze(dim=index_dim).plot.imshow(robust=robust,
                                                        **aspect_size_kwarg,
                                                        **kwargs)
            if titles is not None:
                for ax, title in zip(img.axs.flat, titles):
                    ax.set_title(title)

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
    
    Last modified: February 2023
    
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
    transformer = Transformer.from_crs(crs, "EPSG:4326")
    all_longitude, all_latitude = transformer.transform(all_x, all_y)

    # Calculate zoom level based on coordinates
    lat_zoom_level = _degree_to_zoom_level(
        min(all_latitude), max(all_latitude), margin=margin) + zoom_bias
    lon_zoom_level = _degree_to_zoom_level(
        min(all_longitude), max(all_longitude), margin=margin) + zoom_bias
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
    
    Last modified: April 2023
    
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
        equivalent to xarray's `robust=True`. This parameter is ignored
        completely if `vmin` and `vmax` are provided as kwargs to
        `imshow_kwargs`.
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

        times_list = (times.dt.strftime(show_date).values
                      if show_date else [None] * len(times))
        text_list = show_text if is_sequence else [show_text] * len(times)
        annotation_list = [
            '\n'.join([str(i)
                       for i in (a, b)
                       if i])
            for a, b in zip(times_list, text_list)
        ]

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
        ax.imshow(array[i, ...].clip(0.0, 1.0),
                  extent=extent,
                  vmin=0.0,
                  vmax=1.0,
                  **imshow_defaults)

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

    # Add GeoBox and odc.* accessor to array using `odc-geo`
    try:
        ds = add_geobox(ds)
    except ValueError:
        raise ValueError("Unable to determine `ds`'s coordinate "
                         "reference system (CRS). Please assign a CRS "
                         "to the array before passing it to this "
                         "function, e.g.: "
                         "`ds.odc.assign_crs(crs='EPSG:3577')`")
    
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
    height, width = ds.odc.geobox.shape
    scale = width_pixels / width
    left, bottom, right, top = ds.odc.geobox.extent.boundingbox

    # Prepare annotations
    annotation_list = _frame_annotation(ds.time, show_date, show_text)

    # Prepare geodataframe
    if show_gdf is not None:
        show_gdf = show_gdf.to_crs(ds.odc.geobox.crs)
        show_gdf = gpd.clip(show_gdf, mask=box(
            left, bottom, right, top)).reindex(show_gdf.index).dropna(how='all')
        show_gdf = _start_end_times(show_gdf, ds)

    # Convert data to 4D numpy array of shape [time, y, x, bands]
    ds = ds[bands].to_array().transpose(..., 'variable')[0:limit, ...]
    array = ds.astype(np.float32).values

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
        vmin = imshow_defaults.pop('vmin')
    if 'vmax' in imshow_defaults:
        vmax = imshow_defaults.pop('vmax')

    # Rescale between 0 and 1
    array = rescale_intensity(array,
                              in_range=(vmin, vmax),
                              out_range=(0.0, 1.0))
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


def plot_wo(wo, legend=True, **plot_kwargs):
    """Plot a water observation bit flag image.
    
    Parameters
    ----------
    wo : xr.DataArray
        A DataArray containing water observation bit flags.
    legend : bool
        Whether to plot a legend. Default True.
    plot_kwargs : dict
        Keyword arguments passed on to DataArray.plot.
    
    Returns
    -------
    plot    
    """
    cmap = mcolours.ListedColormap([
        np.array([150, 150, 110]) / 255,  # dry - 0
        np.array([0, 0, 0]) / 255,  # nodata, - 1
        np.array([119, 104, 87]) / 255,  # terrain - 16
        np.array([89, 88, 86]) / 255,  # cloud_shadow - 32
        np.array([216, 215, 214]) / 255,  # cloud - 64
        np.array([242, 220, 180]) / 255,  # cloudy terrain - 80
        np.array([79, 129, 189]) / 255,  # water - 128
        np.array([51, 82, 119]) / 255,  # shady water - 160
        np.array([186, 211, 242]) / 255,  # cloudy water - 192
    ])
    bounds = [
        0,
        1,
        16,
        32,
        64,
        80,
        128,
        160,
        192,
        255,
    ]
    norm = mcolours.BoundaryNorm(np.array(bounds) - 0.1, cmap.N)
    cblabels = [
        'dry', 'nodata', 'terrain', 'cloud shadow', 'cloud', 'cloudy terrain',
        'water', 'shady water', 'cloudy water'
    ]

    try:
        im = wo.plot.imshow(cmap=cmap,
                            norm=norm,
                            add_colorbar=legend,
                            **plot_kwargs)
    except AttributeError:
        im = wo.plot(cmap=cmap, norm=norm, add_colorbar=legend, **plot_kwargs)

    if legend:
        try:
            cb = im.colorbar
        except AttributeError:
            cb = im.cbar
        ticks = cb.get_ticks()
        cb.set_ticks(ticks[:-1] + np.diff(ticks) / 2)
        cb.set_ticklabels(cblabels)
    return im


def plot_fmask(fmask, legend=True, **plot_kwargs):
    """
    Plot an enumerated FMask flag image with human-readable colours.
    
    Parameters
    ----------
    fmask : xr.DataArray
        A DataArray containing Fmask flags.
    legend : bool
        Whether to plot a legend. Default True.
    plot_kwargs : dict
        Keyword arguments passed on to DataArray.plot.
    
    Returns
    -------
    plot    
    """
    cmap = mcolours.ListedColormap([
        np.array([0, 0, 0]) / 255,  # nodata - 0
        np.array([132, 162, 120]) / 255,  # clear - 1
        np.array([208, 207, 206]) / 255,  # cloud - 2
        np.array([70, 70, 51]) / 255,  # cloud_shadow - 3
        np.array([224, 237, 255]) / 255,  # snow - 4
        np.array([71, 91, 116]) / 255,  # water - 5
    ])
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = mcolours.BoundaryNorm(np.array(bounds) - 0.1, cmap.N)
    cblabels = ['nodata', 'clear', 'cloud', 'shadow', 'snow', 'water']

    try:
        im = fmask.plot.imshow(cmap=cmap,
                               norm=norm,
                               add_colorbar=legend,
                               **plot_kwargs)
    except AttributeError:
        im = fmask.plot(cmap=cmap,
                        norm=norm,
                        add_colorbar=legend,
                        **plot_kwargs)

    if legend:
        try:
            cb = im.colorbar
        except AttributeError:
            cb = im.cbar
        ticks = cb.get_ticks()
        cb.set_ticks(ticks[:-1] + np.diff(ticks) / 2)
        cb.set_ticklabels(cblabels)
    return im


def plot_variable_images(img_collection):
    """
    Plot a dynamic number of images from a xarray dataset that
    includes Date and Index in the title. Optional ability to
    also include the sensor in the title if a 'sensor' attribute
    is added to the dataset using dataset.assign_attrs
    Parameters
    ----------
    img_collection : xr.Dataset
        A Dataset containing imagery with RBG bands
    Returns
    -------
    plot
    """
    # Check that img_collection is a xarray dataset
    if not isinstance(img_collection, xr.Dataset):
        raise TypeError("img_collection must be a xarray dataset.")

    # Calculate number of images in `img_collection`
    plot_count = img_collection.dims["time"]
    
    # Check if dataset has 0 images
    if plot_count == 0:
        if hasattr(img_collection, "sensor"):
            raise ValueError("The {} dataset has no images to display for the " 
            "given query parameters".format(img_collection.sensor))
        else:
            raise ValueError("The supplied xarray dataset has no images to "
            "display for the given query parameters")
                  
    # Divide the number of images by 2 rounding up to calculate the
    # number of rows for the below figure are needed
    plot_rows = math.ceil(plot_count / 2)

    # Construct a figure to visualise the imagery
    f, axarr = plt.subplots(plot_rows, 2, figsize=(10, plot_rows * 4.5),
                            squeeze=False)

    # Flatten the subplots so they can easily be enumerated through
    axarr = axarr.flatten()

    # Iterate through each image in the dataset and plot
    # each image as a RGB on a subplot
    for t in range(plot_count):
        rgb(
            img_collection.isel(time=t),
            bands=["nbart_red", "nbart_green", "nbart_blue"],
            ax=axarr[t],
            robust=True,
        )
        # Test to see if the dataset has a custom 'sensor' attribute.
        # If so, include the string in each subplot title.
        if hasattr(img_collection, "sensor"):
            title = (
                str(img_collection.time[t].values)[:10]
                + "  ||  Index: "
                + str(t)
                + "  ||  Sensor: "
                + img_collection.sensor
            )
        else:
            title = (
                str(img_collection.time[t].values)[:10]
                + "  ||  Index: "
                + str(t)
            )
        # Set subplot title, axis label, and shrink offset text
        axarr[t].set_title(title)
        axarr[t].set_xlabel("X coordinate")
        axarr[t].set_ylabel("Y coordinate")
        axarr[t].yaxis.offsetText.set_fontsize(6)
        axarr[t].xaxis.offsetText.set_fontsize(6)

    # Adjust padding arround subplots to prevent overlapping elements
    plt.tight_layout()

    # Remove the last subplot if an odd number of images are being displayed
    if plot_count % 2 != 0:
        f.delaxes(axarr[plot_count])

