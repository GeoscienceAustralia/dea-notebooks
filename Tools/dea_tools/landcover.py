# -*- coding: utf-8 -*-
# Land_cover_plotting.py
"""
Plotting and animating Digital Earth Australia Land Cover data.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one
on GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: May 2025
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Image
from matplotlib import colors as mcolours
from matplotlib import patheffects
from matplotlib.animation import FuncAnimation

# Define colour schemes for each land cover measurement
lc_colours = {
    "level3": {
        111: (172, 188, 45, 255, "Cultivated\nTerrestrial\nVegetation"),
        112: (14, 121, 18, 255, "Natural\nTerrestrial\nVegetation"),
        124: (30, 191, 121, 255, "Natural\nAquatic\nVegetation"),
        215: (218, 92, 105, 255, "Artificial\nSurface"),
        216: (243, 171, 105, 255, "Natural\nBare\nSurface"),
        220: (77, 159, 220, 255, "Water"),
        255: (255, 255, 255, 255, "No Data"),
    },
    "level3_change_colour_scheme": {
        0: (255, 255, 255, 255, "No Change"),
        111112: (14, 121, 18, 255, "CTV -> NTV"),
        111215: (218, 92, 105, 255, "CTV -> AS"),
        111216: (243, 171, 105, 255, "CTV -> BS"),
        111220: (77, 159, 220, 255, "CTV -> Water"),
        112111: (172, 188, 45, 255, "NTV -> CTV"),
        112215: (218, 92, 105, 255, "NTV -> AS"),
        112216: (243, 171, 105, 255, "NTV -> BS"),
        112220: (77, 159, 220, 255, "NTV -> Water"),
        124220: (77, 159, 220, 255, "NAV -> Water"),
        215111: (172, 188, 45, 255, "AS -> CTV"),
        215112: (14, 121, 18, 255, "AS -> NTV"),
        215216: (243, 171, 105, 255, "AS -> BS"),
        215220: (77, 159, 220, 255, "AS -> Water"),
        216111: (172, 188, 45, 255, "BS -> CTV"),
        216112: (14, 121, 18, 255, "BS -> NTV"),
        216215: (218, 92, 105, 255, "BS -> AS"),
        216220: (77, 159, 220, 255, "BS -> Water"),
        220112: (14, 121, 18, 255, "Water -> NTV"),
        220216: (243, 171, 105, 255, "Water -> BS"),
    },
    "level3_change_colour_bar": {
        111: (172, 188, 45, 255, "Changed to Cultivated\n Terrestrial Vegetation"),
        112: (14, 121, 18, 255, "Changed to Natural\n Terrestrial Vegetation"),
        124: (30, 191, 121, 255, "Changed to Natural\n Aquatic Vegetation"),
        215: (218, 92, 105, 255, "Changed to Artificial\n Surface"),
        216: (243, 171, 105, 255, "Changed to Natural\n Bare Surface"),
        220: (77, 159, 220, 255, "Changed to Water"),
        0: (255, 255, 255, 255, "No Change"),
    },
    "level4": {
        1: (151, 187, 26, 255, "Cultivated Terrestrial\n Vegetated:"),
        2: (151, 187, 26, 255, "Cultivated Terrestrial\n Vegetated: Woody"),
        3: (209, 224, 51, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous"),
        4: (197, 168, 71, 255, "Cultivated Terrestrial\n Vegetated: Closed\n (> 65 %)"),
        5: (205, 181, 75, 255, "Cultivated Terrestrial\n Vegetated: Open\n (40 to 65 %)"),
        6: (213, 193, 79, 255, "Cultivated Terrestrial\n Vegetated: Open\n (15 to 40 %)"),
        7: (228, 210, 108, 255, "Cultivated Terrestrial\n Vegetated: Sparse\n (4 to 15 %)"),
        8: (242, 227, 138, 255, "Cultivated Terrestrial\n Vegetated: Scattered\n (1 to 4 %)"),
        9: (197, 168, 71, 255, "Cultivated Terrestrial\n Vegetated: Woody Closed\n (> 65 %)"),
        10: (205, 181, 75, 255, "Cultivated Terrestrial\n Vegetated: Woody Open\n (40 to 65 %)"),
        11: (213, 193, 79, 255, "Cultivated Terrestrial\n Vegetated: Woody Open\n (15 to 40 %)"),
        12: (228, 210, 108, 255, "Cultivated Terrestrial\n Vegetated: Woody Sparse\n (4 to 15 %)"),
        13: (242, 227, 138, 255, "Cultivated Terrestrial\n Vegetated: Woody Scattered\n (1 to 4 %)"),
        14: (228, 224, 52, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous Closed\n (> 65 %)"),
        15: (235, 232, 84, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous Open\n (40 to 65 %)"),
        16: (242, 240, 127, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous Open\n (15 to 40 %)"),
        17: (249, 247, 174, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous Sparse\n (4 to 15 %)"),
        18: (255, 254, 222, 255, "Cultivated Terrestrial\n Vegetated: Herbaceous Scattered\n (1 to 4 %)"),
        19: (14, 121, 18, 255, "Natural Terrestrial Vegetated:"),
        20: (26, 177, 87, 255, "Natural Terrestrial Vegetated: Woody"),
        21: (94, 179, 31, 255, "Natural Terrestrial Vegetated: Herbaceous"),
        22: (14, 121, 18, 255, "Natural Terrestrial Vegetated: Closed (> 65 %)"),
        23: (45, 141, 47, 255, "Natural Terrestrial Vegetated: Open (40 to 65 %)"),
        24: (80, 160, 82, 255, "Natural Terrestrial Vegetated: Open (15 to 40 %)"),
        25: (117, 180, 118, 255, "Natural Terrestrial Vegetated: Sparse (4 to 15 %)"),
        26: (154, 199, 156, 255, "Natural Terrestrial Vegetated: Scattered (1 to 4 %)"),
        27: (14, 121, 18, 255, "Natural Terrestrial Vegetated: Woody Closed (> 65 %)"),
        28: (45, 141, 47, 255, "Natural Terrestrial Vegetated: Woody Open (40 to 65 %)"),
        29: (80, 160, 82, 255, "Natural Terrestrial Vegetated: Woody Open (15 to 40 %)"),
        30: (117, 180, 118, 255, "Natural Terrestrial Vegetated: Woody Sparse (4 to 15 %)"),
        31: (154, 199, 156, 255, "Natural Terrestrial Vegetated: Woody Scattered (1 to 4 %)"),
        32: (119, 167, 30, 255, "Natural Terrestrial Vegetated: Herbaceous Closed (> 65 %)"),
        33: (136, 182, 51, 255, "Natural Terrestrial Vegetated: Herbaceous Open (40 to 65 %)"),
        34: (153, 196, 80, 255, "Natural Terrestrial Vegetated: Herbaceous Open (15 to 40 %)"),
        35: (170, 212, 113, 255, "Natural Terrestrial Vegetated: Herbaceous Sparse (4 to 15 %)"),
        36: (186, 226, 146, 255, "Natural Terrestrial Vegetated: Herbaceous Scattered (1 to 4 %)"),
        37: (86, 236, 231, 255, "Cultivated Aquatic Vegetated:"),
        38: (61, 170, 140, 255, "Cultivated Aquatic Vegetated: Woody"),
        39: (82, 231, 172, 255, "Cultivated Aquatic Vegetated: Herbaceous"),
        40: (43, 210, 203, 255, "Cultivated Aquatic Vegetated: Closed (> 65 %)"),
        41: (73, 222, 216, 255, "Cultivated Aquatic Vegetated: Open (40 to 65 %)"),
        42: (110, 233, 228, 255, "Cultivated Aquatic Vegetated: Open (15 to 40 %)"),
        43: (149, 244, 240, 255, "Cultivated Aquatic Vegetated: Sparse (4 to 15 %)"),
        44: (187, 255, 252, 255, "Cultivated Aquatic Vegetated: Scattered (1 to 4 %)"),
        # 45: (43, 210, 203, 255, 'Cultivated Aquatic Vegetated: Woody Closed (> 65 %)'),
        # 46: (73, 222, 216, 255, 'Cultivated Aquatic Vegetated: Woody Open (40 to 65 %)'),
        # 47: (110, 233, 228, 255, 'Cultivated Aquatic Vegetated: Woody Open (15 to 40 %)'),
        # 48: (149, 244, 240, 255, 'Cultivated Aquatic Vegetated: Woody Sparse (4 to 15 %)'),
        # 49: (187, 255, 252, 255, 'Cultivated Aquatic Vegetated: Woody Scattered (1 to 4 %)'),
        50: (82, 231, 196, 255, "Cultivated Aquatic Vegetated: Herbaceous Closed (> 65 %)"),
        51: (113, 237, 208, 255, "Cultivated Aquatic Vegetated: Herbaceous Open (40 to 65 %)"),
        52: (144, 243, 220, 255, "Cultivated Aquatic Vegetated: Herbaceous Open (15 to 40 %)"),
        53: (175, 249, 232, 255, "Cultivated Aquatic Vegetated: Herbaceous Sparse (4 to 15 %)"),
        54: (207, 255, 244, 255, "Cultivated Aquatic Vegetated: Herbaceous Scattered (1 to 4 %)"),
        55: (30, 191, 121, 255, "Natural Aquatic Vegetated:"),
        56: (18, 142, 148, 255, "Natural Aquatic Vegetated: Woody"),
        57: (112, 234, 134, 255, "Natural Aquatic Vegetated: Herbaceous"),
        58: (25, 173, 109, 255, "Natural Aquatic Vegetated: Closed (> 65 %)"),
        59: (53, 184, 132, 255, "Natural Aquatic Vegetated: Open (40 to 65 %)"),
        60: (93, 195, 155, 255, "Natural Aquatic Vegetated: Open (15 to 40 %)"),
        61: (135, 206, 178, 255, "Natural Aquatic Vegetated: Sparse (4 to 15 %)"),
        62: (176, 218, 201, 255, "Natural Aquatic Vegetated: Scattered (1 to 4 %)"),
        63: (25, 173, 109, 255, "Natural Aquatic Vegetated: Woody Closed (> 65 %)"),
        64: (25, 173, 109, 255, "Natural Aquatic Vegetated: Woody Closed (> 65 %) Water > 3 months (semi-) permanent"),
        65: (
            25,
            173,
            109,
            255,
            "Natural Aquatic Vegetated: Woody Closed (> 65 %) Water < 3 months (temporary or seasonal)",
        ),
        66: (53, 184, 132, 255, "Natural Aquatic Vegetated: Woody Open (40 to 65 %)"),
        67: (
            53,
            184,
            132,
            255,
            "Natural Aquatic Vegetated: Woody Open (40 to 65 %) Water > 3 months (semi-) permanent",
        ),
        68: (
            53,
            184,
            132,
            255,
            "Natural Aquatic Vegetated: Woody Open (40 to 65 %) Water < 3 months (temporary or seasonal)",
        ),
        69: (93, 195, 155, 255, "Natural Aquatic Vegetated: Woody Open (15 to 40 %)"),
        70: (
            93,
            195,
            155,
            255,
            "Natural Aquatic Vegetated: Woody Open (15 to 40 %) Water > 3 months (semi-) permanent",
        ),
        71: (
            93,
            195,
            155,
            255,
            "Natural Aquatic Vegetated: Woody Open (15 to 40 %) Water < 3 months (temporary or seasonal)",
        ),
        72: (135, 206, 178, 255, "Natural Aquatic Vegetated: Woody Sparse (4 to 15 %)"),
        73: (
            135,
            206,
            178,
            255,
            "Natural Aquatic Vegetated: Woody Sparse (4 to 15 %) Water > 3 months (semi-) permanent",
        ),
        74: (
            135,
            206,
            178,
            255,
            "Natural Aquatic Vegetated: Woody Sparse (4 to 15 %) Water < 3 months (temporary or seasonal)",
        ),
        75: (176, 218, 201, 255, "Natural Aquatic Vegetated: Woody Scattered (1 to 4 %)"),
        76: (
            176,
            218,
            201,
            255,
            "Natural Aquatic Vegetated: Woody Scattered (1 to 4 %) Water > 3 months (semi-) permanent",
        ),
        77: (
            176,
            218,
            201,
            255,
            "Natural Aquatic Vegetated: Woody Scattered (1 to 4 %) Water < 3 months (temporary or seasonal)",
        ),
        78: (39, 204, 139, 255, "Natural Aquatic Vegetated: Herbaceous Closed (> 65 %)"),
        79: (
            39,
            204,
            139,
            255,
            "Natural Aquatic Vegetated: Herbaceous Closed (> 65 %) Water > 3 months (semi-) permanent",
        ),
        80: (
            39,
            204,
            139,
            255,
            "Natural Aquatic Vegetated: Herbaceous Closed (> 65 %) Water < 3 months (temporary or seasonal)",
        ),
        81: (66, 216, 159, 255, "Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %)"),
        82: (
            66,
            216,
            159,
            255,
            "Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %) Water > 3 months (semi-) permanent",
        ),
        83: (
            66,
            216,
            159,
            255,
            "Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %) Water < 3 months (temporary or seasonal)",
        ),
        84: (99, 227, 180, 255, "Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %)"),
        85: (
            99,
            227,
            180,
            255,
            "Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %) Water > 3 months (semi-) permanent",
        ),
        86: (
            99,
            227,
            180,
            255,
            "Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %) Water < 3 months (temporary or seasonal)",
        ),
        87: (135, 239, 201, 255, "Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %)"),
        88: (
            135,
            239,
            201,
            255,
            "Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %) Water > 3 months (semi-) permanent",
        ),
        89: (
            135,
            239,
            201,
            255,
            "Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %) Water < 3 months (temporary or seasonal)",
        ),
        90: (171, 250, 221, 255, "Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %)"),
        91: (
            171,
            250,
            221,
            255,
            "Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %) Water > 3 months (semi-) permanent",
        ),
        92: (
            171,
            250,
            221,
            255,
            "Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %) Water < 3 months (temporary or seasonal)",
        ),
        93: (218, 92, 105, 255, "Artificial Surface:"),
        94: (243, 171, 105, 255, "Natural Surface:"),
        95: (255, 230, 140, 255, "Natural Surface: Sparsely vegetated"),
        96: (250, 210, 110, 255, "Natural Surface: Very sparsely vegetated"),
        97: (243, 171, 105, 255, "Natural Surface: Bare areas, unvegetated"),
        98: (77, 159, 220, 255, "Water:"),
        99: (77, 159, 220, 255, "Water: (Water)"),
        100: (187, 220, 233, 255, "Water: (Water) Tidal area"),
        101: (27, 85, 186, 255, "Water: (Water) Perennial (> 9 months)"),
        102: (52, 121, 201, 255, "Water: (Water) Non-perennial (7 to 9 months)"),
        103: (79, 157, 217, 255, "Water: (Water) Non-perennial (4 to 6 months)"),
        104: (133, 202, 253, 255, "Water: (Water) Non-perennial (1 to 3 months)"),
        # 105: (250, 250, 250, 255, 'Water: (Snow)')
        255: (255, 255, 255, 255, "No Data"),
    },
    "level4_colourbar_labels": {
        9: (197, 168, 71, 255, "Cultivated Terrestrial Vegetated: Woody Closed (> 65 %)"),
        10: (205, 181, 75, 255, "Cultivated Terrestrial Vegetated: Woody Open (40 to 65 %)"),
        11: (213, 193, 79, 255, "Cultivated Terrestrial Vegetated: Woody Open (15 to 40 %)"),
        12: (228, 210, 108, 255, "Cultivated Terrestrial Vegetated: Woody Sparse (4 to 15 %)"),
        13: (242, 227, 138, 255, "Cultivated Terrestrial Vegetated: Woody Scattered (1 to 4 %)"),
        14: (228, 224, 52, 255, "Cultivated Terrestrial Vegetated: Herbaceous Closed (> 65 %)"),
        15: (235, 232, 84, 255, "Cultivated Terrestrial Vegetated: Herbaceous Open (40 to 65 %)"),
        16: (242, 240, 127, 255, "Cultivated Terrestrial Vegetated: Herbaceous Open (15 to 40 %)"),
        17: (249, 247, 174, 255, "Cultivated Terrestrial Vegetated: Herbaceous Sparse (4 to 15 %)"),
        18: (255, 254, 222, 255, "Cultivated Terrestrial Vegetated: Herbaceous Scattered (1 to 4 %)"),
        27: (14, 121, 18, 255, "Natural Terrestrial Vegetated: Woody Closed (> 65 %)"),
        28: (45, 141, 47, 255, "Natural Terrestrial Vegetated: Woody Open (40 to 65 %)"),
        29: (80, 160, 82, 255, "Natural Terrestrial Vegetated: Woody Open (15 to 40 %)"),
        30: (117, 180, 118, 255, "Natural Terrestrial Vegetated: Woody Sparse (4 to 15 %)"),
        31: (154, 199, 156, 255, "Natural Terrestrial Vegetated: Woody Scattered (1 to 4 %)"),
        32: (119, 167, 30, 255, "Natural Terrestrial Vegetated: Herbaceous Closed (> 65 %)"),
        33: (136, 182, 51, 255, "Natural Terrestrial Vegetated: Herbaceous Open (40 to 65 %)"),
        34: (153, 196, 80, 255, "Natural Terrestrial Vegetated: Herbaceous Open (15 to 40 %)"),
        35: (170, 212, 113, 255, "Natural Terrestrial Vegetated: Herbaceous Sparse (4 to 15 %)"),
        36: (186, 226, 146, 255, "Natural Terrestrial Vegetated: Herbaceous Scattered (1 to 4 %)"),
        65: (25, 173, 109, 255, "Natural Aquatic Vegetated: Woody Closed (> 65 %)"),
        68: (53, 184, 132, 255, "Natural Aquatic Vegetated: Woody Open (40 to 65 %)"),
        71: (93, 195, 155, 255, "Natural Aquatic Vegetated: Woody Open (15 to 40 %)"),
        74: (135, 206, 178, 255, "Natural Aquatic Vegetated: Woody Sparse (4 to 15 %)"),
        77: (176, 218, 201, 255, "Natural Aquatic Vegetated: Woody Scattered (1 to 4 %)"),
        80: (39, 204, 139, 255, "Natural Aquatic Vegetated: Herbaceous Closed (> 65 %)"),
        83: (66, 216, 159, 255, "Natural Aquatic Vegetated: Herbaceous Open (40 to 65 %)"),
        86: (99, 227, 180, 255, "Natural Aquatic Vegetated: Herbaceous Open (15 to 40 %)"),
        89: (135, 239, 201, 255, "Natural Aquatic Vegetated: Herbaceous Sparse (4 to 15 %)"),
        92: (171, 250, 221, 255, "Natural Aquatic Vegetated: Herbaceous Scattered (1 to 4 %)"),
        93: (218, 92, 105, 255, "Artificial Surface"),
        95: (255, 230, 140, 255, "Natural Surface: Sparsely vegetated"),
        96: (250, 210, 110, 255, "Natural Surface: Very sparsely vegetated"),
        97: (243, 171, 105, 255, "Natural Surface: Bare areas, unvegetated"),
        100: (187, 220, 233, 255, "Water: (Water) Tidal area"),
        101: (27, 85, 186, 255, "Water: (Water) Perennial (> 9 months)"),
        102: (52, 121, 201, 255, "Water: (Water) Non-perennial (7 to 9 months)"),
        103: (79, 157, 217, 255, "Water: (Water) Non-perennial (4 to 6 months)"),
        104: (133, 202, 253, 255, "Water: (Water) Non-perennial (1 to 3 months)"),
        255: (255, 255, 255, 255, "No Data"),
    },
}

# dictionary needed to generate colour schemes of descriptors from the level 4 colour scheme. The structure is as follow:
# long_descriptor_name[string]: {keyword_for_finding_classes_in_level4_colourscheme[string] : (RGB_colourscheme[4 integers], label_of_descriptor[string])}
lc_colours_mapping = {
    "lifeform_veg_cat_l4a": {
        "Woody": (14, 121, 18, 255, "Woody\nVegetation"),
        "Herbaceous": (172, 188, 45, 255, "Herbaceous\nVegetation"),
    },
    "canopyco_veg_cat_l4d": {
        "> 65 %": (14, 121, 18, 255, "> 65 %\ncover"),
        "40 to 65 %": (45, 141, 47, 255, "40 to 65 %\ncover"),
        "15 to 40 %": (80, 160, 82, 255, "15 to 40 %\ncover"),
        "4 to 15 %": (117, 180, 118, 255, "4 to 15 %\ncover"),
        "1 to 4 %": (154, 199, 156, 255, "1 to 4 %\ncover"),
    },
    "watersea_veg_cat_l4a_au": {
        "(semi-) permanent": (25, 173, 109, 255, "> 3 months"),
        "(temporary or seasonal)": (176, 218, 201, 255, "< 3 months"),
    },
    "waterstt_wat_cat_l4a": {"Water: (Water)": (77, 159, 220, 255, "Water")},
    "inttidal_wat_cat_l4a": {"Tidal area": (77, 159, 220, 255, "Tidal area")},
    "waterper_wat_cat_l4d_au": {
        "> 9 months": (27, 85, 186, 255, "> 9\nmonths"),
        "7 to 9 months": (52, 121, 201, 255, "7 to 9\nmonths"),
        "4 to 6 months": (79, 157, 217, 255, "4 to 6\nmonths"),
        "1 to 3 months": (113, 202, 253, 255, "1 to 3\nmonths"),
    },
    "baregrad_phy_cat_l4d_au": {
        "Sparsely vegetated": (255, 230, 140, 255, "Sparsely\nvegetated\n(< 20% bare)"),
        "Very sparesely": (250, 210, 110, 255, "Very sparsely\nvegetated\n(20 to 60% bare)"),
        "Bare areas": (243, 171, 105, 255, "Bare areas,\nunvegetated\n(> 60% bare)"),
    },
}

aliases = {
    "lifeform": "lifeform_veg_cat_l4a",
    "vegetation_cover": "canopyco_veg_cat_l4d",
    "water_seasonality": "watersea_veg_cat_l4a_au",
    "water_state": "waterstt_wat_cat_l4a",
    "intertidal": "inttidal_wat_cat_l4a",
    "water_persistence": "waterper_wat_cat_l4d_au",
    "bare_gradation": "baregrad_phy_cat_l4d_au",
    "full_classification": "level4",
    "level_4": "level4",
}


def get_label(lc_value, level, lc_dictionary=lc_colours):
    """
    Returns the name of the Land Cover class given its value.

    Parameters
    ---------
    lc_value : int
        Value of a landcover class.
    level : str
        Either 'level3' or 'level4'.
    lc_dictionary : dict, optional
        A dictionary specifying color schemes.
        Defaults to a nested dictionary with keys `level3` and `level4`,
        each mapping to their respective sub-dictionaries.

    Returns
    ---------
    a string indicating the name of the land cover class
    """

    level_dict = lc_dictionary[level]
    label = level_dict[lc_value][-1]  # it's the last element of the tuple
    label = label.replace("\n", " ")  # replace '\n' with a space
    label = " ".join(label.split())  # delete double spaces, if any
    # if the string ends with a ":" (as it may happens with the highest level categories) remove it
    if label.endswith(":"):
        label = label[:-1]

    return label


def _get_layer_name(measurement, da, aliases=aliases):
    """
    Returns detailed name of descriptor given the short alias
    """

    # Use provided measurement if able
    measurement = measurement.lower() if measurement else da.name
    return aliases[measurement] if measurement in aliases.keys() else measurement


def _descriptors_colours(lc_colours, lc_colours_mapping, descriptor):
    """
    Generates a sorted dictionary of colours based on a given descriptor.

    This function takes in a dictionary of Land Cover classes, a mapping of descriptors to colours,
    and a specific descriptor. It returns a dictionary where the keys (i.e., classes values) are sorted
    and the values are the corresponding colours and labels from the descriptor mapping.

    Parameters
    ---------
    lc_colours : dict
        Dictionary containing colour schemes for all Land Cover classes,
        including Level 4 scheme (needed in this function).

    lc_colours_mapping : dict
        Dictionary mapping descriptors (e.g., lifeform) to their corresponding colours and labels.

    descriptor : str
        The descriptor to be used for mapping colours.

    Returns
    ---------
    sorted_colours_dict : dict
        Sorted dictionary with class values as keys and colour tuples as values.
    """

    # get the level 4 colour scheme from the lc_colours dictionary
    level4_colours = lc_colours["level4"]

    # get the descriptor dictionary from the lc_colours_mapping
    descriptor_dict = lc_colours_mapping[descriptor]

    # create a new colours dictionary with all level 4 values set to white colour
    # this dictionary is the foundation of the output returned at the end
    colours_dict = level4_colours.copy()
    for key in colours_dict:
        colours_dict[key] = (255, 255, 255, 255, "No Data/\nOther\nClasses")

    # based on the descriptor, update the colours dictionary with the descriptor-specific colours
    # (all the rest will stay white)
    for class_keyword, colour_n_label in descriptor_dict.items():  # iterate over descriptors mapping keys
        for class_value, lvl4_scheme in level4_colours.items():  # iterate over Level 4 colour scheme
            # get the label of current Level 4 class colour
            label_lvl4 = lvl4_scheme[4]

            if (
                class_keyword in label_lvl4
            ):  # check if the current Level 4 class colour contains the current descriptor mapping key
                # replace white colour with RGB indicated by the descriptor mapping dictionary
                colours_dict[class_value] = colour_n_label

    # sort the colours dictionary by keys (i.e., the values of classes)
    return {key: colours_dict[key] for key in sorted(colours_dict.keys())}


def get_colour_scheme(measurement):
    """
    Retrieves a colour scheme dictionary for a specified measurement.

    This function determines the appropriate colour scheme based on a given
    measurement name. If the measurement refers to a descriptor,
    the colour scheme is built from the descriptor definitions.
    Otherwise, a standard predefined colour scheme is returned.

    Parameters
    ---------
    measurement : str
        The name of the measurement or descriptor for which the colour
        scheme is requested. Must match a key in `lc_colours`,
        `lc_colours_mapping`, or `aliases`.

    Returns
    ---------
    colour_scheme : dict
        Dictionary containing the colour scheme associated with the
        specified measurement or descriptor.
    """

    # ensure a valid colour scheme was requested
    assert (
        (measurement in lc_colours)  # either in main colour scheme dictionary
        or (measurement in lc_colours_mapping)  # or in mapping dictionary for descriptors
        or (measurement in aliases)  # or short aliases of descriptors
    ), (
        f'colour scheme must be one of {lc_colours.keys()} {lc_colours_mapping.keys()} {aliases.keys()} (got "{measurement}")'
    )

    # if a descriptor colour scheme is required, use the _descriptors_colours function
    if measurement in lc_colours_mapping:
        colour_scheme = _descriptors_colours(lc_colours, lc_colours_mapping, measurement)

    else:  # else, use standard colours scheme
        colour_scheme = lc_colours[measurement]

    return colour_scheme


def _reduce_colour_scheme(colour_scheme):
    """
    Takes a colour scheme dictionary and returns the dictionary without duplicate values.
    This also replaces classes values with subsequent integers, useful for placing ticks of colourbar on the side
    """

    # foundation of the output dictionary
    reduced_scheme = {}

    # empty list to be filled with names of classes added to the output dictionary
    classes_added = []

    new_key = 2  # key 1 was added earlier and corresponds with "no data"

    for _key, value in colour_scheme.items():
        # get string with class name
        class_name = value[4]

        if class_name not in classes_added:  # check if already added in list
            classes_added.append(class_name)

            # assign the colour scheme and label to a new key in reduced_scheme
            reduced_scheme[new_key] = value
            # increase value of new_key for next iteration
            new_key += 1

    return reduced_scheme


def lc_colourmap(colour_scheme):
    """
    Takes a colour scheme dictionary and returns colormap for matplotlib.

    Returns
    ---------
    cmap : matplotlib colormap
        Matplotlib colormap containing the colour scheme for the
        specified DEA Land Cover measurement.
    norm : matplotlib colormap index
        Matplotlib colormap index based on the discrete intervals of the
        classes in the specified DEA Land Cover measurement. Ensures the
        colormap maps the colours to the class numbers correctly.
    """

    colour_arr = []  # empty list to be populated with colours
    for _key, value in colour_scheme.items():
        colour_arr.append(np.array(value[:-2]) / 255)  # add colour to list

    # create a colour map from the list of colours
    cmap = mcolours.ListedColormap(colour_arr)

    # create boundaries of colours by using the exact class values and adding a larger value at the end
    bounds = list(colour_scheme)
    bounds.append(bounds[-1] + 1)

    # shift all boundaries back by 0.5 to make sure level4 values are within bounds
    # this is a robust method to make sure each value is within a colour bin
    bounds = [i - 0.5 for i in bounds]

    # normalisation for colourmap
    norm = mcolours.BoundaryNorm(np.array(bounds), cmap.N)

    return (cmap, norm)


def _legend_colourmap(colour_scheme):
    """
    Returns colour map and normalisation specifically for the colourbar
    of the provided DEA Land Cover measurement, for use in plotting with Matplotlib library

    Parameters
    ----------
    colour_scheme : dictionary with colour scheme

    Returns
    ---------
    cb_cmap : matplotlib colormap
        Matplotlib colormap containing the colour scheme for the
        specified DEA Land Cover measurement.
    cb_norm : matplotlib colormap index
        Matplotlib colormap index based on the discrete intervals of the
        classes in the specified DEA Land Cover measurement. Ensures the
        colormap maps the colours to the class numbers correctly.
    cb_labels : list
        string labels of the classes found
        in the chosen DEA Land Cover measurement.
    cb_ticks : list
        position of ticks in colour bar

    """

    # delete duplicates to create colour bar (this effectively applies only with descriptors),
    # and fix values for correct colourbar label positioning
    colour_scheme = _reduce_colour_scheme(colour_scheme)

    cb_cmap, cb_norm = lc_colourmap(colour_scheme)

    cb_ticks = list(colour_scheme)
    cb_labels = []
    for x in cb_ticks:
        cb_labels.append(colour_scheme[x][4])

    return (cb_cmap, cb_norm, cb_labels, cb_ticks)


def make_colourbar(fig, ax, measurement, labelsize=10, horizontal=False, animation=False):
    """
    Adds a new colourbar with appropriate Land Cover colours and labels.

    For DEA Land Cover Level 4 data, this function must be used with a double plot.
    The 'ax' should be on the left side of the figure, and the colour bar will added
    on the right hand side.

    Parameters
    ----------
    fig : matplotlib figure
        Figure to add colourbar to
    ax : matplotlib ax
        Matplotlib figure ax to add colorbar to.
    measurement : string
        Name of the layer or descriptor of interest.
    labelsize : int, optional
        Size of labels in the colourbar.
    horizontal : bool, optional
        If True, displays the colourbar horizontally; otherwise, uses vertical orientation.
    animation : bool, optional
        If True, adjusts layout and axis size for animation display.

    Returns
    ----------
    Matplotlib colorbar in its own colour axis
    """

    if measurement == "level4":
        colour_scheme = lc_colours["level4_colourbar_labels"]  # use shorten labels dictionary

        if animation:
            # special spacing settings for level 4
            cax = fig.add_axes([
                0.62,
                0.05,
                0.02,
                0.90,
            ])  # parameters for add_axes are [left, bottom, width, height], in fractions of total plot
            orient = "vertical"
            # get level 4 colour bar colour map
            cb_cmap, cb_norm, cb_labels, cb_ticks = _legend_colourmap(colour_scheme)

        elif not animation:
            # move plot over to make room for colourbar
            fig.subplots_adjust(right=0.825)
            # Settings for axis positions
            cax = fig.add_axes([0.84, 0.145, 0.02, 0.70])
            orient = "vertical"
            # get level 4 colour bar colour map
            cb_cmap, cb_norm, cb_labels, cb_ticks = _legend_colourmap(colour_scheme)

    else:  # for all other measurements
        colour_scheme = get_colour_scheme(measurement)  # use standard colour scheme

        # move plot over to make room for colourbar
        fig.subplots_adjust(right=0.825)

        # settings for different axis positions
        if horizontal:
            cax = fig.add_axes([0.02, 0.05, 0.90, 0.03])
            orient = "horizontal"
        else:
            cax = fig.add_axes([0.84, 0.145, 0.02, 0.70])
            orient = "vertical"

        # get measurement colour bar colour map
        cb_cmap, cb_norm, cb_labels, cb_ticks = _legend_colourmap(colour_scheme)

    img = ax.imshow([cb_ticks], cmap=cb_cmap, norm=cb_norm)
    cb = fig.colorbar(img, cax=cax, orientation=orient)

    cb.ax.tick_params(labelsize=labelsize)
    cb.set_ticks(cb_ticks)
    cb.set_ticklabels(cb_labels)


def plot_land_cover(
    data,
    labelsize=10,
    year=None,
    measurement=None,
    width_pixels=500,
    cols=4,
):
    """
    Plot a single land cover measurement with appropriate colour scheme.

    Parameters
    ---------
    data : xarray.DataArray
        A dataArray containing a DEA Land Cover classification.
    labelsize : int, optional
        Font size for the labels on the colourbar.
    year : int, optional
        Can be used to select to plot a specific year. If not provided,
        all time slices are plotted.
    measurement : string, optional
        Name of the DEA land cover classification to be plotted. Passed to
        _legend_colourmap to specify which colour scheme will be used. If non
        provided, reads data array name from `da` to determine.
    width_pixels : int, optional
        An integer defining the output width in pixels for the
        resulting animation. The height of the animation is set
        automatically based on the dimensions/ratio of the input
        xarray dataset. Defaults to 500 pixels wide.
    cols: integer, optional
        Sets number of columns if multiple time steps are visualised.

    Returns
    ---------
    Matplotlib image.

    """

    # get measurement name
    measurement = _get_layer_name(measurement, data)

    colour_scheme = get_colour_scheme(measurement)

    cmap, norm = lc_colourmap(colour_scheme)

    height, width = data.geobox.shape
    scale = width_pixels / width

    if year:
        # plotting protocol if 'year' variable is passed
        if int(year) not in pd.to_datetime(data.time.values).year:  # check if year selected is in the datacube
            raise ValueError(f"Year {year} is not in the data array.")

        year_string = f"{year}-07-01"  # LC collection 3 dates are in July
        data = data.sel(time=year_string, method="nearest")

        fig, ax = plt.subplots()
        fig.set_size_inches(width * scale / 72, height * scale / 72)
        make_colourbar(fig, ax, measurement, labelsize)
        im = ax.imshow(data.values, cmap=cmap, norm=norm, interpolation="nearest")

    elif len(data.time) == 1:
        # plotting protocol if only one time step is passed and not a year variable
        fig, ax = plt.subplots()
        fig.set_size_inches(width * scale / 72, height * scale / 72)
        make_colourbar(fig, ax, measurement, labelsize)
        im = ax.imshow(data.isel(time=0), cmap=cmap, norm=norm, interpolation="nearest")

    else:
        # plotting protocol if multiple time steps are passed to plot
        if cols > len(data.time):
            cols = len(data.time)
        rows = int((len(data.time) + cols - 1) / cols)

        fig, ax = plt.subplots(nrows=rows, ncols=cols)
        fig.set_size_inches(width * scale / 72, (height * scale / 72 / cols) * (len(data.time) / cols))

        make_colourbar(fig, ax.flat[0], measurement, labelsize)

        for a, b in enumerate(ax.flat):
            if a < data.shape[0]:
                im = b.imshow(data[a], cmap=cmap, norm=norm, interpolation="nearest")

    return im


def _calc_class_ratio(da, measurement):
    """
    Creates a table listing year by year what percentage of the
    total area is taken up by each class.
    Parameters
    ---------
    da : xarray.DataArray with time dimension
    measurement: string with name of descriptor/measurement

    Returns
    ---------
    Pandas Dataframe : containing class percentages per year
    """

    # list all class codes in dataset
    list_classes = (np.unique(da, return_counts=False)).tolist()

    # if a descriptor colour scheme is required, list_classes need to be changed to contain only classes of that descriptor
    # the following code uses the _descriptors_colours function to get the colours scheme and then the values of the descriptor of interest
    if measurement in lc_colours_mapping:
        lc_colour_scheme = _descriptors_colours(lc_colours, lc_colours_mapping, measurement)
        # sort based on RGB colour, so stack plot will show same colours next to each other
        lc_colour_scheme = dict(sorted(lc_colour_scheme.items(), key=lambda item: item[1][0:3]))
        # create list of values
        all_classes_descriptor = list(lc_colour_scheme.keys())
        # out of all possible classes of that descriptor, keep only the ones actually in the data array
        list_classes = [
            i for i in all_classes_descriptor if i in list_classes
        ]  # the order of all_classes_descriptor and list_classes is important: the correct sorting order is the one of all_classes_descriptor

    # create empty dataframe & dictionary
    ratio_table = pd.DataFrame(data=None, columns=list_classes)
    date_line = {}

    # count all pixels, should be consistent
    total_pix = da.isel(time=1).size

    # iterate through each year in dataset
    for i in range(0, len(da.time)):
        date = str(da.time[i].data)[0:10]

        # for each year iterate though each present class number
        # and count pixels
        for n in list_classes:
            number_of_pixles = int(np.sum(da.isel(time=i) == n))
            percentage = number_of_pixles / total_pix * 100
            date_line[n] = percentage

        # add each year's counts to dataframe
        ratio_table.loc[date] = date_line

    return ratio_table


def lc_animation(
    da,
    file_name="default_animation",
    measurement=None,
    stacked_plot=False,
    colour_bar=False,
    animation_interval=500,
    width_pixels=500,
    dpi=150,
    font_size=15,
    label_size=15,
    label_ax=True,
):
    """
    Creates an animation of DEA Landcover though time beside
    corresponding stacked plots of the landcover classes. Saves the
    animation to a file and displays the animation in notebook.

    Parameters
    ---------
    da : xarray.DataArray
        An xarray.DataArray containing a multi-date stack of
        observations of a single landcover level.
    file_name: string, optional.
        string used to create filename for saved animation file.
        Default: "default_animation" code adds .gif suffix.
    measurement : string, optional
        Name of the DEA land cover classification to be plotted. Passed to
        _legend_colourmap to specify which colour scheme will be used. If non
        provided, reads data array name from `da` to determine.
    stacked_plot: boolean, optional
        Determines if a stacked plot showing the percentage of area
        taken up by each class in each time slice is added to the
        animation. Default: False.
    colour_bar : boolean, optional
        Determines if a colour bar is generated for the stand alone
        animation. This is NOT recommended for use with level 4 data.
        Does not work with stacked plot. Default: False.
    animation_interval : int , optional
        How quickly the frames of the animations should be re-drawn.
        Default: 500.
    width_pixels : int, optional
        An integer defining the output width in pixels for the
        resulting animation. The height of the animation is set
        automatically based on the dimensions/ratio of the input
        xarray dataset. Defaults to 500 pixels wide.
    dpi : int, optional
        Stands for 'Dots Per Inch'. Passed to the fuction that saves the
        animation and determines the resolution. A higher number will
        produce a higher resolution image but a larger file size and
        slower processing. Default: 150.
    font_size : int, optional
        Controls the size of the text on the axes and colour bar. Default: 15.
    label_size : int, optional.
        Controls the size of the text which indicates the year
        displayed. Default: 15.
    label_ax : boolean, optional
        Determines if animation plot should have tick marks and numbers
        on axes. Also removes white space around plot. Default: True


    Returns
    ---------
    A GIF (.gif) animation file.
    """

    # Add gif to end of filename
    file_name = file_name + ".gif"

    # get long name of measurement/variable
    measurement = _get_layer_name(measurement, da)

    # get colour scheme
    colour_scheme = get_colour_scheme(measurement)

    # Create colour map and normalisation for specified lc measurement
    layer_cmap, layer_norm = lc_colourmap(colour_scheme)

    # Get info on dataset dimensions and define size of output
    height, width = da.geobox.shape
    scale = width_pixels / width
    left, bottom, right, top = da.geobox.extent.boundingbox
    extent = [left, right, bottom, top]

    # settings for the label showed on top of the images
    annotation_defaults = {
        "xy": (1, 1),
        "xycoords": "axes fraction",
        "xytext": (-5, -5),
        "textcoords": "offset points",
        "horizontalalignment": "right",
        "verticalalignment": "top",
        "fontsize": label_size,
        "color": "white",
        "path_effects": [patheffects.withStroke(linewidth=1, foreground="black")],
    }

    # Get information needed to display the year in the top corner
    times_list = da.time.dt.strftime("%Y").values
    text_list = [False] * len(times_list)
    annotation_list = ["\n".join([str(i) for i in (a, b) if i]) for a, b in zip(times_list, text_list)]

    if stacked_plot:  # if need to add stacked line plot on the right
        # Create table for stacked plot
        stacked_plot_table = _calc_class_ratio(da, measurement)

        # Build colour list of hex vals for stacked plot
        def _rgb_to_hex(r, g, b):
            hex = "#%x%x%x" % (r, g, b)
            if len(hex) < 7:
                hex = "#0" + hex[1:]
            return hex

        hex_colour_list = []
        for val in list(stacked_plot_table):
            r, g, b = colour_scheme[val][0:3]
            hex_val = _rgb_to_hex(r, g, b)
            hex_colour_list.append(hex_val)

        # Define & set up figure (two axes: the LC array and the stacked line plot)
        fig, (ax1, ax2) = plt.subplots(1, 2, dpi=dpi, constrained_layout=True)
        fig.set_size_inches(width * scale / 72, height * scale / 72 / 2, forward=True)
        fig.set_constrained_layout_pads(w_pad=0.2, h_pad=0.2, hspace=0, wspace=0)

        # set the size of the ticks labels using font_size
        ax1.tick_params(axis="both", which="major", labelsize=font_size)
        ax2.tick_params(axis="both", which="major", labelsize=font_size)

        # define list of axes to use in anim_fargs and, in turn, in _update_frames
        axes = [ax1, ax2]

    else:  # i.e., stacked_plot == False
        # if plotting level 4 with colourbar
        if measurement == "level4" and colour_bar:
            # specific setting to fit level 4 colour bar beside the plot
            # we will plot the animation in the left hand plot
            # and put the colour bar on the right hand side

            # Define & set up figure, two subplots so colour bar fits :)
            fig, (ax1, ax2) = plt.subplots(1, 2, dpi=dpi, constrained_layout=True, gridspec_kw={"width_ratios": [3, 1]})
            fig.set_size_inches(width * scale / 72, height * scale / 72 / 2, forward=True)
            fig.set_constrained_layout_pads(w_pad=0.2, h_pad=0.2, hspace=0, wspace=0)

            # make colour bar
            # provide left hand canvas to colour bar function which is where the image will go
            # colourbar will plot on right side beside it
            make_colourbar(fig, ax1, measurement, labelsize=font_size, animation=True)

            # turn off lines for second plot so it's not on top of colourbar
            ax2.set_axis_off()

        # plotting any other measurement with or with-out colour bar or level 4 without
        else:
            # Define & set up figure
            fig, ax1 = plt.subplots(1, 1, dpi=dpi)
            fig.set_size_inches(width * scale / 72, height * scale / 72, forward=True)

            if not label_ax:
                fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
            # make colourbar if required
            if colour_bar:
                make_colourbar(fig, ax1, measurement, labelsize=font_size)

        # set the size of the ticks labels using font_size
        ax1.tick_params(axis="both", which="major", labelsize=font_size)

        # define list of axes to use in anim_fargs and, in turn, in _update_frames
        axes = [ax1]

    #################################################################
    #### This function is called at the end at regular intervals ####
    #### with changing i values for each frame                   ####
    #################################################################
    def _update_frames(i, axes, extent, annotation_text, annotation_defaults, cmap, norm):
        ax1 = axes[0]  # at least one axis is always present

        # Clear previous frame to optimise render speed and plot imagery
        ax1.clear()

        # Add annotation text
        ax1.annotate(annotation_text[i], **annotation_defaults)

        # Generate image
        ax1.imshow(da[i, ...], cmap=cmap, norm=norm, extent=extent, interpolation="nearest")

        # set size of 1e6 using font_size
        ax1.yaxis.get_offset_text().set_fontsize(font_size)
        ax1.xaxis.get_offset_text().set_fontsize(font_size)

        # if asked that axes have no labels, remove them
        if not label_ax:
            ax1.set_axis_off()

        try:  # this will fail and be skipped if a second axes (i.e. stacked line plot) does not exist
            ax2 = axes[1]
            ax2.clear()

            # get the classes ratio up to the current time step i
            clipped_table = stacked_plot_table.iloc[: int(i + 1)]
            data = clipped_table.to_dict(orient="list")
            date = clipped_table.index

            # add stacked line plot to axes 2
            ax2.stackplot(date, data.values(), colors=hex_colour_list)
            ax2.tick_params(axis="x", labelrotation=-90)
            ax2.margins(x=0, y=0)

            # Add annotation text
            ax2.annotate(annotation_text[i], **annotation_defaults)

            # set size of 1e6 using font_size
            ax2.yaxis.get_offset_text().set_fontsize(font_size)
            ax2.xaxis.get_offset_text().set_fontsize(font_size)

        except:
            pass

    #################################################################
    #################################################################

    # anim_fargs contains all the values we send to our
    # _update_frames function.
    anim_fargs = (
        axes,
        [left, right, bottom, top],  # imshow extent
        annotation_list,
        annotation_defaults,
        layer_cmap,
        layer_norm,
    )

    # create animation
    anim = FuncAnimation(
        fig=fig,
        func=_update_frames,
        fargs=anim_fargs,
        frames=len(da.time),
        interval=animation_interval,
        repeat=False,
    )

    # save animation
    anim.save(file_name, writer="pillow", dpi=dpi)

    plt.close()

    return Image(filename=file_name)
