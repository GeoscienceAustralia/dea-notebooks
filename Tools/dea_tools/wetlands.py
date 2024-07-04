# wetlands.py
"""
This module is for processing DEA wetlands data. 

License: The code in this notebook is licensed under the Apache 
License,Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). 
Digital Earth Australia data is licensed under the Creative Commons 
by Attribution 4.0 license 
(https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open 
Data Cube Slack channel (http://slack.opendatacube.org/) or on the 
GIS Stack Exchange 
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube)using
the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, file one on 
GitHub: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Last modified: July 2023
"""

import seaborn as sns
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

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
    polygon_base_df.loc[:, "veg_areas"] = (
        1 - polygon_base_df["water"] - polygon_base_df["wet"]
    )

    # 2. normalise the vegetation values based on vegetation size (to handle FC values more than 100 issue)
    # WARNNING: Not touch the water and wet, cause they are pixel classification result
    polygon_base_df.loc[:, "overall_veg_num"] = (
        polygon_base_df["pv"] + polygon_base_df["npv"] + polygon_base_df["bs"]
    )

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
    polygon_base_df.loc[:, "date"] = pd.to_datetime(
        polygon_base_df["date"], infer_datetime_format=True
    )

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
                df[
                    (df["date"] >= df.loc[i, "date"])
                    & (df["date"] <= df.loc[i + 3, "date"])
                ].index,
                "off_value",
            ] = 100

    return df


def display_wit_stack_with_df(
    polygon_base_df,
    polygon_name="your_wetland_name",
    png_name="your_file_name",
    width=32,
    height=6,
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

    # modify the xaxis settings
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    x_label_text = "The Fractional Cover algorithm developed by the Joint Remote Sensing Research Program and\n the Water Observations from Space algorithm developed by Geoscience Australia are used in the production of this data"

    ax.set_xlabel(x_label_text, style="italic")

    plt.savefig(f"{png_name}.png", bbox_inches="tight")
    plt.show()

    plt.close(fig)
