## dea_coastaltools.py
"""
Coastal and intertidal analysis tools.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, post a question on the Open Data Cube
Discord chat (https://discord.com/invite/4hhBQVas5U) or the GIS Stack Exchange
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using
the `open-data-cube` tag (you can view previously asked questions here:
https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one
on GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: July 2024

"""

# Import required packages
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from owslib.wfs import WebFeatureService
from pandas.plotting import register_matplotlib_converters
from shapely.geometry import box

register_matplotlib_converters()


WFS_ADDRESS = "https://geoserver.dea.ga.gov.au/geoserver/wfs"


def transect_distances(transects_gdf, lines_gdf, mode="distance"):
    """
    Take a set of transects (e.g. shore-normal beach survey lines), and
    determine the distance along the transect to each object in a set of
    lines (e.g. shorelines). Distances are measured in the CRS of the
    input datasets.

    For coastal applications, transects should be drawn from land to
    water (with the first point being on land so that it can be used
    as a consistent location from which to measure distances.

    The distance calculation can be performed using two modes:
        - 'distance': Distances are measured from the start of the
          transect to where it intersects with each line. Any transect
          that intersects a line more than once is ignored. This mode is
          useful for measuring e.g. the distance to the shoreline over
          time from a consistent starting location.
        - 'width' Distances are measured between the first and last
          intersection between a transect and each line. Any transect
          that intersects a line only once is ignored. This is useful
          for e.g. measuring the width of a narrow area of coastline over
          time, e.g. the neck of a spit or tombolo.

    Parameters
    ----------
    transects_gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing one or multiple vector profile lines.
        The GeoDataFrame's index column will be used to name the rows in
        the output distance table.
    lines_gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing one or multiple vector line features
        that intersect the profile lines supplied to `transects_gdf`.
        The GeoDataFrame's index column will be used to name the columns
        in the output distance table.
    mode : string, optional
        Whether to use 'distance' (for measuring distances from the
        start of a profile) or 'width' mode (for measuring the width
        between two profile intersections). See docstring above for more
        info; defaults to 'distance'.

    Returns
    -------
    distance_df : pandas.DataFrame
        A DataFrame containing distance measurements for each profile
        line (rows) and line feature (columns).
    """

    from shapely.errors import ShapelyDeprecationWarning
    from shapely.geometry import Point

    def _intersect_dist(transect_gdf, lines_gdf, mode=mode):
        """
        Take an individual transect, and determine the distance along
        the transect to each object in a set of lines (e.g. shorelines).
        """

        # Identify intersections between transects and lines
        intersect_points = lines_gdf.apply(lambda x: x.geometry.intersection(transect_gdf.geometry), axis=1)

        # In distance mode, identify transects with one intersection only,
        # and use this as the end point and the start of the transect as the
        # start point when measuring distances
        if mode == "distance":
            start_point = Point(transect_gdf.geometry.coords[0])
            point_df = intersect_points.apply(
                lambda x: (
                    pd.Series({"start": start_point, "end": x})
                    if x.type == "Point"
                    else pd.Series({"start": None, "end": None})
                )
            )

        # In width mode, identify transects with multiple intersections, and
        # use the first intersection as the start point and the second
        # intersection for the end point when measuring distances
        if mode == "width":
            point_df = intersect_points.apply(
                lambda x: (
                    pd.Series({"start": x.geoms[0], "end": x.geoms[-1]})
                    if x.type == "MultiPoint"
                    else pd.Series({"start": None, "end": None})
                )
            )

        # Calculate distances between valid start and end points
        return point_df.apply(lambda x: x.start.distance(x.end) if x.start else None, axis=1)

    # Run code after ignoring Shapely pre-v2.0 warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

        # Assert that both datasets use the same CRS
        assert transects_gdf.crs == lines_gdf.crs, "Please ensure both input datasets use the same CRS."

        # Run distance calculations
        distance_df = transects_gdf.apply(lambda x: _intersect_dist(x, lines_gdf), axis=1)

        return pd.DataFrame(distance_df)


def get_coastlines(bbox: tuple, crs="EPSG:4326", layer="shorelines_annual", drop_wms=True) -> gpd.GeoDataFrame:
    """
    Load DEA Coastlines annual shorelines or rates of change points data
    for a provided bounding box using WFS.

    For a full description of the DEA Coastlines dataset, refer to the
    official Geoscience Australia product description:
    /data/product/dea-coastlines

    Parameters
    ----------
    bbox : (xmin, ymin, xmax, ymax), or geopandas object
        Bounding box expressed as a tutple. Alternatively, a bounding
        box can be automatically extracted by suppling a
        geopandas.GeoDataFrame or geopandas.GeoSeries.
    crs : str, optional
        Optional CRS for the bounding box. This is ignored if `bbox`
        is provided as a geopandas object.
    layer : str, optional
        Which DEA Coastlines layer to load. Options include the annual
        shoreline vectors ("shorelines_annual") and the rates of change
        points ("rates_of_change"). Defaults to "shorelines_annual".
    drop_wms : bool, optional
        Whether to drop WMS-specific attribute columns from the data.
        These columns are used for visualising the dataset on DEA Maps,
        and are unlikely to be useful for scientific analysis. Defaults
        to True.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing shoreline or point features and
        associated metadata.
    """

    # If bbox is a geopandas object, convert to bbox
    try:
        crs = str(bbox.crs)
        bbox = bbox.total_bounds
    except:
        pass

    # Query WFS
    wfs = WebFeatureService(url=WFS_ADDRESS, version="1.1.0")
    layer_name = f"dea:{layer}"
    response = wfs.getfeature(
        typename=layer_name,
        bbox=tuple(bbox) + (crs,),
        outputFormat="json",
    )

    # Load data as a geopandas.GeoDataFrame
    coastlines_gdf = gpd.read_file(response)

    # Clip to extent of bounding box
    extent = gpd.GeoSeries(box(*bbox), crs=crs).to_crs(coastlines_gdf.crs)
    coastlines_gdf = coastlines_gdf.clip(extent)

    # Optionally drop WMS-specific columns
    if drop_wms:
        coastlines_gdf = coastlines_gdf.loc[:, ~coastlines_gdf.columns.str.contains("wms_")]

    return coastlines_gdf


def glint_angle(solar_azimuth, solar_zenith, view_azimuth, view_zenith):
    """
    Calculates glint angles for each pixel in a satellite image based
    on the relationship between the solar and sensor zenith and azimuth
    viewing angles at the moment the image was acquired.

    Glint angle is considered a predictor of sunglint over water; small
    glint angles (e.g. < 20 degrees) are associated with a high
    probability of sunglint due to the viewing angle of the sensor
    being aligned with specular reflectance of the sun from the water's
    surface.

    Based on code from https://towardsdatascience.com/how-to-implement-
    sunglint-detection-for-sentinel-2-images-in-python-using-metadata-
    info-155e683d50

    Parameters
    ----------
    solar_azimuth : array-like
        Array of solar azimuth angles in degrees. In DEA Collection 3,
        this is contained in the "oa_solar_azimuth" band.
    solar_zenith : array-like
        Array of solar zenith angles in degrees. In DEA Collection 3,
        this is contained in the "oa_solar_zenith" band.
    view_azimuth : array-like
        Array of sensor/viewing azimuth angles in degrees. In DEA
        Collection 3, this is contained in the "oa_satellite_azimuth"
        band.
    view_zenith : array-like
        Array of sensor/viewing zenith angles in degrees. In DEA
        Collection 3, this is contained in the "oa_satellite_view" band.

    Returns
    -------
    glint_array : numpy.ndarray
        Array of glint angles in degrees. Small values indicate higher
        probabilities of sunglint.
    """

    # Convert angle arrays to radians
    solar_zenith_rad = np.deg2rad(solar_zenith)
    solar_azimuth_rad = np.deg2rad(solar_azimuth)
    view_zenith_rad = np.deg2rad(view_zenith)
    view_azimuth_rad = np.deg2rad(view_azimuth)

    # Calculate sunglint angle
    phi = solar_azimuth_rad - view_azimuth_rad
    glint_angle = np.cos(view_zenith_rad) * np.cos(solar_zenith_rad) - np.sin(view_zenith_rad) * np.sin(
        solar_zenith_rad
    ) * np.cos(phi)

    # Convert to degrees
    return np.degrees(np.arccos(glint_angle))


def model_tides(*args, **kwargs):
    raise ImportError(
        "The `model_tides` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )


def pixel_tides(*args, **kwargs):
    raise ImportError(
        "The `pixel_tides` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )


def tidal_tag(*args, **kwargs):
    raise ImportError(
        "The `tidal_tag` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )


def tidal_stats(*args, **kwargs):
    raise ImportError(
        "The `tidal_stats` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )


def tidal_tag_otps(*args, **kwargs):
    raise ImportError(
        "The `tidal_tag_otps` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )


def tidal_stats_otps(*args, **kwargs):
    raise ImportError(
        "The `tidal_stats_otps` function has been removed and is no longer available in this package.\n"
        "Please install and use the `eo-tides` package instead:\n"
        "https://geoscienceaustralia.github.io/eo-tides/migration/"
    )
