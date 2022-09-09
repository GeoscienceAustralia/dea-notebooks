"""
Description: module to allow tide height calculations with the FES2014 model
using the [CNES aviso-fes](https://github.com/CNES/aviso-fes) Python
implementation. It is coded to be used as a drop-in replacement for the default
OTPS-based estimations in coastal.tidal_tag.

This module requires the Aviso FES2014 calibration data to be obtained from
Aviso and extracted in a location and the corresponding (normal or extrapolated)
`.ini` file path to be exported in the `FES2014_OCEAN_INI` environment variable.

While not as flexible in terms of model choice as the `pyTMD` approach proposed
in
[DEAfrica](https://github.com/GeoscienceAustralia/dea-coastlines/blob/deafrica/deafrica_coastlines/raster.py),
the `aviso-fes` proved to be dramatically faster.
""" 

from os import environ
from pathlib import Path
from types import SimpleNamespace

import numpy as np

def initialise_handler():
    """Initialise Aviso FES Handler from INI file.

    The path to the INI file must be set in the `FES2014_OCEAN_INI` environment
    variable.
    """
    from pyfes import Handler
    
    ini_path = Path(environ.get("FES2014_OCEAN_INI", "."))
    if not ini_path.exists() or not ini_path.is_file():
        raise ValueError("FES2014_OCEAN_INI environment variable must be set")
    short_tide = Handler("ocean", "io", str(ini_path))
    print(f"Initialised FES2014 from {ini_path}")
    return short_tide

def predict_tide(timepoints):
    """Compute tide heights using the pyfes handler.

    This method computes the tide heights at a given (latitude, longitude) for a
    set of naive UTC times array. These should be packaged as a list of
    `TimePoint` i.e., tuples of (lon, lat, time).

    It returns a list of SimpleNamespaces, each containing the "pure tide" as
    seen by a tide gauge, expressed in meters at the corresponding time.
    This is the sum of the computed height of the diurnal and semi-diurnal
    constituents of the tidal spectrum and of the long period wave constituents
    of the tidal spectrum.
    """
    from pyfes import Handler
    
    lons, lats, times = tuple(np.array(timepoints).T)
    # aviso-fes requires naive UTC times in microseconds
    times_us = times.astype("datetime64[us]")
    tide, lp, _ = SHORT_TIDE.calculate(lons, lats, times_us)

    # Heights correspond to tide + lp converted from cm to m
    heights = (tide + lp) / 100
    # Package result to be compatible with OTPS, as needed by coastal.py
    return [SimpleNamespace(tide_m=val) for val in heights]


def TimePoint(*args):
    """Dummy method to package data as requied by `coastal`."""
    return args


# Initialise Aviso FES handler
SHORT_TIDE = initialise_handler()
