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
    get_layer_name
    lc_colourmap
    plot_land_cover
    lc_animation
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

# Define colour schemes for each land cover layer
lc_colours = {
    'level3': {0: (255, 255, 255, 255, "No Data"),
               111: (172, 188, 45, 255, "Cultivated terrestrial vegetation"),
               112: (14, 121, 18, 255, "Natural terrestrial vegetation"),
               124: (30, 191, 121, 255, "Natural aquatic vegetation"),
               215: (218, 92, 105, 255, "Artificial surface"),
               216: (243, 171, 105, 255, "Natural bare surface"),
               220: (77, 159, 220, 255, "Water")},

    'lifeform_veg_cat_l4a': {0: (255, 255, 255, 255, "No Data / Not vegetated"),
                             1: (14, 121, 18, 255, "Woody Vegetation"),
                             2: (172, 188, 45, 255, "Herbaceous Vegetation")},

    'canopyco_veg_cat_l4d': {0: (255, 255, 255, 255, "No Data / Not vegetated"),
                             10: (14,  121, 18,  255, "> 65 % cover"),
                             12: (45,  141, 47,  255, "40 to 65 % cover"),
                             13: (80,  160, 82,  255, "15 to 40 % cover"),
                             15: (117, 180, 118, 255, "4 to 15 % cover"),
                             16: (154, 199, 156, 255, "1 to 4 % cover")},

    'waterstt_wat_cat_l4a': {0: (255, 255, 255, 255, "No Data / Not water"),
                             1: (77, 159, 220, 255, "water")},

    'watersea_veg_cat_l4a_au': {0: (255, 255, 255, 255, "No data / Not aquatic vegetation"),
                                1: (25,  173, 109, 255, "> 3 months"),
                                2: (176, 218, 201, 255, "< 3 months")},

    'inttidal_wat_cat_l4a': {0: (255, 255, 255, 255, "No data / Not intertidal"),
                             3: (77, 159, 220, 255, "Intertidal")},

    'waterper_wat_cat_l4d_au': {0: (255, 255, 255, 255, "No data / Not water"),
                                1: (27,  85,  186, 255, "> 9 months"),
                                7: (52,  121, 201, 255, "7 to 9 months"),
                                8: (79,  157, 217, 255, "4 to 6 months"),
                                9: (113, 202, 253, 255, "1 to 3 months")},

    'baregrad_phy_cat_l4d_au': {0: (255, 255, 255, 255, "No data / Not bare"),
                                10: (255, 230, 140, 255, "Sparsely vegetated (< 20% bare)"),
                                12: (250, 210, 110, 255, "Very sparsely vegetated (20 to 60% bare)"),
                                15: (243, 171, 105, 255, "Bare areas, unvegetated (> 60% bare)")},

    'level4': {0: (255, 255, 255, 255, "No Data"),
               1: (151, 187, 26, 255, 'Cultivated Terrestrial Vegetated:'),
               2: (151, 187, 26, 255, 'Cultivated Terrestrial Vegetated: Woody'),
               3: (209, 224, 51, 255, 'Cultivated Terrestrial Vegetated: Herbaceous'),
               4: (197, 168, 71, 255, 'Cultivated Terrestrial Vegetated: Closed (> 65 %)'),
               5: (205, 181, 75, 255, 'Cultivated Terrestrial Vegetated: Open (40 to 65 %)'),
               6: (213, 193, 79, 255, 'Cultivated Terrestrial Vegetated: Open (15 to 40 %)'),
               7: (228, 210, 108, 255, 'Cultivated Terrestrial Vegetated: Sparse (4 to 15 %)'),
               8: (242, 227, 138, 255, 'Cultivated Terrestrial Vegetated: Scattered (1 to 4 %)'),
               9: (197, 168, 71, 255, 'Cultivated Terrestrial Vegetated: Woody Closed (> 65 %)'),
               10: (205, 181, 75, 255, 'Cultivated Terrestrial Vegetated: Woody Open (40 to 65 %)'),
               11: (213, 193, 79, 255, 'Cultivated Terrestrial Vegetated: Woody Open (15 to 40 %)'),
               12: (228, 210, 108, 255, 'Cultivated Terrestrial Vegetated: Woody Sparse (4 to 15 %)'),
               13: (242, 227, 138, 255, 'Cultivated Terrestrial Vegetated: Woody Scattered (1 to 4 %)'),
               14: (228, 224, 52, 255, 'Cultivated Terrestrial Vegetated: Herbaceous Closed (> 65 %)'),
               15: (235, 232, 84, 255, 'Cultivated Terrestrial Vegetated: Herbaceous Open (40 to 65 %)'),
               16: (242, 240, 127, 255, 'Cultivated Terrestrial Vegetated: Herbaceous Open (15 to 40 %)'),
               17: (249, 247, 174, 255, 'Cultivated Terrestrial Vegetated: Herbaceous Sparse (4 to 15 %)'),
               18: (255, 254, 222, 255, 'Cultivated Terrestrial Vegetated: Herbaceous Scattered (1 to 4 %)'),
               19: (14, 121, 18, 255, 'Natural Terrestrial Vegetated:'),
               20: (26, 177, 87, 255, 'Natural Terrestrial Vegetated: Woody'),
               21: (94, 179, 31, 255, 'Natural Terrestrial Vegetated: Herbaceous'),
               22: (14, 121, 18, 255, 'Natural Terrestrial Vegetated: Closed (> 65 %)'),
               23: (45, 141, 47, 255, 'Natural Terrestrial Vegetated: Open (40 to 65 %)'),
               24: (80, 160, 82, 255, 'Natural Terrestrial Vegetated: Open (15 to 40 %)'),
               25: (117, 180, 118, 255, 'Natural Terrestrial Vegetated: Sparse (4 to 15 %)'),
               26: (154, 199, 156, 255, 'Natural Terrestrial Vegetated: Scattered (1 to 4 %)'),
               27: (14, 121, 18, 255, 'Natural Terrestrial Vegetated: Woody Closed (> 65 %)'),
               28: (45, 141, 47, 255, 'Natural Terrestrial Vegetated: Woody Open (40 to 65 %)'),
               29: (80, 160, 82, 255, 'Natural Terrestrial Vegetated: Woody Open (15 to 40 %)'),
               30: (117, 180, 118, 255, 'Natural Terrestrial Vegetated: Woody Sparse (4 to 15 %)'),
               31: (154, 199, 156, 255, 'Natural Terrestrial Vegetated: Woody Scattered (1 to 4 %)'),
               32: (119, 167, 30, 255, 'Natural Terrestrial Vegetated: Herbaceous Closed (> 65 %)'),
               33: (136, 182, 51, 255, 'Natural Terrestrial Vegetated: Herbaceous Open (40 to 65 %)'),
               34: (153, 196, 80, 255, 'Natural Terrestrial Vegetated: Herbaceous Open (15 to 40 %)'),
               35: (170, 212, 113, 255, 'Natural Terrestrial Vegetated: Herbaceous Sparse (4 to 15 %)'),
               36: (186, 226, 146, 255, 'Natural Terrestrial Vegetated: Herbaceous Scattered (1 to 4 %)'),
               37: (86, 236, 231, 255, 'Cultivated Aquatic Vegetated:'),
               38: (61, 170, 140, 255, 'Cultivated Aquatic Vegetated: Woody'),
               39: (82, 231, 172, 255, 'Cultivated Aquatic Vegetated: Herbaceous'),
               40: (43, 210, 203, 255, 'Cultivated Aquatic Vegetated: Closed (> 65 %)'),
               41: (73, 222, 216, 255, 'Cultivated Aquatic Vegetated: Open (40 to 65 %)'),
               42: (110, 233, 228, 255, 'Cultivated Aquatic Vegetated: Open (15 to 40 %)'),
               43: (149, 244, 240, 255, 'Cultivated Aquatic Vegetated: Sparse (4 to 15 %)'),
               44: (187, 255, 252, 255, 'Cultivated Aquatic Vegetated: Scattered (1 to 4 %)'),
               45: (43, 210, 203, 255, 'Cultivated Aquatic Vegetated: Woody Closed (> 65 %)'),
               46: (73, 222, 216, 255, 'Cultivated Aquatic Vegetated: Woody Open (40 to 65 %)'),
               47: (110, 233, 228, 255, 'Cultivated Aquatic Vegetated: Woody Open (15 to 40 %)'),
               48: (149, 244, 240, 255, 'Cultivated Aquatic Vegetated: Woody Sparse (4 to 15 %)'),
               49: (187, 255, 252, 255, 'Cultivated Aquatic Vegetated: Woody Scattered (1 to 4 %)'),
               50: (82, 231, 196, 255, 'Cultivated Aquatic Vegetated: Herbaceous Closed (> 65 %)'),
               51: (113, 237, 208, 255, 'Cultivated Aquatic Vegetated: Herbaceous Open (40 to 65 %)'),
               52: (144, 243, 220, 255, 'Cultivated Aquatic Vegetated: Herbaceous Open (15 to 40 %)'),
               53: (175, 249, 232, 255, 'Cultivated Aquatic Vegetated: Herbaceous Sparse (4 to 15 %)'),
               54: (207, 255, 244, 255, 'Cultivated Aquatic Vegetated: Herbaceous Scattered (1 to 4 %)'),
               55: (30, 191, 121, 255, 'Natural Aquatic Vegetated:'),
               56: (18, 142, 148, 255, 'Natural Aquatic Vegetated: Woody'),
               57: (112, 234, 134, 255, 'Natural Aquatic Vegetated: Herbaceous'),
               58: (25, 173, 109, 255, 'Natural Aquatic Vegetated: Closed (> 65 %)'),
               59: (53, 184, 132, 255, 'Natural Aquatic Vegetated: Open (40 to 65 %)'),
               60: (93, 195, 155, 255, 'Natural Aquatic Vegetated: Open (15 to 40 %)'),
               61: (135, 206, 178, 255, 'Natural Aquatic Vegetated: Sparse (4 to 15 %)'),
               62: (176, 218, 201, 255, 'Natural Aquatic Vegetated: Scattered (1 to 4 %)'),
               63: (25, 173, 109, 255, 'Natural Aquatic Vegetated: Woody Closed (> 65 %)'),
               64: (25, 173, 109, 255, 'Natural Aquatic Vegetated: Woody Closed (> 65 %) Water > 3 months (semi-) permenant'),
               65: (25, 173, 109, 255, 'Natural Aquatic Vegetated: Woody Closed (> 65 %) Water < 3 months (temporary or seasonal)'),
               66: (53, 184, 132, 255, 'Natural Aquatic Vegetated: Woody Open (40 to 65 %)'),
               67: (53, 184, 132, 255, 'Natural Aquatic Vegetated: Woody Open (40 to 65 %) Water > 3 months (semi-) permenant'),
               68: (53, 184, 132, 255, 'Natural Aquatic Vegetated: Woody Open (40 to 65 %) Water < 3 months (temporary or seasonal)'),
               69: (93, 195, 155, 255, 'Natural Aquatic Vegetated: Woody Open (15 to 40 %)'),
               70: (93, 195, 155, 255, 'Natural Aquatic Vegetated: Woody Open (15 to 40 %) Water > 3 months (semi-) permenant'),
               71: (93, 195, 155, 255, 'Natural Aquatic Vegetated: Woody Open (15 to 40 %) Water < 3 months (temporary or seasonal)'),
               72: (135, 206, 178, 255, 'Natural Aquatic Vegetated: Woody Sparse (4 to 15 %)'),
               73: (135, 206, 178, 255, 'Natural Aquatic Vegetated: Woody Sparse (4 to 15 %) Water > 3 months (semi-) permenant'),
               74: (135, 206, 178, 255, 'Natural Aquatic Vegetated: Woody Sparse (4 to 15 %) Water < 3 months (temporary or seasonal)'),
               75: (176, 218, 201, 255, 'Natural Aquatic Vegetated: Woody Scattered (1 to 4 %)'),
               76: (176, 218, 201, 255, 'Natural Aquatic Vegetated: Woody Scattered (1 to 4 %) Water > 3 months (semi-) permenant'),
               77: (176, 218, 201, 255, 'Natural Aquatic Vegetated: Woody Scattered (1 to 4 %) Water < 3 months (temporary or seasonal)'),
               78: (39, 204, 139, 255, 'Natural Aquatic Vegetated: Herbaceous Closed (> 65 %)'),
               79: (39, 204, 139, 255, 'Natural Aquatic Vegetated: Herbaceous Closed (> 65 %) Water > 3 months (semi-) permenant'),
               80: (39, 204, 139, 255, 'Natural Aquatic Vegetated: Herbaceous Closed (> 65 %) Water < 3 months (temporary or seasonal)'),
               81: (66, 216, 159, 255, 'Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %)'),
               82: (66, 216, 159, 255, 'Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %) Water > 3 months (semi-) permenant'),
               83: (66, 216, 159, 255, 'Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %) Water < 3 months (temporary or seasonal)'),
               84: (99, 227, 180, 255, 'Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %)'),
               85: (99, 227, 180, 255, 'Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %) Water > 3 months (semi-) permenant'),
               86: (99, 227, 180, 255, 'Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %) Water < 3 months (temporary or seasonal)'),
               87: (135, 239, 201, 255, 'Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %)'),
               88: (135, 239, 201, 255, 'Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %) Water > 3 months (semi-) permenant'),
               89: (135, 239, 201, 255, 'Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %) Water < 3 months (temporary or seasonal)'),
               90: (171, 250, 221, 255, 'Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %)'),
               91: (171, 250, 221, 255, 'Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %) Water > 3 months (semi-) permenant'),
               92: (171, 250, 221, 255, 'Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %) Water < 3 months (temporary or seasonal)'),
               93: (218, 92, 105, 255, 'Artificial Surface:'),
               94: (243, 171, 105, 255, 'Natural Surface:'),
               95: (255, 230, 140, 255, 'Natural Surface: Sparsely vegetated'),
               96: (250, 210, 110, 255, 'Natural Surface: Very sparsely vegetated'),
               97: (243, 171, 105, 255, 'Natural Surface: Bare areas, unvegetated'),
               98: (77, 159, 220, 255, 'Water:'),
               99: (77, 159, 220, 255, 'Water: (Water)'),
               100: (187, 220, 233, 255, 'Water: (Water) Tidal area'),
               101: (27, 85, 186, 255, 'Water: (Water) Perennial (> 9 months)'),
               102: (52, 121, 201, 255, 'Water: (Water) Non-perennial (7 to 9 months)'),
               103: (79, 157, 217, 255, 'Water: (Water) Non-perennial (4 to 6 months)'),
               104: (133, 202, 253, 255, 'Water: (Water) Non-perennial (1 to 3 months)'),
               105: (250, 250, 250, 255, 'Water: (Snow)')}
}


def get_layer_name(layer, da):
    aliases = {
        'lifeform':'lifeform_veg_cat_l4a',
        'vegetation_cover':'canopyco_veg_cat_l4d',
        'water_seasonality':'watersea_veg_cat_l4a_au',
        'water_state':'waterstt_wat_cat_l4a',
        'intertidal':'inttidal_wat_cat_l4a',
        'water_persistence':'waterper_wat_cat_l4d_au',
        'bare_gradation':'baregrad_phy_cat_l4d_au',
        'full_classification':'level4'
    }

    # use provided layer if able
    layer = layer.lower() if layer else da.name
    layer = aliases[layer] if layer in aliases.keys() else layer
    return layer

def wrap_label_txt(class_lablels):
    """
    this fuction adds new line breaks to the lables of
    land Cover classes in order to wrap the text on colour bars and axes lables
    for level 4 classes with very long names (Aquatic vegetation classes with 
    details of both cover fraction and water sasonality) are cut to the first 9 'words' 

    Parameters
    --------------
    class_lablels : a list of strings
                    Lables of classes to have line breaks added

    returns:
    -------------
    new_listoflabels : a list of strings

    """
    new_listoflabels = []

    for label in class_lablels:
        words = label.split()
        x_words = len(words)

        if x_words == 3:
            new_label = words[0] + " " + words[1] + "\n " + words[2]

        elif x_words == 4:
            new_label = words[0] + " " + words[1] + "\n " + words[2] + " " + words[3]

        elif x_words == 7:
            new_label = (words[0] + " " + words[1] + "\n " + words[2] + " "
            + words[3]+ "\n " + words[4] + " " + words[5]+ " " + words[6])
            
        elif x_words == 8:
            new_label = (words[0] + " " + words[1] + "\n " + words[2] + " "
            + words[3]+ "\n " + words[4] + " " + words[5]+ " " + words[6]
            + " " + words[7])

        elif x_words >= 9:
            
            if words[8] == 'Water':
            
                new_label = (words[0] + " " + words[1] + "\n " + words[2] + " "
                + words[3]+ "\n " + words[4] + " " + words[5]+ " " + words[6]
                + " " + words[7])

            else:
                
                new_label = (words[0] + " " + words[1] + "\n " + words[2] + " "
                + words[3]+ "\n " + words[4] + " " + words[5]+ " " + words[6]
                + " " + words[7] + " " + words[8])
        

        try:
            new_listoflabels.append(new_label)
        
        except:
            new_listoflabels.append(label)
        

    return new_listoflabels


def lc_colourmap(colour_scheme, colour_bar=False):
    """
    returns colour map and normalisation for the provided DEA Land Cover layer, for use in plotting with Maptplotlib library

    Parameters
    ----------
    colour_scheme : string
        Name of land cover colour scheme to use
        Valid options: 'level3', 'level4', 'lifeform_veg_cat_l4a', 'canopyco_veg_cat_l4d', 'watersea_veg_cat_l4a_au',
        'waterstt_wat_cat_l4a', 'inttidal_wat_cat_l4a', 'waterper_wat_cat_l4d_au', 'baregrad_phy_cat_l4d_au'
    colour_bar : bool, optional
        Controls if colour bar labels are returned as a list for plotting a colour bar.
        Default :  False
    Returns
    ---------
    cmap : matplotlib colormap
        matplotlib colormap containing the colour scheme for the specified DEA Land Cover layer
    norm : matplotlib colormap index
        matplotlib colormap index based on the descrete intervals of the classes in the specified DEA Land Cover layer.
        ensures the colormap maps the colours to the class numbers correctly
    cblables : list
        A list of strings containing the lables of the classes found in the chosen  DEA Land Cover layer
    """

    colour_scheme = colour_scheme.lower()
    # ensure a valid colour scheme was requested
    assert (colour_scheme in lc_colours.keys()), f'colour scheme must be one of [{lc_colours.keys()}] (got "{colour_scheme}")'

    # get colour definitions
    lc_colour_scheme = lc_colours[colour_scheme]

    # create colour map
    colour_arr = []
    cblabels = []
    for key, value in lc_colour_scheme.items():
        colour_arr.append(np.array(value[:-2]) / 255)
        if colour_bar:
            cblabels.append(value[-1])

    cmap = mcolours.ListedColormap(colour_arr)
    bounds = list(lc_colour_scheme)
    bounds.append(255)
    norm = mcolours.BoundaryNorm(np.array(bounds) - 0.1, cmap.N)

    if colour_bar == False:
        return (cmap, norm)
    else:
        return (cmap, norm, cblabels)


# plot layer from colour map
def plot_land_cover(data, year=None, layer=None, out_width=15, col_wrap=4):
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

    layer = get_layer_name(layer, data)
    cmap, norm, cblabels = lc_colourmap(layer, colour_bar=True)

    height, width = data.geobox.shape
    scale = out_width / width

    if year == None:
        # plot all dates for the provided layer
        if len(data.dims) < 3:
            im = data.plot.imshow(cmap=cmap, norm=norm, add_colorbar=True, figsize=(width * scale, height * scale))
            cb = im.colorbar
        else:
            if col_wrap > len(data.time): col_wrap = len(data.time)
            im = data.plot.imshow(cmap=cmap, norm=norm, add_colorbar=True, col="time", col_wrap=col_wrap,
                                  figsize=(width * scale, (height * scale / col_wrap) * (len(data.time) / col_wrap)))
            cb = im.cbar
    else:
        # plot only the provided year
        year_string = f"{year}-01-01"
        data = data.sel(time=year_string, method="nearest")
        im = data.plot.imshow(cmap=cmap, norm=norm, add_colorbar=True, figsize=(width * scale, height * scale))
        cb = im.colorbar

    ticks = cb.get_ticks()
    cb.set_ticks(ticks + np.diff(ticks, append=256) / 2)
    cb.set_ticklabels(cblabels)

    return im


def lc_animation(
    da,
    file_name="default_animation",
    layer=None,
    stacked_plot=False,
    colour_bar=False,
    animation_interval=500,
    width_pixels=25,
    dpi=72,
    ticks=True
):
    """
    creates an animation of a landcover maps though time beside corrosponding stacked plots of the landcover classes. Saves the
    animation to a file and   displays the annimation in notebook
    Inputs
    -------
    da : xarray.DataArray
        xarray containing a multi-date stack of observations of a single landcover level.
    file_name: String, optional.
        string used to create filename for saved animation file. Default: "default_animation" code adds gif suffix.
    layer : String, optional
        string specifiying wich DEA land cover layer colour scheme should be used. If non provided reads data array.name from ds to determine.
    Stacked_plot: Boolean, Optional
        determines if a stacked plot showing the percentage of area taken up by each class in each time slice is added to the animation. Default : False
    colour_bar : Boolean, Optional
        determines if a colour bar is generated for the animation. this is NOT recommended for use with level 4 data. Default : False
    animation_interval : int , optional
        How quickly the frames of the animations should be re-drawn. default : 500
    Width_pixels : int , optional
        how wide in pixles the animation plot should be. default : 500
    dpi : int : optional
        stands for 'Dots Per Inch'. passed to the fuction that saves the animation and deterimines the resolution. A higher number will produce a higher 
        resolution image but a larger file size and slower processing. default : 400

    Returns
    ---------
    A gif file animation
    """

    def calc_class_ratio(da):
        """creates a table listing year by year what percentage of the total area is taken up by each class.

        Parameters
        ----------
        da : xarray.DataArray with time dimension

        Returns
        -------
        Pandas Dataframe : containing class percentages per year
        """

        # list all class codes in dataset
        list_classes = (np.unique(da, return_counts=False)).tolist()

        # create empty dataframe & dictionary
        ratio_table = pd.DataFrame(data=None, columns=list_classes)
        date_line = {}

        # count all pixels, should be consistent
        total_pix = int(np.sum(da.isel(time=1)))

        # iterate through each year in dataset
        for i in range(0, len(da.time)):
            date = str(da.time[i].data)[0:10]

            # for each year iterate though each present class number and count pixels
            for n in list_classes:
                number_of_pixles = int(np.sum(da.isel(time=i) == n))
                percentage = number_of_pixles / total_pix * 100
                date_line[n] = percentage

            # add each year's counts to dataframe
            ratio_table.loc[date] = date_line

        return ratio_table
    
    
    def make_colorbar(fig, ax, da, layer_cmap, layer_norm, cblabels, horizontal=False):
        """
        Adds a new colorbar to the animation with apropreate land cover 
        colours and lables
        """
        # Create new axis object for colorbar
        
        # perameters for add_axes are [left, bottom, width, height], in fractions of total plot
        
        if horizontal == True: 
            # axes settings for horizontal position
            cax = fig.add_axes([0.02, 0.05, 0.90, 0.03])
            
        else:
            
            # axes settings for Vertical position
            cax = fig.add_axes([0.84, 0.15, 0.03, 0.70])

        # Initialise color bar using plot min and max values
        img = ax.imshow(da, cmap=layer_cmap, norm=layer_norm)
        cb=fig.colorbar(img,
                     cax=cax,
#                      orientation='horizontal',
                     )
                #set colourbar lables
            
        # apply text wrapping to lables
        cblabels = wrap_label_txt(cblabels)
            
        tick_font_size = 18
        cb.ax.tick_params(labelsize=tick_font_size)
        ticks = cb.get_ticks()
        cb.set_ticks(ticks + np.diff(ticks, append=256) / 2)
        cb.set_ticklabels(cblabels)


    def rgb_to_hex(r, g, b):
        hex = "#%x%x%x" % (r, g, b)
        if len(hex) < 7:
            hex = "#0" + hex[1:]
        return hex

    layer = get_layer_name(layer, da)

    # add gif to end of filename
    file_name = file_name + ".gif"

    # create colour map and normalisation for specified lc layer
    layer_cmap, layer_norm, cblabels = lc_colourmap(layer, colour_bar=True)

    # prepare variables needed
    # Get info on dataset dimensions
    height, width = da.geobox.shape
    scale = width_pixels / width
    left, bottom, right, top = da.geobox.extent.boundingbox
    extent = [left, right, bottom, top]

    outline = [patheffects.withStroke(linewidth=2.5, foreground="black")]
    annotation_defaults = {
        "xy": (1, 1),
        "xycoords": "axes fraction",
        "xytext": (-5, -5),
        "textcoords": "offset points",
        "horizontalalignment": "right",
        "verticalalignment": "top",
        "fontsize": 25,
        "color": "white",
        "path_effects": outline,
    }

    # Get information needed to display the year in the top corner
    times_list = da.time.dt.strftime("%Y").values
    text_list = [False] * len(times_list)
    annotation_list = ["\n".join([str(i) for i in (a, b) if i]) for a, b in zip(times_list, text_list)]

    if stacked_plot == True:

        # create table for stacked plot
        stacked_plot_table = calc_class_ratio(da)


        # build colour list of hex vals for stacked plot
        hex_colour_list = []
        colour_def = lc_colours[layer]

        # custom error message to help if user puts incorrect layer name
        for val in list(stacked_plot_table):
            try:
                r, g, b = colour_def[val][0:3]
            except KeyError:
                raise KeyError("class number not found in colour definition. Ensure layer name provided matches the dataset being used")
            hex_val = rgb_to_hex(r,g,b)
            hex_colour_list.append(hex_val)

        # define & set up figure
        fig, (ax1, ax2) = plt.subplots(1, 2, dpi=dpi, constrained_layout=True)
        fig.set_size_inches(width * scale * 2, height * scale, forward=True)
        fig.set_constrained_layout_pads(w_pad=0.2, h_pad=0.2, hspace=0, wspace=0)
        #add colourbar here

        # This function is called at regular intervals with changing i values for each frame
        def _update_frames(i, ax1, ax2, extent, annotation_text, annotation_defaults, cmap, norm):
            # Clear previous frame to optimise render speed and plot imagery
            ax1.clear()
            ax2.clear()

            ax1.imshow(da[i, ...], cmap=cmap, norm=norm, extent=extent, interpolation="nearest")
            if(not ticks): ax1.set_axis_off()

            clipped_table = stacked_plot_table.iloc[: int(i + 1)]
            data = clipped_table.to_dict(orient="list")
            date = clipped_table.index

            ax2.stackplot(date, data.values(), colors=hex_colour_list)
            ax2.tick_params(axis="x", labelrotation=-45)
            ax2.margins(x=0, y=0)

            # Add annotation text
            ax1.annotate(annotation_text[i], **annotation_defaults)
            ax2.annotate(annotation_text[i], **annotation_defaults)

        # anim_fargs contains all the values we send to our _update_frames function.
        # Note the layer_cmap and layer_norm which were calculated earlier being passed through
        anim_fargs = (
            ax1,
            ax2,  # axis to plot into
            [left, right, bottom, top],  # imshow extent
            annotation_list,
            annotation_defaults,
            layer_cmap,
            layer_norm,
        )

    else: # stacked_plot = False
        # define & set up figure
        fig, ax1 = plt.subplots(1, 1, dpi=dpi)
        fig.set_size_inches(width * scale, height * scale, forward=True)

        #add colourbar here
        if colour_bar:
            # shift plot over make room for colour bar
            fig.subplots_adjust(right=0.825)
            make_colorbar(fig, ax1, da[0], layer_cmap, layer_norm, cblabels)

        # This function is called at regular intervals with changing i values for each frame
        def _update_frames(i, ax1, extent, annotation_text, annotation_defaults, cmap, norm):
            # Clear previous frame to optimise render speed and plot imagery
            ax1.clear()
            ax1.imshow(da[i, ...], cmap=cmap, norm=norm, extent=extent, interpolation="nearest")
            if(not ticks): ax1.set_axis_off()

            # Add annotation text
            ax1.annotate(annotation_text[i], **annotation_defaults)
            

        # anim_fargs contains all the values we send to our _update_frames function.
        # Note the layer_cmap and layer_norm which were calculated earlier being passed through
        anim_fargs = (
            ax1,
            [left, right, bottom, top],  # imshow extent
            annotation_list,
            annotation_defaults,
            layer_cmap,
            layer_norm,
        )

    # animate
    anim = FuncAnimation(
        fig=fig,
        func=_update_frames,
        fargs=anim_fargs,
        frames=len(da.time),
        interval=animation_interval,
        repeat=False,
    )

    anim.save(file_name, writer="pillow", dpi=dpi)
    plt.close()
    return Image(filename=file_name)