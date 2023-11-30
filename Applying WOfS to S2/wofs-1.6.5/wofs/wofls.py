"""
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

from wofs import classifier, filters
from wofs.constants import NO_DATA
from wofs.filters import eo_filter, fmask_filter, terrain_filter, c2_filter


def woffles(nbar, pq, dsm, dsm_no_data=-1000, ignore_dsm_no_data=False):
    """Generate a Water Observation Feature Layer from NBAR, PQ and surface elevation inputs."""

    water = classifier.classify(nbar.to_array(dim='band')) \
        | filters.eo_filter(nbar) \
        | filters.pq_filter(pq.pqa) \
        | filters.terrain_filter(
            dsm,
            nbar,
            no_data=dsm_no_data,
            ignore_dsm_no_data=ignore_dsm_no_data)

    _fix_nodata_to_single_value(water)

    assert water.dtype == np.uint8

    return water


def woffles_ard(ard, dsm, dsm_no_data=-1000, ignore_dsm_no_data=False):
    """Generate a Water Observation Feature Layer from ARD (NBART and FMASK) and surface elevation inputs."""
    nbar_bands = spectral_bands(ard)
    water = classifier.classify(nbar_bands) \
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


def woffles_usgs_c2(c2, dsm, dsm_no_data=-1000, ignore_dsm_no_data=False):
    """Generate a Water Observation Feature Layer from USGS Collection 2 and surface elevation inputs."""
    nbar_bands = spectral_bands(c2)
    water = classifier.classify(nbar_bands) \
        | eo_filter(c2) \
        | c2_filter(c2.fmask)
    if dsm is not None:
        # terrain_filter arbitrarily expects a band named 'blue'
        water |= terrain_filter(
            dsm,
            c2.rename({"nbart_blue": "blue"}),
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


def _fix_nodata_to_single_value(dataarray):
    # Force any values with the NODATA bit set, to be the nodata value
    nodata_set = np.bitwise_and(dataarray.data, NO_DATA) == NO_DATA

    # If we don't specifically set the dtype in the following line,
    # dask arrays explode to int64s. Make sure it stays a uint8!
    dataarray.data[nodata_set] = np.array(NO_DATA, dtype="uint8")
