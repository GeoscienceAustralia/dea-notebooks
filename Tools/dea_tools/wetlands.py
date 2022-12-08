"""
Functions for working with the Wetlands Insight Tool (WIT)
This is the deafrica version. needs to be rewritten for dea & change fractional cover calculation.
"""

# Import required packages
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import xarray as xr
import matplotlib.pyplot as plt
from skimage import exposure
import matplotlib.animation as animation
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from dask.distributed import progress

import datacube
from datacube.utils import masking
from datacube.utils import geometry

from dea_tools.bandindices import calculate_indices #
from dea_tools.datahandling import load_ard, wofs_fuser # 
from dea_tools.spatial import xr_rasterize # 
from dea_tools.classification import HiddenPrints #


def WIT_drill(
    gdf,
    time,
    min_gooddata=0.85,
    TCW_threshold=-0.035,
    resample_frequency=None,
    export_csv=None,
    dask_chunks=None,
    verbose=False,
    verbose_progress=False,
):
    """
    The Wetlands Insight Tool run onver an extent covered by a polygon.
    This function loads FC, WOfS, and Landsat data, and calculates tasseled
    cap wetness, in order to determine the dominant land cover class
    within a polygon at each satellite observation.

    The output is a pandas dataframe containing a timeseries of the relative
    fractions of each class at each time-step. This forms the input to produce
    a stacked line-plot.

    Last modified: Oct 2021

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The dataframe must only contain a single row,
        containing the polygon you wish to interrograte.
    time : tuple
        a tuple containing the time range over which to run the WIT.
        e.g. ('2015-01' , '2019-12')
    min_gooddata : Float, optional
        A number between 0 and 1 (e.g 0.8) indicating the minimum percentage
        of good quality pixels required for a satellite observation to be loaded
        and therefore included in the WIT plot. This number should, at a minimum,
        be set to 0.80 to limit biases in the result if not resampling the time-series.
        If resampling the data using the parameter `resample_frequency`, then
        setting this number to 0 (or a low float number) is acceptable.
    TCW_threshold : Int, optional
        The tasseled cap wetness threshold, beyond which a pixel will be
        considered 'wet'. Defaults to -0.035.
    resample_frequency : str 
        Option for resampling time-series of input datasets. This option is useful
        for either smoothing the WIT plot, or because the area of analysis is larger
        than a scene width and therefore requires composites. Options include any
        str accepted by `xarray.resample(time=)`. The resampling method used is .max()
    export_csv : str, optional
        To save the returned pandas dataframe as a .csv file, pass a
        a location string (e.g. 'output/results.csv')
    dask_chunks : dict, optional
        To lazily load the datasets using dask, pass a dictionary containing
        the dimensions over which to chunk e.g. {'time':-1, 'x':250, 'y':250}.
    verbose: bool, optional
        If true, print statements are putput detailing the progress of the tool.
    verbose_progress: bool, optional
        For use with Dask progress bar

    Returns
    -------
    df : Pandas.Dataframe
        A pandas dataframe containing the timeseries of relative fractions
        of each land cover class (WOfs, FC, TCW)

    """
    # add geom to dc query dict
    if isinstance(gdf, datacube.utils.geometry._base.Geometry):
        gdf = gpd.GeoDataFrame({'col1':['name'],'geometry':gdf.geom}, crs=gdf.crs)
    geom = geometry.Geometry(geom=gdf.iloc[0].geometry, crs=gdf.crs)
    query = {"geopolygon": geom, "time": time}

    # Create a datacube instance
    dc = datacube.Datacube(app="wetlands insight tool")

    # load landsat 5,7,8 data
    warnings.filterwarnings("ignore")

    if verbose_progress:
        print("Loading Landsat data")
    ds_ls = load_ard(
        dc=dc,
        products=["ls8_sr", "ls7_sr", "ls5_sr"],
        output_crs="epsg:6933",
        min_gooddata=min_gooddata,
        mask_filters=(['opening', 3], ['dilation', 3]),
        measurements=["red", "green", "blue", "nir", "swir_1", "swir_2"],
        dask_chunks=dask_chunks,
        group_by="solar_day",
        resolution=(-30, 30),
        verbose=verbose,
        **query,
    )
    
    # create polygon mask
    mask = xr_rasterize(gdf.iloc[[0]], ds_ls)
    ds_ls = ds_ls.where(mask)
    
    # calculate tasselled cap wetness within masked AOI
    if verbose:
        print("calculating tasseled cap wetness index ")
    
    with HiddenPrints(): #suppres the prints from this func
        tcw = calculate_indices(
            ds_ls, index=["TCW"], normalise=False, satellite_mission="ls", drop=True
        )
    
    if resample_frequency is not None:
        if verbose:
            print('Resampling TCW to '+ resample_frequency)
        tcw = tcw.resample(time=resample_frequency).max()
    
    tcw = tcw.TCW >= TCW_threshold
    tcw = tcw.where(mask, 0)
    tcw = tcw.persist() 

    if verbose:
        print("Loading WOfS layers ")

    wofls = dc.load(
        product="wofs_ls",
        like=ds_ls,
        fuse_func=wofs_fuser,
        dask_chunks=dask_chunks,
        collection_category="T1",
    )

    # boolean of wet/dry
    wofls_wet = masking.make_mask(wofls.water, wet=True)
    
    if resample_frequency is not None:
        if verbose:
            print('Resampling WOfS to '+ resample_frequency)
        wofls_wet = wofls_wet.resample(time=resample_frequency).max()
    
    # mask sure wofs matches other datasets
    wofls_wet = wofls_wet.where(wofls_wet.time == tcw.time)
    
    # apply the polygon mask
    wofls_wet = wofls_wet.where(mask)

    # load Fractional cover
    if verbose:
        print("Loading fractional Cover")

    # load fractional cover
    fc_ds = dc.load(
        product="fc_ls",
        time=time,
        dask_chunks=dask_chunks,
        like=ds_ls,
        measurements=["pv", "npv", "bs"],
        collection_category="T1",
    )
    
    # use wofls mask to cloud mask FC
    clear_and_dry = masking.make_mask(wofls, dry=True).water
    fc_ds = fc_ds.where(clear_and_dry)
    
    if resample_frequency is not None:
        if verbose:
            print('Resampling FC to '+ resample_frequency)
        fc_ds = fc_ds.resample(time=resample_frequency).max()
    
    # mask sure fc matches other datasets
    fc_ds = fc_ds.where(fc_ds.time == tcw.time)

    # mask with polygon
    fc_ds = fc_ds.where(mask)

    # mask with TC wetness
    fc_ds_noTCW = fc_ds.where(tcw == False)

    if verbose:
        print("Generating classification")

    # Cast the dataset to a dataarray
    fc_ds_noTCW = fc_ds_noTCW.to_array(dim="variable", name="fc_ds_noTCW")

    # turn FC array into integer only as nanargmax doesn't
    # seem to handle floats the way we want it to
    fc_int = fc_ds_noTCW.astype("int8")

    # use nanargmax to get the index of the maximum value
    BSPVNPV = fc_int.argmax(dim="variable")
    
    #int dytype remocves NaNs so we need to create mask again
    FC_mask = xr.ufuncs.isfinite(fc_ds_noTCW).all(dim="variable")
    BSPVNPV = BSPVNPV.where(FC_mask)

    # Restack the Fractional cover dataset all together
    # CAUTION:ARGMAX DEPENDS ON ORDER OF VARIABALES IN
    # DATASET. NEED TO ADJUST BELOW DEPENDING ON ORDER OF FC VARIABLES
    
    FC_dominant = xr.Dataset(
        {
            "bs": (BSPVNPV == 2).where(FC_mask),
            "pv": (BSPVNPV == 0).where(FC_mask),
            "npv": (BSPVNPV == 1).where(FC_mask),
        }
    )

    # pixel counts
    pixels = mask.sum(dim=["x", "y"])
    

    if verbose_progress:
        print("Computing wetness")
    tcw_pixel_count = tcw.sum(dim=["x", "y"]).compute()
    
    if verbose_progress:
        print("Computing green veg, dry veg, and bare soil")
    FC_count = FC_dominant.sum(dim=["x", "y"]).compute()
    
    if verbose_progress:
        print("Computing open water")
    wofs_pixels = wofls_wet.sum(dim=["x", "y"]).compute()

    # count percentages
    wofs_area_percent = (wofs_pixels / pixels) * 100
    tcw_area_percent = (tcw_pixel_count / pixels) * 100
    tcw_less_wofs = tcw_area_percent - wofs_area_percent  # wet not wofs

    # Fractional cover pixel count method
    # Get number of FC pixels, divide by total number of pixels per polygon
    # Work out the number of nodata pixels in the data
    BS_percent = (FC_count.bs / pixels) * 100
    PV_percent = (FC_count.pv / pixels) * 100
    NPV_percent = (FC_count.npv / pixels) * 100
    NoData_count = ((
        100 - wofs_area_percent - tcw_less_wofs - PV_percent - NPV_percent - BS_percent
    ) / 100) * pixels

    # re-do percentages but now handling any no-data pixels within polygon
    BS_percent = (FC_count.bs / (pixels - NoData_count)) * 100
    PV_percent = (FC_count.pv / (pixels - NoData_count)) * 100
    NPV_percent = (FC_count.npv / (pixels - NoData_count)) * 100
    wofs_area_percent = (wofs_pixels / (pixels - NoData_count)) * 100
    tcw_area_percent = (tcw_pixel_count / (pixels - NoData_count)) * 100
    tcw_less_wofs = tcw_area_percent - wofs_area_percent
    
    # Sometimes when we resample datastes, WOfS extent can be
    # greater than the wetness extent, thus make negative values == zero
    tcw_less_wofs = tcw_less_wofs.where(tcw_less_wofs>=0, 0) 

    # start setup of dataframe by adding only one dataset
    df = pd.DataFrame(
        data=wofs_area_percent.data,
        index=wofs_area_percent.time.values,
        columns=["wofs_area_percent"],
    )

    # add data into pandas dataframe for export
    df["wet_percent"] = tcw_less_wofs.data
    df["green_veg_percent"] = PV_percent.data
    df["dry_veg_percent"] = NPV_percent.data
    df["bare_soil_percent"] = BS_percent.data

    # round numbers
    df = df.round(2)
    
    # save the csv of the output data used to create the stacked plot for the polygon drill
    if export_csv:
        if verbose:
            print("exporting csv: " + export_csv)
        df.to_csv(export_csv, index_label="Datetime")

    return df


def animated_timeseries_WIT(
    ds,
    df,
    output_path,
    width_pixels=1000,
    interval=200,
    bands=["red", "green", "blue"],
    percentile_stretch=(0.02, 0.98),
    image_proc_func=None,
    title=False,
    show_date=True,
    annotation_kwargs={},
    onebandplot_cbar=True,
    onebandplot_kwargs={},
    shapefile_path=None,
    shapefile_kwargs={},
    pandasplot_kwargs={},
    time_dim="time",
    x_dim="x",
    y_dim="y",
):

    ###############
    # Setup steps #
    ###############

    # Test if all dimensions exist in dataset
    if time_dim in ds and x_dim in ds and y_dim in ds:

        # Test if there is one or three bands, and that all exist in both datasets:
        if ((len(bands) == 3) | (len(bands) == 1)) & all(
            [(b in ds.data_vars) for b in bands]
        ):

            # Import xarrays as lists of three band numpy arrays
            imagelist, vmin, vmax = _ds_to_arrraylist(
                ds,
                bands=bands,
                time_dim=time_dim,
                x_dim=x_dim,
                y_dim=y_dim,
                percentile_stretch=percentile_stretch,
                image_proc_func=image_proc_func,
            )

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
            onebandplot_kwargs = dict(
                {
                    "cmap": "Greys",
                    "interpolation": "bilinear",
                    "vmin": vmin,
                    "vmax": vmax,
                    "tick_colour": "black",
                    "tick_fontsize": 11,
                },
                **onebandplot_kwargs,
            )

            # Use pop to remove the two special tick kwargs from the onebandplot_kwargs dict, and save individually
            onebandplot_tick_colour = onebandplot_kwargs.pop("tick_colour")
            onebandplot_tick_fontsize = onebandplot_kwargs.pop("tick_fontsize")

            # Set up annotation parameters that control font etc. The nested dict structure sets default
            # values which can be overwritten/customised by the manually specified `annotation_kwargs`
            annotation_kwargs = dict(
                {
                    "xy": (1, 1),
                    "xycoords": "axes fraction",
                    "xytext": (-5, -5),
                    "textcoords": "offset points",
                    "horizontalalignment": "right",
                    "verticalalignment": "top",
                    "fontsize": 15,
                    "color": "white",
                    "path_effects": [
                        PathEffects.withStroke(linewidth=3, foreground="black")
                    ],
                },
                **annotation_kwargs,
            )

            # Define default plotting parameters for the overlaying shapefile(s). The nested dict structure sets
            # default values which can be overwritten/customised by the manually specified `shapefile_kwargs`
            shapefile_kwargs = dict(
                {"linewidth": 2, "edgecolor": "black", "facecolor": "#00000000"},
                **shapefile_kwargs,
            )

            # Define default plotting parameters for the right-hand line plot. The nested dict structure sets
            # default values which can be overwritten/customised by the manually specified `pandasplot_kwargs`
            pandasplot_kwargs = dict({}, **pandasplot_kwargs)

            ###################
            # Initialise plot #
            ###################

            # Set up figure
            fig, (ax1, ax2) = plt.subplots(
                ncols=2, gridspec_kw={"width_ratios": [1, 2]}
            )
            fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0.2, hspace=0)
            fig.set_size_inches(10.0, height * 0.5, forward=True)
            ax1.axis("off")
            ax2.margins(x=0.01)
            ax2.xaxis.label.set_visible(False)

            # Initialise axesimage objects to be updated during animation, setting extent from dims
            extents = [
                float(ds[x_dim].min()),
                float(ds[x_dim].max()),
                float(ds[y_dim].min()),
                float(ds[y_dim].max()),
            ]
            im = ax1.imshow(imagelist[0], extent=extents, **onebandplot_kwargs)

            # Initialise right panel and set y axis limits
            # set up color palette
            pal = [
                sns.xkcd_rgb["cobalt blue"],
                sns.xkcd_rgb["neon blue"],
                sns.xkcd_rgb["grass"],
                sns.xkcd_rgb["beige"],
                sns.xkcd_rgb["brown"],
            ]

            # make a stacked area plot
            ax2.stackplot(
                df.index,
                df.wofs_area_percent,
                df.wet_percent,
                df.green_veg_percent,
                df.dry_veg_percent,
                df.bare_soil_percent,
                labels=["open water", "wet", "green veg", "dry veg", "bare soil"],
                colors=pal,
                alpha=0.6,
                **pandasplot_kwargs,
            )

            ax2.legend(loc="lower left", framealpha=0.6)

            df1 = pd.DataFrame(
                {
                    "wofs_area_percent": df.wofs_area_percent,
                    "wet_percent": df.wofs_area_percent + df.wet_percent,
                    "green_veg_percent": df.wofs_area_percent
                    + df.wet_percent
                    + df.green_veg_percent,
                    "dry_veg_percent": df.wofs_area_percent
                    + df.wet_percent
                    + df.green_veg_percent
                    + df.dry_veg_percent,
                    "bare_soil_percent": df.dry_veg_percent
                    + df.green_veg_percent
                    + df.wofs_area_percent
                    + df.wet_percent
                    + df.bare_soil_percent,
                }
            )
            df1 = df1.set_index(df.index)

            line_test = df1.plot(
                ax=ax2, legend=False, color="black", **pandasplot_kwargs
            )

            # set axis limits to the min and max
            ax2.set(xlim=(df.index[0], df.index[-1]), ylim=(0, 100))

            # add a legend and a tight plot box

            ax2.set_title("Fractional Cover, Wetness, and Water")

            # Initialise annotation objects to be updated during animation
            t = ax1.annotate("", **annotation_kwargs)

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

            # After adding shapefile, fix extents of plot
            ax1.set_xlim(extents[0], extents[1])
            ax1.set_ylim(extents[2], extents[3])

            # Optionally add colourbar for one band images
            if (len(bands) == 1) & onebandplot_cbar:
                _add_colourbar(
                    ax1,
                    im,
                    tick_fontsize=onebandplot_tick_fontsize,
                    tick_colour=onebandplot_tick_colour,
                    vmin=onebandplot_kwargs["vmin"],
                    vmax=onebandplot_kwargs["vmax"],
                )

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
                    ts = ds[time_dim][{time_dim: frame_i}].dt
                    year = ts.year.item()
                    month = ts.month.item()
                    day = ts.day.item()
                    date_string = "{} {} {}".format(
                        day, calendar.month_abbr[month], year
                    )

                except:

                    date_string = ds[time_dim][{time_dim: frame_i}].values.item()

                # Create annotation string based on title and date specifications:
                title = title_list[frame_i]
                if title and show_date:
                    title_date = "{}\n{}".format(date_string, title)
                elif title and not show_date:
                    title_date = "{}".format(title)
                elif show_date and not title:
                    title_date = "{}".format(date_string)
                else:
                    title_date = ""

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

                    # Clip line data to current time, and get x and y values
                    y = df1[
                        df1.index
                        <= datetime(year=year, month=month, day=day, hour=23, minute=59)
                    ].iloc[:, i]
                    x = df1[
                        df1.index
                        <= datetime(year=year, month=month, day=day, hour=23, minute=59)
                    ].index

                    # Plot lines after stripping NaNs (this produces continuous, unbroken lines)
                    line.set_data(x[y.notnull()], y[y.notnull()])
                    artist_list.extend([line])

                # Return the artists set
                return artist_list

            # Nicely space subplots
            fig.tight_layout()

            ##############################
            # Generate and run animation #
            ##############################

            # Generate animation
            ani = animation.FuncAnimation(
                fig=fig,
                func=update_figure,
                frames=timesteps,
                interval=interval,
                blit=True,
            )

            # Export as either MP4 or GIF
            if output_path[-3:] == "mp4":
                print("    Exporting animation to {}".format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0)

            elif output_path[-3:] == "wmv":
                print("    Exporting animation to {}".format(output_path))
                ani.save(
                    output_path,
                    dpi=width_pixels / 10.0,
                    writer=animation.FFMpegFileWriter(
                        fps=1000 / interval, bitrate=4000, codec="wmv2"
                    ),
                )

            elif output_path[-3:] == "gif":
                print("    Exporting animation to {}".format(output_path))
                ani.save(output_path, dpi=width_pixels / 10.0, writer="imagemagick")

            else:
                print("    Output file type must be either .mp4, .wmv or .gif")

        else:
            print(
                "Please select either one or three bands that all exist in the input dataset"
            )

    else:
        print(
            "At least one x, y or time dimension does not exist in the input dataset. Please use the `time_dim`,"
            "`x_dim` or `y_dim` parameters to override the default dimension names used for plotting"
        )


# Define function to convert xarray dataset to list of one or three band numpy arrays


def _ds_to_arrraylist(
    ds, bands, time_dim, x_dim, y_dim, percentile_stretch, image_proc_func=None
):
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
            img_toshow = exposure.rescale_intensity(
                ds_i[bands[0]].values, in_range=(p_low, p_high), out_range="image"
            )

        else:

            # Create new three band array
            rawimg = np.zeros((y, x, 3), dtype=np.float32)

            # Add xarray bands into three dimensional numpy array
            for band, colour in enumerate(bands):

                rawimg[:, :, band] = ds_i[colour].values

            # Stretch contrast using percentile values
            img_toshow = exposure.rescale_intensity(
                rawimg, in_range=(p_low, p_high), out_range=(0, 1.0)
            )

            # Optionally image processing
            if image_proc_func:

                img_toshow = image_proc_func(img_toshow).clip(0, 1)

        array_list.append(img_toshow)

    return array_list, p_low, p_high


def _add_colourbar(
    ax, im, vmin, vmax, cmap="Greys", tick_fontsize=15, tick_colour="black"
):
    """
    Add a nicely formatted colourbar to an animation panel
    """

    # Add colourbar
    axins2 = inset_axes(ax, width="97%", height="4%", loc=8, borderpad=1)
    plt.gcf().colorbar(
        im, cax=axins2, orientation="horizontal", ticks=np.linspace(vmin, vmax, 3)
    )
    axins2.xaxis.set_ticks_position("top")
    axins2.tick_params(axis="x", colors=tick_colour, labelsize=tick_fontsize)

    # Justify left and right labels to edge of plot
    axins2.get_xticklabels()[0].set_horizontalalignment("left")
    axins2.get_xticklabels()[-1].set_horizontalalignment("right")
    labels = [item.get_text() for item in axins2.get_xticklabels()]
    labels[0] = "  " + labels[0]
    labels[-1] = labels[-1] + "  "


if __name__ == "__main__":
    # print that we are running the testing
    print("Testing..")
    # import doctest to test our module for documentation
    import doctest

    doctest.testmod()
    print("Testing done")
