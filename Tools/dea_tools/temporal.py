## dea_temporal.py
"""
Conducting temporal (time-domain) analyses on Digital Earth Australia.

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
GitHub: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new
    
Last modified: May 2024
"""

import sys
import dask
import dask.array as da
import hdstats
import warnings
import numpy as np
import xarray as xr
import pandas as pd
import scipy.signal
from scipy.signal import wiener
from scipy.stats import t
from packaging import version

from datacube.utils.geometry import assign_crs


def allNaN_arg(da, dim, stat):
    """
    Calculate da.argmax() or da.argmin() while handling
    all-NaN slices. Fills all-NaN locations with an
    float and then masks the offending cells.

    Parameters
    ----------
    da : xarray.DataArray
    dim : str
        Dimension over which to calculate argmax, argmin e.g. 'time'
    stat : str
        The statistic to calculte, either 'min' for argmin()
        or 'max' for .argmax()

    Returns
    -------
    xarray.DataArray
    """
    # generate a mask where entire axis along dimension is NaN
    mask = da.isnull().all(dim)

    if stat == "max":
        y = da.fillna(float(da.min() - 1))
        y = y.argmax(dim=dim, skipna=True).where(~mask)
        return y

    if stat == "min":
        y = da.fillna(float(da.max() + 1))
        y = y.argmin(dim=dim, skipna=True).where(~mask)
        return y


def _vpos(da):
    """
    vPOS = Value at peak of season
    """
    return da.max("time")


def _pos(da):
    """
    POS = DOY of peak of season
    """
    return da.isel(time=da.argmax("time")).time.dt.dayofyear


def _trough(da):
    """
    Trough = Minimum value
    """
    return da.min("time")


def _aos(vpos, trough):
    """
    AOS = Amplitude of season
    """
    return vpos - trough


def _vsos(da, pos, method_sos="first"):
    """
    vSOS = Value at the start of season
    Params
    -----
    da : xarray.DataArray
    method_sos : str,
        If 'first' then vSOS is estimated
        as the first positive slope on the
        greening side of the curve. If 'median',
        then vSOS is estimated as the median value
        of the postive slopes on the greening side
        of the curve.
    """
    # select timesteps before peak of season (AKA greening)
    greenup = da.where(da.time < pos.time)
    # find the first order slopes
    green_deriv = greenup.differentiate("time")
    # find where the first order slope is postive
    pos_green_deriv = green_deriv.where(green_deriv > 0)
    # positive slopes on greening side
    pos_greenup = greenup.where(~np.isnan(pos_green_deriv))
    # find the median
    median = pos_greenup.median("time")
    # distance of values from median
    distance = pos_greenup - median

    if method_sos == "first":
        # find index (argmin) where distance is most negative
        idx = allNaN_arg(distance, "time", "min").astype("int16")

    if method_sos == "median":
        # find index (argmin) where distance is smallest absolute value
        idx = allNaN_arg(np.fabs(distance), "time", "min").astype("int16")

    return pos_greenup.isel(time=idx)


def _sos(vsos):
    """
    SOS = DOY for start of season
    """
    return vsos.time.dt.dayofyear


def _veos(da, pos, method_eos="last"):
    """
    vEOS = Value at the end of season
    Params
    -----
    method_eos : str
        If 'last' then vEOS is estimated
        as the last negative slope on the
        senescing side of the curve. If 'median',
        then vEOS is estimated as the 'median' value
        of the negative slopes on the senescing
        side of the curve.
    """
    # select timesteps before peak of season (AKA greening)
    senesce = da.where(da.time > pos.time)
    # find the first order slopes
    senesce_deriv = senesce.differentiate("time")
    # find where the fst order slope is negative
    neg_senesce_deriv = senesce_deriv.where(~np.isnan(senesce_deriv < 0))
    # negative slopes on senescing side
    neg_senesce = senesce.where(neg_senesce_deriv)
    # find medians
    median = neg_senesce.median("time")
    # distance to the median
    distance = neg_senesce - median

    if method_eos == "last":
        # index where last negative slope occurs
        idx = allNaN_arg(distance, "time", "min").astype("int16")

    if method_eos == "median":
        # index where median occurs
        idx = allNaN_arg(np.fabs(distance), "time", "min").astype("int16")

    return neg_senesce.isel(time=idx)


def _eos(veos):
    """
    EOS = DOY for end of seasonn
    """
    return veos.time.dt.dayofyear


def _los(da, eos, sos):
    """
    LOS = Length of season (in DOY)
    """
    los = eos - sos
    # handle negative values
    los = xr.where(
        los >= 0,
        los,
        da.time.dt.dayofyear.values[-1] + (eos.where(los < 0) - sos.where(los < 0)),
    )

    return los


def _rog(vpos, vsos, pos, sos):
    """
    ROG = Rate of Greening (Days)
    """
    return (vpos - vsos) / (pos - sos)


def _ros(veos, vpos, eos, pos):
    """
    ROG = Rate of Senescing (Days)
    """
    return (veos - vpos) / (eos - pos)


def xr_phenology(
    da,
    stats=[
        "SOS",
        "POS",
        "EOS",
        "Trough",
        "vSOS",
        "vPOS",
        "vEOS",
        "LOS",
        "AOS",
        "ROG",
        "ROS",
    ],
    method_sos="first",
    method_eos="last",
    verbose=True,
):
    """
    Obtain land surface phenology metrics from an
    xarray.DataArray containing a timeseries of a
    vegetation index like NDVI.

    Last modified February 2023

    Parameters
    ----------
    da :  xarray.DataArray
        DataArray should contain a 2D or 3D time series of a
        vegetation index like NDVI, EVI
    stats : list
        list of phenological statistics to return. Regardless of
        the metrics returned, all statistics are calculated
        due to inter-dependencies between metrics.
        Options include:

        * ``'SOS'``: DOY of start of season
        * ``'POS'``: DOY of peak of season
        * ``'EOS'``: DOY of end of season
        * ``'vSOS'``: Value at start of season
        * ``'vPOS'``: Value at peak of season
        * ``'vEOS'``: Value at end of season
        * ``'Trough'``: Minimum value of season
        * ``'LOS'``: Length of season (DOY)
        * ``'AOS'``: Amplitude of season (in value units)
        * ``'ROG'``: Rate of greening
        * ``'ROS'``: Rate of senescence

    method_sos : str
        If 'first' then vSOS is estimated as the first positive
        slope on the greening side of the curve. If 'median',
        then vSOS is estimated as the median value of the postive
        slopes on the greening side of the curve.
    method_eos : str
        If 'last' then vEOS is estimated as the last negative slope
        on the senescing side of the curve. If 'median', then vEOS is
        estimated as the 'median' value of the negative slopes on the
        senescing side of the curve.

    Returns
    -------
    xarray.Dataset
        Dataset containing variables for the selected
        phenology statistics

    """
    # Check inputs before running calculations
    if dask.is_dask_collection(da):
        if version.parse(xr.__version__) < version.parse("0.16.0"):
            raise TypeError(
                "Dask arrays are not currently supported by this function, "
                + "run da.compute() before passing dataArray."
            )
        stats_dtype = {
            "SOS": np.int16,
            "POS": np.int16,
            "EOS": np.int16,
            "Trough": np.float32,
            "vSOS": np.float32,
            "vPOS": np.float32,
            "vEOS": np.float32,
            "LOS": np.int16,
            "AOS": np.float32,
            "ROG": np.float32,
            "ROS": np.float32,
        }
        da_template = da.isel(time=0).drop("time")
        template = xr.Dataset(
            {
                var_name: da_template.astype(var_dtype)
                for var_name, var_dtype in stats_dtype.items()
                if var_name in stats
            }
        )
        da_all_time = da.chunk({"time": -1})

        lazy_phenology = da_all_time.map_blocks(
            xr_phenology,
            kwargs=dict(
                stats=stats,
                method_sos=method_sos,
                method_eos=method_eos,
            ),
            template=xr.Dataset(template),
        )

        try:
            crs = da.geobox.crs
            lazy_phenology = assign_crs(lazy_phenology, str(crs))
        except:
            pass

        return lazy_phenology

    if method_sos not in ("median", "first"):
        raise ValueError("method_sos should be either 'median' or 'first'")

    if method_eos not in ("median", "last"):
        raise ValueError("method_eos should be either 'median' or 'last'")

    # If stats supplied is not a list, convert to list.
    stats = stats if isinstance(stats, list) else [stats]

    # try to grab the crs info
    try:
        crs = da.geobox.crs
    except:
        pass

    # remove any remaining all-NaN pixels
    mask = da.isnull().all("time")
    da = da.where(~mask, other=0)

    # calculate the statistics
    if verbose:
        print("      Phenology...")
    vpos = _vpos(da)
    pos = _pos(da)
    trough = _trough(da)
    aos = _aos(vpos, trough)
    vsos = _vsos(da, pos, method_sos=method_sos)
    sos = _sos(vsos)
    veos = _veos(da, pos, method_eos=method_eos)
    eos = _eos(veos)
    los = _los(da, eos, sos)
    rog = _rog(vpos, vsos, pos, sos)
    ros = _ros(veos, vpos, eos, pos)

    # Dictionary containing the statistics
    stats_dict = {
        "SOS": sos.astype(np.int16),
        "EOS": eos.astype(np.int16),
        "vSOS": vsos.astype(np.float32),
        "vPOS": vpos.astype(np.float32),
        "Trough": trough.astype(np.float32),
        "POS": pos.astype(np.int16),
        "vEOS": veos.astype(np.float32),
        "LOS": los.astype(np.int16),
        "AOS": aos.astype(np.float32),
        "ROG": rog.astype(np.float32),
        "ROS": ros.astype(np.float32),
    }

    # intialise dataset with first statistic
    ds = stats_dict[stats[0]].to_dataset(name=stats[0])

    # add the other stats to the dataset
    for stat in stats[1:]:
        if verbose:
            print("         " + stat)
        stats_keep = stats_dict.get(stat)
        ds[stat] = stats_dict[stat]

    try:
        ds = assign_crs(ds, str(crs))
    except:
        pass

    return ds.drop("time")


def temporal_statistics(da, stats):
    """
    Calculate various generic summary statistics on any timeseries.

    This function uses the hdstats temporal library:
    https://github.com/daleroberts/hdstats/blob/master/hdstats/ts.pyx

    Last modified June 2020

    Parameters
    ----------
    da :  xarray.DataArray
        DataArray should contain a 3D time series.
    stats : list
        List of temporal statistics to calculate. Options include:

        * ``'discordance'``: TODO
        * ``'f_std'``: std of discrete fourier transform coefficients, returns
        three layers: f_std_n1, f_std_n2, f_std_n3
        * ``'f_mean'``: mean of discrete fourier transform coefficients, returns
        three layers: f_mean_n1, f_mean_n2, f_mean_n3
        * ``'f_median'``: median of discrete fourier transform coefficients, returns
        three layers: f_median_n1, f_median_n2, f_median_n3
        * ``'mean_change'``: mean of discrete difference along time dimension
        * ``'median_change'``: median of discrete difference along time dimension
        * ``'abs_change'``: mean of absolute discrete difference along time dimension
        * ``'complexity'``: TODO
        * ``'central_diff'``: TODO
        * ``'num_peaks'``: The number of peaks in the timeseries, defined with a local
            window of size 10.  NOTE: This statistic is very slow

    Returns
    -------
    xarray.Dataset
        Dataset containing variables for the selected
        temporal statistics

    """

    # if dask arrays then map the blocks
    if dask.is_dask_collection(da):
        if version.parse(xr.__version__) < version.parse("0.16.0"):
            raise TypeError(
                "Dask arrays are only supported by this function if using, "
                + "xarray v0.16, run da.compute() before passing dataArray."
            )

        # create a template that matches the final datasets dims & vars
        arr = da.isel(time=0).drop("time")

        # deal with the case where fourier is first in the list
        if stats[0] in ("f_std", "f_median", "f_mean"):
            template = xr.zeros_like(arr).to_dataset(name=stats[0] + "_n1")
            template[stats[0] + "_n2"] = xr.zeros_like(arr)
            template[stats[0] + "_n3"] = xr.zeros_like(arr)

            for stat in stats[1:]:
                if stat in ("f_std", "f_median", "f_mean"):
                    template[stat + "_n1"] = xr.zeros_like(arr)
                    template[stat + "_n2"] = xr.zeros_like(arr)
                    template[stat + "_n3"] = xr.zeros_like(arr)
                else:
                    template[stat] = xr.zeros_like(arr)
        else:
            template = xr.zeros_like(arr).to_dataset(name=stats[0])

            for stat in stats:
                if stat in ("f_std", "f_median", "f_mean"):
                    template[stat + "_n1"] = xr.zeros_like(arr)
                    template[stat + "_n2"] = xr.zeros_like(arr)
                    template[stat + "_n3"] = xr.zeros_like(arr)
                else:
                    template[stat] = xr.zeros_like(arr)
        try:
            template = template.drop("spatial_ref")
        except:
            pass

        # ensure the time chunk is set to -1
        da_all_time = da.chunk({"time": -1})

        # apply function across chunks
        lazy_ds = da_all_time.map_blocks(
            temporal_statistics, kwargs={"stats": stats}, template=template
        )

        try:
            crs = da.geobox.crs
            lazy_ds = assign_crs(lazy_ds, str(crs))
        except:
            pass

        return lazy_ds

    # If stats supplied is not a list, convert to list.
    stats = stats if isinstance(stats, list) else [stats]

    # grab all the attributes of the xarray
    x, y, time, attrs = da.x, da.y, da.time, da.attrs

    # deal with any all-NaN pixels by filling with 0's
    mask = da.isnull().all("time")
    da = da.where(~mask, other=0)

    # ensure dim order is correct for functions
    da = da.transpose("y", "x", "time").values

    stats_dict = {
        "discordance": lambda da: hdstats.discordance(da, n=10),
        "f_std": lambda da: hdstats.fourier_std(da, n=3, step=5),
        "f_mean": lambda da: hdstats.fourier_mean(da, n=3, step=5),
        "f_median": lambda da: hdstats.fourier_median(da, n=3, step=5),
        "mean_change": lambda da: hdstats.mean_change(da),
        "median_change": lambda da: hdstats.median_change(da),
        "abs_change": lambda da: hdstats.mean_abs_change(da),
        "complexity": lambda da: hdstats.complexity(da),
        "central_diff": lambda da: hdstats.mean_central_diff(da),
        "num_peaks": lambda da: hdstats.number_peaks(da, 10),
    }

    print("   Statistics:")
    # if one of the fourier functions is first (or only)
    # stat in the list then we need to deal with this
    if stats[0] in ("f_std", "f_median", "f_mean"):
        print("      " + stats[0])
        stat_func = stats_dict.get(str(stats[0]))
        zz = stat_func(da)
        n1 = zz[:, :, 0]
        n2 = zz[:, :, 1]
        n3 = zz[:, :, 2]

        # intialise dataset with first statistic
        ds = xr.DataArray(
            n1, attrs=attrs, coords={"x": x, "y": y}, dims=["y", "x"]
        ).to_dataset(name=stats[0] + "_n1")

        # add other datasets
        for i, j in zip([n2, n3], ["n2", "n3"]):
            ds[stats[0] + "_" + j] = xr.DataArray(
                i, attrs=attrs, coords={"x": x, "y": y}, dims=["y", "x"]
            )
    else:
        # simpler if first function isn't fourier transform
        first_func = stats_dict.get(str(stats[0]))
        print("      " + stats[0])
        ds = first_func(da)

        # convert back to xarray dataset
        ds = xr.DataArray(
            ds, attrs=attrs, coords={"x": x, "y": y}, dims=["y", "x"]
        ).to_dataset(name=stats[0])

    # loop through the other functions
    for stat in stats[1:]:
        print("      " + stat)

        # handle the fourier transform examples
        if stat in ("f_std", "f_median", "f_mean"):
            stat_func = stats_dict.get(str(stat))
            zz = stat_func(da)
            n1 = zz[:, :, 0]
            n2 = zz[:, :, 1]
            n3 = zz[:, :, 2]

            for i, j in zip([n1, n2, n3], ["n1", "n2", "n3"]):
                ds[stat + "_" + j] = xr.DataArray(
                    i, attrs=attrs, coords={"x": x, "y": y}, dims=["y", "x"]
                )

        else:
            # Select a stats function from the dictionary
            # and add to the dataset
            stat_func = stats_dict.get(str(stat))
            ds[stat] = xr.DataArray(
                stat_func(da), attrs=attrs, coords={"x": x, "y": y}, dims=["y", "x"]
            )

    # try to add back the geobox
    try:
        crs = da.geobox.crs
        ds = assign_crs(ds, str(crs))
    except:
        pass

    return ds


def time_buffer(input_date, buffer="30 days", output_format="%Y-%m-%d"):
    """
    Create a buffer of a given duration (e.g. days) around a time query.
    Output is a string in the correct format for a datacube query.

    Parameters
    ----------
    input_date : str, yyyy-mm-dd
        Time to buffer
    buffer : str, optional
        Default is '30 days', can be any string supported by the
        `pandas.Timedelta` function
    output_format : str, optional
        Optional string giving the `strftime` format used to convert
        buffered times to strings; defaults to '%Y-%m-%d'
        (e.g. '2017-12-02')

    Returns
    -------
    early_buffer, late_buffer : str
        A tuple of strings to pass to the datacube query function
        e.g. `('2017-12-02', '2018-01-31')` for input
        `input_date='2018-01-01'` and `buffer='30 days'`
    """
    # Use assertions to check we have the correct function input
    assert isinstance(
        input_date, str
    ), "Input date must be a string in quotes in 'yyyy-mm-dd' format"
    assert isinstance(
        buffer, str
    ), "Buffer must be a string supported by `pandas.Timedelta`, e.g. '5 days'"

    # Convert inputs to pandas format
    buffer = pd.Timedelta(buffer)
    input_date = pd.to_datetime(input_date)

    # Apply buffer
    early_buffer = input_date - buffer
    late_buffer = input_date + buffer

    # Convert back to string using strftime
    early_buffer = early_buffer.strftime(output_format)
    late_buffer = late_buffer.strftime(output_format)

    return early_buffer, late_buffer


def calculate_vector_stat(
    vec: "data dim",
    stat: "data dim -> target dim",
    window_size=365,
    step=10,
    target_dim=365,
    progress=None,
    window="hann",
):
    """Calculates a vector statistic over a rolling window.

    Parameters
    ----------
    vec : d-dimensional np.ndarray
        Vector to calculate over, e.g. a time series.
    stat : R^d -> R^t function
        Statistic function.
    window_size : int
        Sliding window size (default 365).
    step : int
        Step size (default 10).
    target_dim : int
        Dimensionality of the output of `stat` (default 365).
    progress : iterator -> iterator
        Optional progress decorator, e.g. tqdm.notebook.tqdm. Default None.
    window : str
        What kind of window function to use. Default 'hann', but you might
        also want to use 'boxcar'. Any scipy window
        function is allowed (see documentation for scipy.signal.get_window
        for more information).

    Returns
    -------
    (d / step)-dimensional np.ndarray
        y values (the time axis)
    t-dimensional np.ndarray
        x values (the statistic axis)
    (d / step) x t-dimensional np.ndarray
        The vector statistic array.
    """
    # Initialise output array.
    spectrogram_values = np.zeros((vec.shape[0] // step, target_dim))

    # Apply the progress decorator, if specified.
    r = range(0, vec.shape[0] - window_size, step)
    if progress:
        r = progress(r)

    # Convert the window str argument into a window function.
    window = scipy.signal.get_window(window, window_size)

    # Iterate over the sliding window and compute the statistic.
    for base in r:
        win = vec[base : base + window_size] * window
        sad = stat(win)
        spectrogram_values[base // step, :] = sad

    return (
        np.linspace(0, vec.shape[0], vec.shape[0] // step, endpoint=False),
        np.arange(target_dim),
        spectrogram_values,
    )


class LinregressResult:
    def __init__(self, cov, cor, slope, intercept, pval, stderr):
        self.cov = cov
        self.cor = cor
        self.slope = slope
        self.intercept = intercept
        self.pval = pval
        self.stderr = stderr

    def __repr__(self):
        return "LinregressResult({})".format(
            ", ".join(
                "{}={}".format(k, getattr(self, k))
                for k in dir(self)
                if not k.startswith("_")
            )
        )


def lag_linregress_3D(x, y, lagx=0, lagy=0, first_dim="time"):
    """
    Takes two xr.Datarrays of any dimensions (input data could be a 1D time series, or for example, have
    three dimensions e.g. time, lat, lon), and return covariance, correlation, regression slope and intercept,
    p-value, and standard error on regression between the two datasets along their aligned first dimension.

    Datasets can be provided in any order, but note that the regression slope and intercept will be calculated
    for y with respect to x.

    NOTE: This function is deprecated and will be retired in a future
    release. Please use `xr_regression` instead."

    Parameters
    ----------
    x, y : xarray DataArray
        Two xarray DataArrays with any number of dimensions, both sharing the same first dimension
    lagx, lagy : int, optional
        Optional integers giving lag values to assign to either of the data, with lagx shifting x, and lagy
        shifting y with the specified lag amount.
    first_dim : str, optional
        An optional string giving the name of the first dimension on which to align datasets. The default is
        'time'.

    Returns
    -------
    cov, cor, slope, intercept, pval, stderr : xarray DataArray
        Covariance, correlation, regression slope and intercept, p-value, and standard error on
        regression between the two datasets along their aligned first dimension.

    """
    warnings.warn(
        "This function is deprecated and will be retired in a future "
        "release. Please use `xr_regression` instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # 1. Ensure that the data are properly alinged to each other.
    x, y = xr.align(x, y)

    # 2. Add lag information if any, and shift the data accordingly
    if lagx != 0:

        # If x lags y by 1, x must be shifted 1 step backwards. But as the 'zero-th' value is nonexistant, xr
        # assigns it as invalid (nan). Hence it needs to be dropped:
        x = x.shift(**{first_dim: -lagx}).dropna(dim=first_dim)

        # Next re-align the two datasets so that y adjusts to the changed coordinates of x:
        x, y = xr.align(x, y)

    if lagy != 0:

        y = y.shift(**{first_dim: -lagy}).dropna(dim=first_dim)
        x, y = xr.align(x, y)

    # 3. Compute data length, mean and standard deviation along time axis for further use:
    n = y.notnull().sum(dim=first_dim)
    xmean = x.mean(axis=0)
    ymean = y.mean(axis=0)
    xstd = x.std(axis=0)
    ystd = y.std(axis=0)

    # 4. Compute covariance along first axis
    cov = np.sum((x - xmean) * (y - ymean), axis=0) / (n)

    # 5. Compute correlation along time axis
    cor = cov / (xstd * ystd)

    # 6. Compute regression slope and intercept:
    slope = cov / (xstd**2)
    intercept = ymean - xmean * slope

    # 7. Compute P-value and standard error
    # Compute t-statistics
    tstats = cor * np.sqrt(n - 2) / np.sqrt(1 - cor**2)
    stderr = slope / tstats

    from scipy.stats import t

    pval = t.sf(tstats, n - 2) * 2
    pval = xr.DataArray(pval, dims=cor.dims, coords=cor.coords)

    return LinregressResult(cov, cor, slope, intercept, pval, stderr)


def mad_outliers(da, dim="time", threshold=3.5):
    """
    Identify outliers along an xarray dimension using Median Absolute
    Deviation (MAD).

    Parameters
    ----------
    da : xarray.DataArray)
        The input data array with dimensions time, x, y.
    dim : str, optional
        An optional string giving the name of the dimension on which to
        apply the MAD calculation. The default is 'time'.
    threshold : float)
        The number of MADs away from the median to consider an
        observation an outlier.

    Returns
    -------
    xarray.DataArray:
        A boolean array with the same dimensions as input data, where
        True indicates an outlier.
    """
    # Calculate the median along the time dimension
    median = da.median(dim=dim)

    # Calculate the absolute deviations from the median
    abs_deviation = np.abs(da - median)

    # Calculate MAD (median of absolute deviations)
    mad = abs_deviation.median(dim=dim)

    # Deviations greater than (threshold * MAD) are considered outliers
    outliers = abs_deviation > (threshold * mad)

    return outliers


def xr_regression(
    x,
    y,
    dim="time",
    alternative="two-sided",
    outliers_x=None,
    outliers_y=None,
):
    """
    Compare two multi-dimensional ``xr.Datarrays`` and calculate linear
    least-squares regression along a dimension, returning slope,
    intercept, p-value, standard error, covariance, correlation, and
    valid observation counts (n).

    Input arrays can have any number of dimensions, for example: a
    one-dimensional time series (dims: time), or three-dimensional data
    (dims: time, lat, lon). Regressions will be calculated for y with
    respect to x.

    Results should be equivelent to one-dimensional regression performed
    using `scipy.stats.linregress`. Implementation inspired by:
    https://hrishichandanpurkar.blogspot.com/2017/09/vectorized-functions-for-correlation.html

    Parameters
    ----------
    x, y : xarray DataArray
        Two xarray.DataArrays with any number of dimensions. Both arrays
        should have the same length along the `dim` dimension. Regression
        slope and intercept will be calculated for y with respect to x.
    dim : str, optional
        An optional string giving the name of the dimension along which
        to compare datasets. The default is 'time'.
    alternative : string, optional
        Defines the alternative hypothesis. Default is 'two-sided'.
        The following options are available:
        * 'two-sided': slope of the regression line is nonzero
        * 'less': slope of the regression line is less than zero
        * 'greater':  slope of the regression line is greater than zero
    outliers_x, outliers_y : bool or float, optional
        Whether to mask out outliers in each input array prior to
        regression calculation using MAD outlier detection. If True,
        use a default threshold of 3.5 MAD to identify outliers. Custom
        thresholds can be provided as a float.

    Returns
    -------
    regression_ds : xarray.Dataset
        A dataset comparing the two input datasets along their aligned
        dimension, containing variables including covariance, correlation,
        coefficient of determination, regression slope, intercept,
        p-value and standard error, and number of valid observations (n).

    """

    def _pvalue(tstats, n, alternative):
        """
        Function for calculating p-values.
        Can be made lazy by wrapping in `dask.delayed` to
        avoid dask computation occuring too early.
        """
        if alternative == "two-sided":
            pval = t.sf(np.abs(tstats), n - 2) * 2
        elif alternative == "greater":
            pval = t.sf(tstats, n - 2)
        elif alternative == "less":
            pval = t.cdf(np.abs(tstats), n - 2)

        return pval

    # Assert that "dim" is in both datasets
    assert dim in y.dims, f"Array `y` does not contain dimension '{dim}'."
    assert dim in x.dims, f"Array `x` does not contain dimension '{dim}'."

    # Assert that both arrays have the same length along "dim"
    assert len(x[dim]) == len(
        y[dim]
    ), f"Arrays `x` and `y` have different lengths along dimension '{dim}'."

    # Apply optional outlier masking to x and y variable
    if outliers_y is not None:
        mad_thresh_y = 3.5 if outliers_y is True else outliers_y
        y_outliers = mad_outliers(y, dim=dim, threshold=mad_thresh_y)
        y = y.where(~y_outliers)

    if outliers_x is not None:
        mad_thresh_x = 3.5 if outliers_x is True else outliers_x
        x_outliers = mad_outliers(x, dim=dim, threshold=mad_thresh_x)
        x = x.where(~x_outliers)

    # Compute data length, mean and standard deviation along dim
    n = y.notnull().sum(dim=dim)
    xmean = x.mean(dim=dim)
    ymean = y.mean(dim=dim)
    xstd = x.std(dim=dim)
    ystd = y.std(dim=dim)

    # Compute covariance, correlation and coefficient of determination
    cov = ((x - xmean) * (y - ymean)).sum(dim=dim) / (n)
    cor = cov / (xstd * ystd)
    r2 = cor**2

    # Compute regression slope and intercept
    slope = cov / (xstd**2)
    intercept = ymean - xmean * slope

    # Compute t-statistics and standard error
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        tstats = cor * np.sqrt(n - 2) / np.sqrt(1 - cor**2)
    stderr = slope / tstats

    # Calculate p-values for different alternative hypotheses.
    # If data is dask, then delay computation of p-value
    if dask.is_dask_collection(cor):

        _pvalue_lazy = dask.delayed(_pvalue)
        pval = xr.DataArray(
            da.from_delayed(
                _pvalue_lazy(tstats, n, alternative),
                shape=cor.shape,
                dtype=cor.dtype,
            ),
            dims=cor.dims,
            coords=cor.coords,
        ).chunk(cor.chunksizes)

    else:
        pval = xr.DataArray(
            _pvalue(tstats, n, alternative),
            dims=cor.dims,
            coords=cor.coords,
        )

    # Combine into single dataset
    regression_ds = xr.merge(
        [
            cov.rename("cov").astype(np.float32),
            cor.rename("cor").astype(np.float32),
            r2.rename("r2").astype(np.float32),
            slope.rename("slope").astype(np.float32),
            intercept.rename("intercept").astype(np.float32),
            pval.rename("pvalue").astype(np.float32),
            stderr.rename("stderr").astype(np.float32),
            n.rename("n").astype(np.int16),
        ]
    )

    return regression_ds


def calculate_sad(vec):
    """Calculates the surface area duration curve for a given vector of heights.

    Parameters
    ----------
    vec : d-dimensional np.ndarray
        Vector of heights over time.

    Returns
    -------
    d-dimensional np.ndarray
        Surface area duration curve vector over the same time scale.
    """
    return np.sort(vec)[::-1]


def calculate_stsad(vec, window_size=365, step=10, progress=None, window="hann"):
    """Calculates the short-time surface area duration curve for a given vector of heights.

    Parameters
    ----------
    vec : d-dimensional np.ndarray
        Vector of heights over time.
    window_size : int
        Sliding window size (default 365).
    step : int
        Step size (default 10).
    progress : iterator -> iterator
        Optional progress decorator, e.g. tqdm.notebook.tqdm. Default None.
    window : str
        What kind of window function to use. Default 'hann', but you might
        also want to use 'boxcar'. Any scipy window
        function is allowed (see documentation for scipy.signal.get_window
        for more information).

    Returns
    -------
    (d / step)-dimensional np.ndarray
        y values (the time axis)
    t-dimensional np.ndarray
        x values (the statistic axis)
    (d / step) x t-dimensional np.ndarray
        The short-time surface area duration curve array.
    """
    return calculate_vector_stat(
        vec,
        calculate_sad,
        window_size=window_size,
        step=step,
        target_dim=window_size,
        progress=progress,
        window=window,
    )
