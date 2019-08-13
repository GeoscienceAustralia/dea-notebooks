#Fang's de-speckling function

import numpy as np

from scipy.ndimage import grey_dilation, grey_erosion
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from skimage.morphology import disk

def lee_filter(da, size):
    """
    Apply lee filter of specified window size.
    Adapted from https://stackoverflow.com/questions/39785970/speckle-lee-filter-in-python

    Option to fill negative pixel with grey_dilation
    """
    img = da.values
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img**2, (size, size))
    img_variance = img_sqr_mean - img_mean**2

    overall_variance = variance(img)

    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    
    return img_output


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

def load_cleaned_SAR(query,dc):
    """put all the nasty loading and filtering code for the SAR scenes in a simple-to-use function.
    
    Arguments:
    query -- a query for dc.load()
    dc -- a datacube.Datacube instance for loading the SAR data from.
    
    Returns:
    An xarray.Dataset with the SAR data matching the query. Includes VH, VV and VH/VV segments.
    
    """
    
    #load the raw SAR scenes
    sardata = dc.load(product='s1_gamma0_scene_v2', group_by='solar_day', output_crs='EPSG:3577',resolution=(25,25), **query)

    #Denoise and mask the radar data with the actual polygon - it will have been returned as a rectangle
    sardata=sardata.where(sardata!=0)
    clean=denoise(sardata)
    #mask = rasterio.features.geometry_mask([geom.to_crs(sardata.geobox.crs)for geoms in [geom]],
    #                                           out_shape=sardata.geobox.shape,
    #                                           transform=sardata.geobox.affine,
    #                                           all_touched=False,
    #                                           invert=False)
    #clean=clean.where(~mask)

    #drop scenes with a lot of NaN pixels
    nanmask = ((np.isnan(clean).mean(dim = ['x','y'])) > 0.2).vv
    valtimes = nanmask.where(~nanmask).dropna(dim='time')['time']

    clean = clean.sel(time = valtimes)
    
    clean['vh_over_vv'] = clean.vh/clean.vv
    
    return clean