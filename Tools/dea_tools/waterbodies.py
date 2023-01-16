## dea_waterbodies.py
"""
Loading and processing DEA Waterbodies data.

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

Last modified: September 2021
"""

import geopandas as gpd
from owslib.wfs import WebFeatureService
from owslib.fes import PropertyIsEqualTo
from owslib.etree import etree
import pandas as pd

WFS_ADDRESS = "https://geoserver.dea.ga.gov.au/geoserver/wfs"


def get_waterbody(geohash: str) -> gpd.GeoDataFrame:
    """Gets a waterbody polygon and metadata by geohash.
    
    Parameters
    ----------
    geohash : str
        The geohash/UID for a waterbody in DEA Waterbodies.
    
    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame with the polygon.
    """
    wfs = WebFeatureService(url=WFS_ADDRESS, version="1.1.0")
    filter_ = PropertyIsEqualTo(propertyname="uid", literal=geohash)
    filterxml = etree.tostring(filter_.toXML()).decode("utf-8")
    response = wfs.getfeature(
        typename="DigitalEarthAustraliaWaterbodies_v2",
        filter=filterxml,
        outputFormat="json",
    )
    wb_gpd = gpd.read_file(response)
    return wb_gpd


def get_waterbodies(bbox: tuple, crs="EPSG:4326") -> gpd.GeoDataFrame:
    """Gets the polygons and metadata for multiple waterbodies by bbox.
    
    Parameters
    ----------
    bbox : (xmin, ymin, xmax, ymax)
        Bounding box.
    crs : str
        Optional CRS for the bounding box.
    
    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame with the polygons and metadata.
    """
    wfs = WebFeatureService(url=WFS_ADDRESS, version="1.1.0")
    response = wfs.getfeature(
        typename="DigitalEarthAustraliaWaterbodies_v2",
        bbox=tuple(bbox) + (crs,),
        outputFormat="json",
    )
    wb_gpd = gpd.read_file(response)
    return wb_gpd


def get_geohashes(bbox: tuple = None, crs: str = "EPSG:4326") -> [str]:
    """Gets all waterbody geohashes.
    
    Parameters
    ----------
    bbox : (xmin, ymin, xmax, ymax)
        Optional bounding box.
    crs : str
        Optional CRS for the bounding box.
    
    Returns
    -------
    [str]
        A list of geohashes.
    """
    wfs = WebFeatureService(url=WFS_ADDRESS, version="1.1.0")
    if bbox is not None:
        bbox = tuple(bbox) + (crs,)
    response = wfs.getfeature(
        typename="DigitalEarthAustraliaWaterbodies_v2",
        propertyname="uid",
        outputFormat="json",
        bbox=bbox,
    )
    wb_gpd = gpd.read_file(response)
    return list(wb_gpd["uid"])


def get_time_series(geohash: str = None, waterbody: pd.Series = None) -> pd.DataFrame:
    """Gets the time series for a waterbody. Specify either a GeoDataFrame row or a geohash.
    
    Parameters
    ----------
    geohash : str
        The geohash/UID for a waterbody in DEA Waterbodies.
    waterbody : pd.Series
        One row of a GeoDataFrame representing a waterbody.
    
    Returns
    -------
    pd.DataFrame
        A time series for the waterbody.
    """
    if waterbody is not None and geohash is not None:
        raise ValueError("One of waterbody and geohash must be None")
    if waterbody is None and geohash is None:
        raise ValueError("One of waterbody and geohash must be specified")

    if geohash is not None:
        wb = get_waterbody(geohash)
        url = wb.timeseries[0]
    else:
        url = waterbody.timeseries
    wb_timeseries = pd.read_csv(url)
    # Tidy up the dataframe.
    wb_timeseries.dropna(inplace=True)
    wb_timeseries.columns = ["date", "pc_wet", "px_wet"]
    wb_timeseries = wb_timeseries.set_index("date")
    wb_timeseries.index = pd.to_datetime(wb_timeseries.index)
    return wb_timeseries
