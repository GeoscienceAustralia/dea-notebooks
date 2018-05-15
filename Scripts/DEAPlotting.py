# DEAPlotting.py
"""
This file contains a set of python functions for plotting DEA data.
Available functions:

    three_band_image
    three_band_image_subplots

Last modified: May 2018
Author: Claire Krause
Modified by: Robbi Bishop-Taylor

"""

# Load modules
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt


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

        # Stretch contrast using defined reflectance standardisation; defaults to 5000
        img_toshow = rawimg / reflect_stand

    # Plot figure, setting x and y axes from extent of xarray dataset
    fig, ax = plt.subplots(figsize=figsize)

    try:

        # Plot with correct coords by setting extent if dataset has spatial data (e.g. an `.extent` method).
        # This also allows the resulting image to be overlaid with other spatial data (e.g. a polygon or point)
        left, bottom, right, top = ds.extent.boundingbox
        plt.imshow(img_toshow, extent=[left, right, bottom, top])

    except:

        # Plot without coords if dataset has no spatial data (e.g. an `.extent` method)
        warnings.warn("xarray dataset has no spatial data; defaulting to plotting without coordinates. "
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
