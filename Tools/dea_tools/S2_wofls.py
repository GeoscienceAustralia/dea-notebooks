"""
A combination of .py files from the wofs GitHub repository which are necessary to run the S2 Waterbodies time series notebook. 
"""

"""
FROM wofs.constants:

WOfS (wofl) product specification
=================================

Each value in a ``wofl`` indicates whether it contains a valid water determination,
and if it is not valid, why it has been excluded.

The clear and valid observations are:

clear dry == 0

clear wet == 128

===  =============  ==========  =======
Bit  Decimal value  Value       Meaning
===  =============  ==========  =======
     0              0           no water present
0    1              1<<0        nodata (missing all earth observation bands)
1    2              1<<1        noncontiguous (at least one EO band is missing or saturated)
2    4              1<<2        low solar incidence angle
3    8              1<<3        terrain shadow
4    16             1<<4        high slope
5    32             1<<5        cloud shadow
6    64             1<<6        cloud
7    128            1<<7        classified as water by the decision tree
===  =============  ==========  =======

The land/sea mask (bit 2) should be ignored. It is based on a vector sea mask
which excludes useful data. We are interested in keeping ocean observations
anyway.
"""

# pylint: disable=bad-whitespace, line-too-long
# For the following bits, 0=unmasked
WATER_PRESENT = 1 << 7  # (dec 128) bit 7: 1=water present, 0=no water if all other bits zero
MASKED_CLOUD = 1 << 6  # (dec 64)  bit 6: 1=pixel masked out due to cloud
MASKED_CLOUD_SHADOW = 1 << 5  # (dec 32)  bit 5: 1=pixel masked out due to cloud shadow
MASKED_HIGH_SLOPE = 1 << 4  # (dec 16)  bit 4: 1=pixel masked out due to high slope
MASKED_TERRAIN_SHADOW = 1 << 3  # (dec 8)   bit 3: 1=pixel masked out due to terrain shadow
MASKED_LOW_SOLAR_ANGLE = 1 << 2  # (dec 4) bit 2: 1=pixel masked out due to low solar incidence angle
MASKED_NO_CONTIGUITY = 1 << 1  # (dec 2)   bit 1: 1=pixel masked out due to lack of data contiguity
NO_DATA = 1 << 0  # (dec 1)   bit 0: 1=pixel masked out due to NO_DATA in NBAR source, 0=valid data in NBAR
WATER_NOT_PRESENT = 0  # (dec 0)          All bits zero indicated valid observation, no water present

# Water detected on slopes equal or greater than this value are masked out
SLOPE_THRESHOLD_DEGREES = 12.0

# If the sun only grazes a hillface, observation unreliable (vegetation shadows etc)
LOW_SOLAR_INCIDENCE_THRESHOLD_DEGREES = 10


"""
FROM wofs.boilerplate:
"""

import xarray


def simple_numpify(f):
    """Transform a numpy operation to an xarray DataArray operation
    Assumes only (y,x) arrays."""
    def wrapped(xr):
        return xarray.DataArray(f(xr.data), coords=[xr.y, xr.x])
        # return xarray.DataArray(f(xr.data), coords=[x[c] for c in list(x.dims) if c in {'y','x'}])
    wrapped.__name__ = f.__name__
    return wrapped

"""
FROM wofs.classifier
"""

# Josh Sixsmith, refactored by BL.
import numpy
import logging
import gc

try:
    import dask.array
    dask_array_type = (dask.array.Array,)
except ImportError:  # pragma: no cover
    dask_array_type = ()

#from wofs import boilerplate

simple_numpify

def classify(images, float64=False):
    if isinstance(images, dask_array_type):
        # Apply the classify function on each block in the x and y dimensions
        # Remove chunks and reduce along the 'band' dimension (axis 0)
        return dask.array.map_blocks(_classify, images.rechunk({0: -1}), drop_axis=0, dtype='uint8')
    return _classify(images, float64)

"""
FROM wofs.wofls:

Produce water observation feature layers (i.e. water extent foliation).

These are the WOfS product with temporal extent (i.e. multiple time values).
Consists of wet/dry estimates and filtering flags,
with one-to-one correspondence to earth observation layers.

Not to be confused with the wofs summary products,
which are derived from a condensed mosaic of the wofl archive.

Issues:
    - previous documentation may be ambiguous or previous implementations may differ
      (e.g. saturation, bitfield)
    - Tile edge artifacts concerning cloud buffers and cloud or terrain shadows.
    - DSM may have different natural resolution to EO source.
      Should think about what CRS to compute in, and what resampling methods to use.
      Also, should quantify whether earth's curvature is significant on tile scale.
    - Yet to profile memory, CPU or IO usage.
"""
import numpy as np

#from wofs import classifier, filters
#from wofs.constants import NO_DATA
#from wofs.filters import eo_filter, fmask_filter, terrain_filter, c2_filter

def woffles_ard(ard, dsm, dsm_no_data=-1000, ignore_dsm_no_data=False):
    """Generate a Water Observation Feature Layer from ARD (NBART and FMASK) and surface elevation inputs."""
    nbar_bands = spectral_bands(ard)
    water = classify(nbar_bands) \
        | eo_filter(ard) \
        | fmask_filter(ard.fmask)

    if dsm is not None:
        # terrain_filter arbitrarily expects a band named 'blue'
        water |= terrain_filter(
            dsm,
            ard.rename({"nbart_blue": "blue"}),
            no_data=dsm_no_data,
            ignore_dsm_no_data=ignore_dsm_no_data
        )

    _fix_nodata_to_single_value(water)

    assert water.dtype == np.uint8

    return water

def spectral_bands(ds):
    bands = [
        "nbart_blue",
        "nbart_green",
        "nbart_red",
        "nbart_nir",
        "nbart_swir_1",
        "nbart_swir_2",
    ]
    return ds[bands].to_array(dim="band")


"""
FROM wofs.filters:

Set individual bitflags needed for wofls.
"""
import numpy as np
import scipy.ndimage
import xarray

#from wofs import terrain, constants, boilerplate
#from wofs.constants import MASKED_CLOUD, MASKED_CLOUD_SHADOW, NO_DATA

PQA_SATURATION_BITS = sum(2 ** n for n in [0, 1, 2, 3, 4, 7])  # exclude thermal
PQA_CONTIGUITY_BITS = 0x01FF
PQA_CLOUD_BITS = 0x0C00
PQA_CLOUD_SHADOW_BITS = 0x3000
PQA_SEA_WATER_BIT = 0x0200

def eo_filter(source):
    """
    Find where there is no data

    Input must be dataset, not array (since bands could have different nodata values).

    Contiguity can easily be tested either here or using PQ.
    """
    nodata_bools = source.map(lambda array: array == array.nodata).to_array(dim="band")

    nothingness = nodata_bools.all(dim="band")
    noncontiguous = nodata_bools.any(dim="band")

    return (
        np.uint8(NO_DATA) * nothingness
        | np.uint8(MASKED_NO_CONTIGUITY) * noncontiguous
    )


def fmask_filter(fmask):
    masking = np.zeros(fmask.shape, dtype=np.uint8)
    masking[fmask == 0] += NO_DATA
    masking[fmask == 2] += MASKED_CLOUD
    masking[fmask == 3] += MASKED_CLOUD_SHADOW

    return masking

