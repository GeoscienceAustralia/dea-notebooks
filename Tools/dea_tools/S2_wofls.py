"""
A combination of .py files from the wofs GitHub repository which are necessary to run the S2 Waterbodies time series notebook. 
"""
import xarray
import numpy as np
import logging
import gc
import scipy.ndimage

try:
    import dask.array
    dask_array_type = (dask.array.Array,)
except ImportError:  # pragma: no cover
    dask_array_type = ()
    
import math

import ephem
from datacube.utils.geometry import CRS, line
from pandas import to_datetime


"""
FROM wofs.boilerplate:
"""

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


#from wofs import boilerplate

#@boilerplate.simple_numpify
@simple_numpify

def classify(images, float64=False):
    if isinstance(images, dask_array_type):
        # Apply the classify function on each block in the x and y dimensions
        # Remove chunks and reduce along the 'band' dimension (axis 0)
        return dask.array.map_blocks(_classify, images.rechunk({0: -1}), drop_axis=0, dtype='uint8')
    return _classify(images, float64)

# pylint: disable=too-many-locals,too-many-statements
def _classify(images, float64=False):
    """
    Produce a water classification image from the supplied images (6 bands of an NBAR, multiband Landsat image)
    This method evaluates N.Mueller's decision tree as follows:

                    -----------------------------N1---------------------------------
                    |                                                              |
                    |                                                              |
                 ---N2-----                                           -------------N21---------------------
                 |        |                                           |                                   |
                 |        |                                           |                                   |
       ----------N4----   N3                                    ------N22---                           ---N35-------
       |              |                                         |          |                           |           |
       |              |                                         |          |                           |           |
    ---N5---       ---N8--------------                       ---N24----    N23                      ---N37------   N36
    |      |       |                 |                       |        |                             |          |
    |      |       |                 |                       |        |                             |          |
    N6     N7   ---N12------------   N9             ---------N26---   N25                        ---N39-----   N38
                |                |                  |             |                              |         |
                |                |                  |             |                              |         |
             ---N16---        ---N13---             N27   --------N28---                   ------N41---    N40
             |       |        |       |                   |            |                   |          |
             |       |        |       |                   |            |                   |          |
             N17  ---N18---   N14     N15              ---N29---    ---N30---           ---N43---     N42
                  |       |                            |       |    |       |           |       |
                  |       |                            |       |    |       |           |       |
                  N19     N20                          N31     N32  N33     N34         N44     N45

    :param images:
        A 3D numpy array ordered in (bands,rows,columns), containing the spectral data.
        It is assumed that the spectral bands follow Landsat 5 & 7, Band 1, Band 2, Band 3, Band 4, Band 5, Band 7.

    :param float64:
        Boolean keyword. If set to True then the data will be converted to type float64 if not already float64.
        Default is False.

    :return:
        A 2D numpy array of type UInt8.  Values will be 0 for No Water, 1 for Unclassified and 128 for water.

    :notes:
        The input array will be converted to type float32 if not already float32.
        If images is of type float64, then images datatype will be left as is.

    :transcription:
        Transcribed from a Tree diagram output by CART www.salford-systems.com
        Josh Sixsmith; joshua.sixsmith@ga.gov.au

    """

    logger = logging.getLogger("WaterClasserfier")  # !? typo..
    logger.debug("Started")

    def band_ratio(a, b):
        """
        Calculates a normalised ratio index.
        """
        c = (a - b) / (a + b)
        return c

    dims = images.shape
    if len(dims) == 3:
        bands = dims[0]
        rows = dims[1]
        cols = dims[2]
    else:
        rows = dims[0]
        cols = dims[1]

    dtype = images.dtype

    # Check whether to enforce float64 calcs, unless the datatype is already float64
    # Otherwise force float32
    if float64:
        if dtype != 'float64':
            images = images.astype('float64')
    else:
        if dtype == 'float64':
            # Do nothing, leave as float64
            images = images
        elif dtype != 'float32':
            images = images.astype('float32')

    classified = np.ones((rows, cols), dtype='uint8')

    ndi_52 = band_ratio(images[4], images[1])
    ndi_43 = band_ratio(images[3], images[2])
    ndi_72 = band_ratio(images[5], images[1])

    b1 = images[0]
    b2 = images[1]
    b3 = images[2]
    b4 = images[3]
    b5 = images[4]
    b7 = images[5]

    # Lets start going down the trees left branch, finishing nodes as needed
    # Lots of result arrays eg r1, r2 etc of type bool are created
    # These could be recycled to save memory, but at the moment they serve to show the tree structure
    # Temporary arrays of type bool (_tmp, _tmp2) are used to combine the boolean decisions
    r1 = ndi_52 <= -0.01

    r2 = b1 <= 2083.5
    classified[r1 & ~r2] = 0  # Node 3

    r3 = b7 <= 323.5
    _tmp = r1 & r2
    _tmp2 = _tmp & r3
    _tmp &= ~r3

    r4 = ndi_43 <= 0.61
    classified[_tmp2 & r4] = 128  # Node 6
    classified[_tmp2 & ~r4] = 0  # Node 7

    r5 = b1 <= 1400.5
    _tmp2 = _tmp & ~r5
    r6 = ndi_43 <= -0.01
    classified[_tmp2 & r6] = 128  # Node 10
    classified[_tmp2 & ~r6] = 0  # Node 11

    _tmp &= r5

    r7 = ndi_72 <= -0.23
    _tmp2 = _tmp & ~r7
    r8 = b1 <= 379
    classified[_tmp2 & r8] = 128  # Node 14
    classified[_tmp2 & ~r8] = 0  # Node 15

    _tmp &= r7

    r9 = ndi_43 <= 0.22
    classified[_tmp & r9] = 128  # Node 17

    _tmp &= ~r9

    r10 = b1 <= 473
    classified[_tmp & r10] = 128  # Node 19
    classified[_tmp & ~r10] = 0  # Node 20

    # Left branch is completed; cleanup
    logger.debug("B4 cleanup 1")
    del r2, r3, r4, r5, r6, r7, r8, r9, r10
    gc.collect()
    logger.debug("cleanup 1 done")

    # Right branch of the tree
    r1 = ~r1

    r11 = ndi_52 <= 0.23
    _tmp = r1 & r11

    r12 = b1 <= 334.5
    _tmp2 = _tmp & ~r12
    classified[_tmp2] = 0  # Node 23

    _tmp &= r12

    r13 = ndi_43 <= 0.54
    _tmp2 = _tmp & ~r13
    classified[_tmp2] = 0  # Node 25

    _tmp &= r13

    r14 = ndi_52 <= 0.12
    _tmp2 = _tmp & r14
    classified[_tmp2] = 128  # Node 27

    _tmp &= ~r14

    r15 = b3 <= 364.5
    _tmp2 = _tmp & r15

    r16 = b1 <= 129.5
    classified[_tmp2 & r16] = 128  # Node 31
    classified[_tmp2 & ~r16] = 0  # Node 32

    _tmp &= ~r15

    r17 = b1 <= 300.5
    _tmp2 = _tmp & ~r17
    _tmp &= r17
    classified[_tmp] = 128  # Node 33
    classified[_tmp2] = 0  # Node 34

    _tmp = r1 & ~r11

    r18 = ndi_52 <= 0.34
    classified[_tmp & ~r18] = 0  # Node 36
    _tmp &= r18

    r19 = b1 <= 249.5
    classified[_tmp & ~r19] = 0  # Node 38
    _tmp &= r19

    r20 = ndi_43 <= 0.45
    classified[_tmp & ~r20] = 0  # Node 40
    _tmp &= r20

    r21 = b3 <= 364.5
    classified[_tmp & ~r21] = 0  # Node 42
    _tmp &= r21

    r22 = b1 <= 129.5
    classified[_tmp & r22] = 128  # Node 44
    classified[_tmp & ~r22] = 0  # Node 45

    logger.debug("completed")

    return classified

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
FROM wofs.filters:

Set individual bitflags needed for wofls.
"""


#from wofs import terrain, constants, boilerplate
#from wofs.constants import MASKED_CLOUD, MASKED_CLOUD_SHADOW, NO_DATA

PQA_SATURATION_BITS = sum(2 ** n for n in [0, 1, 2, 3, 4, 7])  # exclude thermal
PQA_CONTIGUITY_BITS = 0x01FF
PQA_CLOUD_BITS = 0x0C00
PQA_CLOUD_SHADOW_BITS = 0x3000
PQA_SEA_WATER_BIT = 0x0200

def dilate(array):
    """Dilation e.g. for cloud and cloud/terrain shadow"""
    # kernel = [[1] * 7] * 7 # blocky 3-pixel dilation
    y, x = np.ogrid[-3:4, -3:4]
    kernel = (x * x) + (y * y) <= 3.5 ** 2  # disk-like 3-pixel radial dilation
    return scipy.ndimage.binary_dilation(array, structure=kernel)

def terrain_filter(dsm, nbar, no_data=-1000, ignore_dsm_no_data=False):
    """Terrain shadow masking, slope masking, solar incidence angle masking.

    Args:
        dsm: An XArray Dataset
        nbar: a Dataset that can be used to get a time
        no_data: NoDATA value from the DSM, defaults to -1000
        ignore_dsm_no_data: If True, don't flag nodata areas as shadow
    """

    shadows, slope, sia = shadows_and_slope(
        dsm, nbar.blue.time.values, no_data=no_data
    )

    # Alex Leith 2021: Assuming that the intention is that nodata
    # in the DSM means nodata in the WOfS. I'm making this
    # an option so we can include dsm no_data areas.
    if ignore_dsm_no_data:
        shadowy = dilate(shadows == SHADED)
    else:
        shadowy = dilate(shadows != LIT)

    low_sia = sia < LOW_SOLAR_INCIDENCE_THRESHOLD_DEGREES

    steep = slope > SLOPE_THRESHOLD_DEGREES

    result = (
        np.uint8(MASKED_TERRAIN_SHADOW) * shadowy
        | np.uint8(MASKED_HIGH_SLOPE) * steep
        | np.uint8(MASKED_LOW_SOLAR_ANGLE) * low_sia
    )

    return xarray.DataArray(
        result, coords=[dsm.y, dsm.x]
    )  # note, assumes (y,x) axis ordering

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

"""
From wofs.terrain
"""

UNKNOWN = -1
LIT = 255
SHADED = 0
def _shade_row(shade_mask, elev_m, sun_alt_deg, pixel_scale_m, no_data, fuzz=0.0):
    """
    shade the supplied row of the elevation model
    """

    # threshold is TAN of sun's altitude
    tan_sun_alt = math.tan(sun_alt_deg)

    # pure terrain angle shadow
    shade_mask[0] = LIT
    shade_mask[1:] = np.where((elev_m[:-1] - elev_m[1:]) / pixel_scale_m < tan_sun_alt, LIT, SHADED)

    # project shadows from tips (light->shadow transition)
    switch = np.where(shade_mask[:-1] != shade_mask[1:])
    for i in switch[0]:  # note: could use flatnonzero instead of where; or else switch,=; to avoid [0]. --BL
        if shade_mask[i] == LIT:
            # TODO: horizontal fuzz?
            shadow_level = (elev_m[i] + fuzz) - np.arange(shade_mask.size - i) * (tan_sun_alt * pixel_scale_m)
            shade_mask[i:][shadow_level > elev_m[i:]] = SHADED

    shade_mask[elev_m == no_data] = UNKNOWN

    return shade_mask

def vector_to_crs(point, vector, original_crs, destination_crs):
    """
    Transform a vector (in the tangent space of a particular point) to a new CRS

    Expects point and vector to each be a 2-tuple in the original CRS.
    Returns a pair of 2-tuples (transformed point and vector).
    Order of coordinates is specified by the CRS (or the OGR library).
    """
    # pylint: disable=zip-builtin-not-iterating
    # theoretically should use infinitesimal displacement
    # i.e. jacobian of the transformation
    # but here just use a finite displatement (for convenience of implementation)
    original_line = line([point, tuple(map(sum, zip(point, vector)))], crs=original_crs)
    transformed_line = original_line.to_crs(destination_crs)

    transformed_point, _ = transformed_line.points

    # take difference (i.e. remove origin offset)
    transformed_vector = tuple(map(lambda x: x[1] - x[0], zip(*transformed_line.points)))
    return transformed_point, transformed_vector

def solar_vector(point, time, crs):
    (lon, lat), (dlon, dlat) = vector_to_crs(point, (0, 100),
                                             original_crs=CRS(crs),
                                             destination_crs=CRS('EPSG:4326'))

    # azimuth north to east of the vertical direction of the crs
    vert_az = math.atan2(dlon * math.cos(math.radians(lat)), dlat)

    observer = ephem.Observer()
    # pylint: disable=assigning-non-slot
    observer.lat = math.radians(lat)
    observer.lon = math.radians(lon)
    observer.date = time
    sun = ephem.Sun(observer)

    sun_az = sun.az - vert_az
    x = math.sin(sun_az) * math.cos(sun.alt)
    y = -math.cos(sun_az) * math.cos(sun.alt)
    z = math.sin(sun.alt)

    return x, y, z, sun_az, sun.alt


def shadows_and_slope(tile, time, no_data=-1000):
    """
    Terrain shadow masking (Greg's implementation) and slope masking.

    Input: Digital Surface Model xarray DataSet (need metadata e.g. resolution, CRS)

    Uses Sobel filter to estimate the slope gradients (assuming raster is non-rotated wrt. crs) and magnitude.
    Ignores curvature of earth (picking middle of tile for solar elevation and azimuth) calculating surface incidence.
    Reprojects (rotates/resamples) DSM to align rows with shadows (at 25m resolution,
    and assuming the input projection is Mercator-like i.e. preserves bearings).
    For each row, finds each threshold pixel (where the slope just turns away from the sun) and raytraces
    (i.e. using a ramp, masks the other pixels shaded by the pillar of that pixel).
    Reprojects shadow mask (and undoes border enlargement associated with the rotation).

    TODO (BL) -- profile, and explore numpy.minimum.accumulate (make-monotonic) style alternative
                 and maybe fewer resamplings (or come up with something better still).
    """

    y_size, x_size = tile.elevation.shape

    # row spacing
    pixel_scale_m = abs(tile.affine.e)

    # gradient and slope
    xgrad = scipy.ndimage.sobel(tile.elevation, axis=1) / abs(8 * tile.affine.a)
    ygrad = scipy.ndimage.sobel(tile.elevation, axis=0) / abs(8 * tile.affine.e)

    # length of the terrain normal vector
    norm_len = np.sqrt((xgrad * xgrad) + (ygrad * ygrad) + 1.0)
    slope = np.degrees(np.arccos(1.0 / norm_len))

    x, y = tile.dims.keys()
    tile_center = (tile[x].values[x_size // 2], tile[y].values[y_size // 2])
    solar_vec = solar_vector(tile_center, to_datetime(time), tile.crs)
    sia = (solar_vec[2] - (xgrad * solar_vec[0]) - (ygrad * solar_vec[1])) / norm_len
    sia = 90 - np.degrees(np.arccos(sia))

    rot_degrees = 90.0 + math.degrees(solar_vec[3])

    buff_elv_array = np.pad(tile.elevation.values, 4, mode='edge')
    rotated_elv_array = scipy.ndimage.interpolation.rotate(buff_elv_array,
                                                     rot_degrees,
                                                     reshape=True,
                                                     output=np.float32,
                                                     cval=no_data,
                                                     prefilter=False)

    # create the shadow mask by ray-tracying along each row
    shadows = np.zeros_like(rotated_elv_array)
    for row in range(0, rotated_elv_array.shape[0]):
        _shade_row(shadows[row], rotated_elv_array[row], solar_vec[4], pixel_scale_m, no_data, fuzz=10.0)

    del rotated_elv_array
    del buff_elv_array

    shadows = scipy.ndimage.interpolation.rotate(shadows, -rot_degrees, reshape=False, output=np.float32, cval=no_data,
                                           prefilter=False)

    dr = (shadows.shape[0] - y_size) // 2
    dc = (shadows.shape[1] - x_size) // 2

    shadows = shadows[dr:dr + y_size, dc:dc + x_size]
    shadows = xarray.DataArray(shadows.reshape(tile.elevation.shape), coords=tile.elevation.coords)

    return shadows, slope, sia

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

def _fix_nodata_to_single_value(dataarray):
    # Force any values with the NODATA bit set, to be the nodata value
    nodata_set = np.bitwise_and(dataarray.data, NO_DATA) == NO_DATA

    # If we don't specifically set the dtype in the following line,
    # dask arrays explode to int64s. Make sure it stays a uint8!
    dataarray.data[nodata_set] = np.array(NO_DATA, dtype="uint8")



