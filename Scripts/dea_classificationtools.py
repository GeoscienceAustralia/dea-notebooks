## dea_classificationtools.py
'''
Description: This file contains a set of python functions for applying 
machine learning classifiying remote sensing data from Digital Earth 
Australia.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data 
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one on 
Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: November 2019

Authors: Richard Taylor, Sean Chua, Dan Clewley

'''

import numpy as np
import xarray as xr
import geopandas as gp
import datacube
from dask.diagnostics import ProgressBar
from rasterio.features import geometry_mask
from rasterio.features import rasterize
from sklearn.cluster import KMeans
from sklearn.base import ClusterMixin
import sys

sys.path.append('../Scripts')
import dea_bandindices


# 'Wrappers' to translate xarrays to np arrays and back for interfacing 
# with sklearn models
def sklearn_flatten(input_xr):
    """
    Reshape a DataArray or Dataset with spatial (and optionally 
    temporal) structure into an np.array with the spatial and temporal 
    dimensions flattened into one dimension.

    This flattening procedure enables DataArrays and Datasets to be used 
    to train and predict
    with sklearn models.

    Last modified: September 2019

    Parameters
    ----------
    input_xr : xarray.DataArray or xarray.Dataset 
        Must have dimensions 'x' and 'y', may have dimension 'time'.
        Dimensions other than 'x', 'y' and 'time' are unaffected by the 
        flattening.

    Returns
    ----------
    input_np : numpy.array 
        A numpy array corresponding to input_xr.data (or 
        input_xr.to_array().data), with dimensions 'x','y' and 'time' 
        flattened into a single dimension, which is the first axis of 
        the returned array. input_np contains no NaNs.

    """
    # cast input Datasets to DataArray
    if isinstance(input_xr, xr.Dataset):
        input_xr = input_xr.to_array()

    # stack across pixel dimensions, handling timeseries if necessary
    if 'time' in input_xr.dims:
        stacked = input_xr.stack(z=['x', 'y', 'time'])
    else:
        stacked = input_xr.stack(z=['x', 'y'])

    # finding 'bands' dimensions in each pixel - these will not be 
    # flattened as their context is important for sklearn
    pxdims = []
    for dim in stacked.dims:
        if dim != 'z':
            pxdims.append(dim)

    # mask NaNs - we mask pixels with NaNs in *any* band, because 
    # sklearn cannot accept NaNs as input
    mask = np.isnan(stacked)
    if len(pxdims) != 0:
        mask = mask.any(dim=pxdims)

    # turn the mask into a numpy array (boolean indexing with xarrays 
    # acts weird)
    mask = mask.data

    # the dimension we are masking along ('z') needs to be the first 
    # dimension in the underlying np array for the boolean indexing to work
    stacked = stacked.transpose('z', *pxdims)
    input_np = stacked.data[~mask]

    return input_np


def sklearn_unflatten(output_np, input_xr):
    """
    Reshape a numpy array with no 'missing' elements (NaNs) and 
    'flattened' spatiotemporal structure into a DataArray matching the 
    spatiotemporal structure of the DataArray

    This enables an sklearn model's prediction to be remapped to the 
    correct pixels in the input DataArray or Dataset.

    Last modified: September 2019

    Parameters
    ----------
    output_np : numpy.array 
        The first dimension's length should correspond to the number of 
        valid (non-NaN) pixels in input_xr.
    input_xr : xarray.DataArray or xarray.Dataset 
        Must have dimensions 'x' and 'y', may have dimension 'time'. 
        Dimensions other than 'x', 'y' and 'time' are unaffected by the 
        flattening.

    Returns
    ----------
    output_xr : xarray.DataArray 
        An xarray.DataArray with the same dimensions 'x', 'y' and 'time'
        as input_xr, and the same valid (non-NaN) pixels. These pixels 
        are set to match the data in output_np.

    """

    # the output of a sklearn model prediction should just be a numpy array
    # with size matching x*y*time for the input DataArray/Dataset.

    # cast input Datasets to DataArray
    if isinstance(input_xr, xr.Dataset):
        input_xr = input_xr.to_array()

    # generate the same mask we used to create the input to the sklearn model
    if 'time' in input_xr.dims:
        stacked = input_xr.stack(z=['x', 'y', 'time'])
    else:
        stacked = input_xr.stack(z=['x', 'y'])

    pxdims = []
    for dim in stacked.dims:
        if dim != 'z':
            pxdims.append(dim)

    mask = np.isnan(stacked)
    if len(pxdims) != 0:
        mask = mask.any(dim=pxdims)

    # handle multivariable output
    output_px_shape = ()
    if len(output_np.shape[1:]):
        output_px_shape = output_np.shape[1:]

    # use the mask to put the data in all the right places
    output_ma = np.ma.empty((len(stacked.z), *output_px_shape))
    output_ma[~mask] = output_np
    output_ma.mask = mask

    # set the stacked coordinate to match the input
    output_xr = xr.DataArray(output_ma, coords={'z': stacked['z']},
                             dims=['z', *['output_dim_' + str(idx) for 
                                          idx in range(len(output_px_shape))]])

    output_xr = output_xr.unstack()

    return output_xr


def fit_xr(model, input_xr):
    """
    Utilise our wrappers to fit a vanilla sklearn model.

    Last modified: September 2019

    Parameters
    ----------
    model : scikit-learn model or compatible object
        Must have a fit() method that takes numpy arrays.
    input_xr : xarray.DataArray or xarray.Dataset. 
        Must have dimensions 'x' and 'y', may have dimension 'time'.

    Returns
    ----------
    model : a scikit-learn model which has been fitted to the data in 
    the pixels of input_xr.

    """

    model = model.fit(sklearn_flatten(input_xr))
    return model


def predict_xr(model, input_xr, progress=True):
    """
    Utilise our wrappers to predict with a vanilla sklearn model.

    Last modified: September 2019

    Parameters
    ----------
    model : a scikit-learn model or compatible object
        Must have a predict() method that takes numpy arrays.
    input_xr : xarray.DataArray or xarray.Dataset
        Must have dimensions 'x' and 'y', may have dimension 'time'.

    Returns
    ----------
    output_xr : xarray.DataArray 
        An xarray.DataArray containing the prediction output from model 
        with input_xr as input. Has the same spatiotemporal structure 
        as input_xr.

    """

    def _get_class_ufunc(*args):
        """
        ufunc to apply classification to chunks of data
        """
        input_data_flattened = []
        for data in args:
            input_data_flattened.append(data.flatten())

        # Flatten array
        input_data_flattened = np.array(input_data_flattened).transpose()

        # Mask out no-data in input (not all classifiers can cope with 
        # Inf or NaN values)
        input_data_flattened = np.where(np.isfinite(input_data_flattened),
                                        input_data_flattened, 0)

        # Actually apply the classification
        out_class = model.predict(input_data_flattened)

        # Mask out NaN or Inf values in results
        out_class = np.where(np.isfinite(out_class), out_class, 0)

        # Reshape when writing out
        return out_class.reshape(args[0].shape)

    def _get_class(*args):
        """
        Apply classification to xarray DataArrays.

        Uses dask to run chunks at a time in parallel

        """
        out = xr.apply_ufunc(_get_class_ufunc, *args,
                             dask='parallelized', output_dtypes=[np.uint8])

        return out

    # Set up a list of input data using variables passed in
    input_data = []

    for var_name in input_xr.data_vars:
        input_data.append(input_xr[var_name])

    # Run through classification. Need to expand and have a separate 
    # dataframe for each variable so chunking in dask works.
    if progress:
        with ProgressBar():
            out_class = _get_class(*input_data).compute()
    else:
        out_class = _get_class(*input_data).compute()

    # Set the stacked coordinate to match the input
    output_xr = xr.DataArray(out_class, coords=input_xr.coords)

    return output_xr


def get_training_data_for_shp(path, 
                              out, 
                              product, 
                              time, 
                              crs='EPSG:3577', 
                              field='classnum',
                              calc_indices=None, 
                              feature_stats=None, 
                              collection='ga_ls_2'):
    """
    Function to extract data for training classifier using a shapefile 
    of labelled polygons. Currently works for single time steps.

    Parameters
    ----------
    path : string
        Path to shapefile containing labelled polygons.
    out : list
        Empty list to contain output data.
    product : string
        String of product name from which to load and extract datacube 
        data e.g. 'ls8_nbart_tmad_annual'
    time : tuple 
        A tuple containing the time period from which to extract 
        training data e.g. ('2015-01-01', '2015-12-31').
    crs : string
        A string containing desired crs e.g. 'EPSG:3577'
    field : string 
        A string containing name of column with labels in shapefile 
        attribute table. Field must contain numeric values.
    calc_indices: list, optional
        An optional list giving the names of any remote sensing indices 
        to be calculated on the loaded data (e.g. `['NDWI', 'NDVI']`. 
        This step will be skipped if any of the indices cannot be 
        computed on the input product.
    feature_stats: string, optional
        An optional string giving the names of statistics to calculate 
        for the polygon. Default is None (all pixel values). Supported 
        values are 'mean' or 'geomedian' (from the `hdstats` module).

    Returns
    --------
    A list of numpy.arrays containing classes and extracted data for 
    each pixel or polygon.

    """
    # Import hdstats as only needed for this function
    if feature_stats == 'geomedian':
        try:
            import hdstats
        except ImportError as err:
            raise
            raise ImportError('Can not import hdstats module needed to calculate'
                              ' geomedian.\n{}'.format(err))
            
    dc = datacube.Datacube(app='training_data')
    query = {'time': time}
    query['crs'] = crs
    shp = gp.read_file(path)
    bounds = shp.total_bounds
    minx = bounds[0]
    maxx = bounds[2]
    miny = bounds[1]
    maxy = bounds[3]
    query['x'] = (minx, maxx)
    query['y'] = (miny, maxy)

    print("Loading data...")

    data = dc.load(product=product, group_by='solar_day', **query)

    # Check if geomedian is in the product and if indices are wanted
    if calc_indices is not None:
        try:
            print("Calculating indices...")
            # Calculate indices - will use for all features
            for index in calc_indices:
                data = dea_bandindices.calculate_indices(data, 
                                                         index, 
                                                         collection=collection)
        except ValueError:
            print("Input dataset not suitable for selected indices, just extracting product data")
            pass 

    # Remove time step if present
    try:
        data = data.isel(time=0)
    # Don't worry if it isn't
    except ValueError:
        pass

    print("Rasterizing features and extracting data...")
    # Initialize counter for status messages.
    i = 0
    # Go through each feature
    for poly_geom, poly_class_id in zip(shp.geometry, shp[field]):
        print(" Feature {:04}/{:04}\r".format(i + 1, len(shp.geometry)), 
              end='')

        # Rasterise the feature
        mask = rasterize([(poly_geom, poly_class_id)],
                         out_shape=(data.y.size, data.x.size),
                         transform=data.affine)

        # Convert mask from numpy to DataArray
        mask = xr.DataArray(mask, coords=(data.y, data.x))
        # Mask out areas that were not within the labelled feature
        data_masked = data.where(mask == poly_class_id, np.nan)

        if feature_stats is None:
            # If no summary stats were requested then
            # extract all pixel values
            flat_train = sklearn_flatten(data_masked)
            # Make a labelled array of identical size
            flat_val = np.repeat(poly_class_id, flat_train.shape[0])
            stacked = np.hstack((np.expand_dims(flat_val, axis=1), flat_train))
        elif feature_stats == 'mean':
            # For the mean of each polygon take the mean over all
            # axis, ignoring masked out values (nan).
            # This gives a single pixel value for each band
            flat_train = data_masked.mean(axis=None, skipna=True)
            flat_train = flat_train.to_array()
            stacked = np.hstack((poly_class_id, flat_train))
        elif feature_stats == 'geomedian':
            # For the geomedian flatten so have a 2D array with
            # bands and pixel values. Then use hdstats
            # to calculate the geomedian
            flat_train = sklearn_flatten(data_masked)
            flat_train_median = hdstats.geomedian(flat_train, axis=0)
            # Geomedian will return a single value for each band so join
            # this with class id to create a single row in output
            stacked = np.hstack((poly_class_id, flat_train_median))

        # Append training data and label to list
        out.append(stacked)

        # Update status counter (feature number)
        i = i + 1

    # Return a list of labels for columns in output array
    return [field] + list(data.data_vars)


class KMeans_tree(ClusterMixin):
    """
    A hierarchical KMeans unsupervised clustering model. This class is 
    a clustering model, so it inherits scikit-learn's ClusterMixin 
    base class.

    Parameters
    ----------
    n_levels : integer, default 2
        number of levels in the tree of clustering models.
    n_clusters : integer, default 3
        Number of clusters in each of the constituent KMeans models in 
        the tree.
    **kwargs : optional
        Other keyword arguments to be passed directly to the KMeans 
        initialiser.

    """

    def __init__(self, n_levels=2, n_clusters=3, **kwargs):

        assert (n_levels >= 1)

        self.base_model = KMeans(n_clusters=3, **kwargs)
        self.n_levels = n_levels
        self.n_clusters = n_clusters
        # make child models
        if n_levels > 1:
            self.branches = [KMeans_tree(n_levels=n_levels - 1, 
                                         n_clusters=n_clusters, 
                                         **kwargs) 
                             for _ in range(n_clusters)]

    def fit(self, X, y=None, sample_weight=None):
        """
        Fit the tree of KMeans models. All parameters mimic those 
        of KMeans.fit().

        Parameters
        ----------
        X : array-like or sparse matrix, shape=(n_samples, n_features)
            Training instances to cluster. It must be noted that the 
            data will be converted to C ordering, which will cause a 
            memory copy if the given data is not C-contiguous.
        y : Ignored
            not used, present here for API consistency by convention.
        sample_weight : array-like, shape (n_samples,), optional
            The weights for each observation in X. If None, all 
            observations are assigned equal weight (default: None)
        """

        self.labels_ = self.base_model.fit(X, 
                                           sample_weight=sample_weight).labels_

        if self.n_levels > 1:
            labels_old = np.copy(self.labels_)
            # make room to add the sub-cluster labels
            self.labels_ *= (self.n_clusters) ** (self.n_levels - 1)

            for clu in range(self.n_clusters):
                # fit child models on their corresponding partition of the training set
                self.branches[clu].fit(X[labels_old == clu], sample_weight=(
                    sample_weight[labels_old == clu] 
                    if sample_weight is not None else None))
                self.labels_[labels_old == clu] += self.branches[clu].labels_

        return self

    def predict(self, X, sample_weight=None):
        """
        Send X through the KMeans tree and predict the resultant 
        cluster. Compatible with KMeans.predict().
        
        Parameters
        ----------
        X : {array-like, sparse matrix}, shape = [n_samples, n_features]
            New data to predict.
        sample_weight : array-like, shape (n_samples,), optional
            The weights for each observation in X. If None, all 
            observations are assigned equal weight (default: None)
            
        Returns
        -------
        labels : array, shape [n_samples,]
            Index of the cluster each sample belongs to.
        """

        result = self.base_model.predict(X, sample_weight=sample_weight)

        if self.n_levels > 1:
            rescpy = np.copy(result)
            
            # make room to add the sub-cluster labels
            result *= (self.n_clusters) ** (self.n_levels - 1)

            for clu in range(self.n_clusters):
                result[rescpy == clu] += self.branches[clu].predict(X[rescpy == clu], sample_weight=(
                    sample_weight[rescpy == clu] if sample_weight is not None else None))

        return result
