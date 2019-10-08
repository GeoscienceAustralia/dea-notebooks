## dea_masking.py
'''
Description: This file contains a set of python functions for conducting spatial analyses on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

'''

# Import required packages
import json
import numpy as np
from pyproj import Proj, transform

wgs84_proj = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs "
au_albers = "+proj=aea +lat_1=-18 +lat_2=-36 +lat_0=0 +lon_0=132 +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs "


def _is_point_in_path(x, y, poly):
    num = len(poly)
    i = 0
    j = num - 1
    c = False
    for i in range(num):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and \
                (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                  (poly[j][1] - poly[i][1])):
            c = not c
        j = i
    return c


def mask(ds, json_poly):
    p = json.loads(json_poly)
    coords = p['geometry']['coordinates']

    au_poly = _transform_poly(coords)

    canvas = np.full(ds.shape, False, dtype=bool)

    for j, b in enumerate(ds.y.data):
        for i, a in enumerate(ds.x.data):
            if _is_point_in_path(a, b, au_poly):
                canvas[j,i] = True

    return canvas

def _transform_poly(poly_coords):
    out = []
    for point in poly_coords:
        x, y = reproject(point[0], point[1])
        out.append([x,y])

    return out


def reproject(lon,lat):
    inProj = Proj(wgs84_proj)
    outProj = Proj(au_albers)
   
    return transform(inProj,outProj,lon,lat)
