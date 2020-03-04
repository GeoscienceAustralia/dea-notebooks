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
    size = 4096 * 4
    chunksize = 512

    src = Source(size, size)
    dst = Destination(size // zoomfactor, size // zoomfactor)

    Z = np.empty((chunksize, chunksize), dtype=np.float32)

    for i in range(0, size, chunksize):
        for j in range(0, size, chunksize):
            ii, jj = i//2, j//2
            X = src[i : i + chunksize*2, j : j + chunksize*2]
            core(X, Z)
            dst[i//zoomfactor, j//zoomfactor] = Z



class Destination:
    """ Output file """
    def __init__(self, shape):
        rows, cols = shape
        self.file = rasterio.open('test.tif', mode='w',
                                  driver='GTiff', dtype=np.float32, nodata=0,
                                  width=cols, height=rows, count=1,
                                  tiled=True, blockxsize=256, blockysize=256,
                                  compress='lzw', num_threads='all_cpus')
    def __setitem__(self, key, value):
        row, col = key
        rows, cols = value.shape
        self.file.write(value, window=((row, row+rows), (col, col+cols)))

class Source:
    """ Input file """
    def __init__(self, blocksize):
        self.blocksize = blocksize
        #self.file = rasterio.open('test.tif', mode='r', driver='GTiff')
    def __getitem__(self, key):
        #return self.file.read(1, window=rasterio.windows.Window.from_slice(key))
        return np.random.random((self.blocksize, self.blocksize))

class task:
    """
    This represents the processing of one chunk,
    that will be written to one of the output files.
    It first requires several sub-chunks to be calculated.
    Afterwards it
    """