## dea_coastaltools.py
"""
Coastal analysis and tide modelling tools.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, post a question on the Open Data Cube 
Slack channel (http://slack.opendatacube.org/) or the GIS Stack Exchange 
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using 
the `open-data-cube` tag (you can view previously asked questions here: 
https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one 
on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: January 2023

"""

# Import required packages
import os
import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy import stats
from shapely.geometry import box, shape
from owslib.wfs import WebFeatureService

import odc.algo
from datacube.utils.geometry import CRS
from dea_tools.datahandling import parallel_apply

# Fix converters for tidal plot
from pandas.plotting import register_matplotlib_converters

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

    import warnings
    from shapely.errors import ShapelyDeprecationWarning
    from shapely.geometry import Point

    def _intersect_dist(transect_gdf, lines_gdf, mode=mode):
        """
        Take an individual transect, and determine the distance along
        the transect to each object in a set of lines (e.g. shorelines).
        """

        # Identify intersections between transects and lines
        intersect_points = lines_gdf.apply(
            lambda x: x.geometry.intersection(transect_gdf.geometry), axis=1
        )

        # In distance mode, identify transects with one intersection only,
        # and use this as the end point and the start of the transect as the
        # start point when measuring distances
        if mode == "distance":
            start_point = Point(transect_gdf.geometry.coords[0])
            point_df = intersect_points.apply(
                lambda x: pd.Series({"start": start_point, "end": x})
                if x.type == "Point"
                else pd.Series({"start": None, "end": None})
            )

        # In width mode, identify transects with multiple intersections, and
        # use the first intersection as the start point and the second
        # intersection for the end point when measuring distances
        if mode == "width":
            point_df = intersect_points.apply(
                lambda x: pd.Series({"start": x.geoms[0], "end": x.geoms[-1]})
                if x.type == "MultiPoint"
                else pd.Series({"start": None, "end": None})
            )

        # Calculate distances between valid start and end points
        distance_df = point_df.apply(
            lambda x: x.start.distance(x.end) if x.start else None, axis=1
        )

        return distance_df

    # Run code after ignoring Shapely pre-v2.0 warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

        # Assert that both datasets use the same CRS
        assert transects_gdf.crs == lines_gdf.crs, (
            "Please ensure both " "input datasets use the same CRS."
        )

        # Run distance calculations
        distance_df = transects_gdf.apply(
            lambda x: _intersect_dist(x, lines_gdf), axis=1
        )

        return pd.DataFrame(distance_df)


def get_coastlines(
    bbox: tuple, crs="EPSG:4326", layer="shorelines", drop_wms=True
) -> gpd.GeoDataFrame:
    """
    Get DEA Coastlines data for a provided bounding box using WFS.

    For a full description of the DEA Coastlines dataset, refer to the
    official Geoscience Australia product description:
    https://cmi.ga.gov.au/data-products/dea/581/dea-coastlines

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
        shoreline vectors ("shorelines") and the rates of change
        statistics points ("statistics"). Defaults to "shorelines".
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
    layer_name = (
        "dea:coastlines" if layer == "shorelines" else "dea:coastlines_statistics"
    )
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
        coastlines_gdf = coastlines_gdf.loc[
            :, ~coastlines_gdf.columns.str.contains("wms_")
        ]

    return coastlines_gdf


def model_tides(
    x,
    y,
    time,
    model="FES2014",
    directory="/var/share/tide_models",
    epsg=4326,
    method="bilinear",
    extrapolate=True,
    cutoff=10.0,
):
    """
    Compute tides at points and times using tidal harmonics.
    If multiple x, y points are provided, tides will be
    computed for all timesteps at each point.

    This function supports any tidal model supported by
    `pyTMD`, including the FES2014 Finite Element Solution
    tide model, and the TPXO8-atlas and TPXO9-atlas-v5
    TOPEX/POSEIDON global tide models.

    This function requires access to tide model data files
    to work. These should be placed in a folder with
    subfolders matching the formats specified by `pyTMD`:
    https://pytmd.readthedocs.io/en/latest/getting_started/Getting-Started.html#directories

    For FES2014 (https://www.aviso.altimetry.fr/es/data/products/auxiliary-products/global-tide-fes/description-fes2014.html):
        - {directory}/fes2014/ocean_tide/
          {directory}/fes2014/load_tide/

    For TPXO8-atlas (https://www.tpxo.net/tpxo-products-and-registration):
        - {directory}/tpxo8_atlas/

    For TPXO9-atlas-v5 (https://www.tpxo.net/tpxo-products-and-registration):
        - {directory}/TPXO9_atlas_v5/

    This function is a minor modification of the `pyTMD`
    package's `compute_tide_corrections` function, adapted
    to process multiple timesteps for multiple input point
    locations. For more info:
    https://pytmd.readthedocs.io/en/stable/user_guide/compute_tide_corrections.html

    Parameters:
    -----------
    x, y : float or list of floats
        One or more x and y coordinates used to define
        the location at which to model tides. By default these
        coordinates should be lat/lon; use `epsg` if they
        are in a custom coordinate reference system.
    time : A datetime array or pandas.DatetimeIndex
        An array containing 'datetime64[ns]' values or a
        'pandas.DatetimeIndex' providing the times at which to
        model tides in UTC time.
    model : string
        The tide model used to model tides. Options include:
        - "FES2014" (only pre-configured option on DEA Sandbox)
        - "TPXO8-atlas"
        - "TPXO9-atlas-v5"
    directory : string
        The directory containing tide model data files. These
        data files should be stored in sub-folders for each
        model that match the structure provided by `pyTMD`:
        https://pytmd.readthedocs.io/en/latest/getting_started/Getting-Started.html#directories
        For example:
        - {directory}/fes2014/ocean_tide/
          {directory}/fes2014/load_tide/
        - {directory}/tpxo8_atlas/
        - {directory}/TPXO9_atlas_v5/
    epsg : int
        Input coordinate system for 'x' and 'y' coordinates.
        Defaults to 4326 (WGS84).
    method : string
        Method used to interpolate tidal contsituents
        from model files. Options include:
        - bilinear: quick bilinear interpolation
        - spline: scipy bivariate spline interpolation
        - linear, nearest: scipy regular grid interpolations
    extrapolate : bool
        Whether to extrapolate tides for locations outside of
        the tide modelling domain using nearest-neighbor
    cutoff : int or float
        Extrapolation cutoff in kilometers. Set to `np.inf`
        to extrapolate for all points.

    Returns
    -------
    A pandas.DataFrame containing tide heights for every
    combination of time and point coordinates.
    """

    import os
    import pyproj
    import numpy as np
    import pyTMD.time
    import pyTMD.model
    import pyTMD.utilities
    from pyTMD.calc_delta_time import calc_delta_time
    from pyTMD.infer_minor_corrections import infer_minor_corrections
    from pyTMD.predict_tide_drift import predict_tide_drift
    from pyTMD.read_tide_model import extract_tidal_constants
    from pyTMD.read_netcdf_model import extract_netcdf_constants
    from pyTMD.read_GOT_model import extract_GOT_constants
    from pyTMD.read_FES_model import extract_FES_constants

    # Check that tide directory is accessible
    try:
        os.access(directory, os.F_OK)
    except:
        raise FileNotFoundError("Invalid tide directory")

    # Get parameters for tide model
    model = pyTMD.model(directory, format="netcdf", compressed=False).elevation(model)

    # If time passed as a single Timestamp, convert to datetime64
    if isinstance(time, pd.Timestamp):
        time = time.to_datetime64()

    # Handle numeric or array inputs
    x = np.atleast_1d(x)
    y = np.atleast_1d(y)
    time = np.atleast_1d(time)

    # Determine point and time counts
    assert len(x) == len(y), "x and y must be the same length"
    n_points = len(x)
    n_times = len(time)

    # Converting x,y from EPSG to latitude/longitude
    try:
        # EPSG projection code string or int
        crs1 = pyproj.CRS.from_string("epsg:{0:d}".format(int(epsg)))
    except (ValueError, pyproj.exceptions.CRSError):
        # Projection SRS string
        crs1 = pyproj.CRS.from_string(epsg)

    crs2 = pyproj.CRS.from_string("epsg:{0:d}".format(4326))
    transformer = pyproj.Transformer.from_crs(crs1, crs2, always_xy=True)
    lon, lat = transformer.transform(x.flatten(), y.flatten())

    # Assert delta time is an array and convert datetime
    time = np.atleast_1d(time)
    t = pyTMD.time.convert_datetime(time, epoch=(1992, 1, 1, 0, 0, 0)) / 86400.0

    # Delta time (TT - UT1) file
    delta_file = pyTMD.utilities.get_data_path(["data", "merged_deltat.data"])

    # Read tidal constants and interpolate to grid points
    if model.format in ("OTIS", "ATLAS"):
        amp, ph, D, c = extract_tidal_constants(
            lon,
            lat,
            model.grid_file,
            model.model_file,
            model.projection,
            TYPE=model.type,
            METHOD=method,
            EXTRAPOLATE=extrapolate,
            CUTOFF=cutoff,
            GRID=model.format,
        )
        deltat = np.zeros_like(t)

    elif model.format == "netcdf":
        amp, ph, D, c = extract_netcdf_constants(
            lon,
            lat,
            model.grid_file,
            model.model_file,
            TYPE=model.type,
            METHOD=method,
            EXTRAPOLATE=extrapolate,
            CUTOFF=cutoff,
            SCALE=model.scale,
            GZIP=model.compressed,
        )
        deltat = np.zeros_like(t)

    elif model.format == "GOT":
        amp, ph, c = extract_GOT_constants(
            lon,
            lat,
            model.model_file,
            METHOD=method,
            EXTRAPOLATE=extrapolate,
            CUTOFF=cutoff,
            SCALE=model.scale,
            GZIP=model.compressed,
        )

        # Interpolate delta times from calendar dates to tide time
        deltat = calc_delta_time(delta_file, t)

    elif model.format == "FES":
        amp, ph = extract_FES_constants(
            lon,
            lat,
            model.model_file,
            TYPE=model.type,
            VERSION=model.version,
            METHOD=method,
            EXTRAPOLATE=extrapolate,
            CUTOFF=cutoff,
            SCALE=model.scale,
            GZIP=model.compressed,
        )

        # Available model constituents
        c = model.constituents

        # Interpolate delta times from calendar dates to tide time
        deltat = calc_delta_time(delta_file, t)

    # Calculate complex phase in radians for Euler's
    cph = -1j * ph * np.pi / 180.0

    # Calculate constituent oscillation
    hc = amp * np.exp(cph)

    # Repeat constituents to length of time and number of input
    # coords before passing to `predict_tide_drift`
    t, hc, deltat = (
        np.tile(t, n_points),
        hc.repeat(n_times, axis=0),
        np.tile(deltat, n_points),
    )

    # Predict tidal elevations at time and infer minor corrections
    npts = len(t)
    tide = np.ma.zeros((npts), fill_value=np.nan)
    tide.mask = np.any(hc.mask, axis=1)

    # Depending on pyTMD version (<=1.06 vs > 1.06), use different params
    # TODO: Remove once Sandbox is updated to use pyTMD version 1.0.9
    try:
        tide.data[:] = predict_tide_drift(
            t, hc, c, deltat=deltat, corrections=model.format
        )
        minor = infer_minor_corrections(
            t, hc, c, deltat=deltat, corrections=model.format
        )
    except:
        tide.data[:] = predict_tide_drift(
            t, hc, c, DELTAT=deltat, CORRECTIONS=model.format
        )
        minor = infer_minor_corrections(
            t, hc, c, DELTAT=deltat, CORRECTIONS=model.format
        )
    tide.data[:] += minor.data[:]

    # Replace invalid values with fill value
    tide.data[tide.mask] = tide.fill_value

    # Export data as a dataframe
    return pd.DataFrame(
        {
            "time": np.tile(time, n_points),
            "x": np.repeat(x, n_times),
            "y": np.repeat(y, n_times),
            "tide_m": tide,
        }
    ).set_index("time")


def pixel_tides(
    ds,
    times=None,
    resample=True,
    calculate_quantiles=None,
    resolution=5000,
    buffer=12000,
    resample_method="bilinear",
    **model_tides_kwargs,
):
    """
    Obtain tide heights for each pixel in a dataset by modelling
    tides into a low-resolution grid surrounding the dataset,
    then (optionally) spatially reprojecting this low-res data back
    into the original higher resolution dataset extent and resolution.

    Parameters:
    -----------
    ds : xarray.Dataset
        A dataset whose geobox (`ds.odc.geobox`) will be used to define
        the spatial extent of the low resolution tide modelling grid.
    times : list or pandas.Series, optional
        By default, the function will model tides using the times
        contained in the `time` dimension of `ds`. This param can be used
        to model tides for a custom set of times instead, for example:
        `times=pd.date_range(start="2000", end="2020", freq="30min")`
    resample : bool, optional
        Whether to resample low resolution tides back into `ds`'s original
        higher resolution grid. Set this to `False` if you do not want
        low resolution tides to be re-projected back to higher resolution.
    calculate_quantiles : list or np.array, optional
        Rather than returning all individual tides, low-resolution tides
        can be first aggregated using a quantile calculation by passing in
        a list or array of quantiles to compute. For example, this could
        be used to calculate the min/max tide across all times:
        `calculate_quantiles=[0.0, 1.0]`.
    resolution: int, optional
        The desired resolution of the low-resolution grid used for tide
        modelling. Defaults to 5000 for a 5,000 m grid (assuming `ds`'s
        CRS uses project/metre units).
    buffer : int, optional
        The amount by which to buffer the higher resolution grid extent
        when creating the new low resolution grid. This buffering is
        important as it ensures that ensure pixel-based tides are seamless
        across dataset boundaries. This buffer will eventually be clipped
        away when the low-resolution data is re-projected back to the
        resolution and extent of the higher resolution dataset. Defaults
        to 12,000 m to ensure that at least two 5,000 m pixels occur
        outside of the dataset bounds.
    resample_method : string, optional
        If resampling is requested (see `resample` above), use this
        resampling method when converting from low resolution to high
        resolution pixels. Defaults to "bilinear"; valid options include
        "nearest", "cubic", "min", "max", "average" etc.
    **model_tides_kwargs :
        Optional parameters passed to the `dea_tools.coastal.model_tides`
        function. Important parameters include "model" and "directory",
        used to specify the tide model to use and the location of its files.

    Returns:
    --------
    If `resample` is True:

        tides_lowres : xr.DataArray
            A low resolution data array giving either tide heights every
            timestep in `ds` (if `times` is None), tide heights at every
            time in `times` (if `times` is not None), or tide height quantiles
            for every quantile provided by `calculate_quantiles`.

    If `resample` is False:

        tides_highres, tides_lowres : tuple of xr.DataArrays
            In addition to `tides_lowres` (see above), a high resolution
            array of tide heights will be generated that matches the
            exact spatial resolution and extent of `ds`. This will contain
            either tide heights every timestep in `ds` (if `times` is None),
            tide heights at every time in `times` (if `times` is not None),
            or tide height quantiles for every quantile provided by
            `calculate_quantiles`.
    """

    import odc.geo.xr
    from odc.geo.geobox import GeoBox

    # Create a new reduced resolution (5km) tide modelling grid after
    # first buffering the grid by 12km (i.e. at least two 5km pixels)
    print("Creating reduced resolution tide modelling array")
    buffered_geobox = ds.odc.geobox.buffered(buffer)
    rescaled_geobox = GeoBox.from_bbox(
        bbox=buffered_geobox.boundingbox, resolution=resolution
    )
    rescaled_ds = odc.geo.xr.xr_zeros(rescaled_geobox)

    # Flatten grid to 1D, then add time dimension. If custom times are
    # provided use these, otherwise use times from `ds`
    time_coords = ds.coords["time"] if times is None else times
    flattened_ds = rescaled_ds.stack(z=("x", "y"))
    flattened_ds = flattened_ds.expand_dims(dim={"time": time_coords.values})

    # Model tides for each timestep
    model = (
        "FES2014" if "model" not in model_tides_kwargs else model_tides_kwargs["model"]
    )
    print(f"Modelling tides using {model} tide model")
    tide_df = model_tides(
        x=flattened_ds.x,
        y=flattened_ds.y,
        time=flattened_ds.time,
        epsg=ds.odc.geobox.crs.epsg,
        **model_tides_kwargs,
    )

    # Insert modelled tide values back into flattened array, then unstack
    # back to 3D (x, y, time)
    tides_lowres = (
        tide_df.set_index(["x", "y"], append=True)
        .to_xarray()
        .tide_m.reindex_like(rescaled_ds)
        .transpose(*list(ds.dims.keys()))
        .astype(np.float32)
    )

    # Optionally calculate and return quantiles rather than raw data
    if calculate_quantiles is not None:

        print("Computing tide quantiles")
        tides_lowres = tides_lowres.quantile(q=calculate_quantiles, dim="time")
        reproject_dim = "quantile"

    else:
        reproject_dim = "time"

    # Ensure CRS is present
    tides_lowres = tides_lowres.odc.assign_crs(ds.odc.geobox.crs)

    # Reproject each timestep into original high resolution grid
    if resample:

        print("Reprojecting tides into original array")
        tides_highres = parallel_apply(
            tides_lowres,
            reproject_dim,
            odc.algo.xr_reproject,
            ds.odc.geobox.compat,
            resample_method,
        )

        return tides_highres, tides_lowres

    else:
        print("Returning low resolution tide array")
        return tides_lowres


def tidal_tag(
    ds,
    ebb_flow=False,
    swap_dims=False,
    tidepost_lat=None,
    tidepost_lon=None,
    return_tideposts=False,
    **model_tides_kwargs,
):
    """
    Takes an xarray.Dataset and returns the same dataset with a new
    `tide_m` variable giving the height of the tide at the exact
    moment of each satellite acquisition.

    The function models tides at the centroid of the dataset by default, 
    but a custom tidal modelling location can be specified using 
    `tidepost_lat` and `tidepost_lon`.

    The default settings use the FES2014 global tidal model, implemented
    using the pyTMD Python package. FES2014 was produced by NOVELTIS, 
    LEGOS, CLS Space Oceanography Division and CNES. It is distributed 
    by AVISO, with support from CNES (http://www.aviso.altimetry.fr/).

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions
    ebb_flow : bool, optional
        An optional boolean indicating whether to compute if the
        tide phase was ebbing (falling) or flowing (rising) for each
        observation. The default is False; if set to True, a new
        `ebb_flow` variable will be added to the dataset with each
        observation labelled with 'Ebb' or 'Flow'.
    swap_dims : bool, optional
        An optional boolean indicating whether to swap the `time`
        dimension in the original xarray.Dataset to the new
        `tide_m` variable. Defaults to False.
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling
        location.
    return_tideposts : bool, optional
        An optional boolean indicating whether to return the `tidepost_lat`
        and `tidepost_lon` location used to model tides in addition to the
        xarray.Dataset. Defaults to False.
    **model_tides_kwargs :
        Optional parameters passed to the `dea_tools.coastal.model_tides`
        function. Important parameters include "model" and "directory",
        used to specify the tide model to use and the location of its files.

    Returns
    -------
    The original xarray.Dataset with a new `tide_m` variable giving
    the height of the tide (and optionally, its ebb-flow phase) at the
    exact moment of each satellite acquisition (if `return_tideposts=True`,
    the function will also return the `tidepost_lon` and `tidepost_lat`
    location used in the analysis).

    """

    import odc.geo.xr

    # If custom tide modelling locations are not provided, use the
    # dataset centroid
    if not tidepost_lat or not tidepost_lon:

        tidepost_lon, tidepost_lat = ds.odc.geobox.geographic_extent.centroid.coords[0]
        print(
            f"Setting tide modelling location from dataset centroid: "
            f"{tidepost_lon:.2f}, {tidepost_lat:.2f}"
        )

    else:
        print(
            f"Using user-supplied tide modelling location: "
            f"{tidepost_lon:.2f}, {tidepost_lat:.2f}"
        )

    # Use tidal model to compute tide heights for each observation:
    model = (
        "FES2014" if "model" not in model_tides_kwargs else model_tides_kwargs["model"]
    )
    print(f"Modelling tides using {model} tidal model")
    tide_df = model_tides(
        x=tidepost_lon,
        y=tidepost_lat,
        time=ds.time,
        epsg="EPSG:4326",
        **model_tides_kwargs,
    )

    # If tides cannot be successfully modeled (e.g. if the centre of the
    # xarray dataset is located is over land), raise an exception
    if tide_df.tide_m.isnull().all():

        raise ValueError(
            f"Tides could not be modelled for dataset centroid located "
            f"at {tidepost_lon:.2f}, {tidepost_lat:.2f}. This can occur if "
            f"this coordinate occurs over land. Please manually specify "
            f"a tide modelling location located over water using the "
            f"`tidepost_lat` and `tidepost_lon` parameters."
        )

    # Assign tide heights to the dataset as a new variable
    ds["tide_m"] = xr.DataArray(tide_df.tide_m, coords=[ds.time])

    # Optionally calculate the tide phase for each observation
    if ebb_flow:

        # Model tides for a time 15 minutes prior to each previously
        # modelled satellite acquisition time. This allows us to compare
        # tide heights to see if they are rising or falling.
        print("Modelling tidal phase (e.g. ebb or flow)")
        tide_pre_df = model_tides(
            x=tidepost_lon,
            y=tidepost_lat,
            time=(ds.time - pd.Timedelta("15 min")),
            epsg="EPSG:4326",
            **model_tides_kwargs,
        )

        # Compare tides computed for each timestep. If the previous tide
        # was higher than the current tide, the tide is 'ebbing'. If the
        # previous tide was lower, the tide is 'flowing'
        tidal_phase = [
            "Ebb" if i else "Flow"
            for i in tide_pre_df.tide_m.values > tide_df.tide_m.values
        ]

        # Assign tide phase to the dataset as a new variable
        ds["ebb_flow"] = xr.DataArray(tidal_phase, coords=[ds.time])

    # If swap_dims = True, make tide height the primary dimension
    # instead of time
    if swap_dims:

        # Swap dimensions and sort by tide height
        ds = ds.swap_dims({"time": "tide_m"})
        ds = ds.sortby("tide_m")
        ds = ds.drop("time")

    if return_tideposts:
        return ds, tidepost_lon, tidepost_lat
    else:
        return ds


def tidal_stats(
    ds,
    tidepost_lat=None,
    tidepost_lon=None,
    plain_english=True,
    plot=True,
    modelled_freq="2h",
    linear_reg=False,
    round_stats=3,
    **model_tides_kwargs,
):
    """
    Takes an xarray.Dataset and statistically compares the tides
    modelled for each satellite observation against the full modelled
    tidal range. This comparison can be used to evaluate whether the
    tides observed by satellites (e.g. Landsat) are biased compared to
    the natural tidal range (e.g. fail to observe either the highest or
    lowest tides etc).
    
    For more information about the tidal statistics computed by this
    function, refer to Figure 8 in Bishop-Taylor et al. 2018:
    https://www.sciencedirect.com/science/article/pii/S0272771418308783#fig8

    The function models tides at the centroid of the dataset by default, 
    but a custom tidal modelling location can be specified using 
    `tidepost_lat` and `tidepost_lon`.
    
    The default settings use the FES2014 global tidal model, implemented
    using the pyTMD Python package. FES2014 was produced by NOVELTIS, 
    LEGOS, CLS Space Oceanography Division and CNES. It is distributed 
    by AVISO, with support from CNES (http://www.aviso.altimetry.fr/).

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling
        location.
    plain_english : bool, optional
        An optional boolean indicating whether to print a plain english
        version of the tidal statistics to the screen. Defaults to True.
    plot : bool, optional
        An optional boolean indicating whether to plot how satellite-
        observed tide heights compare against the full tidal range.
        Defaults to True.
    modelled_freq : str, optional
        An optional string giving the frequency at which to model tides
        when computing the full modelled tidal range. Defaults to '2h',
        which computes a tide height for every two hours across the
        temporal extent of `ds`.
    linear_reg: bool, optional
        Experimental: whether to return linear regression stats that
        assess whether dstellite-observed and all available tides show
        any decreasing or increasing trends over time. Not currently
        recommended as all observed regressions always return as
        significant due to far larger sample size.
    round_stats : int, optional
        The number of decimal places used to round the output statistics.
        Defaults to 3.
    **model_tides_kwargs :
        Optional parameters passed to the `dea_tools.coastal.model_tides`
        function. Important parameters include "model" and "directory",
        used to specify the tide model to use and the location of its files.

    Returns
    -------
    A pandas.Series object containing the following statistics:

        tidepost_lat: latitude used for modelling tide heights
        tidepost_lon: longitude used for modelling tide heights
        observed_min_m: minimum tide height observed by the satellite
        all_min_m: minimum tide height from all available tides
        observed_max_m: maximum tide height observed by the satellite
        all_max_m: maximum tide height from all available tides
        observed_range_m: tidal range observed by the satellite
        all_range_m: full astronomical tidal range based on all
                  available tides
        spread_m: proportion of the full astronomical tidal range observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        low_tide_offset: proportion of the lowest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        high_tide_offset: proportion of the highest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)

    If `linear_reg = True`, the output will also contain:

        observed_slope: slope of any relationship between observed tide
                  heights and time
        all_slope: slope of any relationship between all available tide
                  heights and time
        observed_pval: significance/p-value of any relationship between
                  observed tide heights and time
        all_pval: significance/p-value of any relationship between
                  all available tide heights and time

    """

    # Load tide modelling functions from either OTPS for pyfes
    try:
        from otps import TimePoint
        from otps import predict_tide
    except ImportError:
        from dea_tools.pyfes_model import TimePoint, predict_tide

    # Model tides for each observation in the supplied xarray object
    ds_tides, tidepost_lon, tidepost_lat = tidal_tag(
        ds,
        tidepost_lat=tidepost_lat,
        tidepost_lon=tidepost_lon,
        return_tideposts=True,
        **model_tides_kwargs,
    )

    # Drop spatial ref for nicer plotting
    if "spatial_ref" in ds_tides:
        ds_tides = ds_tides.drop("spatial_ref")

    # Generate range of times covering entire period of satellite record
    all_timerange = pd.date_range(
        start=ds_tides.time.min().item(),
        end=ds_tides.time.max().item(),
        freq=modelled_freq,
    )

    # Model tides for each timestep
    all_tides_df = model_tides(
        x=tidepost_lon,
        y=tidepost_lat,
        time=all_timerange,
        epsg="EPSG:4326",
        **model_tides_kwargs,
    )

    # Get coarse statistics on all and observed tidal ranges
    obs_mean = ds_tides.tide_m.mean().item()
    all_mean = all_tides_df.tide_m.mean()
    obs_min, obs_max = ds_tides.tide_m.quantile([0.0, 1.0]).values
    all_min, all_max = all_tides_df.tide_m.quantile([0.0, 1.0]).values

    # Calculate tidal range
    obs_range = obs_max - obs_min
    all_range = all_max - all_min

    # Calculate Bishop-Taylor et al. 2018 tidal metrics
    spread = obs_range / all_range
    low_tide_offset = abs(all_min - obs_min) / all_range
    high_tide_offset = abs(all_max - obs_max) / all_range

    # Extract x (time in decimal years) and y (distance) values
    all_x = (
        all_tides_df.index.year
        + ((all_tides_df.index.dayofyear - 1) / 365)
        + ((all_tides_df.index.hour - 1) / 24)
    )
    all_y = all_tides_df.tide_m.values.astype(np.float)
    time_period = all_x.max() - all_x.min()

    # Extract x (time in decimal years) and y (distance) values
    obs_x = (
        ds_tides.time.dt.year
        + ((ds_tides.time.dt.dayofyear - 1) / 365)
        + ((ds_tides.time.dt.hour - 1) / 24)
    )
    obs_y = ds_tides.tide_m.values.astype(np.float)

    # Compute linear regression
    obs_linreg = stats.linregress(x=obs_x, y=obs_y)
    all_linreg = stats.linregress(x=all_x, y=all_y)

    if plain_english:

        print(
            f"\n{spread:.0%} of the {all_range:.2f} m modelled astronomical "
            f"tidal range is observed at this location.\nThe lowest "
            f"{low_tide_offset:.0%} and highest {high_tide_offset:.0%} "
            f"of astronomical tides are never observed.\n"
        )

        if linear_reg:

            if obs_linreg.pvalue > 0.05:
                print(
                    f"Observed tides show no significant trends "
                    f"over the ~{time_period:.0f} year period."
                )
            else:
                obs_slope_desc = "decrease" if obs_linreg.slope < 0 else "increase"
                print(
                    f"Observed tides {obs_slope_desc} significantly "
                    f"(p={obs_linreg.pvalue:.3f}) over time by "
                    f"{obs_linreg.slope:.03f} m per year (i.e. a "
                    f"~{time_period * obs_linreg.slope:.2f} m "
                    f"{obs_slope_desc} over the ~{time_period:.0f} year period)."
                )

            if all_linreg.pvalue > 0.05:
                print(
                    f"All tides show no significant trends "
                    f"over the ~{time_period:.0f} year period."
                )
            else:
                all_slope_desc = "decrease" if all_linreg.slope < 0 else "increase"
                print(
                    f"All tides {all_slope_desc} significantly "
                    f"(p={all_linreg.pvalue:.3f}) over time by "
                    f"{all_linreg.slope:.03f} m per year (i.e. a "
                    f"~{time_period * all_linreg.slope:.2f} m "
                    f"{all_slope_desc} over the ~{time_period:.0f} year period)."
                )

    if plot:

        # Create plot and add all time and observed tide data
        fig, ax = plt.subplots(figsize=(10, 5))
        all_tides_df.tide_m.plot(ax=ax, alpha=0.4)
        ds_tides.tide_m.plot.line(
            ax=ax, marker="o", linewidth=0.0, color="black", markersize=2
        )

        # Add horizontal lines for spread/offsets
        ax.axhline(obs_min, color="black", linestyle=":", linewidth=1)
        ax.axhline(obs_max, color="black", linestyle=":", linewidth=1)
        ax.axhline(all_min, color="black", linestyle=":", linewidth=1)
        ax.axhline(all_max, color="black", linestyle=":", linewidth=1)

        # Add text annotations for spread/offsets
        ax.annotate(
            f"    High tide\n    offset ({high_tide_offset:.0%})",
            xy=(all_timerange.max(), np.mean([all_max, obs_max])),
            va="center",
        )
        ax.annotate(
            f"    Spread\n    ({spread:.0%})",
            xy=(all_timerange.max(), np.mean([obs_min, obs_max])),
            va="center",
        )
        ax.annotate(
            f"    Low tide\n    offset ({low_tide_offset:.0%})",
            xy=(all_timerange.max(), np.mean([all_min, obs_min])),
        )

        # Remove top right axes and add labels
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.set_ylabel("Tide height (m)")
        ax.set_xlabel("")
        ax.margins(x=0.015)

    # Export pandas.Series containing tidal stats
    output_stats = {
        "tidepost_lat": tidepost_lat,
        "tidepost_lon": tidepost_lon,
        "observed_mean_m": obs_mean,
        "all_mean_m": all_mean,
        "observed_min_m": obs_min,
        "all_min_m": all_min,
        "observed_max_m": obs_max,
        "all_max_m": all_max,
        "observed_range_m": obs_range,
        "all_range_m": all_range,
        "spread": spread,
        "low_tide_offset": low_tide_offset,
        "high_tide_offset": high_tide_offset,
    }

    if linear_reg:
        output_stats.update(
            {
                "observed_slope": obs_linreg.slope,
                "all_slope": all_linreg.slope,
                "observed_pval": obs_linreg.pvalue,
                "all_pval": all_linreg.pvalue,
            }
        )

    return pd.Series(output_stats).round(round_stats)


def tidal_tag_otps(
    ds,
    tidepost_lat=None,
    tidepost_lon=None,
    ebb_flow=False,
    swap_dims=False,
    return_tideposts=False,
):
    """
    Takes an xarray.Dataset and returns the same dataset with a new
    `tide_m` variable giving the height of the tide at the exact
    moment of each satellite acquisition.

    By default, the function models tides for the centroid of the
    dataset, but a custom tidal modelling location can be specified
    using `tidepost_lat` and `tidepost_lon`.

    Tides are modelled using the OTPS tidal modelling software based on
    the TPXO8 tidal model: http://volkov.oce.orst.edu/tides/tpxo8_atlas.html

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling
        location.
    ebb_flow : bool, optional
        An optional boolean indicating whether to compute if the
        tide phase was ebbing (falling) or flowing (rising) for each
        observation. The default is False; if set to True, a new
        `ebb_flow` variable will be added to the dataset with each
        observation labelled with 'Ebb' or 'Flow'.
    swap_dims : bool, optional
        An optional boolean indicating whether to swap the `time`
        dimension in the original xarray.Dataset to the new
        `tide_m` variable. Defaults to False.
    return_tideposts : bool, optional
        An optional boolean indicating whether to return the `tidepost_lat`
        and `tidepost_lon` location used to model tides in addition to the
        xarray.Dataset. Defaults to False.

    Returns
    -------
    The original xarray.Dataset with a new `tide_m` variable giving
    the height of the tide (and optionally, its ebb-flow phase) at the
    exact moment of each satellite acquisition (if `return_tideposts=True`,
    the function will also return the `tidepost_lon` and `tidepost_lat`
    location used in the analysis).

    """

    # Load tide modelling functions from either OTPS for pyfes
    try:
        from otps import TimePoint
        from otps import predict_tide
    except ImportError:
        from dea_tools.pyfes_model import TimePoint, predict_tide

    # If custom tide modelling locations are not provided, use the
    # dataset centroid
    if not tidepost_lat or not tidepost_lon:

        tidepost_lon, tidepost_lat = ds.extent.centroid.to_crs(
            crs=CRS("EPSG:4326")
        ).coords[0]
        print(
            f"Setting tide modelling location from dataset centroid: "
            f"{tidepost_lon:.2f}, {tidepost_lat:.2f}"
        )

    else:
        print(
            f"Using user-supplied tide modelling location: "
            f"{tidepost_lon:.2f}, {tidepost_lat:.2f}"
        )

    # Use the tidal model to compute tide heights for each observation:
    print(f"Modelling tides using OTPS and the TPXO8 tidal model")
    obs_datetimes = ds.time.data.astype("M8[s]").astype("O").tolist()
    obs_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) for dt in obs_datetimes]
    obs_predictedtides = predict_tide(obs_timepoints)

    # If tides cannot be successfully modeled (e.g. if the centre of the
    # xarray dataset is located is over land), raise an exception
    if len(obs_predictedtides) > 0:

        # Extract tide heights
        obs_tideheights = [predictedtide.tide_m for predictedtide in obs_predictedtides]

        # Assign tide heights to the dataset as a new variable
        ds["tide_m"] = xr.DataArray(obs_tideheights, coords=[ds.time])

        # Optionally calculate the tide phase for each observation
        if ebb_flow:

            # Model tides for a time 15 minutes prior to each previously
            # modelled satellite acquisition time. This allows us to compare
            # tide heights to see if they are rising or falling.
            print("Modelling tidal phase (e.g. ebb or flow)")
            pre_times = ds.time - pd.Timedelta("15 min")
            pre_datetimes = pre_times.data.astype("M8[s]").astype("O").tolist()
            pre_timepoints = [
                TimePoint(tidepost_lon, tidepost_lat, dt) for dt in pre_datetimes
            ]
            pre_predictedtides = predict_tide(pre_timepoints)

            # Compare tides computed for each timestep. If the previous tide
            # was higher than the current tide, the tide is 'ebbing'. If the
            # previous tide was lower, the tide is 'flowing'
            tidal_phase = [
                "Ebb" if pre.tide_m > obs.tide_m else "Flow"
                for pre, obs in zip(pre_predictedtides, obs_predictedtides)
            ]

            # Assign tide phase to the dataset as a new variable
            ds["ebb_flow"] = xr.DataArray(tidal_phase, coords=[ds.time])

        # If swap_dims = True, make tide height the primary dimension
        # instead of time
        if swap_dims:

            # Swap dimensions and sort by tide height
            ds = ds.swap_dims({"time": "tide_m"})
            ds = ds.sortby("tide_m")
            ds = ds.drop("time")

        if return_tideposts:
            return ds, tidepost_lon, tidepost_lat
        else:
            return ds

    else:

        raise ValueError(
            f"Tides could not be modelled for dataset centroid located "
            f"at {tidepost_lon:.2f}, {tidepost_lat:.2f}. This can occur if "
            f"this coordinate occurs over land. Please manually specify "
            f"a tide modelling location located over water using the "
            f"`tidepost_lat` and `tidepost_lon` parameters."
        )


def tidal_stats_otps(
    ds,
    tidepost_lat=None,
    tidepost_lon=None,
    plain_english=True,
    plot=True,
    modelled_freq="2h",
    linear_reg=False,
    round_stats=3,
):
    """
    Takes an xarray.Dataset and statistically compares the tides
    modelled for each satellite observation against the full modelled
    tidal range. This comparison can be used to evaluate whether the
    tides observed by satellites (e.g. Landsat) are biased compared to
    the natural tidal range (e.g. fail to observe either the highest or
    lowest tides etc).

    By default, the function models tides for the centroid of the
    dataset, but a custom tidal modelling location can be specified
    using `tidepost_lat` and `tidepost_lon`.

    For more information about the tidal statistics computed by this
    function, refer to Figure 8 in Bishop-Taylor et al. 2018:
    https://www.sciencedirect.com/science/article/pii/S0272771418308783#fig8
    
    Tides are modelled using the OTPS tidal modelling software based on
    the TPXO8 tidal model: http://volkov.oce.orst.edu/tides/tpxo8_atlas.html

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset object with x, y and time dimensions
    tidepost_lat, tidepost_lon : float or int, optional
        Optional coordinates used to model tides. The default is None,
        which uses the centroid of the dataset as the tide modelling
        location.
    plain_english : bool, optional
        An optional boolean indicating whether to print a plain english
        version of the tidal statistics to the screen. Defaults to True.
    plot : bool, optional
        An optional boolean indicating whether to plot how satellite-
        observed tide heights compare against the full tidal range.
        Defaults to True.
    modelled_freq : str, optional
        An optional string giving the frequency at which to model tides
        when computing the full modelled tidal range. Defaults to '2h',
        which computes a tide height for every two hours across the
        temporal extent of `ds`.
    linear_reg: bool, optional
        Experimental: whether to return linear regression stats that
        assess whether dstellite-observed and all available tides show
        any decreasing or increasing trends over time. Not currently
        recommended as all observed regressions always return as
        significant due to far larger sample size.
    round_stats : int, optional
        The number of decimal places used to round the output statistics.
        Defaults to 3.

    Returns
    -------
    A pandas.Series object containing the following statistics:

        tidepost_lat: latitude used for modelling tide heights
        tidepost_lon: longitude used for modelling tide heights
        observed_min_m: minimum tide height observed by the satellite
        all_min_m: minimum tide height from all available tides
        observed_max_m: maximum tide height observed by the satellite
        all_max_m: maximum tide height from all available tides
        observed_range_m: tidal range observed by the satellite
        all_range_m: full astronomical tidal range based on all
                  available tides
        spread_m: proportion of the full astronomical tidal range observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        low_tide_offset: proportion of the lowest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)
        high_tide_offset: proportion of the highest tides never observed
                  by the satellite (see Bishop-Taylor et al. 2018)

    If `linear_reg = True`, the output will also contain:

        observed_slope: slope of any relationship between observed tide
                  heights and time
        all_slope: slope of any relationship between all available tide
                  heights and time
        observed_pval: significance/p-value of any relationship between
                  observed tide heights and time
        all_pval: significance/p-value of any relationship between
                  all available tide heights and time

    """

    # Load tide modelling functions from either OTPS for pyfes
    try:
        from otps import TimePoint
        from otps import predict_tide
    except ImportError:
        from dea_tools.pyfes_model import TimePoint, predict_tide

    # Model tides for each observation in the supplied xarray object
    ds_tides, tidepost_lon, tidepost_lat = tidal_tag_otps(
        ds, tidepost_lat=tidepost_lat, tidepost_lon=tidepost_lon, return_tideposts=True
    )

    # Drop spatial ref for nicer plotting
    if "spatial_ref" in ds_tides:
        ds_tides = ds_tides.drop("spatial_ref")

    # Generate range of times covering entire period of satellite record
    all_timerange = pd.date_range(
        start=ds_tides.time.min().item(),
        end=ds_tides.time.max().item(),
        freq=modelled_freq,
    )
    all_datetimes = all_timerange.values.astype("M8[s]").astype("O").tolist()

    # Use the tidal model to compute tide heights for each observation:
    all_timepoints = [TimePoint(tidepost_lon, tidepost_lat, dt) for dt in all_datetimes]
    all_predictedtides = predict_tide(all_timepoints)
    all_tideheights = [predictedtide.tide_m for predictedtide in all_predictedtides]

    # Get coarse statistics on all and observed tidal ranges
    obs_mean = ds_tides.tide_m.mean().item()
    all_mean = np.mean(all_tideheights)
    obs_min, obs_max = ds_tides.tide_m.quantile([0.0, 1.0]).values
    all_min, all_max = np.quantile(all_tideheights, [0.0, 1.0])

    # Calculate tidal range
    obs_range = obs_max - obs_min
    all_range = all_max - all_min

    # Calculate Bishop-Taylor et al. 2018 tidal metrics
    spread = obs_range / all_range
    low_tide_offset = abs(all_min - obs_min) / all_range
    high_tide_offset = abs(all_max - obs_max) / all_range

    # Extract x (time in decimal years) and y (distance) values
    all_x = (
        all_timerange.year
        + ((all_timerange.dayofyear - 1) / 365)
        + ((all_timerange.hour - 1) / 24)
    )
    all_y = all_tideheights
    time_period = all_x.max() - all_x.min()

    # Extract x (time in decimal years) and y (distance) values
    obs_x = (
        ds_tides.time.dt.year
        + ((ds_tides.time.dt.dayofyear - 1) / 365)
        + ((ds_tides.time.dt.hour - 1) / 24)
    )
    obs_y = ds_tides.tide_m.values.astype(np.float)

    # Compute linear regression
    obs_linreg = stats.linregress(x=obs_x, y=obs_y)
    all_linreg = stats.linregress(x=all_x, y=all_y)

    if plain_english:

        print(
            f"\n{spread:.0%} of the {all_range:.2f} m modelled astronomical "
            f"tidal range is observed at this location.\nThe lowest "
            f"{low_tide_offset:.0%} and highest {high_tide_offset:.0%} "
            f"of astronomical tides are never observed.\n"
        )
        
        if linear_reg:

            # Plain english
            if obs_linreg.pvalue > 0.05:
                print(
                    f"Observed tides show no significant trends "
                    f"over the ~{time_period:.0f} year period."
                )
            else:
                obs_slope_desc = "decrease" if obs_linreg.slope < 0 else "increase"
                print(
                    f"Observed tides {obs_slope_desc} significantly "
                    f"(p={obs_linreg.pvalue:.3f}) over time by "
                    f"{obs_linreg.slope:.03f} m per year (i.e. a "
                    f"~{time_period * obs_linreg.slope:.2f} m "
                    f"{obs_slope_desc} over the ~{time_period:.0f} year period)."
                )

            if all_linreg.pvalue > 0.05:
                print(
                    f"All tides show no significant trends "
                    f"over the ~{time_period:.0f} year period."
                )
            else:
                all_slope_desc = "decrease" if all_linreg.slope < 0 else "increase"
                print(
                    f"All tides {all_slope_desc} significantly "
                    f"(p={all_linreg.pvalue:.3f}) over time by "
                    f"{all_linreg.slope:.03f} m per year (i.e. a "
                    f"~{time_period * all_linreg.slope:.2f} m "
                    f"{all_slope_desc} over the ~{time_period:.0f} year period)."
                )

    if plot:

        # Create plot and add all time and observed tide data
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(all_timerange, all_tideheights, alpha=0.4)
        ds_tides.tide_m.plot.line(
            ax=ax, marker="o", linewidth=0.0, color="black", markersize=2
        )

        # Add horizontal lines for spread/offsets
        ax.axhline(obs_min, color="black", linestyle=":", linewidth=1)
        ax.axhline(obs_max, color="black", linestyle=":", linewidth=1)
        ax.axhline(all_min, color="black", linestyle=":", linewidth=1)
        ax.axhline(all_max, color="black", linestyle=":", linewidth=1)

        # Add text annotations for spread/offsets
        ax.annotate(
            f"    High tide\n    offset ({high_tide_offset:.0%})",
            xy=(all_timerange.max(), np.mean([all_max, obs_max])),
            va="center",
        )
        ax.annotate(
            f"    Spread\n    ({spread:.0%})",
            xy=(all_timerange.max(), np.mean([obs_min, obs_max])),
            va="center",
        )
        ax.annotate(
            f"    Low tide\n    offset ({low_tide_offset:.0%})",
            xy=(all_timerange.max(), np.mean([all_min, obs_min])),
        )

        # Remove top right axes and add labels
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.set_ylabel("Tide height (m)")
        ax.set_xlabel("")
        ax.margins(x=0.015)

    # Export pandas.Series containing tidal stats
    output_stats = {
        "tidepost_lat": tidepost_lat,
        "tidepost_lon": tidepost_lon,
        "observed_mean_m": obs_mean,
        "all_mean_m": all_mean,
        "observed_min_m": obs_min,
        "all_min_m": all_min,
        "observed_max_m": obs_max,
        "all_max_m": all_max,
        "observed_range_m": obs_range,
        "all_range_m": all_range,
        "spread": spread,
        "low_tide_offset": low_tide_offset,
        "high_tide_offset": high_tide_offset,
    }

    if linear_reg:
        output_stats.update(
            {
                "observed_slope": obs_linreg.slope,
                "all_slope": all_linreg.slope,
                "observed_pval": obs_linreg.pvalue,
                "all_pval": all_linreg.pvalue,
            }
        )

    return pd.Series(output_stats).round(round_stats)
