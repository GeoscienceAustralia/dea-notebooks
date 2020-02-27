"""
Fast Overview Generation
========================

Overviews are image pyramids, needed for responsive display in GIS or image
viewing software.

Generation of overviews by the GDAL tool gdaladdo tends to be slow. For
example, it can be quicker to compute a continental product than to generate
the overview for inspecting it, when the former task is readily parallelisable.

The performance is so much worse than simple file copying, despite that minimal
computation is required, as to suggest potential for a more optimised
algorithm. This needs to perform well on very large rasters, and does not need
to be particularly configurable.

One limitation is that overviews natively use a multipage TIFF format,
and TIFF is a format that does not naturally lend itself to parallelisation
or streaming (since chunks of compressed data have arbitrary sizes, so an index
of offsets is maintained).

"""
import numpy as np


def core(source, destination, zoomfactor=2):
    """
    The basic core algorithm (viz.: arithmetic mean), while minimising
    memory copying and allocation. Input and output are numpy arrays.
    """
    sx, sy = destination.shape
    assert source.shape == (sx*zoomfactor, sy*zoomfactor)

    view = source.reshape(sx, zoomfactor, sy, zoomfactor)
    assert source.ctypes.data == view.ctypes.data

    np.mean(view, axis=(1,3), out=destination)
    return destination

def shallowpass(chunksize=1024, zoomfactor=2):
    """
    Perhaps the simplest algorithm is to only compute one level of overview.

    This would require additional passes, e.g. to add further levels.

    Even for a single-pass multi-level algorithm, a significant expected
    bottleneck is the writing of output at the first (least coarse) level.
    Assuming the output cannot be parallelised, the performance for just this
    level will estimate the performance upper bound for any algorithm.
    """
    pass

def dummywrite(chunksize=1024):
    """
    Simpler than shallowpass. Just write anything at all.

    Verify how fast python can write out data to TIFF.

    This should help ascertain the main performance limitation, and
    whether it is a problem, and whether something must be done about it.
    """
    data = np.random.random((chunksize, chunksize), dtype=np.float32)


    pass

class sourcesink:
    """
    This represents a single raster file,
    such as the input raster or any of the output overview levels.
    """
    def __init__(x, y):
        self.shape = x, y
    def __getitem__(self, key):
        assert isinstance(key, slice)
        raise NotImplementedError
    def __setitem__(self, key, value):
        assert isinstance(key, slice)
        assert len(value.shape) == 2
        raise NotImplementedError

class task:
    """
    This represents the processing of one chunk,
    that will be written to one of the output files.
    It first requires several sub-chunks to be calculated.
    Afterwards it
    """