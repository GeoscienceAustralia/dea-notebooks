## dea_temporaltools.py
'''
Description: This file contains a set of python functions for conducting
temporal (time-domain) analyses on Digital Earth Australia data.

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
    time_buffer

Last modified: September 2020

'''

# Import required packages
import numpy as np
import pandas as pd
import scipy.signal


def time_buffer(input_date, buffer='30 days', output_format='%Y-%m-%d'):

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
    assert isinstance(input_date, str), "Input date must be a string in quotes in 'yyyy-mm-dd' format"
    assert isinstance(buffer, str), "Buffer must be a string supported by `pandas.Timedelta`, e.g. '5 days'"
    
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