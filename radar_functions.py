#Fang's de-speckling function

import numpy as np

from scipy.ndimage import grey_dilation, grey_erosion
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from skimage.morphology import disk

import xarray as xr

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
    nan_mask = (xr.apply_ufunc(np.isnan,ds,dask='parallelized',output_dtypes=[bool])).to_array().any(axis=0)
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

def np_lee_filter(img,size):
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img**2, (size, size))
    img_variance = img_sqr_mean - img_mean**2

    overall_variance = variance(img)

    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    
    return img_output
    

def np_denoise(scene, fill_negative = True, remove_high = False):
    """denoise but for a single scene given as numpy array. Useful for xarray's reduce() method."""
    # save the nodata mask
    zero_mask = scene==0
    nan_mask = np.isnan(scene)
    nodata_mask = np.logical_or(zero_mask,nan_mask)
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

def load_cleaned_SAR(query,dc,drop_bad_scenes=True, incidence_angle=False, **kwargs):
    """put all the nasty loading and filtering code for the SAR scenes in a simple-to-use function.
    
    Arguments:
    query -- a query for dc.load()
    
    dc -- a datacube.Datacube instance for loading the SAR data from.

    Keyword arguments:
    drop_bad_scenes=True -- Boolean, drop scenes in the dataset with a lot of NaNs if this is true. Useful
    if loading a small area on a boundary between passes
    
    incidence_angle=False -- whether to try to load the product with the local incidence angle rather than without.
    
    Returns:
    An xarray.Dataset with the SAR data matching the query. Includes VH, VV and VH/VV segments.
    
    """
    
    #load the raw SAR scenes
    if incidence_angle:
        sardata = dc.load(product='s1_gamma0_scene_v5', group_by='solar_day', output_crs='EPSG:3577',resolution=(25,25), **query,**kwargs)
    else:
        sardata = dc.load(product='s1_gamma0_scene_v2', group_by='solar_day', output_crs='EPSG:3577',resolution=(25,25), **query,**kwargs)

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
    if drop_bad_scenes:
        nanmask = ((np.isnan(clean).mean(dim = ['x','y'])) > 0.2).vv
        valtimes = nanmask.where(~nanmask).dropna(dim='time')['time']

        clean = clean.sel(time = valtimes)
    
    clean['vh_over_vv'] = clean.vh/clean.vv
    
    return clean

def bulknorm_SAR_ds(sar_ds,dask=False, scaling_dict = None):
    """Takes a SAR dataset and normalises each channel based on mu and sigma over
       all observations in the dataset (i.e. this does not operate per-scene).
    """
    nscene = sar_ds.copy(deep=True)

    if scaling_dict:
        vvmid = scaling_dict['mu']['vv']
        vhmid = scaling_dict['mu']['vh']
        vhvvmid = scaling_dict['mu']['vh_over_vv']
        
        vvs = scaling_dict['sigma']['vv']
        vhs = scaling_dict['sigma']['vh']
        vhvvs = scaling_dict['sigma']['vh_over_vv']
    else:
        vvs = 2*nscene['vv'].std()
        vhs = 2*nscene['vh'].std()
        vhvvs = 2*nscene['vh_over_vv'].std()
        if dask: #dask can't handle median finding
            vvmid = nscene['vv'].mean()
            vhmid = nscene['vh'].mean()
            vhvvmid = nscene['vh_over_vv'].mean()
        else:
            vvmid = nscene['vv'].median()
            vhmid = nscene['vh'].median()
            vhvvmid = nscene['vh_over_vv'].median()

    nscene['vv'] = (nscene['vv']-vvmid)/vvs
    nscene['vh'] = (nscene['vh']-vhmid)/vhs
    nscene['vh_over_vv'] = (nscene['vh_over_vv']-vhvvmid)/vhvvs
        
    return nscene

def downsample_ds(normlogSAR, downsample_factor=5):
    """Spatially downsample an xarray DataArray or Dataset.
    """
    downsampled = normlogSAR.groupby_bins('x',len(normlogSAR.x)/downsample_factor).mean(dim='x').groupby_bins('y',len(normlogSAR.y)/downsample_factor).mean(dim='y')
    downsampled = downsampled.rename({'x_bins':'x','y_bins':'y'})
    return downsampled
