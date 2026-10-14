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
# import shutil
import warnings
from dataclasses import dataclass

import geopandas as gpd
# import imageio 
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import rioxarray # added
import xarray as xr
from matplotlib.patches import Patch # added
from odc.geo.geom import Geometry

from dea_tools.bandindices import calculate_indices
from dea_tools.dask import create_local_dask_cluster
from dea_tools.datahandling import load_ard
from dea_tools.spatial import xr_rasterize

# disable DeprecationWarning for chained assignments in conversion to
# datetime format
pd.options.mode.chained_assignment = None  # default='warn'

@dataclass(frozen=True)
class WITScheme:
    """
    Class codes, labels and colours for a spatial WIT classification.

    The position of a label in `labels` is its class code, so `labels[3]`
    is the label for pixels with value 3 in the 'wetland' band.
    """

    name: str
    labels: tuple
    colors: tuple

    @property
    def codes(self):
        return tuple(range(len(self.labels)))

    @property
    def cmap(self):
        return mcolors.ListedColormap(self.colors)

    @property
    def norm(self):
        n = len(self.colors)
        return mcolors.BoundaryNorm(np.arange(n + 1) - 0.5, n)

    @property
    def legend_handles(self):
        return [Patch(facecolor=c, label=l)
                for c, l in zip(self.colors, self.labels)]

    def _bary(self, npv, bs, pv):
        """Barycentric (npv, bs, pv) to cartesian, with npv at the apex."""
        top = np.array([0.5, np.sqrt(3) / 2])
        left = np.array([0.0, 0.0])
        right = np.array([1.0, 0.0])
        return npv * top + bs * left + pv * right

    def draw_legend(self, ax, orientation="horizontal"):
        """
        Draw the scheme's classes on the given axes.

        The simple scheme is drawn as a row or column of labelled swatches.
        The detailed scheme is drawn as a ternary diagram, which shows how the
        nine cover classes divide the space of possible fractional cover
        mixes, with wet and water as separate swatches — they are not
        fractional and override the cover class where present.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes to draw into. Its ticks and frame are removed.
        orientation : {"horizontal", "vertical"}, optional
            Layout to use. "horizontal" suits a wide strip below a figure;
            "vertical" suits a narrow or roughly square cell.

        Returns
        -------
        matplotlib.axes.Axes
        """
        import matplotlib.patches as mpatches

        if orientation not in ("horizontal", "vertical"):
            raise ValueError(
                f"orientation must be 'horizontal' or 'vertical', got {orientation!r}"
            )

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        if self.name == "simple":
            if orientation == "horizontal":
                for i, (label, color) in enumerate(zip(self.labels, self.colors)):
                    ax.add_patch(
                        mpatches.Rectangle(
                            (i, 0), 0.25, 0.25, facecolor=color,
                            edgecolor="black", linewidth=0.5,
                        )
                    )
                    ax.text(i + 0.33, 0.125, label,
                            ha="left", va="center", fontsize=11)
                ax.set_xlim(-0.1, len(self.labels))
                ax.set_ylim(-0.15, 0.4)
            else:
                for i, (label, color) in enumerate(zip(self.labels, self.colors)):
                    y = -i * 0.3
                    ax.add_patch(
                        mpatches.Rectangle(
                            (0, y), 0.22, 0.22, facecolor=color,
                            edgecolor="black", linewidth=0.5,
                        )
                    )
                    ax.text(0.3, y + 0.11, label,
                            ha="left", va="center", fontsize=11)
                ax.set_xlim(-0.1, 2.0)
                ax.set_ylim(-0.3 * len(self.labels) + 0.05, 0.3)
            ax.set_aspect("equal")
            return ax

        # Detailed: nine regions in (npv, bs, pv) barycentric coordinates.
        t = 1 / 3
        regions = {
            0: [(1, 0, 0), (2 * t, t, 0), (2 * t, 0, t)],                    # dry veg
            4: [(0, 1, 0), (t, 2 * t, 0), (0, 2 * t, t)],                    # bare soil
            8: [(0, 0, 1), (t, 0, 2 * t), (0, t, 2 * t)],                    # green veg
            1: [(2 * t, t, 0), (t, 2 * t, 0), (t, t, t), (2 * t, t, 0)],     # dry & bare
            3: [(2 * t, 0, t), (t, 0, 2 * t), (t, t, t), (2 * t, 0, t)],     # dry & green
            6: [(0, 2 * t, t), (0, t, 2 * t), (t, t, t), (0, 2 * t, t)],     # bare & green
            2: [(2 * t, t, 0), (2 * t, 0, t), (t, t, t)],                    # dry mix
            5: [(t, 2 * t, 0), (0, 2 * t, t), (t, t, t)],                    # bare mix
            7: [(t, 0, 2 * t), (0, t, 2 * t), (t, t, t)],                    # green mix
        }

        for code, corners in regions.items():
            xy = np.array([self._bary(*c) for c in corners])
            ax.add_patch(
                mpatches.Polygon(
                    xy, facecolor=self.colors[code],
                    edgecolor="black", linewidth=0.5,
                )
            )

        for corner, label, ha, va in [
            ((1, 0, 0), self.labels[0], "center", "bottom"),
            ((0, 1, 0), self.labels[4], "right", "top"),
            ((0, 0, 1), self.labels[8], "left", "top"),
        ]:
            x, y = self._bary(*corner)
            ax.text(x, y + (0.04 if va == "bottom" else -0.04), label,
                    ha=ha, va=va, fontsize=10)

        # Wet and water are not fractional, so they sit outside the triangle.
        for i, code in enumerate([9, 10]):
            y = 0.55 - i * 0.16
            ax.add_patch(
                mpatches.Rectangle(
                    (1.12, y), 0.12, 0.09, facecolor=self.colors[code],
                    edgecolor="black", linewidth=0.5,
                )
            )
            ax.text(1.28, y + 0.045, self.labels[code],
                    ha="left", va="center", fontsize=10)

        ax.set_xlim(-0.25, 1.75)
        ax.set_ylim(-0.1, 1.05)
        ax.set_aspect("equal")
        return ax
        
WIT_SCHEMES = {
    "simple": WITScheme(
        name="simple",
        labels=("dry veg", "bare soil", "green veg", "wet", "water"),
        colors=("#F1E8C9", "#93724C", "#8CC46B", "#6CE6F8", "#676DCA"),
    ),
    "detailed": WITScheme(
        name="detailed",
        labels=(
            "dry veg",                 # 0  ng
            "dry veg and bare mix",    # 1  ng_bs
            "dry mix",                 # 2  ng_mix
            "dry veg and green veg",   # 3  ng_pv
            "bare soil",               # 4  bs
            "bare soil mix",           # 5  bs_mix
            "bare soil and green veg", # 6  bs_pv
            "green veg mix",           # 7  pv_mix
            "green veg",               # 8  pv
            "wet",                     # 9
            "water",                   # 10
        ),
        colors=(
            "#F1E8C9", "#C0AB86", "#D6D2A7", "#BCD495", "#93724C",
            "#9C895D", "#8F9C5C", "#9DBD74", "#8CC46B", "#6CE6F8", "#676DCA",
        ),
    ),
}

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

    # load Landsat 5,7,8,9 data
    warnings.filterwarnings("ignore")

    # load wetland polygon and specify the coordinate reference system of the polygon
    if isinstance(gdf, Geometry):
        gdf = gpd.GeoDataFrame({"col1": ["name"], "geometry": gdf.geom}, crs=gdf.crs)
    gpgon = Geometry(gdf.geometry[0], crs=gdf.crs)

    # Define which spectral bands are being used in the analysis
    bands = [f"nbart_{band}" for band in ("blue", "green", "red", "nir", "swir_1", "swir_2")]

    if verbose_progress:
        print("Loading Landsat data")

    # Load Landsat 5, 7, 8 and 9 data. Not including Landsat 7 SLC off period (31-05-2003 to 06-04-2022)
    ds_ls = load_ard(
        dc,
        products=["ga_ls9c_ard_3", "ga_ls8c_ard_3", "ga_ls7e_ard_3", "ga_ls5t_ard_3"],
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

# Notes on ambiguous pixels
# -------------------------
# Both classification schemes contain a small number of pixels that cannot be
# assigned unambiguously. In the simple scheme, two or more fractions may be
# exactly equal; `argmax` resolves these towards the lowest class code, so an
# npv == bs pixel is reported as dry veg. In the detailed scheme, a pixel sitting
# exactly on a 1/3 or 2/3 boundary satisfies none of the nine conditions and is
# returned as NaN.

# These behaviours are deterministic and are not configurable. A tie means the
# data does not distinguish the classes, so any rule is arbitrary; fixing the
# rule keeps outputs comparable between users. On Hird Swamp (2014, 96,112
# in-polygon pixel-timesteps) each case affects under 1% of pixels: 730 ties in
# the simple scheme, 716 unclassified in the detailed scheme. Unclassified
# pixels do not contribute to the seasonal observation counts and so make it
# marginally more likely that a cell falls below MIN_OBS and is blanked.

def _classify_simple(pv, npv, bs):
    """
    Dominant fractional cover class: 0 = dry veg, 1 = bare soil, 2 = green veg.

    Ties are broken towards the lowest class code, so an exact npv == bs pixel
    is reported as dry veg. FC values are integer percentages before
    normalisation, so exact ties do occur, though they are rare.
    """
    # fillna(-1) keeps argmax from raising on all-NaN pixels; those pixels are
    # removed again by the `valid` mask in spatial_wit.
    stack = xr.concat([npv, bs, pv], dim="fc").fillna(-1)
    return stack.argmax("fc")


def _classify_detailed(pv, npv, bs):
    """
    Nine-class fractional cover classification.

    Conditions are evaluated in order and the first match wins, so the result
    is deterministic. A fraction of exactly 1/3 is treated as not co-dominant,
    so a pixel at pv = 1/3, npv = 0.53, bs = 0.14 is classified as dry mix
    rather than dry veg and green veg. Exact thirds are common because
    fractional cover arrives as integer percentages, which frequently sum to
    99.

    A pixel with all three fractions at exactly 1/3 has no dominant component,
    satisfies no condition, and is returned as NaN. 
    """
    conds = [
        pv > 2 / 3,
        npv > 2 / 3,
        bs > 2 / 3,
        (npv > 1 / 3) & (bs > 1 / 3) & (pv <= 1 / 3),
        (npv > 1 / 3) & (pv > 1 / 3) & (bs <= 1 / 3),
        (npv > 1 / 3) & (pv <= 1 / 3) & (bs <= 1 / 3),
        (bs > 1 / 3) & (pv > 1 / 3) & (npv <= 1 / 3),
        (bs > 1 / 3) & (pv <= 1 / 3) & (npv <= 1 / 3),
        (pv > 1 / 3) & (npv <= 1 / 3) & (bs <= 1 / 3),
    ]
    codes = [8, 0, 4, 1, 3, 2, 6, 5, 7]

    out = np.select(
        [c.values for c in conds], codes, default=np.nan
    ).astype("float64")
    return xr.DataArray(out, coords=pv.coords, dims=pv.dims)

def spatial_wit(ds, scheme="simple"):
    """
    Turn Wetlands Insight Tool cover fractions into a categorical map.

    Fractional cover is renormalised per pixel so pv + npv + bs sums to 1, the
    dominant class is found, and 'wet' and 'water' are layered on top as the
    two highest class codes. The same caveats as the timeseries WIT apply
    (see Dunn et al., 2023).

    Parameters
    ----------
    ds : xarray.Dataset
        WIT cube with 'pv', 'npv', 'bs', 'wet' and 'water' bands, as returned
        by `WIT_drill`. Not modified.
    scheme : str, optional
        'simple' for three fractional cover classes plus wet and water, or
        'detailed' for the nine-class breakdown plus wet and water.

    Returns
    -------
    ds_spatial : xarray.Dataset
        Copy of `ds` with an added categorical 'wetland' band. Timesteps where
        every pixel is missing are dropped.
    scheme : WITScheme
        Codes, labels, colours, cmap, norm and legend handles for the result.
    """
    if scheme not in WIT_SCHEMES:
        raise ValueError(
            f"Unknown scheme {scheme!r}; expected one of {sorted(WIT_SCHEMES)}"
        )
    scheme = WIT_SCHEMES[scheme]

    ds_spatial = ds.dropna(dim="time", how="all").copy()
    if ds_spatial.sizes["time"] == 0:
        raise ValueError("No timesteps remain after dropping all-missing observations.")

    # Renormalise FC, guarding against 0/0 where wet or water has zeroed all
    # three fractions.
    fc_sum = ds_spatial["pv"] + ds_spatial["npv"] + ds_spatial["bs"]
    valid = fc_sum > 0
    pv = (ds_spatial["pv"] / fc_sum).where(valid)
    npv = (ds_spatial["npv"] / fc_sum).where(valid)
    bs = (ds_spatial["bs"] / fc_sum).where(valid)

    classify = _classify_simple if scheme.name == "simple" else _classify_detailed
    wetland = classify(pv, npv, bs).where(valid)

    # Wet and water take the two highest codes in every scheme.
    water_code = len(scheme.labels) - 1
    wet_code = water_code - 1
    wetland = xr.where(ds_spatial["wet"] == 1, wet_code, wetland)
    wetland = xr.where(ds_spatial["water"] == 1, water_code, wetland)

    # xr.where drops coords that are not on both inputs; put the CRS back so
    # the band can still be written as a GeoTIFF.
    if "spatial_ref" in ds_spatial.coords:
        wetland = wetland.assign_coords(spatial_ref=ds_spatial.spatial_ref)

    ds_spatial["wetland"] = wetland
    return ds_spatial, scheme

def plot_wit_timesteps(
    da, scheme, ncols=4, max_panels=16, title=None, output_path=None, dpi=200):
    """
    Plot individual timesteps of a categorical WIT band as a grid of panels.

    Intended for a short window — a flood event, a watering action, a single
    season — where each observation is worth looking at. Beyond about sixteen
    panels the individual maps become too small to read; use `animate_wit` or
    the seasonal composites for longer periods instead.

    The legend is placed in a trailing empty cell where the panel count leaves
    one, and in a row of its own below the panels otherwise.

    Parameters
    ----------
    da : xarray.DataArray
        A categorical band such as `ds_spatial["wetland"]`, already sliced to
        the period of interest.
    scheme : WITScheme
        The scheme the band was produced with.
    ncols : int, optional
        Number of panels per row.
    max_panels : int, optional
        Refuse to plot more than this many timesteps.
    title : str, optional
        Figure title. The date range covered is appended beneath it.
    output_path : str, optional
        If given, the figure is saved here.
    dpi : int, optional
        Resolution used when saving.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If `da` has no timesteps, or more than `max_panels`.

    Example
    -------
    >>> ds_spatial, scheme = spatial_wit(ds_wit, scheme="simple")
    >>> fig = plot_wit_timesteps(
    ...     ds_spatial["wetland"].sel(time=slice("2014-06-01", "2014-12-01")),
    ...     scheme,
    ...     title="Hird Swamp",
    ... )
    """
    n = da.sizes.get("time", 0)
    if n == 0:
        raise ValueError("No observations in `da` — widen the time slice.")
    if n > max_panels:
        raise ValueError(
            f"{n} timesteps selected; this plot is only legible up to about "
            f"{max_panels}. Narrow the slice, or use animate_wit or the "
            "seasonal composites for longer periods."
        )

    nrows = int(np.ceil(n / ncols))
    inline_legend = (nrows * ncols - n) >= 1
    leg_ratio = 0.25 if scheme.name == "simple" else 1.0

    if inline_legend:
        fig_height = nrows * 3.2
        gs_rows, ratios = nrows, [1] * nrows
    else:
        fig_height = nrows * 3.2 + leg_ratio * 3.2
        gs_rows, ratios = nrows + 1, [1] * nrows + [leg_ratio]

    fig = plt.figure(figsize=(ncols * 3.2, fig_height), constrained_layout=True)
    gs = fig.add_gridspec(gs_rows, ncols, height_ratios=ratios)

    for t in range(n):
        ax = fig.add_subplot(gs[t // ncols, t % ncols])
        da.isel(time=t).plot.imshow(
            cmap=scheme.cmap, norm=scheme.norm, ax=ax, add_colorbar=False
        )
        ax.set_aspect("equal")
        ax.set_box_aspect(1)
        ax.set_title(
            pd.to_datetime(da.time.values[t]).strftime("%d-%m-%Y"), fontsize=10
        )
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])

    if inline_legend:
        ax_leg = fig.add_subplot(gs[n // ncols, n % ncols])
        scheme.draw_legend(ax_leg, orientation="vertical")
    else:
        ax_leg = fig.add_subplot(gs[nrows, :])
        scheme.draw_legend(ax_leg, orientation="horizontal")

    start = pd.to_datetime(da.time.values[0]).strftime("%d %b %Y")
    end = pd.to_datetime(da.time.values[-1]).strftime("%d %b %Y")
    span = f"{start} to {end}"
    fig.suptitle(f"{title}\n{span}" if title else span, fontsize=14)

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig

def plot_wit_season_year(
    sc, scheme, years=None, da=None, title=None, output_path=None,
    cell_width=2.6, dpi=200,
):
    """
    Plot modal class for every season of every year as a year x season matrix.

    Rows are season-years and columns are DJF, MAM, JJA and SON, so reading
    down a column shows how one season changed over the record and reading
    across a row shows one year's annual cycle. Cells with fewer than
    `min_obs` clear observations are left blank.

    Modal class is shown without purity here. Use
    `plot_wit_seasonal_climatology` to see how consistent each class
    assignment is.

    Before plotting, the number of clear observations available in each season
    is printed. Observation density varies widely across Australia, so this is
    worth checking — a wetland in a cloudier region may not have enough
    observations to support seasonal composites at the default `min_obs`.

    Parameters
    ----------
    sc : xarray.Dataset
        Output of `wit_seasonal_composites`.
    scheme : WITScheme
        The scheme the composites were produced with.
    years : int or sequence of int, optional
        Season-years to plot. Defaults to all years in `sc`.
    da : xarray.DataArray, optional
        The band the composites were built from, such as
        `ds_spatial["wetland"]`. If given, observation counts per month are
        printed as well as per season.
    title : str, optional
        Figure title.
    output_path : str, optional
        If given, the figure is saved here.
    cell_width : float, optional
        Width of each panel in inches. Panel height follows the data's aspect
        ratio so the wetland keeps its true proportions.
    dpi : int, optional
        Resolution used when saving.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If none of the requested years are present in `sc`.
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    sy_season = [str(s) for s in sc.sy_season.values]
    sy_year = [int(y) for y in sc.season_year.values]

    all_years = sorted(set(sy_year))
    if years is None:
        years = all_years
    else:
        if isinstance(years, (int, np.integer)):
            years = [int(years)]
        years = sorted(int(y) for y in years)
        missing = [y for y in years if y not in all_years]
        if missing:
            warnings.warn(
                f"No data for season-year(s) {missing}; available: "
                f"{all_years[0]}–{all_years[-1]}.",
                stacklevel=2,
            )
        years = [y for y in years if y in all_years]
        if not years:
            raise ValueError(
                f"None of the requested years are in the composites. "
                f"Available: {all_years[0]}–{all_years[-1]}."
            )

    lookup = {(y, s): i for i, (y, s) in enumerate(zip(sy_year, sy_season))}

    # Observation counts. Restrict to the polygon footprint — pixels outside
    # it count as zero and would drag the median down.
    inside = sc["sy_modal"].notnull().any("time")
    print(f"Clear observations per season (min_obs = {sc.attrs.get('min_obs', '?')}):")
    for yr in years:
        row = []
        for sn in seasons:
            i = lookup.get((yr, sn))
            if i is None:
                row.append(f"{sn} —")
            else:
                med = float(sc["sy_n"].isel(time=i).where(inside).median())
                row.append(f"{sn} {med:.0f}")
        print(f"  {yr}:  " + "   ".join(row))

    if da is not None:
        months = pd.to_datetime(da.time.values).month
        counts = pd.Series(months).value_counts().sort_index()
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        print("\nObservations per month, whole record:")
        print("  " + "  ".join(
            f"{names[m - 1]} {counts.get(m, 0)}" for m in range(1, 13)
        ))
    print()

    # Size cells to the data's own aspect ratio. With set_aspect("equal") a
    # mismatched cell is padded with white, which is where gaps come from.
    ny, nx = sc["sy_modal"].isel(time=0).shape
    cell_height = cell_width * (ny / nx) + 0.25  # headroom for labels

    leg_ratio = 0.35 if scheme.name == "simple" else 1.0
    fig = plt.figure(
        figsize=(4 * cell_width, len(years) * cell_height + leg_ratio * cell_height),
        constrained_layout=True,
    )
    fig.set_constrained_layout_pads(w_pad=0.02, h_pad=0.02, wspace=0.01, hspace=0.01)
    gs = fig.add_gridspec(
        len(years) + 1, 4, height_ratios=[1] * len(years) + [leg_ratio]
    )
    axes = [[fig.add_subplot(gs[r, c]) for c in range(4)] for r in range(len(years))]

    for r, yr in enumerate(years):
        for c, sn in enumerate(seasons):
            ax = axes[r][c]
            i = lookup.get((yr, sn))

            if i is None or bool(sc["sy_modal"].isel(time=i).isnull().all()):
                # No such quarter, or every pixel below min_obs.
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
            else:
                sc["sy_modal"].isel(time=i).plot.imshow(
                    cmap=scheme.cmap, norm=scheme.norm, ax=ax, add_colorbar=False
                )
                ax.set_aspect("equal")
                ax.set_xticks([])
                ax.set_yticks([])

            ax.set_title("")
            ax.set_xlabel("")
            ax.set_ylabel("")

        # Year label in the left margin. Set on the axes rather than a rendered
        # panel so it survives rows where every season is blank.
        axes[r][0].set_ylabel(
            str(yr), fontsize=11, rotation=0, labelpad=22, va="center"
        )

    for c, sn in enumerate(seasons):
        axes[0][c].set_title(sn, fontsize=12)

    ax_leg = fig.add_subplot(gs[len(years), :])
    scheme.draw_legend(ax_leg, orientation="horizontal")

    if title:
        fig.suptitle(title, fontsize=14)
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig
    
def write_class_geotiffs(da, output_dir=".", prefix="wetland", crs="EPSG:3577"):
    """
    Write a categorical WIT band to one uint8 GeoTIFF per timestep.

    Class codes are written as-is and missing pixels become 255, so the files
    can be loaded straight into a GIS and styled with the class labels from the
    scheme used to produce them. Note that GeoTIFFs carry no legend — record
    which scheme was used alongside the files.

    Parameters
    ----------
    da : xarray.DataArray
        A categorical band such as `ds_spatial["wetland"]`. May have a time
        dimension, in which case one file is written per timestep, or be a
        single timestep already selected with `.isel(time=...)`.
    output_dir : str, optional
        Directory to write into. Created if it does not exist.
    prefix : str, optional
        Filename prefix. Files are named `<prefix>_<YYYY-MM-DD>.tif`, or
        `<prefix>.tif` if `da` has no time coordinate.
    crs : str, optional
        CRS to write. Used only if `da` does not already carry one.

    Returns
    -------
    list of str
        Paths written, in time order.

    Example
    -------
    >>> ds_spatial, scheme = spatial_wit(ds_wit, scheme="simple")
    >>> paths = write_class_geotiffs(
    ...     ds_spatial["wetland"].isel(time=slice(0, 5)),
    ...     output_dir="geotiffs",
    ...     prefix="hird_swamp",
    ... )
    """
    os.makedirs(output_dir, exist_ok=True)

    if "time" in da.dims:
        slices = [(da.isel(time=i), str(da.time.values[i])[:10])
                  for i in range(da.sizes["time"])]
    else:
        stamp = str(da.time.values)[:10] if "time" in da.coords else None
        slices = [(da, stamp)]

    paths = []
    for arr, stamp in slices:
        name = f"{prefix}_{stamp}.tif" if stamp else f"{prefix}.tif"
        path = os.path.join(output_dir, name)

        # 255 as nodata: class codes go no higher than 10, so there is no clash.
        out = arr.fillna(255).astype("uint8")
        if out.rio.crs is None:
            out = out.rio.write_crs(crs)
        out = out.rio.write_nodata(255)
        out.rio.to_raster(path, compress="deflate")

        paths.append(path)

    return paths

def wit_seasonal_composites(da, scheme, min_obs=3, min_obs_clim=1):
    """
    Summarise a categorical WIT band by season.

    Two summaries are produced. The season-year composite treats each season of
    each year separately, showing how the wetland behaved in a particular
    season. The climatology pools all occurrences of a season across the whole
    record, showing the wetland's typical behaviour in that season.

    For each pixel the modal (most frequent) class is reported along with its
    purity: the share of clear observations that fell in the modal class. A
    purity near 1 means the pixel was consistently that class; a purity near
    1/n means the observations were split and the modal class is close to
    arbitrary. The two should always be read together — a modal class shown
    without its purity implies more confidence than the data supports.

    Ties are resolved towards the lowest class code, so a pixel with an even
    2-2 split reports the lower-numbered class at a purity of 0.5.

    Seasons are the standard Australian quarters, with December grouped
    forward into the following year's summer (DJF).

    Parameters
    ----------
    da : xarray.DataArray
        A categorical band such as `ds_spatial["wetland"]`, with a time
        dimension.
    scheme : WITScheme
        The scheme `da` was produced with, as returned by `spatial_wit`.
    min_obs : int, optional
        Minimum clear observations for a season-year pixel. A single season of
        a single year typically has only a handful of clear observations, so
        the modal class is fragile below this. Pixels below it are NaN.
    min_obs_clim : int, optional
        Minimum clear observations for a climatology pixel. The climatology
        pools a season across the whole record, so over a multi-decade run
        this is far from binding — it excludes pixels that are almost always
        cloud-affected, where a high purity would otherwise imply confidence
        the sample does not support. Set it to 1 when testing over a single
        year, where no pixel will reach 10.

    Returns
    -------
    xarray.Dataset
        Season-year variables on a `time` dimension:
          sy_modal, sy_purity, sy_n
        Climatology variables on a `season` dimension (DJF, MAM, JJA, SON):
          clim_modal, clim_purity, clim_n
        Season-year time steps also carry `sy_season` and `season_year`
          coordinates for labelling.
    """
    if "time" not in da.dims:
        raise ValueError("`da` must have a time dimension.")

    codes = list(scheme.codes)

    # Season-year: QS-DEC starts quarters in December, so DJF stays intact.
    counts = xr.concat(
        [(da == c).resample(time="QS-DEC").sum() for c in codes], dim="cls"
    ).assign_coords(cls=codes)

    sy_n = counts.sum("cls")
    enough = sy_n >= min_obs
    sy_modal = counts.idxmax("cls").where(enough)
    sy_purity = (counts.max("cls") / sy_n).where(enough)

    # Label each quarter. December belongs to the next year's summer.
    stamps = pd.to_datetime(sy_modal.time.values)
    season_of = {12: "DJF", 3: "MAM", 6: "JJA", 9: "SON"}
    seasons = [season_of[d.month] for d in stamps]
    season_years = [d.year + 1 if d.month == 12 else d.year for d in stamps]

    # Climatology: pool every occurrence of each season.
    clim_counts = xr.concat(
        [(da == c).groupby("time.season").sum("time") for c in codes], dim="cls"
    ).assign_coords(cls=codes)

    # groupby sorts seasons alphabetically; restore calendar order.
    clim_counts = clim_counts.sel(season=["DJF", "MAM", "JJA", "SON"])
    clim_n = clim_counts.sum("cls")
    enough_clim = clim_n >= min_obs_clim
    clim_modal = clim_counts.idxmax("cls").where(enough_clim)
    clim_purity = (clim_counts.max("cls") / clim_n).where(enough_clim)

    out = xr.Dataset(
        {
            "sy_modal": sy_modal,
            "sy_purity": sy_purity,
            "sy_n": sy_n,
            "clim_modal": clim_modal,
            "clim_purity": clim_purity,
            "clim_n": clim_n,
        }
    )
    out = out.assign_coords(
        sy_season=("time", seasons),
        season_year=("time", season_years),
    )
    out.attrs["min_obs"] = min_obs
    out.attrs["min_obs_clim"] = min_obs_clim
    out.attrs["scheme"] = scheme.name
    return out



def plot_wit_seasonal_climatology(
    sc, scheme, title=None, output_path=None, purity_vmin=0.2, dpi=200
):
    """
    Plot the seasonal climatology as modal class over purity.

    The top row shows the most likely class for each season, pooled across the
    whole record. The bottom row shows purity: the share of clear observations
    that fell in the modal class. The two must be read together — a pixel can
    have a confident-looking modal class at a purity of barely over 1/n, which
    means the observations were split and the class shown is close to
    arbitrary. Dark areas in the purity row mark where the top row should not
    be trusted.

    Parameters
    ----------
    sc : xarray.Dataset
        Output of `wit_seasonal_composites`.
    scheme : WITScheme
        The scheme the composites were produced with.
    title : str, optional
        Figure title.
    output_path : str, optional
        If given, the figure is saved here.
    purity_vmin : float, optional
        Lower limit of the purity colour scale. The default of 0.2 suits a
        five-class scheme; for the detailed scheme a lower value spreads the
        range more usefully.
    dpi : int, optional
        Resolution used when saving.

    Returns
    -------
    matplotlib.figure.Figure
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]

    fig, axes = plt.subplots(
        2, 4, figsize=(16, 8.5), squeeze=False, constrained_layout=True
    )

    for c, sn in enumerate(seasons):
        sc["clim_modal"].sel(season=sn).plot.imshow(
            cmap=scheme.cmap, norm=scheme.norm, ax=axes[0][c], add_colorbar=False
        )
        axes[0][c].set_title(sn, fontsize=12)

        im = sc["clim_purity"].sel(season=sn).plot.imshow(
            ax=axes[1][c],
            vmin=purity_vmin,
            vmax=1.0,
            cmap="magma",
            add_colorbar=False,
        )
        axes[1][c].set_title(f"{sn} — purity", fontsize=11)

    for ax in axes.flat:
        ax.set_aspect("equal")
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])

    axes[0][0].set_ylabel("most likely class", fontsize=11, rotation=90, labelpad=12)
    axes[1][0].set_ylabel("purity", fontsize=11, rotation=90, labelpad=12)

    fig.legend(
        handles=scheme.legend_handles,
        loc="upper center",
        ncol=min(len(scheme.labels), 6),
        fontsize=9,
        frameon=False,
        bbox_to_anchor=(0.5, 0.53),
    )
    fig.colorbar(im, ax=axes[1], shrink=0.7, label="share of obs in modal class")

    if title:
        fig.suptitle(title, fontsize=14)
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig

def animate_wit(
    ds_spatial,
    scheme,
    output_path=None,
    fps=8,
    width_pixels=600,
    limit=None,
):
    """
    Animate a categorical WIT band as a map through time.

    Uses `dea_tools.plotting.xr_animation`. Writes MP4 if the ffmpeg binary is
    available and GIF otherwise; GIFs of a full Landsat record are large, so
    prefer MP4 where possible.

    No colourbar is drawn. On a single-band animation `xr_animation` produces a
    continuous colourbar — a smooth ramp through the class colours — which is
    misleading for categorical data and cannot be relabelled through the
    available arguments. Use `scheme.legend_handles` to caption the animation
    instead.

    Parameters
    ----------
    ds_spatial : xarray.Dataset
        Output of `spatial_wit`, containing a 'wetland' band.
    scheme : WITScheme
        The scheme the band was produced with.
    output_path : str, optional
        Path to write. The extension is replaced with '.mp4' or '.gif' to match
        what is actually written. Defaults to 'wit_animation'.
    fps : int, optional
        Frames per second.
    width_pixels : int, optional
        Output width; height follows the data's aspect ratio.
    limit : int, optional
        Animate only the first `limit` timesteps. Useful for a quick check
        before committing to a full record.

    Returns
    -------
    str
        The path written.
    """
    from matplotlib import animation

    from dea_tools.plotting import xr_animation

    has_ffmpeg = "ffmpeg" in animation.writers.list()
    ext = "mp4" if has_ffmpeg else "gif"

    if output_path is None:
        output_path = "wit_animation"
    output_path = f"{os.path.splitext(output_path)[0]}.{ext}"

    if not has_ffmpeg:
        warnings.warn(
            "ffmpeg not found; writing GIF instead of MP4. Expect a large file "
            "at this frame count.",
            stacklevel=2,
        )

    da = ds_spatial[["wetland"]]
    if limit is not None:
        da = da.isel(time=slice(0, limit))

    n = len(scheme.labels)
    xr_animation(
        ds=da,
        bands=["wetland"],
        output_path=output_path,
        width_pixels=width_pixels,
        interval=int(1000 / fps),
        show_date="%d %b %Y",
        show_colorbar=False,
        # vmin/vmax are required: supplying them disables percentile_stretch,
        # which would otherwise rescale the class codes into nonsense. This
        # maps [-0.5, n-0.5] linearly onto n colours, so each integer class
        # lands mid-bin — equivalent to the scheme's BoundaryNorm.
        imshow_kwargs={"cmap": scheme.cmap, "vmin": -0.5, "vmax": n - 0.5},
    )

    return output_path

def animate_wit_with_timeseries(
    ds_spatial,
    scheme,
    polygon_base_df,
    output_path=None,
    fps=8,
    limit=None,
    dpi=110,
):
    """
    Animate the categorical map beside the WIT stack plot, with a moving cursor.

    The left panel steps through the classified map; the right panel shows the
    whole-of-polygon WIT timeseries with a cursor marking the frame being
    displayed. This ties the spatial pattern to the summary statistic — a jump
    in the water fraction on the right can be traced to where the water
    appeared on the left.

    Built on `matplotlib.animation.FuncAnimation` rather than `xr_animation`,
    which animates a single image axis and cannot express the second panel.

    Parameters
    ----------
    ds_spatial : xarray.Dataset
        Output of `spatial_wit`, containing a 'wetland' band.
    scheme : WITScheme
        The scheme the band was produced with.
    polygon_base_df : pandas.DataFrame
        Normalised WIT timeseries from `WIT_drill`, with 'date', 'water',
        'wet', 'norm_bs', 'norm_npv' and 'norm_pv' columns.
    output_path : str, optional
        Path to write. The extension is replaced to match the writer used.
        Defaults to 'wit_sidebyside'.
    fps : int, optional
        Frames per second.
    limit : int, optional
        Animate only the first `limit` timesteps.
    dpi : int, optional
        Output resolution.

    Returns
    -------
    str
        The path written.
    """
    from matplotlib import animation

    has_ffmpeg = "ffmpeg" in animation.writers.list()
    ext = "mp4" if has_ffmpeg else "gif"

    if output_path is None:
        output_path = "wit_sidebyside"
    output_path = f"{os.path.splitext(output_path)[0]}.{ext}"

    da = ds_spatial["wetland"]
    if limit is not None:
        da = da.isel(time=slice(0, limit))

    df = polygon_base_df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.set_index("date")
    df = df.sort_index()

    # The cursor is only meaningful if the two sources share timestamps.
    map_times = pd.to_datetime(da.time.values)
    missing = map_times.difference(df.index)
    if len(missing):
        raise ValueError(
            f"{len(missing)} map timesteps are absent from polygon_base_df "
            f"(first: {missing[0]}). The cursor would not match the map — "
            "check both came from the same WIT_drill call."
        )

    cols = ["water", "wet", "norm_bs", "norm_npv", "norm_pv"]
    colors = ["#676DCA", "#6CE6F8", "#93724C", "#F1E8C9", "#8CC46B"]
    labels = ["water", "wet", "bare soil", "dry veg", "green veg"]
    dates = df.index

    # Build the figure once and swap image data per frame. Much faster than
    # re-rendering, and the fixed axes boxes avoid layout drift.
    fig, (ax_map, ax_wit) = plt.subplots(
        1,
        2,
        figsize=(14, 6),
        gridspec_kw={"width_ratios": [1, 2]},
        constrained_layout=True,
    )

    im = da.isel(time=0).plot.imshow(
        cmap=scheme.cmap, norm=scheme.norm, ax=ax_map, add_colorbar=False
    )
    ax_map.set_aspect("equal")
    ax_map.set_xlabel("")
    ax_map.set_ylabel("")
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    map_title = ax_map.set_title("")

    ax_wit.stackplot(dates, *[df[c] for c in cols], colors=colors, labels=labels)
    cursor = ax_wit.axvline(dates[0], color="red", linewidth=1.5)
    ax_wit.set_xlim(dates.min(), dates.max())
    ax_wit.set_ylim(0, 1)
    ax_wit.set_ylabel("Fraction")
    ax_wit.set_title("Wetlands Insight Tool")
    ax_wit.legend(loc="upper left", fontsize=7, ncol=5, framealpha=0.6)

    def update(t):
        frame = da.isel(time=t)
        d = pd.to_datetime(frame.time.values)
        im.set_data(frame.values)
        map_title.set_text(d.strftime("%d %b %Y"))
        cursor.set_xdata([d, d])
        return im, map_title, cursor

    anim = animation.FuncAnimation(
        fig, update, frames=da.sizes["time"], interval=int(1000 / fps), blit=False
    )

    if has_ffmpeg:
        anim.save(
            output_path, writer=animation.FFMpegWriter(fps=fps, bitrate=3000), dpi=dpi
        )
    else:
        warnings.warn("ffmpeg not found; writing GIF instead of MP4.", stacklevel=2)
        anim.save(output_path, writer=animation.PillowWriter(fps=fps), dpi=70)

    plt.close(fig)
    return output_path

def draw_polygon(center=(-25, 134), zoom=3.5, max_area_km2=2000):
    """
    Show a map for drawing a wetland polygon interactively.

    Run this in one cell, draw a polygon or rectangle using the tools on the
    left of the map, then pass the returned map to `polygon_from_map` in a
    later cell to get a GeoDataFrame.

    Drawing is a convenience for users without a polygon file to hand. A
    mapped wetland boundary from a shapefile will usually be more defensible
    than a hand-drawn outline, particularly if results are going to be
    reported.

    Parameters
    ----------
    center : tuple, optional
        Starting (latitude, longitude) for the map. Defaults to the
        Murray-Darling Basin.
    zoom : int, optional
        Starting zoom level.
    max_area_km2 : float, optional
        Largest polygon `polygon_from_map` will accept. Loading Landsat,
        Water Observations and Fractional Cover for a large area will exhaust
        the memory available on the DEA Sandbox.

    Returns
    -------
    ipyleaflet.Map
        Display this to draw. Pass it to `polygon_from_map` afterwards.
    """
    try:
        from ipyleaflet import DrawControl, Map, basemap_to_tiles, basemaps
    except ImportError as e:
        raise ImportError(
            "`ipyleaflet` is required for `draw_polygon`. Load a polygon file "
            "with geopandas instead, or install ipyleaflet."
        ) from e

    m = Map(center=center, zoom=zoom, scroll_wheel_zoom=True)
    m.add_layer(basemap_to_tiles(basemaps.Esri.WorldImagery))

    draw = DrawControl(
        polygon={"shapeOptions": {"color": "#6bc2e5", "fillOpacity": 0.2}},
        rectangle={"shapeOptions": {"color": "#6bc2e5", "fillOpacity": 0.2}},
        circle={},
        circlemarker={},
        polyline={},
        marker={},
        edit=True,
        remove=True,
    )

    # Keep every shape drawn; polygon_from_map takes the last one.
    shapes = []

    def _on_draw(target, action, geo_json):
        if action == "created":
            shapes.append(geo_json)

    draw.on_draw(_on_draw)
    m.add_control(draw)

    # Stash on the map object so polygon_from_map can find them.
    m._wit_shapes = shapes
    m._wit_max_area_km2 = max_area_km2

    return m


def polygon_from_map(m):
    """
    Convert a polygon drawn with `draw_polygon` into a GeoDataFrame.

    The drawn shape is reprojected from EPSG:4326 to EPSG:3577, which is what
    `WIT_drill` expects.

    Parameters
    ----------
    m : ipyleaflet.Map
        The map returned by `draw_polygon`, after a polygon has been drawn.

    Returns
    -------
    geopandas.GeoDataFrame
        Single-row frame in EPSG:3577, ready to pass to `WIT_drill`.

    Raises
    ------
    ValueError
        If nothing has been drawn, or the polygon is larger than the map's
        `max_area_km2`.
    """
    shapes = getattr(m, "_wit_shapes", None)
    if not shapes:
        raise ValueError(
            "No polygon drawn. Use the polygon or rectangle tool on the map, "
            "then run this cell again."
        )

    if len(shapes) > 1:
        warnings.warn(
            f"{len(shapes)} shapes drawn; using the most recent one.",
            stacklevel=2,
        )

    gdf = gpd.GeoDataFrame.from_features([shapes[-1]], crs="EPSG:4326")
    gdf = gdf.to_crs("EPSG:3577")

    # Albers is equal-area, so this is a fair area in square metres.
    area_km2 = gdf.geometry.area.iloc[0] / 1e6
    limit = getattr(m, "_wit_max_area_km2", 2000)
    if area_km2 > limit:
        raise ValueError(
            f"Drawn polygon is {area_km2:.0f} km2, above the {limit:.0f} km2 "
            "limit. Loading three datasets over an area this large may "
            "exhaust the memory available on the Sandbox. Draw a "
            "smaller polygon, or raise max_area_km2 in draw_polygon if you "
            "are running elsewhere."
        )

    print(f"Polygon area: {area_km2:.1f} km2")
    return gdf[["geometry"]]