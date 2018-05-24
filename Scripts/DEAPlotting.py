# DEAPlotting.py
"""
This file contains a set of python functions for plotting DEA data.
Available functions:

    three_band_image
    three_band_image_subplots
    animated_timeseries
    animated_fade

Last modified: May 2018
Author: Claire Krause
Modified by: Robbi Bishop-Taylor

"""

# Load modules
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import calendar


def three_band_image(ds, bands=['red', 'green', 'blue'], time=0, figsize=(10, 10), title='Time',
                     projection='projected', contrast_enhance=False, reflect_stand=5000):

    """
    This function takes three spectral bands and plots them as the RGB bands of an image.

    Last modified: May 2018
    Author: Mike Barnes
    Modified by: Claire Krause, Cate Kooymans, Robbi Bishop-Taylor


    :param ds:
        An xarray dataset containing the bands to be plotted. For correct axis scales, the xarray
        will ideally have spatial data (e.g. an `.extent` method)

    :param bands:
        Optional list of three bands to be plotted (defaults to `['red', 'green', 'blue']`)

    :param time:
        Optional index value of the time dimension of the xarray dataset to be plotted (defaults to 0)

    :param figsize:
        Optional tuple or list giving the dimensions of the output plot (defaults to `(10, 10)`)

    :param title:
        Optional string for the plot title. If left as the default 'Time', the title will be taken from
        the timestep of the plotted image if available

    :param projection:
        Determines if the image is in degrees or northings (options are 'projected' or 'geographic')

    :param contrast_enhance:
        Optionally transform data using a histogram stretch. If `contrast_enhance = True`,
        exposure.equalize_hist is used to transform the data. Else, the data are standardised relative
        to a default reflectance = 5000 (this can be customised using `reflect_stand`)

    :param reflect_stand:
        Optionally allows you to have greater control over the contrast stretch by manually specifying a
        reflectance standardisation value. Low values (< 5000) typically result in brighter images. Only
        applies if `contrast_enhance=False` (defaults to 5000)


    :return fig:
        A matplotlib figure object for customised plotting

    :return ax:
        A matplotlib axis object for customised plotting


    :example:
        >>> # Import external functions from dea-notebooks
        >>> sys.path.append(os.path.expanduser('~/dea-notebooks/Scripts'))
        >>> import DEAPlotting
        >>>
        >>> # Load Landsat time series
        >>> xarray_dataset = dc.load(product='ls8_nbart_albers', **query)
        >>>
        >>> # Plot as an RGB image
        >>> DEAPlotting.three_band_image(ds=xarray_dataset)

    """

    # Use different approaches to data prep depending on whether dataset has temporal dimension
    try:

        # Create new numpy array matching shape of xarray
        t, y, x = ds[bands[0]].shape
        rawimg = np.zeros((y, x, 3), dtype=np.float32)

        # Add xarray bands for a given time into three dimensional numpy array
        for i, colour in enumerate(bands):

            rawimg[:, :, i] = ds[colour][time].values
            
    except ValueError:

        # Create new numpy array matching shape of xarray
        y, x = ds[bands[0]].shape
        rawimg = np.zeros((y, x, 3), dtype=np.float32)

        # Add xarray bands into three dimensional numpy array
        for i, colour in enumerate(bands):

            rawimg[:, :, i] = ds[colour].values
            
    # Set nodata value to NaN
    rawimg[rawimg == -999] = np.nan

    # Optionally compute contrast based on histogram
    if contrast_enhance:

        # Stretch contrast using histogram
        img_toshow = exposure.equalize_hist(rawimg, mask=np.isfinite(rawimg))
        
    else:

        # Stretch contrast using defined reflectance standardisation and clip to between 0 and 1
        # to prevent warnings; defaults to reflect_stand = 5000
        img_toshow = (rawimg / reflect_stand).clip(0, 1)

    # Plot figure, setting x and y axes from extent of xarray dataset
    fig, ax = plt.subplots(figsize=figsize)

    try:

        # Plot with correct coords by setting extent if dataset has spatial data (e.g. an `.extent` method).
        # This also allows the resulting image to be overlaid with other spatial data (e.g. a polygon or point)
        left, bottom, right, top = ds.extent.boundingbox
        plt.imshow(img_toshow, extent=[left, right, bottom, top])

    except:

        # Plot without coords if dataset has no spatial data (e.g. an `.extent` method)
        print("xarray dataset has no spatial data; defaulting to plotting without coordinates. "
              "This can often be resolved by adding `keep_attrs = True` during an aggregation step")
        plt.imshow(img_toshow)

    # Set title by either time or defined title
    if title == 'Time':

        try:

            # Plot title using timestep
            ax.set_title(str(ds.time[time].values), fontweight='bold', fontsize=14)

        except:

            # No title
            ax.set_title('', fontweight='bold', fontsize=14)

    else:

        # Manually defined title
        ax.set_title(title, fontweight='bold', fontsize=14)

    # Set x and y axis titles depending on projection
    if projection == 'geographic':

        ax.set_xlabel('Longitude', fontweight='bold')
        ax.set_ylabel('Latitude', fontweight='bold')
        
    else:

        ax.set_xlabel('Eastings', fontweight='bold')
        ax.set_ylabel('Northings', fontweight='bold')
        
    return fig, ax


def three_band_image_subplots(ds, bands, num_cols, contrast_enhance = False, figsize = [10,10], 
                              projection = 'projected', left  = 0.125, 
                              right = 0.9, bottom = 0.1, top = 0.9, 
                              wspace = 0.2, hspace = 0.4):
  
    """
    threeBandImage_subplots takes three spectral bands and multiple time steps, 
    and plots them on the RGB bands of an image. 

    Last modified: March 2018
    Author: Mike Barnes
    Modified by: Claire Krause, Robbi Bishop-Taylor

    Inputs: 
    ds - dataset containing the bands to be plotted
    bands - list of three bands to be plotted
    num_cols - number of columns for the subplot

    Optional:
    contrast_enhance - determines the transformation for plotting onto RGB. If contrast_enhance = true, 
                       exposure.equalize_hist is used to transform the data. Else, the data are 
                       standardised relative to reflectance = 5000
    figsize - dimensions for the output figure
    projection - options are 'projected' or 'geographic'; determines if image is in degrees or northings
    left  - the space on the left side of the subplots of the figure
    right - the space on the right side of the subplots of the figure
    bottom - the space on the bottom of the subplots of the figure
    top - the space on the top of the subplots of the figure
    wspace - the amount of width reserved for blank space between subplots
    hspace - the amount of height reserved for white space between subplots
    """

    # Find the number of rows/columns we need, based on the number of time steps in ds
    timesteps = ds.time.size
    num_rows = int(np.ceil(timesteps / num_cols))
    fig, axes = plt.subplots(num_rows, num_cols, figsize = figsize)
    fig.subplots_adjust(left  = left, right = right, bottom = bottom, top = top, 
                        wspace = wspace, hspace = hspace)
    numbers = 0
    try:
        for ax in axes.flat:
            t, y, x = ds[bands[0]].shape
            rawimg = np.zeros((y, x, 3), dtype = np.float32)
            for i, colour in enumerate(bands):
                rawimg[:, :, i] = ds[colour][numbers].values
            rawimg[rawimg == -999] = np.nan
            if contrast_enhance == True:
                img_toshow = exposure.equalize_hist(rawimg, mask = np.isfinite(rawimg))
            else:
                img_toshow = rawimg / 5000
            ax.imshow(img_toshow)
            ax.set_title(str(ds.time[numbers].values), fontweight = 'bold', fontsize = 12)
            ax.set_xticklabels(ds.x.values, fontsize = 8, rotation = 20)
            ax.set_yticklabels(ds.y.values, fontsize = 8)
            if projection == 'geographic':
                ax.set_xlabel('Longitude', fontweight = 'bold', fontsize = 10)
                ax.set_ylabel('Latitude', fontweight = 'bold', fontsize = 10)
            else:
                ax.set_xlabel('Eastings', fontweight = 'bold', fontsize = 10)
                ax.set_ylabel('Northings', fontweight = 'bold', fontsize = 10)
            numbers = numbers + 1
    except IndexError:
        # This error will pop up if there are not enough scenes to fill the number of 
        # rows x columns, so we can safely ignore it
        fig.delaxes(ax)
        plt.draw()    
    return plt, fig


def animated_timeseries(ds, output_path, bands=['red', 'green', 'blue'], reflect_stand=5000, width_pixels=300,
                        interval=100, font_size=25):
    
    """
    Takes an xarray time series and exports a three band (e.g. true or false colour) GIF or MP4 animation showing 
    changes in the landscape across time.
    
    Last modified: May 2018
    Author: Robbi Bishop-Taylor
    
    :param ds: 
        An xarray dataset with multiple time steps (i.e. multiple observations along the `time` dimension)
        
    :param output_path: 
        A string giving the output location and filename of the resulting animation. File extensions of '.gif'
        and '.mp4' are accepted.
        
    :param bands:
        Optional list of exactly three bands to be plotted, all of which must exist in the input xarray dataset.
        Defaults to `['red', 'green', 'blue']`.
        
    :param reflect_stand:
        An integer that allows you to have greater control over the contrast stretch by manually specifying a
        reflectance standardisation value. Low values (< 5000) result in brighter images. Defaults to 5000. 
        
    :param width_pixels:
        An integer defining the output width in pixels for the resulting animation. The height of the animation is
        set automatically based on the dimensions/ratio of the input xarray dataset. Defaults to 300 pixels wide.
        
    :param interval:
        An integer defining the milliseconds between each animation frame used to control the speed of the output
        animation. Higher values result in a slower animation. Defaults to 100 milliseconds between each frame.    
    
    :param font_size:
        An integer that allows you to set the font size for the animation's date annotation. Defaults to 25.   
        
    :example:
    
    >>> # Import modules
    >>> import datacube     
    >>> 
    >>> # Set up datacube instance
    >>> dc = datacube.Datacube(app='Time series animation')
    >>> 
    >>> # Set up spatial and temporal query.
    >>> query = {'x': (-191399.7550998943, -183399.7550998943),
    >>>          'y': (-1423459.1336905062, -1415459.1336905062),
    >>>          'measurements': ['red', 'green', 'blue'],
    >>>          'time': ('2013-01-01', '2018-01-01'),
    >>>          'crs': 'EPSG:3577'}
    >>> 
    >>> # Load in only clear Landsat observations with < 1% unclear values
    >>> combined_ds = load_clearlandsat(dc=dc, query=query, masked_prop=0.99)  
    >>>
    >>> # Produce animation of red, green and blue bands
    >>> animated_timeseries(ds=combined_ds, output_path="output.mp4", 
    >>>                     interval=80, width_pixels=600, reflect_stand=3000)   
        
    """
    
    # First test if there are three bands, and that all exist in dataset:
    if (len(bands) == 3) & all([(band in ds.data_vars) for band in bands]):        

        # Get height relative to a size of 10 inches width
        width_ratio = float(ds.sizes['x']) / float(ds.sizes['y'])
        height = 10 / width_ratio

        # Set up plot
        fig, ax1 = plt.subplots()
        fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
        fig.set_size_inches(10, height, forward=True)
        plt.axis('off')

        # Iterate through each timestep and add plot to list
        ims = []
        print('Generating animation with {} frames'.format(len(ds.time)))
        for i, timestep in enumerate(ds.time):

            # Get human-readable date info (e.g. "16 May 1990")
            year = timestep.time.dt.year.item()
            month = calendar.month_abbr[timestep.time.dt.month.item()]
            day = timestep.time.dt.day.item()
            date_desc = '{} {} {}'.format(day, month, year)

            # Select single timestep from the data array
            ds_i = ds.isel(time = i)

            # Create new three band array
            y, x = ds_i[bands[0]].shape
            rawimg = np.zeros((y, x, 3), dtype=np.float32)

            # Add xarray bands into three dimensional numpy array
            for i, colour in enumerate(bands):

                rawimg[:, :, i] = ds_i[colour].values

            # Stretch contrast using defined reflectance standardisation; defaults to 5000
            img_toshow = (rawimg / reflect_stand).clip(0, 1)

            # Plot image for each timestep and append to list
            im = ax1.imshow(img_toshow, animated=True)

            # Set up text
            t = ax1.annotate(date_desc, 
                             xy=(1, 1), xycoords='axes fraction', 
                             xytext=(-5, -5), textcoords='offset points', 
                             horizontalalignment='right', verticalalignment='top', 
                             fontsize=font_size, color = "white", family='monospace')

            ims.append([im, t])

        # Create and export animation of all plots in list
        ani = animation.ArtistAnimation(fig, ims, interval=interval, blit=True, repeat_delay=interval)

        # Export as either MP4 or GIF
        if output_path[-3:] == 'mp4':
            print('    Exporting animation to {}'.format(output_path))
            ani.save(output_path, dpi=width_pixels / 10.0)

        elif output_path[-3:] == 'gif':
            print('    Exporting animation to {}'.format(output_path))
            ani.save(output_path, dpi=width_pixels / 10.0, writer='imagemagick')

        else:
            print("    Output file type must be either .gif or .mp4")
    
    else:        
            print("Please select exactly three bands that exist in the input dataset")


def animated_fade(ds1, ds2, output_path, bands=['red', 'green', 'blue'], reflect_stand=5000, width_pixels=300, 
                  interval=50, interval_steps=15, endpoint_steps=15, endpoint_text=['Before',  'After'],
                  font_size=25):
    
    """
    Takes two single-timestep xarray datasets, and plots an animation of the two layers fading between each other. 
    Possible applications include comparing an area before and after environmental change (i.e. flood, drought,
    fire, development), or comparing two geographic areas.
    
    
    Last modified: May 2018
    Author: Robbi Bishop-Taylor
    
    :param ds1: 
        An xarray dataset with a single time step (e.g. `xarray_dataset.isel(time=1)`).
        
    :param ds2: 
        An xarray dataset with a single time step (e.g. `xarray_dataset.isel(time=30)`). Ensure that this dataset 
        has the same dimensions/shape as ds1.
        
    :param output_path: 
        A string giving the output location and filename of the resulting animation. File extensions of '.gif'
        and '.mp4' are accepted.
        
    :param bands:
        Optional list of exactly three bands to be plotted, all of which must exist in the input xarray datasets.
        Defaults to `['red', 'green', 'blue']`.
    
    :param reflect_stand:
        An integer that allows you to have greater control over the contrast stretch by manually specifying a
        reflectance standardisation value. Low values (< 5000) result in brighter images. Defaults to 5000. 
    
    :param width_pixels:
        An integer defining the output width in pixels for the resulting animation. The height of the animation is
        set automatically based on the dimensions/ratio of the input xarray dataset. Defaults to 300 pixels wide.
        
    :param interval:
        An integer defining the milliseconds between each animation frame used to control the speed of the output
        animation. Higher values result in a slower animation. Defaults to 50 milliseconds between each frame.
    
    :param interval_steps:
        An integer defining the number of fade steps or frames to compute between ds1 and ds2. A higher number of
        steps results in smoother transitions, but can result in large file sizes for .gif animations. Defaults to 15.
    
    :param endpoint_steps:
        An integer defining the number of steps or frames to insert that the animation should pause for at the beginning 
        and end of each loop. Higher values causes ds1 and ds2 to remain on the screen for a longer period at the start 
        and end of the animation, but can result in large file sizes for .gif animations. Defaults to 15.
        
    :param endpoint_text:
        A list of two strings that match ds1 and ds2, and which are displayed at the start and end of the animation.
        Defaults to `['Before',  'After']`; set to `['',  '']` to hide text.  
        
    :param font_size:
        An integer that allows you to set the font size for the animation's date annotation. Defaults to 25.   
        
    :example:
    
    >>> # Import modules
    >>> import datacube     
    >>> 
    >>> # Set up datacube instance
    >>> dc = datacube.Datacube(app='Time series animation')
    >>> 
    >>> # Set up spatial and temporal query.
    >>> query = {'x': (970476, 987476),
    >>>          'y': (-3568950, -3551951),
    >>>          'measurements': ['red', 'green', 'blue'],
    >>>          'time': ('2013-01-01', '2018-01-01'),
    >>>          'crs': 'EPSG:3577'}
    >>> 
    >>> # Load in only clear Landsat observations with < 1% unclear values
    >>> combined_ds = load_clearlandsat(dc=dc, query=query, masked_prop=0.99)  
    >>>
    >>> # Produce animation that fades between ds1 and ds2
    >>> animated_fade(ds1=combined_ds.isel(time=1), ds2=combined_ds.isel(time=30), 
    >>>               output_path='animated_fade.gif', reflect_stand=2500, 
    >>>               width_pixels=300, font_size = 40)
        
    """

    # First test if there are three bands, and that all exist in dataset:
    if (len(bands) == 3) & all([(band in ds1.data_vars) for band in bands]):  

        # Get height relative to a size of 10 inches width
        width_ratio = float(ds1.sizes['x']) / float(ds1.sizes['y'])
        height = 10 / width_ratio

        # Set up plot
        fig, ax1 = plt.subplots()
        fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
        fig.set_size_inches(10, 10, forward=True)
        plt.axis('off')

        # Convert xarray datasets to numpy arrays
        ds1_rgb = ds1[bands].to_array().values
        ds2_rgb = ds2[bands].to_array().values

        # Test that shapes are the same:
        if ds1_rgb.shape == ds2_rgb.shape:

            # Rearrange arrays to a x by y by bands arrays for RGB plotting using imshow
            ds1_rgb = np.einsum('bxy->xyb', ds1_rgb)
            ds2_rgb = np.einsum('bxy->xyb', ds2_rgb)

            # Stretch contrast using defined reflectance standardisation; defaults to 5000
            ds1_rgb = (ds1_rgb / reflect_stand).clip(0, 1)
            ds2_rgb = (ds2_rgb / reflect_stand).clip(0, 1)

            # Compute spread of fade proportions in forward and reverse direction, with a
            # specified pause (in steps/frames) at the start and finish of the sequence
            fade_props = np.concatenate([np.linspace(0, 1, interval_steps, endpoint=True),
                                         np.array([1] * endpoint_steps),  # pause at ds1
                                         np.linspace(1, 0, interval_steps, endpoint=True),
                                         np.array([0] * endpoint_steps)])  # pause at ds2

            # Iterate through each timestep and add plot to list
            ims = []
            for fade_prop in fade_props:

                # Fade between datasets using fade proportion
                ds_merged = (ds1_rgb * fade_prop) + (ds2_rgb * (1.0 - fade_prop))  

                # Plot image for each timestep and append to list
                im = ax1.imshow(ds_merged, animated=True)

                # If on first or last frame, add text
                if fade_prop in [0, 1]:

                    # Plot either first or second text annotation by indexing 
                    text_index = int(fade_prop)
                    t = ax1.annotate(endpoint_text[text_index], 
                                     xy=(1, 1), xycoords='axes fraction', 
                                     xytext=(-5, -5), textcoords='offset points', 
                                     horizontalalignment='right', verticalalignment='top', 
                                     fontsize=font_size, color='white', family='monospace')
                else:

                    # Set up text
                    t = ax1.annotate("", xy=(1, 1), xycoords='axes fraction')


                ims.append([im, t])

            # Create and export animation of all plots in list
            ani = animation.ArtistAnimation(fig, ims, interval=interval, repeat_delay=interval, blit=True)

            # Export as either MP4 or GIF
            if output_path[-3:] == 'mp4':
                print('Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0)

            elif output_path[-3:] == 'gif':
                print('Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0, writer='imagemagick')

            else:
                print('Output file type must be either .gif or .mp4')

        else:
            print('ds1 has different dimensions {} to ds2 {}'.format(ds1_rgb.shape, ds2_rgb.shape))        

    else:        
        print("Please select exactly three bands that exist in the input dataset")
