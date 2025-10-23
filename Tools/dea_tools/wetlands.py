# wetlands.py
"""
This module is for processing DEA wetlands data, including Spatial WIT.

License: The code in this notebook is licensed under the Apache
License,Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0).
Digital Earth Australia data is licensed under the Creative Commons
by Attribution 4.0 license
(https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open
Data Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the
GIS Stack Exchange
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube)using
the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, file one on
GitHub: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Last modified: July 2025
"""


import datetime

import itertools
import os
import shutil
import warnings

import geopandas as gpd
import imageio
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xarray as xr

from dea_tools.bandindices import calculate_indices
from dea_tools.dask import create_local_dask_cluster
from dea_tools.datahandling import load_ard
from dea_tools.spatial import xr_rasterize

# Create local dask cluster to improve data load time
client = create_local_dask_cluster(return_client=True)

# disable DeprecationWarning for chained assignments in conversion to
# datetime format
pd.options.mode.chained_assignment = None  # default='warn'


def normalise_wit(polygon_base_df):
    """
    This function is to normalise the Fractional Cover vegetation
    components so users can choose to display the WIT plot in a more
    readable way. Normalising vegetation components so they total to 1.
    Normalised values are returned as additional columns.

    Last modified: July 2023

    Parameters
    ----------
    polygon_base_df : pandas DataFrame with columns:
    ['date',
    'pv',
    'npv',
    'bs',
    'wet',
    'water']

    Returns
    -------
    polygon_base_df with columns:
    ['index',
     'date',
     'pv',
     'npv',
     'bs',
     'wet',
     'water',
     'veg_areas',
     'overall_veg_num',
     'norm_bs',
     'norm_pv',
     'norm_npv']

    Example
    --------

    A polygon has 11 pixels

    [cloud][water][wet][wet][wet][wet][wet][wet][wet][wet][vegetation]
      |      |        |                                        |
      |      |        |                                        |
      |      |        |__> wet = 8/10 = 80%                    |__> pv/npv/bs == 1/10 = 10%
      |      |
      |      |__> water = 1/10 = 10%
      |
      |__> pc_missing = 1/11 ~+ 9.1%

    The vegetation pixel relative np, npv, and bs values

     [vegetation]
          |
          |__> [pv] [npv] [bs]
               [ 5] [  4] [ 2]

    Assume vegetation relative values are:

    water = 0.1
    wet = 0.8

    pv = 0.05
    npv = 0.04
    bs = 0.02

    vegetation_area = 1 - water - wet

    vegetation_overall_value = pv + npv + bs

    print(f"The pv is {pv} \nThe npv is {npv} \nThe bs is {bs}
    \nThe overall number is {water + wet + pv + npv + bs}")

    The pv is 0.05
    The npv is 0.04
    The bs is 0.02
    The overall number is 1.01

    The overall number is greater than 1. Let us normalise the result.
    The water and wet are pixel classification result, so we should
    not touch them.

    pv = pv/vegetation_overall_value*vegetation_area
    npv = npv/vegetation_overall_value*vegetation_area
    bs = bs/vegetation_overall_value*vegetation_area

    print(f"The normalised pv is {pv} \nThe normalised npv is {npv}
    \nThe normalised bs is {bs} \nThe normalised overall number is
    {water + wet + pv + npv + bs}")

    The normalised pv is 0.04545454545454545
    The normalised npv is 0.036363636363636355
    The normalised bs is 0.018181818181818177
    The normalised overall number is 1.0

    """

    # ignore high pixel missing timestamp result
    polygon_base_df = polygon_base_df.dropna(subset=["bs"])

    # 1. compute the expected vegetation area total size: 1 - water (%) - wet (%)
    polygon_base_df.loc[:, "veg_areas"] = 1 - polygon_base_df["water"] - polygon_base_df["wet"]

    # 2. normalise the vegetation values based on vegetation size (to handle FC values more than 100 issue)
    # WARNNING: Not touch the water and wet, cause they are pixel classification result
    polygon_base_df.loc[:, "overall_veg_num"] = polygon_base_df["pv"] + polygon_base_df["npv"] + polygon_base_df["bs"]

    # 3. if the overall_veg_num is 0, no need to normalize veg area
    norm_veg_index = polygon_base_df["overall_veg_num"] != 0

    for band in ["bs", "pv", "npv"]:
        polygon_base_df.loc[:, "norm_" + band] = polygon_base_df.loc[:, band]
        polygon_base_df.loc[norm_veg_index, "norm_" + band] = (
            polygon_base_df.loc[norm_veg_index, band]
            / polygon_base_df.loc[norm_veg_index, "overall_veg_num"]
            * polygon_base_df.loc[norm_veg_index, "veg_areas"]
        )

    # convert the string to Python datetime format, easy to do display the result in PNG
    polygon_base_df.loc[:, "date"] = pd.to_datetime(polygon_base_df["date"])

    polygon_base_df.reset_index(inplace=True)

    return polygon_base_df


def generate_low_quality_data_periods(df):
    """
    This function generates low quality data periods, including the SLC off period: https://www.usgs.gov/faqs/what-landsat-7-etm-slc-data
    and periods with an observation density of less than four observations within a twelve month (365 days) period.
    Off value is 100 where there is low data quality and 0 for good data.

    Last modified: July 2023

    Parameters
    ----------
    df : pandas DataFrame with columns including:
    ['date']

    Returns
    -------
    df : pandas DataFrame with additional column:
    ['off_value']

    """

    # default: all data points are good
    df.loc[:, "off_value"] = 0

    # Add the first no-data times (SLC-off only)
    LS5_8_gap_start = datetime.datetime(2011, 11, 1)
    LS5_8_gap_end = datetime.datetime(2013, 4, 1)

    df.loc[
        df[(df["date"] >= LS5_8_gap_start) & (df["date"] <= LS5_8_gap_end)].index,
        "off_value",
    ] = 100

    # periods with an observation density of less than four observations within a twelve month (365 days) period
    for i in range(3, len(df) - 3):
        # can change to another threshold (like: 100 days) to test dynamic no-data-period display
        if ((df.loc[i + 3, "date"] - df.loc[i, "date"]).days) > 365:
            df.loc[
                df[(df["date"] >= df.loc[i, "date"]) & (df["date"] <= df.loc[i + 3, "date"])].index,
                "off_value",
            ] = 100

    return df


def display_wit_stack_with_df(
    polygon_base_df,
    polygon_name="your_wetland_name",
    png_name="your_file_name",
    width=32,
    height=6,
    x_axis_labels="years",
):
    """
    This functions produces WIT plots. Function displays a stack plot and saves as a png.

    Last modified: July 2023

    Parameters
    ----------
    polygon_base_df : pandas DataFrame with columns including:
    ['date',
     'wet',
     'water',
     'norm_bs',
     'norm_pv',
     'norm_npv']
     polygon_name : string
     png_name : string
     x_axis_labels : string with options of "years" or "months"
     to set either years or months on the x axis as labels


    """

    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["text.usetex"] = False

    fig = plt.figure()
    fig.set_size_inches(width, height)
    ax = fig.add_subplot(111)
    ax.autoscale(enable=True)

    pal = [
        sns.xkcd_rgb["cobalt blue"],
        sns.xkcd_rgb["neon blue"],
        sns.xkcd_rgb["grass"],
        sns.xkcd_rgb["beige"],
        sns.xkcd_rgb["brown"],
    ]

    plt.title(
        f"Percentage of area dominated by WOfS, Wetness, Fractional Cover for\n {polygon_name}",
        fontsize=16,
    )

    ax.stackplot(
        polygon_base_df["date"],
        polygon_base_df["water"] * 100,
        polygon_base_df["wet"] * 100,
        polygon_base_df["norm_pv"] * 100,
        polygon_base_df["norm_npv"] * 100,
        polygon_base_df["norm_bs"] * 100,
        colors=pal,
        alpha=0.7,
    )

    # manually change the legend display order
    legend = ax.legend(
        ["open water", "wet", "green veg", "dry veg", "bare soil"][::-1],
        loc="lower left",
    )
    handles = legend.legend_handles

    for i, handle in enumerate(handles):
        handle.set_facecolor(pal[::-1][i])
        handle.set_alpha(0.7)

    # setup the display ranges
    ax.set_ylim(0, 100)
    ax.set_xlim(polygon_base_df["date"].min(), polygon_base_df["date"].max())

    # add a new column: 'off_value' based on low quality data setting
    polygon_base_df = generate_low_quality_data_periods(polygon_base_df)

    ax.fill_between(
        polygon_base_df["date"],
        0,
        100,
        where=polygon_base_df["off_value"] == 100,
        color="white",
        alpha=0.5,
        hatch="//",
    )

    if x_axis_labels == "years":
        # modify the xaxis settings
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    if x_axis_labels == "months":
        # modify the xaxis settings
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
        # Rotates and right-aligns the x labels so they don't crowd each other.
        for label in ax.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")

    x_label_text = "The Fractional Cover algorithm developed by the Joint Remote Sensing Research Program and\n the Water Observations from Space algorithm developed by Geoscience Australia are used in the production of this data"

    ax.set_xlabel(x_label_text, style="italic")

    plt.savefig(f"{png_name}.png", bbox_inches="tight")
    plt.show()

    plt.close(fig)


def WIT_drill(
    gdf,
    time,
    export_csv=None,
    dask_chunks=None,
    verbose=False,
    verbose_progress=False,
):
    """
    Runs the Wetlands Insight Tool over a polygon. The code is based on the DEA Wetlands
    Insight Tool notebook.
    This function loads FC, WOs, and Landsat Data, and calculates Tasseled Cap Wetness, in
    order to summarise how the different classes have changed over time.

    The output is an Xarray dataset and a pandas dataframe containing a timeseries of the
    normalised relative fractions of each class at each time-step. This forms the input to
    produce a stacked line plot.

    Last modified March 2025

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The dataframe must only contain a single row containing the polygon you wish to
        interrogate
    time : tuple
        A tuple containing the time range over which to run the WIT.
        e.g. ("2014-01-01", "2015-01-01")
    export_csv : string, optional
        To save the returned pandas dataframe as a .csv file, pass a location string (e.g.
        'output/results.csv')
    dask_chunks : dict, optional
        To lazily load the datasets using dask, pass a dictionary containing the dimensions
        over which to chunk e.g. {'time':1, 'x':2048, 'y':2048}.
    verbose : bool, optional
        If true, print statements are outputted detailing the progress of the tool.
    verbose_progress : bool, optional
        For use with Dask progress bar.

    Returns
    -------
    ds_wit : xarray.Dataset
        An xarray dataset containing values for each cover class (open water, wet, pv, npv, bs).
    polygon_base_df : pandas.DataFrame
        A DataFrame containing the normalised timeseries of relative fractions of each cover
        class (open water, wet, pv, npv, bs).

    """
    # Attempt to import datacube and raise an error if not available
    try:
        import datacube
    except ImportError as e:
        raise ImportError(
            "`datacube` is required for `WIT_drill`. "
            "Please install DEA Tools with the `[datacube]` extra, e.g.: "
            "`pip install dea-tools[datacube]`"
        ) from e

    # Connect to the datacube
    dc = datacube.Datacube(app="WIT_drill")

    # load landsat 5,7,8 data
    warnings.filterwarnings("ignore")

    # load wetland polygon and specify the coordinate reference system of the polygon
    if isinstance(gdf, datacube.utils.geometry._base.Geometry):
        gdf = gpd.GeoDataFrame({"col1": ["name"], "geometry": gdf.geom}, crs=gdf.crs)
    gpgon = datacube.utils.geometry.Geometry(gdf.geometry[0], crs=gdf.crs)

    # Define which spectral bands are being used in the analysis
    bands = [f"nbart_{band}" for band in ("blue", "green", "red", "nir", "swir_1", "swir_2")]

    if verbose_progress:
        print("Loading Landsat data")

    # Load Landsat 5, 7 and 8 data. Not including Landsat 7 SLC off period (31-05-2003 to 06-04-2022)
    ds_ls = load_ard(
        dc,
        products=["ga_ls8c_ard_3", "ga_ls7e_ard_3", "ga_ls5t_ard_3"],
        ls7_slc_off=False,
        measurements=bands,
        geopolygon=gpgon,
        output_crs="EPSG:3577",
        resolution=(-30, 30),
        resampling={"fmask": "nearest", "*": "bilinear"},
        time=time,
        group_by="solar_day",
        dask_chunks={"time": 1, "x": 2048, "y": 2048},
    )

    # Load into memory using Dask
    ds_ls.load()

    # Load Water Observations dataset into the same spatial grid and resolution of the loaded Landsat dataset
    ds_wo = dc.load(
        "ga_ls_wo_3",
        resampling="nearest",
        group_by="solar_day",
        like=ds_ls,
        dask_chunks={"time": 1, "x": 2048, "y": 2048},
    )

    # Load Fractional Cover dataset into the same spatial grid and resolution of the loaded Landsat dataset
    ds_fc = dc.load(
        "ga_ls_fc_3",
        resampling="nearest",
        group_by="solar_day",
        like=ds_ls,
        dask_chunks={"time": 1, "x": 2048, "y": 2048},
    )

    # Load data into memory
    ds_wo.load()
    ds_fc.load()

    # Locate and remove any observations which aren't in all three datasets
    missing = set()
    for t1, t2 in itertools.product([ds_fc.time.values, ds_wo.time.values, ds_ls.time.values], repeat=2):
        missing_ = set(t1) - set(t2)
        missing |= missing_

    ds_fc = ds_fc.sel(time=[t for t in ds_fc.time.values if t not in missing])
    ds_ls = ds_ls.sel(time=[t for t in ds_ls.time.values if t not in missing])
    ds_wo = ds_wo.sel(time=[t for t in ds_wo.time.values if t not in missing])

    # Calculate Tasseled Cap Wetness from the Landsat data
    tcw = calculate_indices(
        ds_ls,
        index="TCW",
        collection="ga_ls_3",
        normalise=False,
        drop=True,
        inplace=False,
    )

    # Divide Fractional Cover by 100 to keep them in [0,1]. Keeps data types the same in
    # the output raster
    bs = ds_fc.bs / 100
    pv = ds_fc.pv / 100
    npv = ds_fc.npv / 100

    # Generate the WIT raster bands by creating an empty dataset called `output_rast` and
    # populate with values from input datasets
    rast_names = ["pv", "npv", "bs", "wet", "water"]
    output_rast = {n: xr.zeros_like(bs) for n in rast_names}

    output_rast["bs"].values[:] = bs
    output_rast["pv"].values[:] = pv
    output_rast["npv"].values[:] = npv

    # Masking

    # Rasterise the shapefile where gdf is the vector data and pv is the xarray template
    poly_raster = xr_rasterize(gdf, pv) > 0

    # Mask includes No data, Non contiguous data, Cloud shadow, Cloud, and water.
    # See https://knowledge.dea.ga.gov.au/notebooks/DEA_products/DEA_Water_Observations/#Understanding-WOs-bit-flags
    # for more detail.
    mask = (ds_wo.water & 0b01100011) == 0
    mask &= poly_raster

    # Set open water to water present and classified as water as per Water Observations and bit flags
    open_water = ds_wo.water & (1 << 7) > 0

    # Thresholding

    # Set wet pixels where not masked and above threshold of -350
    wet = tcw.where(mask).TCW > -350

    # Adding wet and water values to output raster

    # TCW
    output_rast["wet"].values[:] = wet.values.astype(float)
    for name in rast_names[:3]:
        output_rast[name].values[wet.values] = 0

    # WO
    output_rast["water"].values[:] = open_water.values.astype(float)
    for name in rast_names[:4]:
        output_rast[name].values[open_water.values] = 0

    # Masking again
    ds_wit = xr.Dataset(output_rast).where(mask)

    # Calculate percentage missing
    pc_missing = (~mask).where(poly_raster).mean(dim=["x", "y"])

    # Mask entire observations where the polygon is more than 10% masked
    ds_wit = ds_wit.where(pc_missing < 0.1)

    # Normalise Fractional Cover Values in WIT result

    # Convert ds_wit: xarray.Dataset to polygon_base_df: pandas.DataFrame
    polygon_base_df = pd.DataFrame()
    polygon_base_df["date"] = ds_wit.time.values

    for band in rast_names:
        polygon_base_df[band] = ds_wit[band].mean(dim=["x", "y"])

    polygon_base_df = normalise_wit(polygon_base_df)

    # Create WIT comma-separated values (CSV) output file
    if export_csv:
        polygon_base_df = polygon_base_df.drop("index", axis=1)
        polygon_base_df.to_csv(export_csv, index_label="date")

    return ds_wit, polygon_base_df


def classify_pixel(pv, npv, bs):
    """
    This function sorts the fractional cover values into their classes to be used in Spatial WIT.

    Last modified March 2025

    Parameters
    ----------
    pv : array
        Array containing values for the photosynthetic (green) vegetation class.
    npv : array
        Array containing values for the non-photosynthetic (dry) vegetation class.
    bs : array
        Array containing values for the base soil class.

    Returns
    -------
    integer
        Integer values to assign each of the fractional cover classes (https://knowledge.dea.ga.gov.au/data/product/dea-fractional-cover-landsat/).

    """
    if pv > 2 / 3:
        return 8  # pv
    if npv > 2 / 3:
        return 0  # ng
    if bs > 2 / 3:
        return 4  # bs
    if npv > 1 / 3 and bs > 1 / 3 and pv < 1 / 3:
        return 1  # ng_bs
    if npv > 1 / 3 and pv > 1 / 3 and bs < 1 / 3:
        return 3  # ng_pv
    if npv > 1 / 3 and pv < 1 / 3 and bs < 1 / 3:
        return 2  # ng_mix
    if bs > 1 / 3 and pv > 1 / 3 and npv < 1 / 3:
        return 6  # bs_pv
    if bs > 1 / 3 and pv < 1 / 3 and npv < 1 / 3:
        return 5  # bs_mix
    if pv > 1 / 3 and npv < 1 / 3 and bs < 1 / 3:
        return 7  # pv_mix
    return -1


def spatial_wit(ds, wetland_name):
    """
    Takes Wetlands Insight Tool classifications and represents them in a spatial way. The
    same caveats for those classifications apply (see Dunn et al., 2023 and DEA
    Wetlands Insight Tool notebook). The water and wet classes are binary and the
    vegetation fractional cover classes are percentages per pixel, with the spatial
    representation scaled accordingly.

    Last modified: March 2025

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray dataset containing values for each cover class (open water, wet, pv, npv, bs).

    wetland_name : string
        Value to be used when naming the output files.

    Returns
    -------
    output_path :
        File path where the GIF animation will be saved.


    """
    # Remove time steps where all values are missing (i.e. NaNs)
    ds = ds.dropna(dim="time", how="all")

    # Calculate the sum of the fractional cover values for pv, npv and bs then normalise
    # the values for each class
    fraction_sum = ds["pv"] + ds["npv"] + ds["bs"]
    ds["pv"] = ds["pv"] / fraction_sum
    ds["npv"] = ds["npv"] / fraction_sum
    ds["bs"] = ds["bs"] / fraction_sum

    # Apply the classification function to the dataset across all time, y, x
    fc_class = xr.apply_ufunc(
        classify_pixel,
        ds["pv"],
        ds["npv"],
        ds["bs"],
        vectorize=True,
    )

    fc_class = fc_class.where(fc_class != -1, np.nan)

    # Add the new classification band to the dataset
    ds["fc_class"] = fc_class

    # Make a new band called wetland that combines all the fractional cover classes
    # with the water and wet classes
    # i.e. water == 10, wet == 9, all other areas retain original FC class
    wetland = ds["fc_class"].where((ds["water"] == 0) | ds["water"].isnull(), 10)
    ds["wetland"] = wetland
    wetland = ds["wetland"].where((ds["wet"] == 0) | ds["wet"].isnull(), 9)
    ds["wetland"] = wetland

    # Define labels for each class
    class_labels = [
        "dry veg",  # ng
        "dry veg and bare mix",  # ng_bs
        "dry mix",  # ng_mix
        "dry veg and green veg",  # ng_pv
        "bare soil",  # bs
        "bare soil mix",  # bs_mix
        "bare soil and green veg",  # bs_pv
        "green veg mix",  # pv_mix
        "green veg",  # pv
        "wet",
        "water",
    ]

    # Define the colormap with your custom colors
    cmap = mcolors.ListedColormap([
        "#F1E8C9",  # ng
        "#C0AB86",  # ng_bs
        "#D6D2A7",  # ng_mix
        "#BCD495",  # ng_pv
        "#93724C",  # bs
        "#9C895D",  # bs_mix
        "#8F9C5C",  # bs_pv
        "#9DBD74",  # pv_mix
        "#8CC46B",  # pv
        "#6ce6f8",  # wet
        "#676dca",  # water
    ])

    # Create a BoundedNorm to ensure correct mapping of data to the colormap
    norm = mcolors.Normalize(vmin=0, vmax=10)

    # Create a directory to save the frames
    os.makedirs("deawetlands_outputs", exist_ok=True)

    # Clean the input name to remove spaces
    wetland_name = wetland_name.replace(" ", "_")

    # Save all the time steps

    for t in ds.time:
        wetland_time_step = ds["wetland"].sel(time=t)
        date_str = str(t.values)[:10]  # Extract date as string
        wetland_time_step.rio.to_raster(f"deawetlands_outputs/{wetland_name}_{date_str}.tif")

    # Make one big plot

    num_time_steps = ds.sizes["time"]

    # Set the number of columns as the number of time steps if less than 10
    num_columns = min(num_time_steps, 10)

    # Calculate the number of rows
    num_rows = (num_time_steps + num_columns - 1) // num_columns

    time_step = ds["wetland"].isel(time=0)
    height, width = time_step.shape
    fig, axes = plt.subplots(num_rows, num_columns, figsize=(8 * num_columns * width / height, 8 * num_rows))

    if num_rows == 1:
        axes = axes.reshape(1, num_columns)
    elif num_columns == 1:
        axes = axes.reshape(num_rows, 1)

    # Hide any unused axes
    for i in range(num_rows * num_columns):
        if i >= num_time_steps:
            fig.delaxes(axes.flatten()[i])

    # Plot time steps
    for t in range(num_time_steps):
        time_step = ds["wetland"].isel(time=t)
        time_ns = ds["time"].isel(time=t).values.item()
        time_date = pd.to_datetime(time_ns, unit="ns")
        time_date_str = time_date.strftime("%d-%m-%Y")
        row_idx = t // num_columns
        col_idx = t % num_columns
        time_step.plot.imshow(
            cmap=cmap,
            norm=norm,
            ax=axes[row_idx, col_idx],  # Assign subplot
            add_colorbar=False,  # Avoid multiple colorbars
        )
        axes[row_idx, col_idx].set_aspect("auto")  # keep aspect
        axes[row_idx, col_idx].set_title(f"{time_date_str}")

    plt.tight_layout()
    plt.savefig(f"{wetland_name}_time_steps.png", dpi=72)

    # Make a gif

    # loop through each time step, creating and saving a frame
    num_time_steps = ds.sizes["time"]
    frames = []

    for t in range(num_time_steps):
        time_step = ds["wetland"].isel(time=t)
        height, width = time_step.shape
        fig, ax = plt.subplots(figsize=(8, 8 * height / width))  # dynamic aspect ratio

        time_ns = ds["time"].isel(time=t).values.item()
        time_date = pd.to_datetime(time_ns, unit="ns")
        time_date_str = time_date.strftime("%d-%m-%Y")

        time_step.plot.imshow(
            cmap=cmap,
            norm=norm,
            ax=ax,
            add_colorbar=False,  # Avoid multiple colorbars
            # interpolation='none'
        )
        ax.set_aspect("auto")  # keep aspect
        plt.title(f"Time:{time_date_str}")

        # Rotates and right-aligns the x labels so they don't crowd each other.
        for label in ax.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")

        # Save the frame
        frame_path = f"deawetlands_outputs/{wetland_name}_{time_date_str}.png"
        plt.savefig(frame_path, bbox_inches="tight")
        frames.append(frame_path)
        plt.close(fig)

    # make the gif
    output_path = f"{wetland_name}_animation.gif"
    with imageio.get_writer(output_path, mode="I", duration=0.7, loop=0) as writer:
        for frame_path in frames:
            image = imageio.imread(frame_path)
            writer.append_data(image)

    # print("GIF saved as 'wetland_animation.gif'")

    # clean up
    # for frame_path in frames:
    #    os.remove(frame_path)
    # shutil.rmtree("frames")

    return output_path