# Load modules
import numpy as np
import pandas as pd
from skimage import exposure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patheffects as PathEffects
from datetime import datetime
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import calendar
import geopandas as gpd

def animated_timeseriesline(ds, df, output_path, width_pixels=1000, interval=200, 
                            bands=['red', 'green', 'blue'], reflect_stand=5000, 
                            title=False, show_date=True, annotation_kwargs={},
                            onebandplot_cbar=True, onebandplot_kwargs={}, 
                            shapefile_path=None, shapefile_kwargs={}, pandasplot_kwargs={},
                            time_dim = 'time', x_dim = 'x', y_dim = 'y'):
    
    """
    Takes an xarray time series and a pandas dataframe, and animates a line graph showing change in a variable 
    across time in the right column at the same time as a three-band (e.g. true or false colour) or single-band 
    animation in the left column.
    
    Animations can be exported as .mp4 (ideal for Twitter/social media), .wmv (ideal for Powerpoint) and .gif 
    (ideal for all purposes, but can have large file sizes) format files, and customised to include titles and 
    date annotations or use specific combinations of input bands. 

    A shapefile boundary can be added to the output animation by providing a path to the shapefile.
    
    This function can be used to produce visually appealing cloud-free animations when used in combination with 
    the `load_clearlandsat` function from `dea-notebooks/Scripts/DEADataHandling`.
    
    Last modified: August 2018
    Author: Robbi Bishop-Taylor, Sean Chua       
    
    :param ds: 
        An xarray dataset with multiple time steps (i.e. multiple observations along the `time` dimension) to plot 
        in the left panel of the animation.
        
    :param df: 
        An pandas dataframe with time steps contained in a DatetimeIndex column, and one or more numeric data 
        columns to plot as lines in the right panel. Column names are used to label the lines on the plot, so
        assign them informative names. Lines are plotted by showing all parts of the line with dates on or before
        the current timestep (i.e. for a 2006 time step, only the portion of the lines with dates on or before 
        2006 will be plotted for that frame.
        
    :param output_path: 
        A string giving the output location and filename of the resulting animation. File extensions of '.mp4', 
        '.wmv' and '.gif' are accepted.
    
    :param width_pixels:
        An integer defining the output width in pixels for the resulting animation. The height of the animation is
        set automatically based on the dimensions/ratio of the input xarray dataset. Defaults to 1000 pixels wide.
        
    :param interval:
        An integer defining the milliseconds between each animation frame used to control the speed of the output
        animation. Higher values result in a slower animation. Defaults to 200 milliseconds between each frame. 
        
    :param bands:
        An optional list of either one or three bands to be plotted in the left panel, all of which must exist in 
        `ds`. Defaults to `['red', 'green', 'blue']`. 
        
    :param reflect_stand:
        An optional  integer controlling the brightness of the output image. Low values (< 5000) result in 
        brighter images. Defaults to 5000.
        
    :param title: 
        An optional string or list of strings with a length equal to the number of timesteps in `ds`. This can be
        used to display a static title (using a string), or a dynamic title (using a list) that displays different
        text for each timestep. Defaults to False, which plots no title.
        
    :param show_date:
        An optional boolean that defines whether or not to plot date annotations for each animation frame. Defaults 
        to True, which plots date annotations based on time steps in `ds`.

    :param annotation_kwargs:
        An optional dict of kwargs for controlling the appearance of text annotations in the left panel to pass to the 
        matplotlib `plt.annotate` function (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html). 
        For example, `annotation_kwargs={'fontsize':20, 'color':'red', 'family':'serif'}. By default, text annotations 
        are plotted as white, size 25 mono-spaced font with a 4pt black outline in the top-right of the animation.
        
    :param onebandplot_cbar:
        An optional boolean indicating whether to include a colourbar if `ds` is a one-band array. Defaults to True.
        
    :param onebandplot_kwargs:
        An optional dict of kwargs for controlling the appearance of one-band image arrays in the left panel to pass 
        to matplotlib `plt.imshow` (see https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html for options).
        This only applies if an xarray with a single band is passed to `ds`. For example, a green colour scheme and
        custom stretch could be specified using: `onebandplot_kwargs={'cmap':'Greens`, 'vmin':0.2, 'vmax':0.9}`. 
        By default, one-band arrays are plotted using the 'Greys' cmap with bilinear interpolation.

    :param shapefile_path:
        An optional string or list of strings giving the file paths of shapefiles to overlay on the output animation. 
        The shapefiles must be in the same projection as the input xarray dataset.
        
    :param shapefile_kwargs:
        An optional dict of kwargs to specify the appearance of the shapefile overlay. For example: 
        `shapefile_kwargs = {'linewidth':2, 'edgecolor':'black', 'facecolor':"#00000000"}`

    :param pandasplot_kwargs:
        An optional dict of kwargs to specify the appearance of the right-hand Pandas plot. For example: 
        `pandasplot_kwargs = {'linewidth':2, 'cmap':'viridis'}`

    :param time_dim:
        An optional string allowing you to override the xarray dimension used for time. Defaults to 'time'.
    
    :param x_dim:
        An optional string allowing you to override the xarray dimension used for x coordinates. Defaults to 'x'.
    
    :param y_dim:
        An optional string allowing you to override the xarray dimension used for y coordinates. Defaults to 'y'.  
    """

    # Define function to convert xarray dataset to list of one or three band numpy arrays
    def _ds_to_arrraylist(ds, bands, reflect_stand, time_dim, x_dim, y_dim):   

        array_list = []
        for i, timestep in enumerate(ds[time_dim]):

            # Select single timestep from the data array
            ds_i = ds[{time_dim: i}]

            # Get shape of array
            x = len(ds[x_dim])
            y = len(ds[y_dim])

            if len(bands) == 1:    

                # Create new one band array
                img_toshow = ds_i[bands[0]].values

            else:

                # Create new three band array                
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
        cbbox = inset_axes(ax, '100%', '9.5%', loc = 8, borderpad=0)
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

    # Test if all dimensions exist in dataset
    if time_dim in ds and x_dim in ds and y_dim in ds:
        
        # Get time, x and y dimensions of dataset and calculate width vs height of plot
        timesteps = len(ds[time_dim])    
        width = len(ds[x_dim])
        height = len(ds[y_dim])
        width_ratio = float(width) / float(height)
        height = 10.0 / width_ratio   
        
        # If title is supplied as a string, multiply out to a list with one string per timestep.
        # Otherwise, use supplied list for plot titles.
        if isinstance(title, str) or isinstance(title, bool):
            title_list = [title] * timesteps 
        else:
            title_list = title
            
        # Set up annotation parameters that plt.imshow plotting for single band array images. 
        # The nested dict structure sets default values which can be overwritten/customised by the 
        # manually specified `onebandplot_kwargs`
        onebandplot_kwargs = dict({'cmap':'Greys', 'interpolation':'bilinear'},
                                   **onebandplot_kwargs)         
        
        # Set up annotation parameters that control font etc. The nested dict structure sets default 
        # values which can be overwritten/customised by the manually specified `annotation_kwargs`
        annotation_kwargs = dict({'xy': (1, 1), 'xycoords':'axes fraction', 
                                  'xytext':(-5, -5), 'textcoords':'offset points', 
                                  'horizontalalignment':'right', 'verticalalignment':'top', 
                                  'fontsize':15, 'color':'white', 
                                  'path_effects':[PathEffects.withStroke(linewidth=3, foreground='black')]},
                                  **annotation_kwargs)

        # Define default plotting parameters for the overlaying shapefile(s). The nested dict structure sets 
        # default values which can be overwritten/customised by the manually specified `shapefile_kwargs`
        shapefile_kwargs = dict({'linewidth': 2, 'edgecolor': 'black', 'facecolor': "#00000000"}, 
                                 **shapefile_kwargs) 

        # Define default plotting parameters for the right-hand line plot. The nested dict structure sets 
        # default values which can be overwritten/customised by the manually specified `pandasplot_kwargs`
        pandasplot_kwargs = dict({}, **pandasplot_kwargs) 
        

        ###################
        # Initialise plot #
        ###################
        
        # First test if there is one or three bands, and that all exist in both datasets:
        if ((len(bands) == 3) | (len(bands) == 1)) & all([(b in ds.data_vars) for b in bands]):         
            
            # Import xarrays as lists of three band numpy arrays
            imagelist = _ds_to_arrraylist(ds, bands=bands, reflect_stand=reflect_stand,
                                          time_dim=time_dim, x_dim=x_dim, y_dim=y_dim)
            
            # Set up figure 
            fig, (ax1, ax2) = plt.subplots(ncols=2) 
            fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
            fig.set_size_inches(10.0, height * 0.5, forward=True)
            ax1.axis('off')
            ax2.margins(x=0.01)
            ax2.xaxis.label.set_visible(False)

            # Initialise axesimage objects to be updated during animation, setting extent from dims
            extents = [float(ds[x_dim].min()), float(ds[x_dim].max()), 
                       float(ds[y_dim].min()), float(ds[y_dim].max())]
            im = ax1.imshow(imagelist[0], extent=extents, **onebandplot_kwargs)

            # Initialise right panel and set y axis limits
            line_test = df.plot(ax=ax2, **pandasplot_kwargs)
            ax2.axes.axis(ymin=np.nanmin(df.values), ymax=np.nanmax(df.values) * 1.2)

            # Legend to right panel
            ax2.legend(loc='upper left', bbox_to_anchor=(0, 1), ncol=1, frameon=False) 

            # Initialise annotation objects to be updated during animation
            t = ax1.annotate('', **annotation_kwargs)

            
            #########################
            # Add optional overlays #
            #########################        
            
            # Optionally add shapefile overlay(s) from either string path or list of string paths
            if isinstance(shapefile_path, str):

                shapefile = gpd.read_file(shapefile_path)
                shapefile.plot(**shapefile_kwargs, ax=ax1)
            
            elif isinstance(shapefile_path, list):
        
                # Iterate through list of string paths
                for shapefile in shapefile_path:

                    shapefile = gpd.read_file(shapefile)
                    shapefile.plot(**shapefile_kwargs, ax=ax1) 

            # Optionally add colourbar for one band images
            if (len(bands) == 1) & onebandplot_cbar:                
                _add_colourbar(ax1, im, fontsize=11,
                               vmin=onebandplot_kwargs['vmin'], 
                               vmax=onebandplot_kwargs['vmax'])

            ax1.set_xlim(extents[0],extents[1])
            ax1.set_ylim(extents[2],extents[3])
            ########################################
            # Create function to update each frame #
            ########################################

            # Function to update figure
            def update_figure(frame_i):
     

                ####################
                # Plot image panel #
                ####################  

                # If possible, extract dates from time dimension
                try:

                    # Get human-readable date info (e.g. "16 May 1990")
                    ts = ds[time_dim][{time_dim:frame_i}].dt
                    year = ts.year.item()
                    month = ts.month.item()
                    day = ts.day.item()
                    date_string = '{} {} {}'.format(day, calendar.month_abbr[month], year)
                    
                except:
                    
                    date_string = ds[time_dim][{time_dim:frame_i}].values.item()

                # Create annotation string based on title and date specifications:
                title = title_list[frame_i]
                if title and show_date:
                    title_date = '{}\n{}'.format(date_string, title)
                elif title and not show_date:
                    title_date = '{}'.format(title)
                elif show_date and not title:
                    title_date = '{}'.format(date_string)           
                else:
                    title_date = ''

                # Update left panel with annotation and image
                im.set_array(imagelist[frame_i])
                t.set_text(title_date) 

                
                ########################
                # Plot linegraph panel #
                ########################              
                
                # Create list of artists to return
                artist_list = [im, t]

                # Update right panel with temporal line subset, adding each new line into artist_list
                for i, line in enumerate(line_test.lines):
                    line.set_data(df[df.index <= datetime(year=year, month=month, day=day, hour=23, minute=59)].index,  
                                  df[df.index <= datetime(year=year, month=month, day=day, hour=23, minute=59)].iloc[:,i])
                    artist_list.extend([line])
                    
                # Return the artists set
                return artist_list

            # Nicely space subplots
            fig.tight_layout()
            
            
            ##############################
            # Generate and run animation #
            ##############################

            # Generate animation
            ani = animation.FuncAnimation(fig=fig, func=update_figure, frames=timesteps, interval=interval, blit=True) 

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
    
    else:
        print('At least one x, y or time dimension does not exist in the input dataset. Please use the `time_dim`,' \
              '`x_dim` or `y_dim` parameters to override the default dimension names used for plotting')