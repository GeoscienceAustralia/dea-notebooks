# Josh Sixsmith, refactored by BL.
import numpy
import logging
import gc

try:
    import dask.array
    dask_array_type = (dask.array.Array,)
except ImportError:  # pragma: no cover
    dask_array_type = ()

from wofs import boilerplate


@boilerplate.simple_numpify
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

    classified = numpy.ones((rows, cols), dtype='uint8')

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
