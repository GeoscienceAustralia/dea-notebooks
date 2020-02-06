
import numpy as np
from scipy.ndimage import grey_dilation, grey_erosion
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from skimage.morphology import disk
import xarray as xr

import datacube


class sarcube(datacube.Datacube):
    def __init__(self, **kwargs):
        super(sarcube, self).__init__(**kwargs)
        

    def load(self, speckle_filter=None, filter_size=7, db=True, db_offset=0,
             sar_bands = ['vv','vh','hh','hv'],
             fill_negative=False, remove_high=False,
             verbose=False,
             **kwargs):
        """
        load SAR data with customized fuser and optional speckle filter 
        """
        if not speckle_filter in [None, 'lee','temporal']:
            raise ValueError("filter %s is not supported"%speckle_filter)

        data = super(sarcube, self).load(fuse_func=s1_fuser, **kwargs)
        data = data.where(data!=0)

        # valid backscatter bands
        bands = [b for b in list(data.data_vars) if b.lower() in sar_bands]
        if len(bands)==0:
            # empty data
            return data

        if speckle_filter is None:
            return data.pipe(to_db, bands=bands, db=db, db_offset=db_offset, verbose=verbose, inplace=True)
        
        # prep for speckle filter
        # save the nodata mask
        nodata_mask = (np.isnan(data)).to_array().any(axis=0)
        data = data.where(~nodata_mask, 0)

        if speckle_filter == 'lee':
            if verbose: print("Applying a lee filter with window size of %d..."%filter_size)
            data = data.pipe(lee_filter, size=filter_size, bands=bands, inplace=True)
        
        if speckle_filter == 'temporal':
            if verbose: print("Applying a temporal filter with window size of %d..."%filter_size)
            data = data.pipe(temporal_filter, size=filter_size, bands=bands, inplace=True)
                
        if fill_negative:
            if verbose: print("Filling negative values with a dilation...")
            # reduce impact of negative pixels
            for band in bands:
                dilated = data[band].groupby('time').apply(grey_dilation, footprint=disk(3))
                data[band] = data[band].where(data[band] > 0, dilated)

        if remove_high:
            if verobse: print("Removing high outliers with an erosion...")
            # reduce extreme outliers 
            for band in bands:
                eroded = data[band].groupby('time').apply(grey_erosion, size=(3,3))
                smoothed[band] = data[band].where(data[band] < eroded.max(), eroded)
        
        return data.where(~nodata_mask).pipe(to_db, bands=bands, db=db, db_offset=db_offset, verbose=verbose)


def to_db(inputdata, bands=[], db=False, db_offset=0, verbose=False, inplace=False):
    """
    Convert specified variables in a dataset or an dataarray to db.
    """
    if inplace: data = inputdata
    else: data = inputdata.copy()
    if not db:
        return data
    if verbose: print("Converting to db...")
    if isinstance(data, xr.Dataset):
        if len(bands)==0:
            raise ValueError("Please specify variables to convert to db.")
        for b in bands:
            if not b in data: raise ValueError("Variable %s is not in the dataset."%b)
        for band in bands:
            data[band] = 10*np.log10(data[band]) + db_offset
        return data
    elif isinstance(data, xr.DataArray):
        return 10*np.log10(data) + db_offset


def s1_fuser(dest, src):
    """
    Check for both nan and 0 values
    """
    empty_dest = np.isnan(dest) | (dest==0)
    empty_src = np.isnan(src) | (src==0)
    both = ~empty_dest & ~empty_src
    dest[empty_dest] = src[empty_dest]
    dest[both] = src[both]


def lee_filter_2d(da, size):
    """
    Apply lee filter of specified window size.
    Adapted from https://stackoverflow.com/questions/39785970/speckle-lee-filter-in-python
    Input is a 2d data array.
    """
    img = da.values
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img**2, (size, size))
    img_variance = img_sqr_mean - img_mean**2
    overall_variance = variance(img)
    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    return img_output

def lee_filter(inputdata, size, bands=['vv','vh'], inplace=False):
    if inplace: data = inputdata
    else: data = inputdata.copy()
    if isinstance(data, xr.Dataset):
        if len(bands)==0:
            raise ValueError("Please specify variables to apply speckle filter.")
        for b in bands:
            if not b in data: raise ValueError("Variable %s is not in the dataset."%b)
        for band in bands:
            data[band] = data[band].groupby('time').apply(lee_filter_2d, size=size)
        return data
    elif isinstance(data, xr.DataArray):
        if 'time' in data:
            return da.groupby('time').apply(lee_filter_2d, size=size)
        else:
            return da.pipe(lee_filter_2d, size=size)


def temporal_filter_3d(da, size):
    """
    Multi-temporal filtering from S. Quegan 2001
    Input is a 3d data array or a dataset with 3d array as variables
    """
    M = len(da.time)
    img_mean = da.groupby('time').apply(uniform_filter, (size, size))
    return img_mean*(da/img_mean).sum(dim='time')/M
                 
def temporal_filter(inputdata, size, bands=['vv','vh'], inplace=False):
    if inplace: data=inputdata
    else: data=inputdata.copy()
    if isinstance(data, xr.Dataset):
        if len(bands)==0:
            raise ValueError("Please specify variables to apply speckle filter.")
        for b in bands:
            if not b in data: raise ValueError("Variable %s is not in the dataset."%b)
        for band in bands:
            data[band] = data[band].pipe(temporal_filter_3d, size=size)
        return data
    elif isinstance(data, xr.DataArray):
        if 'time' in data:
            return da.pipe(temporal_filter_3d, size=size)
        else:
            raise TypeError("Time dimension is required for temporal filtering.")


def denoise(ds, verbose = False, bands = None, fill_negative = True, remove_high = False):
    """
    Apply lee filter to a S1 dataset loaded from datacube.
    Keep nodata pixels as lee filter implemnation doesn't consider nan
    """
    if not bands: bands = list(ds.data_vars)
    # save the nodata mask
    zero_mask = (ds==0).to_array().any(axis=0)
    nan_mask = (np.isnan(ds)).to_array().any(axis=0)
    nodata_mask = zero_mask | nan_mask
    ds = ds.where(~nodata_mask, 0)
    smoothed = ds[bands[0]].groupby('time').apply(lee_filter, size=7).to_dataset(name=bands[0])
    for band in bands[1:]: smoothed[band] = ds[band].groupby('time').apply(lee_filter, size=7)
        
    if fill_negative:
        # reduce impact of negative pixels
        for band in bands:
            dilated = smoothed[band].groupby('time').apply(grey_dilation, footprint=disk(3))
            smoothed[band] = smoothed[band].where(smoothed[band] > 0, dilated)

    if verbose:
        for band in bands: print("# of negative pixels in %s:"%band, (smoothed[band]<0).sum().values)

    if remove_high:
        # reduce extreme outliers 
        for band in bands:
            eroded = smoothed[band].groupby('time').apply(grey_erosion, size=(3,3))
            smoothed[band] = smoothed[band].where(smoothed[band] < eroded.max(), eroded)

    return smoothed.where(~nodata_mask)

