# DEAPlotting.py
"""
This file contains a set of python functions for plotting DEA data.
Available functions:

    three_band_image
    three_band_image_subplots
    animated_timeseries
    animated_doubletimeseries

Last modified: June 2018
Author: Claire Krause
Modified by: Robbi Bishop-Taylor

"""

# Load modules
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
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


def animated_timeseries(ds, output_path, width_pixels=600, interval=100, bands=['red', 'green', 'blue'], 
                        reflect_stand=5000, title=False, show_date=True, onebandplot_cbar=True,
                        onebandplot_kwargs={}, annotation_kwargs={}):
    
    """
    Takes an xarray time series and animates the data as either a three-band (e.g. true or false colour) 
    or single-band animation, allowing changes in the landscape to be compared across time.
    
    Animations can be exported as .mp4 (ideal for Twitter/social media), .wmv (ideal for Powerpoint) and .gif 
    (ideal for all purposes, but can have large file sizes) format files, and customised to include titles and 
    date annotations or use specific combinations of input bands. 
    
    This function can be used to produce visually appealing cloud-free animations when used in combination with 
    the `load_clearlandsat` function from `dea-notebooks/Scripts/DEADataHandling`.
    
    Last modified: May 2018
    Author: Robbi Bishop-Taylor    
    
    :param ds: 
        An xarray dataset with multiple time steps (i.e. multiple observations along the `time` dimension).
        
    :param output_path: 
        A string giving the output location and filename of the resulting animation. File extensions of '.mp4', 
        '.wmv' and '.gif' are accepted.
    
    :param width_pixels:
        An integer defining the output width in pixels for the resulting animation. The height of the animation is
        set automatically based on the dimensions/ratio of the input xarray dataset. Defaults to 600 pixels wide.
        
    :param interval:
        An integer defining the milliseconds between each animation frame used to control the speed of the output
        animation. Higher values result in a slower animation. Defaults to 100 milliseconds between each frame. 
        
    :param bands:
        An optional list of either one or three bands to be plotted, all of which must exist in `ds`.
        Defaults to `['red', 'green', 'blue']`. 
        
    :param reflect_stand:
        An optional  integer controlling the brightness of the output image. Low values (< 5000) result in 
        brighter images. Defaults to 5000.

    :param title: 
        An optional string or list of strings with a length equal to the number of timesteps in ds. This can be
        used to display a static title (using a string), or a dynamic title (using a list) that displays different
        text for each timestep. Defaults to False, which plots no title.
        
    :param show_date:
        An optional boolean that defines whether or not to plot date annotations for each animation frame. Defaults 
        to True, which plots date annotations based on ds.
        
    :param onebandplot_cbar:
        An optional boolean indicating whether to include a colourbar for `ds1` one-band arrays. Defaults to True.
        
    :param onebandplot_kwargs:
        An optional dict of kwargs for controlling the appearance of one-band image arrays to pass to matplotlib 
        `plt.imshow` (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html for options).
        This only applies if an xarray with a single band is passed to `ds`. For example, a green colour scheme and
        custom stretch could be specified using: `onebandplot_kwargs={'cmap':'Greens`, 'vmin':0.2, 'vmax':0.9}`. 
        By default, one-band arrays are plotted using the 'Greys' cmap with a vmin of 0.0 and a vmax of 1.0.
    
    :param annotation_kwargs:
        An optional dict of kwargs for controlling the appearance of text annotations to pass to the matplotlib 
        `plt.annotate` function (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html for options). 
        For example, `annotation_kwargs={'fontsize':20, 'color':'red', 'family':'serif'}. By default, text annotations 
        are plotted as white, size 25 mono-spaced font with a 4pt black outline in the top-right of the animation.   
    """

    # Define function to convert xarray dataset to list of three band numpy arrays
    def _ds_to_arrraylist(ds, bands, reflect_stand):   

        array_list = []
        for i, timestep in enumerate(ds.time):

            # Select single timestep from the data array
            ds_i = ds.isel(time = i)

            # Create new three band array
            y, x = ds_i[bands[0]].shape

            if len(bands) == 1:    

                # Create new three band array
                img_toshow = ds_i[bands[0]].values

            else:

                rawimg = np.zeros((y, x, 3), dtype=np.float32)

                # Add xarray bands into three dimensional numpy array
                for band, colour in enumerate(bands):

                    rawimg[:, :, band] = ds_i[colour].values

                # Stretch contrast using defined reflectance standardisation; defaults to 5000
                img_toshow = (rawimg / reflect_stand).clip(0, 1)

            array_list.append(img_toshow)

        return(array_list)
    
    
    def _add_colourbar(ax, im, vmin, vmax, fontsize):
        
        """
        Add a nicely formatted colourbar to an animation panel
        """

        # Add underlying bar
        cbbox = inset_axes(ax, '100%', '7%', loc = 8, borderpad=0)
        [cbbox.spines[k].set_visible(False) for k in cbbox.spines]
        cbbox.tick_params(axis='both', left=False, top=False, right=False, bottom=False, 
                          labelleft=False, labeltop=False, labelright=False, labelbottom=False)
        cbbox.set_facecolor([0, 0, 0, 0.4])

        # Add colourbar
        axins2 = inset_axes(ax, width="90%", height="3%", loc=8) 
        fig.colorbar(im, cax=axins2, orientation="horizontal", ticks=np.linspace(vmin, vmax, 3)) 
        axins2.xaxis.set_ticks_position("top")
        axins2.tick_params(axis='x', colors='white', labelsize=fontsize, pad=1, length=0)
        axins2.get_xticklabels()[0].set_horizontalalignment('left')
        axins2.get_xticklabels()[-1].set_horizontalalignment('right') 
        
    
    ###############
    # Setup steps #
    ############### 
    
    # Get number of timesteps for each dataset
    timesteps = len(ds.time)
    
    # If title is supplied as a string, multiply out to a list with one string per timestep.
    # Otherwise, use supplied list for plot titles.
    if isinstance(title, str) or isinstance(title, bool):
        title_list = [title] * timesteps 
    else:
        title_list = title
    
    # Set up annotation parameters that plt.imshow plotting for single band array images. 
    # The nested dict structure sets default values which can be overwritten/customised by the 
    # manually specified `onebandplot_kwargs`
    onebandplot_kwargs = dict({'cmap':'Greys', 'vmin':0.0, 'vmax':1.0, 'interpolation':'bilinear'},
                               **onebandplot_kwargs)         
    
    # Set up annotation parameters that control font etc. The nested dict structure sets default 
    # values which can be overwritten/customised by the manually specified `annotation_kwargs`
    annotation_kwargs = dict({'xy': (1, 1), 'xycoords':'axes fraction', 
                              'xytext':(-5, -5), 'textcoords':'offset points', 
                              'horizontalalignment':'right', 'verticalalignment':'top', 
                              'fontsize':25, 'color':'white', 'family':'monospace', 
                              'path_effects':[PathEffects.withStroke(linewidth=4, foreground='black')]},
                              **annotation_kwargs)
   
    
    ###################
    # Initialise plot #
    ################### 
    
    # First test if there are three bands, and that all exist in both datasets:
    if ((len(bands) == 3) | (len(bands) == 1)) & all([(b in ds.data_vars) for b in bands]): 
        
        # Get height relative to a size of 10 inches width
        width_ratio = float(ds.sizes['x']) / float(ds.sizes['y'])
        height = 10.0 / width_ratio

        # Import xarrays as lists of three band numpy arrays
        imagelist = _ds_to_arrraylist(ds, bands=bands, reflect_stand=reflect_stand)        

        # Set up figure
        fig, ax1 = plt.subplots(ncols=1) 
        fig.patch.set_facecolor('black')
        fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        fig.set_size_inches(10.0, height, forward=True)
        ax1.axis('off')

        # Initialise axesimage objects to be updated during animation
        im = ax1.imshow(imagelist[0], **onebandplot_kwargs)

        # Initialise annotation objects to be updated during animation
        t = ax1.annotate('', **annotation_kwargs)
        
        # Optionally add colourbar for one band images
        if (len(bands) == 1) & onebandplot_cbar:                
            _add_colourbar(ax1, im, fontsize=20,
                           vmin=onebandplot_kwargs['vmin'], 
                           vmax=onebandplot_kwargs['vmax'])

        # Function to update figure
        def update_figure(frame_i):

            ####################
            # Plot first panel #
            ####################  

            # Get human-readable date info (e.g. "16 May 1990")
            ts = ds.time.isel(time=frame_i).dt
            year = ts.year.item()
            month = ts.month.item()
            day = ts.day.item()

            # Create annotation string based on title and date specifications:
            title = title_list[frame_i]
            if title and show_date:
                title_date = '{} {} {}\n{}'.format(day, calendar.month_abbr[month], year, title)
            elif title and not show_date:
                title_date = '{}'.format(title)
            elif show_date and not title:
                title_date = '{} {} {}'.format(day, calendar.month_abbr[month], year)           
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
        ani = animation.FuncAnimation(fig, update_figure, frames=timesteps, interval=interval, blit=True)

        # Export as either MP4 or GIF
        if output_path[-3:] == 'mp4':
            print('    Exporting animation to {}'.format(output_path))
            ani.save(output_path, dpi=width_pixels / 10.0)

        elif output_path[-3:] == 'wmv':
            print('    Exporting animation to {}'.format(output_path))
            ani.save(output_path, dpi=width_pixels / 10.0, 
                     writer=animation.FFMpegFileWriter(fps=1000 / interval, bitrate=4000, codec='wmv2'))

        elif output_path[-3:] == 'gif':
            print('    Exporting animation to {}'.format(output_path))
            ani.save(output_path, dpi=width_pixels / 10.0, writer='imagemagick')

        else:
            print('    Output file type must be either .mp4, .wmv or .gif')

    else:        
        print('Please select either one or three bands that all exist in the input dataset')  



def animated_doubletimeseries(ds1, ds2, output_path, width_pixels=800, interval=100, 
                              bands1=['red', 'green', 'blue'], bands2=['red', 'green', 'blue'], 
                              reflect_stand1=5000, reflect_stand2=5000, 
                              title1=False, title2=False,
                              show_date1=True, show_date2=True,
                              onebandplot_cbar1=True, onebandplot_cbar2=True,
                              onebandplot_kwargs1={}, onebandplot_kwargs2={},
                              annotation_kwargs1={}, annotation_kwargs2={}):
    
    """
    Takes two xarray time series and animates both side-by-side as either three-band (e.g. true or false colour) 
    or single-band animations, allowing changes in the landscape to be compared across time.
    
    Animations can be exported as .mp4 (ideal for Twitter/social media), .wmv (ideal for Powerpoint) and .gif 
    (ideal for all purposes, but can have large file sizes) format files, and customised to include titles and 
    date annotations for each panel or use different input bands from each dataset. For example, true and false 
    colour band combinations could be plotted at the same time, or different products (i.e. NBAR and NBART) or 
    cloud masking algorithms could be compared. 
    
    This function can be used to produce visually appealing cloud-free animations when used in combination with 
    the `load_clearlandsat` function from `dea-notebooks/Scripts/DEADataHandling`.
    
    Last modified: May 2018
    Author: Robbi Bishop-Taylor    
    
    :param ds1: 
        An xarray dataset with multiple time steps (i.e. multiple observations along the `time` dimension) to be 
        plotted in the left panel of the animation.
        
    :param ds2: 
        A matching xarray dataset with the same number of pixels as ds1, to be plotted in the right panel of the
        animation. ds1 and ds2 do not need to have exactly the same number of timesteps, but the animation will 
        only continue up until the length of the shorted dataset (i.e. if ds1 has 10 timesteps and ds2 has 5, the 
        animation will continue for 5 timesteps).
        
    :param output_path: 
        A string giving the output location and filename of the resulting animation. File extensions of '.mp4', 
        '.wmv' and '.gif' are accepted.
        
    :param width_pixels:
        An optional integer defining the output width in pixels for the resulting animation. The height of the 
        animation is set automatically based on the dimensions/ratio of `ds1`. Defaults to 
        800 pixels wide.
        
    :param interval:
        An optional integer defining the milliseconds between each animation frame used to control the speed of 
        the output animation. Higher values result in a slower animation. Defaults to 100 milliseconds between 
        each frame.
        
    :param bands1:
        An optional list of either one or three bands to be plotted, all of which must exist in `ds1`.
        Defaults to `['red', 'green', 'blue']`.
    
    :param bands2:
        An optional list of either one or three bands to be plotted, all of which must exist in `ds2`.
        Defaults to `['red', 'green', 'blue']`. 
        
    :param reflect_stand1:
        An optional  integer controlling the brightness of the output `ds1` image. Low values (< 5000) result in 
        brighter images. Defaults to 5000.
    
    :param reflect_stand2:
        An optional integer controlling the brightness of the output `ds2` image. Low values (< 5000) result in 
        brighter images. Defaults to 5000.

    :param title1: 
        An optional string or list of strings with a length equal to the number of timesteps in `ds1`. This can be
        used to display a static title for the left panel (using a string), or a dynamic title (using a list)
        that displays different text for each timestep. Defaults to False, which plots no title.
        
    :param title2: 
        An optional string or list of strings with a length equal to the number of timesteps in `ds2`. This can be
        used to display a static title for the left panel (using a string), or a dynamic title (using a list)
        that displays different text for each timestep. Defaults to False, which plots no title.
        
    :param show_date1:
        An optional boolean that defines whether or not to plot date annotations for each animation frame in the 
        left panel. Defaults to True, which plots date annotations for `ds1`.
    
    :param show_date2:
        An optional boolean that defines whether or not to plot date annotations for each animation frame in the 
        right panel. Defaults to True, which plots date annotations for `ds2`.
        
    :param onebandplot_cbar1:
        An optional boolean indicating whether to include a colourbar for `ds1` one-band arrays. Defaults to True.
        
    :param onebandplot_cbar2:
        An optional boolean indicating whether to include a colourbar for `ds2` one-band arrays. Defaults to True.
        
    :param onebandplot_kwargs1:
        An optional dict of kwargs for controlling the appearance of `ds1` one-band image arrays to pass to 
        matplotlib `plt.imshow` (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html for options).
        This only applies if an xarray with a single band is passed to d1. For example, a green colour scheme and
        custom stretch can be specified using: `onebandplot_kwargs1={'cmap':'Greens`, 'vmin':0.2, 'vmax':0.9}`. 
        By default, one-band arrays are plotted using the 'Greys' cmap with a vmin of 0.0 and a vmax of 1.0.
    
    :param onebandplot_kwargs2:
        An optional dict of kwargs for controlling the appearance of `ds2` one-band image arrays to 
        pass to matplotlib `plt.imshow`; only applies if an xarray with a single band is passed to d2 (see above).
    
    :param annotation_kwargs1:
        An optional dict of kwargs for controlling the appearance of `ds1` text annotations to pass to 
        matplotlib `plt.annotate`  (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html). 
        For example, `annotation_kwargs1={'fontsize':20, 'color':'red', 'family':'serif'}. By default, text 
        annotations are white, size 15 mono-spaced font with a 3pt black outline in the panel's top-right. 
    
    :param annotation_kwargs2:
        An optional dict of kwargs for controlling the appearance of the `ds2` text annotations to pass 
        to matplotlib `plt.annotate` (see above).
        
    """

    # Define function to convert xarray dataset to list of three band numpy arrays
    def _ds_to_arrraylist(ds, bands, reflect_stand):  
        
        """
        This function converts xarray dataset time series into a list of numpy arrays.
        Output arrays will be either one or three band arrays for input into plt.imshow
        """

        array_list = []
        for i, timestep in enumerate(ds.time):

            # Select single timestep from the data array
            ds_i = ds.isel(time = i)

            # Create new three band array
            y, x = ds_i[bands[0]].shape

            if len(bands) == 1:    

                # Create new three band array
                img_toshow = ds_i[bands[0]].values

            else:

                rawimg = np.zeros((y, x, 3), dtype=np.float32)

                # Add xarray bands into three dimensional numpy array
                for band, colour in enumerate(bands):

                    rawimg[:, :, band] = ds_i[colour].values

                # Stretch contrast using defined reflectance standardisation; defaults to 5000
                img_toshow = (rawimg / reflect_stand).clip(0, 1)

            array_list.append(img_toshow)

        return(array_list)
    
    def _add_colourbar(ax, im, vmin, vmax, fontsize):
        
        """
        Add a nicely formatted colourbar to an animation panel
        """

        # Add underlying bar
        cbbox = inset_axes(ax, '100%', '9%', loc = 8, borderpad=0)
        [cbbox.spines[k].set_visible(False) for k in cbbox.spines]
        cbbox.tick_params(axis='both', left=False, top=False, right=False, bottom=False, 
                          labelleft=False, labeltop=False, labelright=False, labelbottom=False)
        cbbox.set_facecolor([0, 0, 0, 0.4])

        # Add colourbar
        axins2 = inset_axes(ax, width="90%", height="3%", loc=8) 
        fig.colorbar(im, cax=axins2, orientation="horizontal", ticks=np.linspace(vmin, vmax, 3)) 
        axins2.xaxis.set_ticks_position("top")
        axins2.tick_params(axis='x', colors='white', labelsize=fontsize, pad=1, length=0)
        axins2.get_xticklabels()[0].set_horizontalalignment('left')
        axins2.get_xticklabels()[-1].set_horizontalalignment('right') 
    
    
    ###############
    # Setup steps #
    ############### 
    
    # Get height relative to a size of 10 inches width
    width_ratio = float(ds1.sizes['x']) / float(ds1.sizes['y'])
    height = 10.0 / width_ratio
    
    # Get number of timesteps for each dataset
    timesteps1 = len(ds1.time)
    timesteps2 = len(ds2.time)
    
    # If title is supplied as a string, multiply out to a list with one string per timestep.
    # Otherwise, use supplied list for plot titles.
    if isinstance(title1, str) or isinstance(title1, bool):
        title_list1 = [title1] * timesteps1   
    else:
        title_list1 = title1
        
    # If title is supplied as a string, multiply out to a list with one string per timestep
    if isinstance(title2, str) or isinstance(title2, bool):
        title_list2 = [title2] * timesteps2  
    else:
        title_list2 = title2       
        
    # Set up annotation parameters that plt.imshow plotting for single band array images. 
    # The nested dict structure sets default values which can be overwritten/customised by the 
    # manually specified `onebandplot_kwargs`
    onebandplot_kwargs1 = dict({'cmap':'Greys', 'vmin':0.0, 'vmax':1.0, 'interpolation':'bilinear'},
                                **onebandplot_kwargs1) 
    
    onebandplot_kwargs2 = dict({'cmap':'Greys', 'vmin':0.0, 'vmax':1.0, 'interpolation':'bilinear'},
                                **onebandplot_kwargs2) 
    
    # Set up annotation parameters that control font etc. The nested dict structure sets default 
    # values which can be overwritten/customised by the manually specified `annotation_kwargs`
    annotation_kwargs1 = dict({'xy': (1, 1), 'xycoords':'axes fraction', 
                               'xytext':(-5, -5), 'textcoords':'offset points', 
                               'horizontalalignment':'right', 'verticalalignment':'top', 
                               'fontsize':15, 'color':'white', 'family':'monospace', 
                               'path_effects':[PathEffects.withStroke(linewidth=3, foreground='black')]},
                               **annotation_kwargs1)
    
    annotation_kwargs2 = dict({'xy': (1, 1), 'xycoords':'axes fraction', 
                               'xytext':(-5, -5), 'textcoords':'offset points', 
                               'horizontalalignment':'right', 'verticalalignment':'top', 
                               'fontsize':15, 'color':'white', 'family':'monospace', 
                               'path_effects':[PathEffects.withStroke(linewidth=3, foreground='black')]},
                               **annotation_kwargs2)
   
    
    ###################
    # Initialise plot #
    ################### 
    
    # First test if there are three bands, and that all exist in both datasets:
    if ((len(bands1) == 3) | (len(bands1) == 1)) & all([(b1 in ds1.data_vars) for b1 in bands1]) & \
       ((len(bands2) == 3) | (len(bands2) == 1)) & all([(b2 in ds2.data_vars) for b2 in bands2]):  

        # Import xarrays as lists of three band numpy arrays
        imagelist1 = _ds_to_arrraylist(ds1, bands=bands1, reflect_stand=reflect_stand1)
        imagelist2 = _ds_to_arrraylist(ds2, bands=bands2, reflect_stand=reflect_stand2)
        
        # Test that shapes are the same:
        if imagelist1[0].shape[0:1] == imagelist2[0].shape[0:1]:
            
            # Set up figure
            fig, (ax1, ax2) = plt.subplots(ncols=2) 
            fig.patch.set_facecolor('black')
            fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
            fig.set_size_inches(10.0, height * 0.5, forward=True)
            ax1.axis('off')
            ax2.axis('off')
            
            # Initialise axesimage objects to be updated during animation
            im1 = ax1.imshow(imagelist1[0], **onebandplot_kwargs1)
            im2 = ax2.imshow(imagelist2[0], **onebandplot_kwargs2)
            
            # Initialise annotation objects to be updated during animation
            t1 = ax1.annotate('', **annotation_kwargs1)   
            t2 = ax2.annotate('', **annotation_kwargs2)  
            
            # Optionally add colourbars for one band images
            if (len(bands1) == 1) & onebandplot_cbar1:                
                _add_colourbar(ax1, im1, fontsize=11,
                               vmin=onebandplot_kwargs1['vmin'], 
                               vmax=onebandplot_kwargs1['vmax'])
                
            if (len(bands2) == 1) & onebandplot_cbar2:                
                _add_colourbar(ax2, im2, fontsize=11,
                               vmin=onebandplot_kwargs2['vmin'], 
                               vmax=onebandplot_kwargs2['vmax'])

            # Function to update figure
            def update_figure(frame_i):

                ####################
                # Plot first panel #
                ####################  

                # Get human-readable date info (e.g. "16 May 1990")
                ts = ds1.time.isel(time=frame_i).dt
                year = ts.year.item()
                month = ts.month.item()
                day = ts.day.item()

                # Create annotation string based on title and date specifications:
                title1 = title_list1[frame_i]
                if title1 and show_date1:
                    title_date1 = '{} {} {}\n{}'.format(day, calendar.month_abbr[month], year, title1)
                elif title1 and not show_date1:
                    title_date1 = '{}'.format(title1)
                elif show_date1 and not title1:
                    title_date1 = '{} {} {}'.format(day, calendar.month_abbr[month], year)           
                else:
                    title_date1 = ''

                # Update figure for frame
                im1.set_array(imagelist1[frame_i])
                t1.set_text(title_date1) 


                #####################
                # Plot second panel #
                ##################### 

                # Get human-readable date info (e.g. "16 May 1990")
                ts = ds2.time.isel(time=frame_i).dt
                year = ts.year.item()
                month = ts.month.item()
                day = ts.day.item()

                # Create annotation string based on title and date specifications:
                title2 = title_list2[frame_i]
                if title2 and show_date2:
                    title_date2 = '{} {} {}\n{}'.format(day, calendar.month_abbr[month], year, title2)
                elif title2 and not show_date2:
                    title_date2 = '{}'.format(title2)
                elif show_date2 and not title2:
                    title_date2 = '{} {} {}'.format(day, calendar.month_abbr[month], year)           
                else:
                    title_date2 = ''

                # Update figure for frame
                im2.set_array(imagelist2[frame_i])
                t2.set_text(title_date2) 

                # Return the artists set
                return [im1, im2, t1, t2]


            ##############################
            # Generate and run animation #
            ##############################

            # Generate animation
            frames_to_run = min(timesteps1, timesteps2)
            print('Generating {} frame animation (i.e. timesteps in shortest dataset)'.format(frames_to_run))
            ani = animation.FuncAnimation(fig, update_figure, frames=frames_to_run, interval=interval, blit=True)

            # Export as either MP4 or GIF
            if output_path[-3:] == 'mp4':
                print('    Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0)

            elif output_path[-3:] == 'wmv':
                print('    Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0, 
                         writer=animation.FFMpegFileWriter(fps=1000 / interval, bitrate=4000, codec='wmv2'))

            elif output_path[-3:] == 'gif':
                print('    Exporting animation to {}'.format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0, writer='imagemagick')

            else:
                print('    Output file type must be either .mp4, .wmv or .gif')
        
        else:
            print('Ensure that ds1 {} has the same xy dimensions as ds2 {}'.format(imagelist1[0].shape[0:1], 
                                                                                   imagelist2[0].shape[0:1])) 
    else:        
        print('Please select either one or three bands that all exist in the input datasets')  
