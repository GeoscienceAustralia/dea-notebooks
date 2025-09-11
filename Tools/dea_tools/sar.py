# sar.py
"""
Sentinel-1 and SAR processing tools.

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

Last modified: September 2025
"""

import numpy as np
from scipy.ndimage import uniform_filter
import xarray as xr


def lee_filter(img, size):
    """
    Apply a Lee filter to reduce speckle noise in an individual image.

    Adapted from https://stackoverflow.com/questions/39785970/speckle-lee-filter-in-python

    Parameters
    ----------
    img : numpy.ndarray
        Input image to be filtered.
    size : int
        Size of the uniform filter window.

    Returns
    -------
    numpy.ndarray
        The filtered image.
    """
    img_mean = uniform_filter(img, size)
    img_sqr_mean = uniform_filter(img**2, size)
    img_variance = img_sqr_mean - img_mean**2

    overall_variance = np.nanvar(img)

    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    return img_output


def apply_lee_filter(data_array, size=7):
    """
    Apply a Lee filter to each observation in a provided xarray.DataArray.

    Parameters
    ----------
    data_array : xarray.DataArray
        The data array to be filtered.
    size : int, optional
        Size of the uniform filter window.

    Returns
    -------
    xarray.DataArray
        The filtered data array.
    """
    filtered_data = xr.apply_ufunc(
        lee_filter,
        data_array,
        kwargs={"size": size},
        input_core_dims=[["y", "x"]],
        output_core_dims=[["y", "x"]],
        dask_gufunc_kwargs={"allow_rechunk": True},
        vectorize=True,
        dask="parallelized",
        output_dtypes=[data_array.dtype],
    )
    return filtered_data
