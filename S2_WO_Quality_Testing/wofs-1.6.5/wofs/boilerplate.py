import xarray


def simple_numpify(f):
    """Transform a numpy operation to an xarray DataArray operation
    Assumes only (y,x) arrays."""
    def wrapped(xr):
        return xarray.DataArray(f(xr.data), coords=[xr.y, xr.x])
        # return xarray.DataArray(f(xr.data), coords=[x[c] for c in list(x.dims) if c in {'y','x'}])
    wrapped.__name__ = f.__name__
    return wrapped
