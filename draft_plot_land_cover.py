# Land_cover_plotting.py
"""
Description: This file contains a set of python functions for plotting 
Digital Earth Australia Land Cover data.

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
    lc_animation
    plot_lc
    lc_colours

Last modified: January 2022

"""

import numpy as np
import pandas as pd
import ast
import sys

from IPython.display import Image

import matplotlib.pyplot as plt
from matplotlib import colors as mcolours
from matplotlib import patheffects
from matplotlib.animation import FuncAnimation

sys.path.insert(1, "../Tools/")


def lc_colours(lc_colour_scheme, colour_bar=False):
    """
    Creates custom colour map and normalisation for plotting the provided DEA Land Cover layer

    Parameters
    ----------
    lc_colour_scheme : string
        Name of land cover colour scheme to use.
        Valid options: 'level3', 'level4', 'lifeform_veg_cat_l4a', 'canopyco_veg_cat_l4d', 'watersea_veg_cat_l4a_au',
        'waterstt_wat_cat_l4a', 'inttidal_wat_cat_l4a', 'waterper_wat_cat_l4d_au', 'baregrad_phy_cat_l4d_au'
    colour_bar : bool, optional
        Controls if colour bar labels are returned as a list for plotting a colour bar.
        Default False
    """

    lc_colour_scheme = lc_colour_scheme.lower()

    # read file containing all colour scheme definitions
    with open("draft_lc_colour_definitions.txt", "r") as file:
        contents = file.read()
        valid_layer_list = ast.literal_eval(contents)

    # ensure a valid colour scheme was requested
    assert ( lc_colour_scheme in valid_layer_list.keys()), \
             f'colour scheme must be one of [{valid_layer_list.keys()}] (got "{lc_colour_scheme}")'

    # load selected colour scheme definition
    colours = valid_layer_list[lc_colour_scheme]

    # create colour map
    colour_arr = []
    cblabels = []
    for key, value in colours.items():
        colour_arr.append(np.array(value[:-2]) / 255)
        if colour_bar: cblabels.append(value[-1])

    cmap = mcolours.ListedColormap(colour_arr)
    bounds = list(colours)
    bounds.append(255)
    norm = mcolours.BoundaryNorm(np.array(bounds) - 0.1, cmap.N)

    if colour_bar == False:
        return (cmap, norm)
    else:
        return (cmap, norm, cblabels)


# plot layer from colour map
def plot_land_cover(data, year=None, layer=None):
    """
    Plot a single land cover layer with appropriate colour scheme.

    Parameters
    ----------
    data : xarray.DataArray
        A dataArray containing a DEA Land Cover classification.
    year : int, optional
        Can be used to select to plot a specific year. If not provided, all time slices are plotted.
    layer : string, optional
        Name of the land cover layer to be plotted. If not provided the name on the DataArray is used.
    """

    # determine layer name if not provided
    layer = layer if layer else data.name
    cmap, norm, cblabels = lc_colours(layer, colour_bar=True)

    if year == None:
        # plot all dates for the provided layer
        im = data.plot.imshow(cmap=cmap, norm=norm, add_colorbar=True, col="time", col_wrap=4, size=5)
        cb = im.cbar
    else:
        # plot only the provided year
        year_string = f"{year}-01-01"
        data = data.sel(time=year_string, method="nearest")
        im = data.plot.imshow(cmap=cmap, norm=norm, add_colorbar=True, size=5)
        cb = im.colorbar

    ticks = cb.get_ticks()
    cb.set_ticks(ticks + np.diff(ticks, append=256) / 2)
    cb.set_ticklabels(cblabels)

    return im


def lc_hex_convert(n: int, layer="Level4"):
    """
    Parameters
    ----------
    layer : string.
    accepts one of the following options: 'level4', 'level3', 'lifeform_veg_cat_l4a', 'canopyco_veg_cat_l4d', 'watersea_veg_cat_l4a_au',
    'waterstt_wat_cat_l4a', 'inttidal_wat_cat_l4a', 'waterper_wat_cat_l4d_au', 'baregrad_phy_cat_l4d_au'
    defaults to 'level4'.
    """

    file = open("draft_lc_colour_definitions.txt", "r")

    contents = file.read()
    valid_layer_list = ast.literal_eval(contents)

    file.close()

    # make string all lower case just incase
    layer = layer.lower()

    colour_map = valid_layer_list[layer]

    if n in colour_map:
        r, g, b = colour_map[n][0:3]
        HEX = "#%x%x%x" % (r, g, b)

        if len(HEX) < 7:
            HEX = "#0" + HEX[1:]

        return HEX
    else:
        print(f"ERROR: class code: {n} not valid for {layer}")


def lc_animation(
    ds,
    file_name="default_animation.gif",
    layer="level4",
    stacked_plot=False,
    animation_interval=500,
    width_pixels=500,
    dpi=400,
):
    """
    creates an animation of a landcover maps though time beside corrosponding stacked plots of the landcover classes. Saves the
    animation to a file and   displays the annimation in notebook

    Inputs:
    ds : a xarray Data Array containing a multidate stack of observations of a single landcover level.
    file_name: String, optional.
    """

    # create colour map and normalisation for specified lc layer
    layer_cmap, layer_norm, cblabels = lc_colours(layer, colour_bar=True)

    # prepare variables needed
    # Get info on dataset dimensions
    height, width = ds.geobox.shape
    scale = width_pixels / width
    left, bottom, right, top = ds.geobox.extent.boundingbox
    extent = [left, right, bottom, top]

    outline = [patheffects.withStroke(linewidth=2.5, foreground="black")]
    annotation_defaults = {
        "xy": (1, 1),
        "xycoords": "axes fraction",
        "xytext": (-5, -5),
        "textcoords": "offset points",
        "horizontalalignment": "right",
        "verticalalignment": "top",
        "fontsize": 20,
        "color": "white",
        "path_effects": outline,
    }


    def create_panda(da):
        """creates a pandas dataframe listing what percentage or total area is taken up by each class in given layer for each year of dataset"""
        # list all class codes in dataset
        list_classes = (np.unique(da, return_counts=False)).tolist()

        # create empty dataframe & dictionary
        panda_table = pd.DataFrame(data=None, columns=list_classes)
        date_line = {}

        # count all pixels, should be consistent
        total_pix = int(np.sum(da.isel(time=1)))

        # iterate through each year in dataset
        for i in range(0, len(da.time)):
            date = str(da.time[i].data)[0:10]

            # for each year iterate though each present class number and count pixels
            for (n) in (list_classes):
                number_of_pixles = int(np.sum(da.isel(time=i) == n))
                percentage = number_of_pixles / total_pix * 100
                date_line[n] = percentage

            # add each year's counts to dataframe
            panda_table.loc[date] = date_line

        return panda_table

    # Get information needed to display the year in the top corner
    times_list = ds.time.dt.strftime("%Y").values
    text_list = [False] * len(times_list)

    annotation_list = [
        "\n".join([str(i) for i in (a, b) if i]) for a, b in zip(times_list, text_list)
    ]

    if stacked_plot == True:

        stacked_plot_table = create_panda(ds)

        # define fig
        # Set up figure
        fig, (ax1, ax2) = plt.subplots(1, 2, dpi=dpi, constrained_layout=True)
        fig.set_size_inches(width * scale / 20, height * scale / 40, forward=True)
        fig.set_constrained_layout_pads(w_pad=0.2, h_pad=0.2, hspace=0, wspace=0)

        # define update_frames
        # This function is called at regular intervals with changing i values for each frame

        def _update_frames(
            i, ax1, ax2, extent, annotation_text, annotation_defaults, cmap, norm
        ):
            # Clear previous frame to optimise render speed and plot imagery
            ax1.clear()
            ax2.clear()

            ax1.imshow(
                ds[i, ...], cmap=cmap, norm=norm, extent=extent, interpolation="nearest"
            )

            cliped_table = stacked_plot_table.iloc[: int(i + 1)]
            data = cliped_table.to_dict(orient="list")
            date = cliped_table.index

            # build colour list
            colour_list = []
            for vals in list(cliped_table):
                x = lc_hex_convert(vals, layer)
                colour_list.append(x)

            ax2.stackplot(date, data.values(), colors=colour_list)  # nat bare
            ax2.tick_params(axis="x", labelrotation=-45)
            ax2.margins(x=0, y=0)

            # Add annotation text
            ax1.annotate(annotation_text[i], **annotation_defaults)
            ax2.annotate(annotation_text[i], **annotation_defaults)

        # define anim_fargs
        anim_fargs = (
            ax1,
            ax2,  # axis to plot into
            [left, right, bottom, top],  # imshow extent
            annotation_list,
            annotation_defaults,
            layer_cmap,
            layer_norm,
        )

    if stacked_plot == False:

        # define fig
        # Set up figure
        fig, (ax1) = plt.subplots(
            1, 1, dpi=dpi, constrained_layout=True
        )  # test this is correct
        fig.set_size_inches(width * scale / 20, height * scale / 40, forward=True)
        fig.set_constrained_layout_pads(w_pad=0.2, h_pad=0.2, hspace=0, wspace=0)

        # define update_frames
        # This function is called at regular intervals with changing i values for each frame

        def _update_frames(
            i, ax1, extent, annotation_text, annotation_defaults, cmap, norm
        ):
            # Clear previous frame to optimise render speed and plot imagery
            ax1.clear()
            ax1.imshow(
                ds[i, ...], cmap=cmap, norm=norm, extent=extent, interpolation="nearest"
            )

            # Add annotation text
            ax1.annotate(annotation_text[i], **annotation_defaults)

        # define anim_fargs
        anim_fargs = (
            ax1,
            [left, right, bottom, top],  # imshow extent
            annotation_list,
            annotation_defaults,
            layer_cmap,
            layer_norm,
        )

    # This is the actual animation function
    # fargs contails all the values we send to our _update_frames function.
    # Note the layer_cmap and layer_norm which were calculated earlier being passed through

    anim = FuncAnimation(
        fig=fig,
        func=_update_frames,
        fargs=anim_fargs,
        frames=len(ds.time),
        interval=animation_interval,
        repeat=False,
    )

    anim.save(file_name, writer="pillow", dpi=dpi)
    plt.close()
    #
    return Image(filename=file_name)


# return plotting of animation.
