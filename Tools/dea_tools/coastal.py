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

Last modified: September 2023

"""

# Import required packages
import os
import pyproj
import pathlib
import warnings
import scipy.interpolate
import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy import stats
from warnings import warn
from functools import partial
from shapely.geometry import box, shape
from owslib.wfs import WebFeatureService

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
    bbox: tuple, crs="EPSG:4326", layer="shorelines_annual", drop_wms=True
) -> gpd.GeoDataFrame:
    """
    Load DEA Coastlines annual shorelines or rates of change points data
    for a provided bounding box using WFS.

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
        coastlines_gdf = coastlines_gdf.loc[
            :, ~coastlines_gdf.columns.str.contains("wms_")
        ]

    return coastlines_gdf


def _model_tides(
    model,
    x,
    y,
    time,
    directory,
    crs,
    method,
    extrapolate,
    cutoff,
    output_units,
):
    """
    Worker function applied in parallel by `model_tides`. Handles the
    extraction of tide modelling constituents and tide modelling using
    `pyTMD`.
    """

    import pyTMD.constants
    import pyTMD.eop
    import pyTMD.io
    import pyTMD.time
    import pyTMD.io.model
    import pyTMD.predict
    import pyTMD.spatial
    import pyTMD.utilities

    # Get parameters for tide model; use custom definition file for
    # FES2012 (leave this as an undocumented feature for now)
    if model == "FES2012":
        pytmd_model = pyTMD.io.model(directory).from_file(
            directory / "model_FES2012.def"
        )
    else:
        pytmd_model = pyTMD.io.model(
            directory, format="netcdf", compressed=False
        ).elevation(model)

    # Determine point and time counts
    n_points = len(x)
    n_times = len(time)

    # Convert x, y to latitude/longitude
    transformer = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x.flatten(), y.flatten())

    # Convert datetime
    timescale = pyTMD.time.timescale().from_datetime(time.flatten())

    # Read tidal constants and interpolate to grid points
    if pytmd_model.format in ("OTIS", "ATLAS", "ESR"):
        amp, ph, D, c = pyTMD.io.OTIS.extract_constants(
            lon,
            lat,
            pytmd_model.grid_file,
            pytmd_model.model_file,
            pytmd_model.projection,
            type=pytmd_model.type,
            method=method,
            extrapolate=extrapolate,
            cutoff=cutoff,
            grid=pytmd_model.format,
        )
        # Use delta time at 2000.0 to match TMD outputs
        deltat = np.zeros((n_times), dtype=np.float64)
    elif pytmd_model.format == "netcdf":
        amp, ph, D, c = pyTMD.io.ATLAS.extract_constants(
            lon,
            lat,
            pytmd_model.grid_file,
            pytmd_model.model_file,
            type=pytmd_model.type,
            method=method,
            extrapolate=extrapolate,
            cutoff=cutoff,
            scale=pytmd_model.scale,
            compressed=pytmd_model.compressed,
        )
        # Use delta time at 2000.0 to match TMD outputs
        deltat = np.zeros((n_times), dtype=np.float64)
    elif pytmd_model.format == "GOT":
        amp, ph, c = pyTMD.io.GOT.extract_constants(
            lon,
            lat,
            pytmd_model.model_file,
            method=method,
            extrapolate=extrapolate,
            cutoff=cutoff,
            scale=pytmd_model.scale,
            compressed=pytmd_model.compressed,
        )
        # Delta time (TT - UT1)
        deltat = timescale.tt_ut1
    elif pytmd_model.format == "FES":
        amp, ph = pyTMD.io.FES.extract_constants(
            lon,
            lat,
            pytmd_model.model_file,
            type=pytmd_model.type,
            version=pytmd_model.version,
            method=method,
            extrapolate=extrapolate,
            cutoff=cutoff,
            scale=pytmd_model.scale,
            compressed=pytmd_model.compressed,
        )

        # Available model constituents
        c = pytmd_model.constituents

        # Delta time (TT - UT1)
        deltat = timescale.tt_ut1

    # Calculate complex phase in radians for Euler's
    cph = -1j * ph * np.pi / 180.0

    # Calculate constituent oscillation
    hc = amp * np.exp(cph)

    # Repeat constituents to length of time and number of input
    # coords before passing to `predict_tide_drift`
    t, hc, deltat = (
        np.tile(timescale.tide, n_points),
        hc.repeat(n_times, axis=0),
        np.tile(deltat, n_points),
    )

    # Predict tidal elevations at time and infer minor corrections
    npts = len(t)
    tide = np.ma.zeros((npts), fill_value=np.nan)
    tide.mask = np.any(hc.mask, axis=1)

    # Predict tides
    tide.data[:] = pyTMD.predict.drift(
        t, hc, c, deltat=deltat, corrections=pytmd_model.format
    )
    minor = pyTMD.predict.infer_minor(
        t, hc, c, deltat=deltat, corrections=pytmd_model.format
    )
    tide.data[:] += minor.data[:]

    # Replace invalid values with fill value
    tide.data[tide.mask] = tide.fill_value

    # Convert data to pandas.DataFrame
    tide_df = pd.DataFrame(
        {
            "time": np.tile(time, n_points),
            "x": np.repeat(x, n_times),
            "y": np.repeat(y, n_times),
            "tide_model": model,
            "tide_m": tide,
        }
    ).set_index("time")

    # Optionally convert outputs to integer units (can save memory)
    if output_units == "m":
        tide_df["tide_m"] = tide_df.tide_m.astype(np.float32)
    elif output_units == "cm":
        tide_df["tide_m"] = (tide_df.tide_m * 100).astype(np.int16)
    elif output_units == "mm":
        tide_df["tide_m"] = (tide_df.tide_m * 1000).astype(np.int16)

    return tide_df


def model_tides(
    x,
    y,
    time,
    model="FES2014",
    directory=None,
    crs="EPSG:4326",
    method="bilinear",
    extrapolate=True,
    cutoff=10,
    parallel=True,
    parallel_splits=5,
    output_units="m",
    output_format="long",
    epsg=None,
):
    """
    Compute tides at points and times using tidal harmonics.
    If multiple x, y points are provided, tides will be
    computed for all timesteps at each point.

    This function supports any tidal model supported by
    `pyTMD`, including the FES2014 Finite Element Solution
    tide model, and the TPXO8-atlas and TPXO9-atlas-v5
    TOPEX/POSEIDON global tide models.

    This function requires access to tide model data files.
    These should be placed in a folder with subfolders matching
    the formats specified by `pyTMD`:
    https://pytmd.readthedocs.io/en/latest/getting_started/Getting-Started.html#directories

    For FES2014 (https://www.aviso.altimetry.fr/es/data/products/auxiliary-products/global-tide-fes/description-fes2014.html):
        - {directory}/fes2014/ocean_tide/
        - {directory}/fes2014/load_tide/

    For TPXO8-atlas (https://www.tpxo.net/tpxo-products-and-registration):
        - {directory}/tpxo8_atlas/

    For TPXO9-atlas-v5 (https://www.tpxo.net/tpxo-products-and-registration):
        - {directory}/TPXO9_atlas_v5/

    For EOT20 (https://www.seanoe.org/data/00683/79489/):
        - {directory}/EOT20/ocean_tides/
        - {directory}/EOT20/load_tides/

    For GOT4.10c (https://earth.gsfc.nasa.gov/geo/data/ocean-tide-models):
        - {directory}/GOT4.10c/grids_oceantide_netcdf/

    For HAMTIDE (https://www.cen.uni-hamburg.de/en/icdc/data/ocean/hamtide.html):
        - {directory}/hamtide/

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
    model : string, optional
        The tide model used to model tides. Options include:
        - "FES2014" (only pre-configured option on DEA Sandbox)
        - "TPXO9-atlas-v5"
        - "TPXO8-atlas"
        - "EOT20"
        - "HAMTIDE11"
        - "GOT4.10"
    directory : string, optional
        The directory containing tide model data files. If no path is
        provided, this will default to the environment variable
        "DEA_TOOLS_TIDE_MODELS" if set, otherwise "/var/share/tide_models".
        Tide modelling files should be stored in sub-folders for each
        model that match the structure provided by `pyTMD`:
        https://pytmd.readthedocs.io/en/latest/getting_started/Getting-Started.html#directories
        For example:
        - {directory}/fes2014/ocean_tide/
          {directory}/fes2014/load_tide/
        - {directory}/tpxo8_atlas/
        - {directory}/TPXO9_atlas_v5/
    crs : str, optional
        Input coordinate reference system for 'x' and 'y' coordinates.
        Defaults to "EPSG:4326" (WGS84; degrees latitude, longitude).
    method : string, optional
        Method used to interpolate tidal contsituents
        from model files. Options include:
        - bilinear: quick bilinear interpolation
        - spline: scipy bivariate spline interpolation
        - linear, nearest: scipy regular grid interpolations
    extrapolate : bool, optional
        Whether to extrapolate tides for locations outside of
        the tide modelling domain using nearest-neighbor
    cutoff : int or float, optional
        Extrapolation cutoff in kilometers. Set to `np.inf`
        to extrapolate for all points.
    parallel : boolean, optional
        Whether to parallelise tide modelling using `concurrent.futures`.
        If multiple tide models are requested, these will be run in
        parallel. Optionally, tide modelling can also be run in parallel
        across input x and y coordinates (see "parallel_splits" below).
        Default is True.
    parallel_splits : int, optional
        Whether to split the input x and y coordinates into smaller,
        evenly-sized chunks that are processed in parallel. This can
        provide a large performance boost when processing large numbers
        of coordinates. The default is 5 chunks, which will split
        coordinates into 5 parallelised chunks.
    output_units : str, optional
        Whether to return modelled tides in floating point metre units,
        or integer centimetre units (i.e. scaled by 100) or integer
        millimetre units (i.e. scaled by 1000. Returning outputs in
        integer units can be useful for reducing memory usage.
        Defaults to "m" for metres; set to "cm" for centimetres or "mm"
        for millimetres.
    output_format : str, optional
        Whether to return the output dataframe in long format (with
        results stacked vertically along "tide_model" and "tide_m"
        columns), or wide format (with a column for each tide model).
        Defaults to "long".
    epsg : int, DEPRECATED
        Deprecated; use 'crs' instead.

    Returns
    -------
    A pandas.DataFrame containing tide heights for every
    combination of time and point coordinates.

    """

    # Deprecate `epsg` param
    if epsg is not None:
        warn(
            "The `epsg` parameter is deprecated; please use `crs` to "
            "provide CRS information in the form 'EPSG:XXXX'",
            DeprecationWarning,
            stacklevel=2,
        )

    # Set tide modelling files directory. If no custom path is provided,
    # first try global environmental var, then "/var/share/tide_models"
    if directory is None:
        if "DEA_TOOLS_TIDE_MODELS" in os.environ:
            directory = os.environ["DEA_TOOLS_TIDE_MODELS"]
        else:
            directory = "/var/share/tide_models"

    # Verify path exists
    directory = pathlib.Path(directory).expanduser()
    if not directory.exists():
        raise FileNotFoundError("Invalid tide directory")

    # If time passed as a single Timestamp, convert to datetime64
    if isinstance(time, pd.Timestamp):
        time = time.to_datetime64()

    # Turn inputs into arrays for consistent handling
    model = np.atleast_1d(model)
    x = np.atleast_1d(x)
    y = np.atleast_1d(y)
    time = np.atleast_1d(time)

    # Validate input arguments
    assert method in ("bilinear", "spline", "linear", "nearest")
    assert len(x) == len(y), "x and y must be the same length"

    # Verify that all provided models are in list of supported models
    valid_models = [
        "FES2014",
        "FES2012",
        "TPXO9-atlas-v5",
        "TPXO8-atlas",
        "EOT20",
        "HAMTIDE11",
        "GOT4.10",
    ]
    if not all(m in valid_models for m in model):
        raise ValueError(
            f"One or more of the models requested ({model}) is not valid. "
            f"The following models are currently supported: {valid_models}"
        )

    # Update tide modelling func to add default keyword arguments that
    # are used for every iteration during parallel processing
    iter_func = partial(
        _model_tides,
        time=time,
        directory=directory,
        crs=crs,
        method=method,
        extrapolate=extrapolate,
        cutoff=cutoff,
        output_units=output_units,
    )

    # Ensure requested parallel splits is not smaller than number of points
    parallel_splits = min(parallel_splits, len(x))

    # Parallelise if either multiple models or multiple splits requested
    if parallel & ((len(model) > 1) | (parallel_splits > 1)):
        from concurrent.futures import ProcessPoolExecutor
        from tqdm import tqdm

        with ProcessPoolExecutor() as executor:
            print(f"Modelling tides using {', '.join(model)} in parallel")

            # Optionally split lon/lat points into `splits_n` chunks
            # that will be applied in parallel
            x_split = np.array_split(x, parallel_splits)
            y_split = np.array_split(y, parallel_splits)

            # Get every combination of models and lon/lat points, and
            # extract as iterables that can be passed to `executor.map()`
            model_iters, x_iters, y_iters = zip(
                *[
                    (m, x_split[i], y_split[i])
                    for m in model
                    for i in range(parallel_splits)
                ]
            )

            # Apply func in parallel, iterating through each input param
            model_outputs = list(
                tqdm(
                    executor.map(iter_func, model_iters, x_iters, y_iters),
                    total=len(model_iters),
                )
            )

    # Model tides in series if parallelisation is off
    else:
        model_outputs = []

        for model_i in model:
            print(f"Modelling tides using {model_i}")
            tide_df = iter_func(model_i, x, y)
            model_outputs.append(tide_df)

    # Combine outputs into a single dataframe
    tide_df = pd.concat(model_outputs, axis=0)

    # Optionally convert to a wide format dataframe with a tide model in
    # each dataframe column
    if output_format == "wide":
        print("Converting to a wide format dataframe")
        tide_df = (
            tide_df.set_index(["x", "y"], append=True)
            .pivot(columns="tide_model", values="tide_m")
            .reset_index(["x", "y"])
        )

    return tide_df


def pixel_tides(
    ds,
    times=None,
    resample=True,
    calculate_quantiles=None,
    resolution=None,
    buffer=None,
    resample_method="bilinear",
    model="FES2014",
    dask_chunks="auto",
    dask_compute=True,
    **model_tides_kwargs,
):
    """
    Obtain tide heights for each pixel in a dataset by modelling
    tides into a low-resolution grid surrounding the dataset,
    then (optionally) spatially resample this low-res data back
    into the original higher resolution dataset extent and resolution.

    Parameters:
    -----------
    ds : xarray.Dataset
        A dataset whose geobox (`ds.odc.geobox`) will be used to define
        the spatial extent of the low resolution tide modelling grid.
    times : pandas.DatetimeIndex or list of pandas.Timestamps, optional
        By default, the function will model tides using the times
        contained in the `time` dimension of `ds`. Alternatively, this
        param can be used to model tides for a custom set of times
        instead. For example:
        `times=pd.date_range(start="2000", end="2001", freq="5h")`
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
        modelling. The default None will create a 5000 m resolution grid
        if `ds` has a projected CRS (i.e. metre units), or a 0.05 degree
        resolution grid if `ds` has a geographic CRS (e.g. degree units).
        Note: higher resolutions do not necessarily provide better
        tide modelling performance, as results will be limited by the
        resolution of the underlying global tide model (e.g. 1/16th
        degree / ~5 km resolution grid for FES2014).
    buffer : int, optional
        The amount by which to buffer the higher resolution grid extent
        when creating the new low resolution grid. This buffering is
        important as it ensures that ensure pixel-based tides are seamless
        across dataset boundaries. This buffer will eventually be clipped
        away when the low-resolution data is re-projected back to the
        resolution and extent of the higher resolution dataset. To
        ensure that at least two pixels occur outside of the dataset
        bounds, the default None applies a 12000 m buffer if `ds` has a
        projected CRS (i.e. metre units), or a 0.12 degree buffer if
        `ds` has a geographic CRS (e.g. degree units).
    resample_method : string, optional
        If resampling is requested (see `resample` above), use this
        resampling method when converting from low resolution to high
        resolution pixels. Defaults to "bilinear"; valid options include
        "nearest", "cubic", "min", "max", "average" etc.
    model : string or list of strings
        The tide model or a list of models used to model tides, as
        supported by the `pyTMD` Python package. Options include:
        - "FES2014" (default; pre-configured on DEA Sandbox)
        - "TPXO8-atlas"
        - "TPXO9-atlas-v5"
        - "EOT20"
        - "HAMTIDE11"
        - "GOT4.10"
    dask_chunks : str or tuple, optional
        Can be used to configure custom Dask chunking for the final
        resampling step. The default of "auto" will automatically set
        x/y chunks to match those in `ds` if they exist, otherwise will
        set x/y chunks that cover the entire extent of the dataset.
        For custom chunks, provide a tuple in the form `(y, x)`, e.g.
        `(2048, 2048)`.
    dask_compute : bool, optional
        Whether to compute results of the resampling step using Dask.
        If False, this will return `tides_highres` as a Dask array.
    **model_tides_kwargs :
        Optional parameters passed to the `dea_tools.coastal.model_tides`
        function. Important parameters include "directory" (used to
        specify the location of input tide modelling files) and "cutoff"
        (used to extrapolate modelled tides away from the coast; if not
        specified here, cutoff defaults to `np.inf`).

    Returns:
    --------
    If `resample` is False:

        tides_lowres : xr.DataArray
            A low resolution data array giving either tide heights every
            timestep in `ds` (if `times` is None), tide heights at every
            time in `times` (if `times` is not None), or tide height quantiles
            for every quantile provided by `calculate_quantiles`.

    If `resample` is True:

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

    # Set defaults passed to `model_tides`
    model_tides_kwargs.setdefault("cutoff", np.inf)

    # Standardise model into a list for easy handling
    model = [model] if isinstance(model, str) else model

    # Test if no time dimension and nothing passed to `times`
    if ("time" not in ds.dims) & (times is None):
        raise ValueError(
            "`ds` does not contain a 'time' dimension. Times are required "
            "for modelling tides: please pass in a set of custom tides "
            "using the `times` parameter. For example: "
            "`times=pd.date_range(start='2000', end='2001', freq='5h')`"
        )

    # If custom times are provided, convert them to a consistent
    # pandas.DatatimeIndex format
    if times is not None:
        if isinstance(times, list):
            time_coords = pd.DatetimeIndex(times)
        elif isinstance(times, pd.Timestamp):
            time_coords = pd.DatetimeIndex([times])
        else:
            time_coords = times

    # Otherwise, use times from `ds` directly
    else:
        time_coords = ds.coords["time"]

    # Determine spatial dimensions
    y_dim, x_dim = ds.odc.spatial_dims

    # Determine resolution and buffer, using different defaults for
    # geographic (i.e. degrees) and projected (i.e. metres) CRSs:
    crs_units = ds.odc.geobox.crs.units[0][0:6]
    if ds.odc.geobox.crs.geographic:
        if resolution is None:
            resolution = 0.05
        elif resolution > 360:
            raise ValueError(
                f"A resolution of greater than 360 was "
                f"provided, but `ds` has a geographic CRS "
                f"in {crs_units} units. Did you accidently "
                f"provide a resolution in projected "
                f"(i.e. metre) units?"
            )
        if buffer is None:
            buffer = 0.12
    else:
        if resolution is None:
            resolution = 5000
        elif resolution < 1:
            raise ValueError(
                f"A resolution of less than 1 was provided, "
                f"but `ds` has a projected CRS in "
                f"{crs_units} units. Did you accidently "
                f"provide a resolution in geographic "
                f"(degree) units?"
            )
        if buffer is None:
            buffer = 12000

    # Raise error if resolution is less than dataset resolution
    dataset_res = ds.odc.geobox.resolution.x
    if resolution < dataset_res:
        raise ValueError(
            f"The resolution of the low-resolution tide "
            f"modelling grid ({resolution:.2f}) is less "
            f"than `ds`'s pixel resolution ({dataset_res:.2f}). "
            f"This can cause extremely slow tide modelling "
            f"performance. Please select provide a resolution "
            f"greater than {dataset_res:.2f} using "
            f"`pixel_tides`'s 'resolution' parameter."
        )

    # Create a new reduced resolution tide modelling grid after
    # first buffering the grid
    print(
        f"Creating reduced resolution {resolution} x {resolution} "
        f"{crs_units} tide modelling array"
    )
    buffered_geobox = ds.odc.geobox.buffered(buffer)
    rescaled_geobox = GeoBox.from_bbox(
        bbox=buffered_geobox.boundingbox, resolution=resolution
    )
    rescaled_ds = odc.geo.xr.xr_zeros(rescaled_geobox)

    # Flatten grid to 1D, then add time dimension
    flattened_ds = rescaled_ds.stack(z=(x_dim, y_dim))
    flattened_ds = flattened_ds.expand_dims(dim={"time": time_coords.values})

    # Model tides in parallel, returning a pandas.DataFrame
    tide_df = model_tides(
        x=flattened_ds[x_dim],
        y=flattened_ds[y_dim],
        time=flattened_ds.time,
        crs=f"EPSG:{ds.odc.geobox.crs.epsg}",
        model=model,
        **model_tides_kwargs,
    )

    # Convert our pandas.DataFrame tide modelling outputs to xarray
    tides_lowres = (
        tide_df
        # Rename x and y dataframe columns to match x and y xarray dims
        .rename({"x": x_dim, "y": y_dim}, axis=1)
        # Add x, y and tide model columns to dataframe indexes so we can
        # convert our dataframe to a multidimensional xarray
        .set_index([y_dim, x_dim, "tide_model"], append=True)
        # Convert to xarray and select our tide modelling xr.DataArray
        .to_xarray()
        .tide_m
        # Re-index and transpose into our input coordinates and dim order
        .reindex_like(rescaled_ds)
        .transpose("tide_model", "time", y_dim, x_dim)
    )

    # Optionally calculate and return quantiles rather than raw data.
    # Set dtype to dtype of the input data as quantile always returns
    # float64 (memory intensive)
    if calculate_quantiles is not None:
        print("Computing tide quantiles")
        tides_lowres = tides_lowres.quantile(q=calculate_quantiles, dim="time").astype(
            tides_lowres.dtype
        )

    # If only one tidal model exists, squeeze out "tide_model" dim
    if len(tides_lowres.tide_model) == 1:
        tides_lowres = tides_lowres.squeeze("tide_model")

    # Ensure CRS is present before we apply any resampling
    tides_lowres = tides_lowres.odc.assign_crs(ds.odc.geobox.crs)

    # Reproject into original high resolution grid
    if resample:
        print("Reprojecting tides into original array")
        # Convert array to Dask, using no chunking along y and x dims,
        # and a single chunk for each timestep/quantile and tide model
        tides_lowres_dask = tides_lowres.chunk(
            {d: None if d in [y_dim, x_dim] else 1 for d in tides_lowres.dims}
        )

        # Automatically set Dask chunks for reprojection if set to "auto". 
        # This will either use x/y chunks if they exist in `ds`, else 
        # will cover the entire x and y dims) so we don't end up with 
        # hundreds of tiny x and y chunks due to the small size of 
        # `tides_lowres` (possible odc.geo bug?)
        if dask_chunks == "auto":
            if (y_dim in ds.chunks) & (x_dim in ds.chunks):
                dask_chunks = (ds.chunks[y_dim], ds.chunks[x_dim])
            else:
                dask_chunks = ds.odc.geobox.shape

        # Reproject into the GeoBox of `ds` using odc.geo and Dask
        tides_highres = tides_lowres_dask.odc.reproject(
            how=ds.odc.geobox,
            chunks=dask_chunks,
            resampling=resample_method,
        ).rename("tide_m")

        # Optionally process and load into memory with Dask
        if dask_compute:
            tides_highres.load()

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
    # model = (
    #     "FES2014" if "model" not in model_tides_kwargs else model_tides_kwargs["model"]
    # )
    tide_df = model_tides(
        x=tidepost_lon,
        y=tidepost_lat,
        time=ds.time,
        crs="EPSG:4326",
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
            crs="EPSG:4326",
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
        ds = ds.drop_vars("time")

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
        ds_tides = ds_tides.drop_vars("spatial_ref")

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
        crs="EPSG:4326",
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
    all_y = all_tides_df.tide_m.values.astype(np.float32)
    time_period = all_x.max() - all_x.min()

    # Extract x (time in decimal years) and y (distance) values
    obs_x = (
        ds_tides.time.dt.year
        + ((ds_tides.time.dt.dayofyear - 1) / 365)
        + ((ds_tides.time.dt.hour - 1) / 24)
    )
    obs_y = ds_tides.tide_m.values.astype(np.float32)

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
            ds = ds.drop_vars("time")

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
        ds_tides = ds_tides.drop_vars("spatial_ref")

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
    obs_y = ds_tides.tide_m.values.astype(np.float32)

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
    glint_angle = np.cos(view_zenith_rad) * np.cos(solar_zenith_rad) - np.sin(
        view_zenith_rad
    ) * np.sin(solar_zenith_rad) * np.cos(phi)

    # Convert to degrees
    glint_array = np.degrees(np.arccos(glint_angle))

    return glint_array