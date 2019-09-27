#Gaussian Mixture Model tools for radar wetlands project, including some generic plotting code

#Richard Taylor 2019

from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, Birch, AgglomerativeClustering, MiniBatchKMeans
import xarray as xr
import itertools
from scipy import linalg
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
ma = np.ma

import fastmode

color_iter = itertools.cycle(['navy', 'c', 'cornflowerblue', 'gold',
                              'darkorange'])

#plot the means and variances of each gaussian component in the mixture

def plot_results(means, covariances, index, title):
    splot = plt.subplot(2, 1, 1 + index)
    for i, (mean, covar, color) in enumerate(zip(
            means, covariances, color_iter)):
        v, w = linalg.eigh(covar)
        v = 2. * np.sqrt(2.) * np.sqrt(v)
        u = w[0] / linalg.norm(w[0])
        # as the DP will not use every component it has access to
        # unless it needs it, we shouldn't plot the redundant
        # components.
        
        
        # Plot an ellipse to show the Gaussian component
        angle = np.arctan(u[1] / u[0])
        angle = 180. * angle / np.pi  # convert to degrees
        ell = mpl.patches.Ellipse(mean, v[0], v[1], 180. + angle, color=color)
        ell.set_clip_box(splot.bbox)
        ell.set_alpha(0.5)
        splot.add_artist(ell)

    plt.xlim(0, 0.35)
    plt.ylim(0, 0.1)
    plt.title(title)

def fit_gmm(sar_ds, n_components=4):
    """Wrapper around sklearn's GaussianMixture().fit() method to automatically feed
    an xarray Dataset with specific properties instead of an np.array.
    
    """
    #prepare the sar data in a format that suits the model
    gm_input = _sklearn_flatten(sar_ds)
    
    #pad the list with zeros to force a cluster at or near (0,0) [i.e. open water]
    #gm_input = np.concatenate((gm_input,[[0,0]]*1500))
    
    #fit the model to the data and return the fitted model
    return GaussianMixture(n_components=n_components).fit(gm_input)


def fit_kmeans(sar_ds, n_components=4):
    """Wrapper around sklearn's KMeans().fit() method to automatically feed
    an xarray Dataset with specific properties instead of an np.array.
    
    """
    km_input = _sklearn_flatten(sar_ds)
    
    return KMeans(n_clusters=n_components).fit(km_input)

def plot_gmm_classes(sar_ds,gmm,**kwargs):
    """wrapper around calc_gmm_classes() to automatically plot the result as well
    Arguments:
    sar_ds -- as for calc_gmm_classes()
    gmm -- as for calc_gmm_classes()
    **kwargs -- keyword arguments to be fed to the xarray.DataArray.plot() method
    
    """
    
    #predict
    plottable = calc_gmm_classes(sar_ds,gmm)
    
    #plot
    plottable.plot(**kwargs)
    
def calc_gmm_classes(sar_ds,gmm):
    """return the class predictions on a single scene.
    
    Arguments:
    sar_ds -- an xarray.Dataset containing the SAR backscatter data. Should contain only 
    have only one time index (single scene) and spatial dimensions 'x' and 'y'.
    
    gmm -- a fitted sklearn.mixture.GaussianMixture or sklearn.cluster.KMeans object, which
    should accept the same number of channels that sar_ds has (i.e. don't pass a dataset
    with a 'vh_over_vv' variable to a clustering model that wasn't fit with this extra
    variable, or vice versa)
    
    Returns:
    An xarray.DataArray containing class predictions.
    """
    
    
    #prepare for prediction
    gm_input = _sklearn_flatten(sar_ds)
    
    gm_output = gmm.predict(gm_input)
    
    #rebuild the data array structure

    plottable = _reshape(gm_output,sar_ds)
    
    #if the sar dataset has a time coordinate
    try:
        timec = np.datetime64(sar_ds['time'].data)
        plottable = plottable.expand_dims('time')
        plottable['time'] = [timec]
        return plottable.isel(time=0)
    except:
        return plottable



def _sklearn_flatten(sar_ds):
    """private method to convert SAR datasets to a format suitable for fitting and
    predicting with sklearn.
    
    Arguments:
    sar_ds -- an xarray.Dataset with dimensions 'x' and 'y' and data variables 'vv' and 'vh'
    (and optionally 'vh_over_vv')
    
    Returns:
    A two-dimensional np.array. The number of columns depends on the number of masked elements
    in sar_ds, and the number of rows is 2 or 3 depending on whether 'vh_over_vv' is
    provided.
    """
    stacked_sar = sar_ds.stack(z=['x','y'])
    
    stacked_vv = stacked_sar.vv.to_masked_array()
    stacked_vh = stacked_sar.vh.to_masked_array()
    
    try:
        stacked_vh_vv = stacked_sar.vh_over_vv.to_masked_array()
        stacked_all = np.stack((stacked_vv,stacked_vh,stacked_vh_vv),axis=-1)
        stacked_all = stacked_all[np.logical_and(~stacked_vv.mask,~stacked_vh.mask,~stacked_vh_vv.mask)]
        return stacked_all
    except AttributeError:
        stacked_both = np.stack((stacked_vv,stacked_vh),axis=-1)
        return stacked_both[np.logical_and(~stacked_vv.mask,~stacked_vh.mask)]

def _reshape(output,sar_ds):
    """
    Method to convert the flat output array of predictions from a sklearn clustering
    model to an xarray.DataArray with the same shape as the input dataset.

    Arguments:
    output -- flat predictions from an sklearn clustering model.
    sar_ds -- the input (single-scene) SAR dataset which was used to produce the predictions.
    
    Returns:
    An xarray.DataArray with the same shape and dimension names as sar_ds.

    """
    
    stacked_sar = sar_ds.stack(z=['x','y'])
    
    stacked_vv = stacked_sar.vv.to_masked_array()
    stacked_vh = stacked_sar.vh.to_masked_array()
    try:
        stacked_vh_vv = stacked_sar.vh_over_vv.to_masked_array()
        thirdmask = stacked_vh_vv.mask
    except AttributeError:
        thirdmask = np.zeros(np.shape(stacked_vv.mask))
    
    maskclusters = ma.empty(np.shape(stacked_vv))
    
    #if the output is not empty, otherwise the empty masked_array is fine anyway
    if len(output) > 0:
        maskclusters[np.logical_and(~stacked_vv.mask,~stacked_vh.mask,~thirdmask)] = output
        maskclusters.mask = ~np.logical_and(~stacked_vv.mask,~stacked_vh.mask,~thirdmask)

    #same coords as the original stacked DataArray
    coords = stacked_sar['z']

    cluster_xr = xr.DataArray(maskclusters, coords={'z':coords},dims=['z'])

    return cluster_xr.unstack().transpose('y','x')



def plot_gmm_timeseries(timeseries_ds,gmm):
    """Wrapper around calc_gmm_timeseries() to plot class predictions over time.
    Arguments:
    timeseries_ds -- as for calc_gmm_timeseries()
    gmm -- as for calc_gmm_classes()
    """
    

    times,timeseries = calc_gmm_timeseries(timeseries_ds,gmm)
    
    for cat in range(nc):
        plt.plot(times,timeseries[:,cat])
    plt.show()
    return (times,timeseries)

def calc_gmm_timeseries(timeseries_ds,gmm,tmin=0,tmax=None, subcluster_model = None, wetclass = 1, bareclass = 0):
    """Calculate timeseries of predictions for each class given a clustering model and multi-scene SAR dataset.
    Arguments:
    timeseries_ds -- SAR xarray.Dataset with ['x','y'] spatial dimensions and temporal dimension 'time'.
    gmm -- as for calc_gmm_classes()
    
    Keyword arguments:
    tmin, tmax -- minimum and maximum time indices of timeseries_ds to select and predict. By default,
    tmin is set to zero and tmax to the length of the timeseries.
    
    subcluster_model -- default None. If a model is provided then the 'wet' class output from gmm will be fed through
    this model to differentiate bare soil from flooded vegetation.
    wetclass -- default 1. For use with subcluster_model only.
    bareclass -- the class index of the subcluster_model corresponding to bare soil. For use with subcluster_model only    
    
    Returns:
    np.array of size [tmax-tmin,gmm.n_components] (or [tmax-tmin,gmm.n_clusters] if gmm is a KMeans model),
    containing the ratio of pixels in each scene of timeseries_ds that were predicted in each class.
    """
    
    if tmax is None:
        times = timeseries_ds['time']
        tmax = len(times)

    times = timeseries_ds['time'][tmin:tmax]
    
    try:
        nc=gmm.n_components
    except:
        nc=gmm.n_clusters
        
    if subcluster_model:
        nc += 1
        
    timeseries = np.empty([tmax-tmin,nc])
    
    
    
    for i in range(tmax-tmin):
        sar_ds = timeseries_ds.isel(time=i+tmin)
        gm_input = _sklearn_flatten(sar_ds)
        gm_output = gmm.predict(gm_input)
        if subcluster_model:
            subc_input = gm_input[gm_output==wetclass]
            subc_output = subcluster_model.predict(subc_input)
            bare = (subc_output==bareclass).sum()
            
        timeseries[i] = [(gm_output == cat).sum() for cat in range(nc)]
        timeseries[i,wetclass] -= bare
        timeseries[i,nc-1] = bare
        timeseries[i] = timeseries[i]/len(gm_output)
        
    return (times,timeseries)
    
def gmm_dataset(timeseries_ds,gmm):
    """Calculate a timeseries dataset containing pixel maps of class predictions given a 
    SAR timeseries and a pixel classifier.
    Arguments:
    timeseries_ds -- as for calc_gmm_timeseries().
    gmm -- as for calc_gmm_timeseries()
    
    Returns:
    xarray.DataArray containing timeseries of class predictions from gmm. Shape is same as timeseries_ds.
    
    """
    try:
        times = timeseries_ds['time']
    except:
        return calc_gmm_classes(timeseries_ds,gmm)

    try:
        nc=gmm.n_components
    except:
        nc=gmm.n_clusters
    
    try:
        for i in range(len(times)):
            sar_ds = timeseries_ds.isel(time=i)
            gm_input = _sklearn_flatten(sar_ds)
            if len(gm_input)>0:
                gm_output = gmm.predict(gm_input)
            else:
                gm_output = np.array([])
            gm_xr = _reshape(gm_output,sar_ds).expand_dims('time')
                

            gm_xr['time'] = [np.datetime64(times[i]['time'].data)]

            cluster_xr = gm_xr if i == 0 else xr.concat([cluster_xr,gm_xr],dim='time')
            
    except:
        return calc_gmm_classes(timeseries_ds,gmm)

                
    return cluster_xr
    
    

def fit_birch(sar_ds, n_components = 5, **kwargs):
    """Unsupervised clustering using a feature-tree based algorithm.

    Uses the Birch algorithm as implemented by scikit-learn, inspired by the improved success of hierarchical K-Means clustering
    compared to a single K-Means model on the SAR wetlands classifier.
    
    Wraps the Birch functionality in sklearn with the compatibility methods implemented in this module.
    
    Arguments:
    sar_ds -- SAR data to fit in an xarray.Dataset. Assumes three-component.
    
    Keyword arguments:
    n_components -- the number of clusters in the returned model.
    
    Other **kwargs -- passed to the constructor of the sklearn.cluster.Birch() class.
    
    Returns:
    A fitted sklearn.cluster.Birch object.

    """

    tree_input = _sklearn_flatten(sar_ds)
    
    return Birch(n_clusters=n_components, **kwargs).fit(tree_input)


def fit_ward(sar_ds, **kwargs):
    """Ward hierarchical clustering. Uses a bottom-up method, as opposed to the top-down splitting implemented
    in the SAR_Ktree class below."""
    
    ward_input = _sklearn_flatten(sar_ds)
    
    return AgglomerativeClustering(**kwargs).fit(ward_input)

def calc_ward_classes(sar_ds,**kwargs):
    """The ward tree object has no predict method, only fit_predict.
    this works on a single SAR scene only - don't try it with timeseries.
    """
    ward_input = _sklearn_flatten(sar_ds)
    
    ward_output = AgglomerativeClustering(**kwargs).fit_predict(ward_input)
    
    ward_da = _reshape(ward_output,sar_ds)
    
    #if the sar dataset has a time coordinate
    try:
        timec = np.datetime64(sar_ds['time'].data)
        ward_da = ward_da.expand_dims('time')
        ward_da['time'] = [timec]
        return ward_da.isel(time=0)
    except:
        return ward_da

def ward_dataset(timeseries_ds,**kwargs):
    """Calculate a timeseries dataset containing pixel maps of class predictions given a 
    SAR timeseries, using the ward classification per-scene.
    Arguments:
    timeseries_ds -- as for calc_gmm_timeseries().
    
    Keyword arguments:
    **kwargs -- passed to the constructor for the ward tree. E.g. n_clusters for number of clusters to find.
    
    Returns:
    xarray.DataArray containing timeseries of class predictions from gmm. Shape is same as timeseries_ds.
    
    """
    try:
        times = timeseries_ds['time']
    except:
        return calc_ward_classes(timeseries_ds,**kwargs)


    
    try:
        for i in range(len(times)):
            sar_ds = timeseries_ds.isel(time=i)
            
            ward_xr = calc_ward_classes(sar_ds,**kwargs).expand_dims('time')

            cluster_xr = ward_xr if i == 0 else xr.concat([cluster_xr,ward_xr],dim='time')
            
    except:
        return calc_ward_classes(timeseries_ds,**kwargs)

    return cluster_xr
    

#initial cluster centres to hopefully produce results that are consistent between areas
init_clusters = [
            [[ 0.12511279,  0.18816287,  0.08722887],
            [-0.20368323, -0.418645  , -0.45288726],
            [-1.3724948 , -1.1656201 ,  0.31573383]],
            [
            [[[ 0.2269218 ,  0.34693618,  0.19894943],
            [ 0.37637348,  0.24985192, -0.26655155],
            [-0.06508598, -0.00584951,  0.0741508 ]]],
            [[[-0.50456102, -0.87914398, -0.76641863],
            [-0.2563115 , -0.32433283, -0.17432645],
            [ 0.25679989, -0.27658595, -1.04595977]]],
            [[[-1.06004654, -1.16643965, -0.27202684],
            [-1.72452352, -1.23191235,  0.8497928 ],
            [-1.30253372, -1.1064539 ,  0.29728742]]]
            ]
            ]


class SAR_Ktree():
    """
    Class to implement a hierarchical K-means model for land cover classification of
    SAR images of wetlands.
    
    
    """
    
    def __init__(self,levels = 2, branches = 3, minibatch=False, init_clusters = None, **kwargs):
        if minibatch:
            self.model = MiniBatchKMeans(n_clusters = branches, **kwargs)
        else:
            self.model = KMeans(n_clusters = branches, **kwargs)
            
        if init_clusters:
            self.model.init = np.array(init_clusters[0])

        self.levels = levels
        if levels > 1:
            if init_clusters:
                self.branches = [SAR_Ktree(levels = levels-1,branches = branches, minibatch = minibatch, init_clusters = init_clusters[1][i], **kwargs) for i in range(branches)]
            else:
                self.branches = [SAR_Ktree(levels = levels-1,branches = branches, minibatch = minibatch, **kwargs) for i in range(branches)]
        
        self.landcover_dict = None
        
    def fit(self,sar_ds):
        fit_input = _sklearn_flatten(sar_ds)
        self.model = self.model.fit(fit_input)
        
        self_predictions = gmm_dataset(sar_ds,self.model)
        if self.levels > 1:
            for branch in range(len(self.branches)):
                sub_ds = sar_ds.where(self_predictions == branch)
                self.branches[branch].fit(sub_ds)
    
    def balanced_fit(self,sar_ds,optical_cover,num_classes=5,class_weights=np.array([0.7,1.,0.7,1.3,1.3])):
        """A method to perform a 'semi-supervised' fit based on land-cover classes determined by the optical_cover DataArray.
           The algorithm is as follows:
           1. reindex sar_ds so it only contains scenes that approximately match (within two days) the optical_cover scenes.
           2. Split sar_ds into separate pixel arrays corresponding to each optical_cover class
           3. Repeat pixels according to the relative prevalence of their associated cover class in optical_cover, in order to ensure
              balance in the classes
           4. Feed this final pixel array with repetition into the fit_nparray() method to initialise the model clusters
           5. 'Predict' the data that was used to fit the model, then for each cluster take the modal optical_cover class and use this to
              initialise the landcover dictionary.
        """
        print(class_weights)
        #cluster the raw input data
        self.fit(sar_ds)
        
        #reindex SAR to match the optical WIT and discard optical scenes with no matching SAR
        sar_ds = sar_ds.reindex(time=optical_cover.time,method='nearest',tolerance=np.timedelta64(2,'D'))
        optical_cover = optical_cover.where(~(np.isnan(sar_ds.to_array()).any(dim='variable')))
        sar_ds = sar_ds.where(~np.isnan(optical_cover))
        print(optical_cover)
        
        #define amplification factors for each cover class
        weights = 1./np.array([(optical_cover == cla).sum() for cla in range(num_classes)])
        weights = weights/weights.min()
        
        #by default the class-based fudge factors will weight bare soil & vegetation more heavily - this avoids predicting large areas of flooding
        #you may adjust the weighting to suit your problem. Bare soil tends to be underrepresented so adding weight to this may help too
        weights = weights*class_weights
        
        
        #predict the labelled pixels with the fitted clustering model
        pred_input = _sklearn_flatten(sar_ds)
        covervals = optical_cover.to_masked_array()
        covervals = covervals[~covervals.mask]
        test_out = np.stack([self.predict_nparr(pred_input),covervals])
        
        self.landcover_dict = np.zeros(len(self.branches)**self.levels)
        for clu in range(len(self.branches)**self.levels):
            reduced = test_out[1,test_out[0,:]==clu]
            self.landcover_dict[clu] = fastmode.mode_class(reduced,num_classes=num_classes,weights=weights)
            
    def fit_nparr(self,fit_input):
        self.model = self.model.fit(fit_input)
        
        self_predictions = self.model.predict(fit_input)
        if self.levels > 1:
            for branch in range(len(self.branches)):
                sub_arr = fit_input[self_predictions == branch]
                self.branches[branch].fit_nparr(sub_arr)
                
    def predict_nparr(self,arr):
        pred_out = self.model.predict(arr)

        #if not a leaf
        if self.levels > 1:        
            num_values = len(self.branches) ** (self.levels - 1)
            pred_out *= num_values

            for branch in range(len(self.branches)):
                branch_arr = arr[pred_out == num_values*branch]
                branch_out = self.branches[branch].predict_nparr(branch_arr)

                pred_out[pred_out == num_values*branch] = pred_out[pred_out == num_values*branch] + branch_out

        
        #copy the defined landcover classes if available
        if (np.array(self.landcover_dict).any()):
            cover = pred_out.copy(deep=True)
            for i in range(len(self.landcover_dict)):
                cover[pred_out==i] = self.landcover_dict[i]
            pred_out = cover
        
        return pred_out
    
    def predict(self,sar_ds):
        """predict a single scene."""
        pred_input = _sklearn_flatten(sar_ds)
        if len(pred_input) > 0:
            pred_out = _reshape(self.model.predict(pred_input),sar_ds)
        else:
            pred_out = _reshape([],sar_ds)
        
        if self.levels > 1:
            #define number of possible classes in each branch's output
            num_values = len(self.branches) ** (self.levels - 1)
            pred_out *= num_values
            
            for branch in range(len(self.branches)):
                branch_ds = sar_ds.where(pred_out == num_values*branch)
                branch_out = self.branches[branch].predict(branch_ds)
                
                for value in range(num_values):
                    np.place(pred_out.data, branch_out.data == value, branch*num_values + value)
                    
        #if the sar dataset has a time coordinate
        try:
            timec = np.datetime64(sar_ds['time'].data)
            pred_out = pred_out.expand_dims('time')
            pred_out['time'] = [timec]
            ret = pred_out.isel(time=0)
        except:
            ret = pred_out
        
        #copy the defined landcover classes if available
        if (np.array(self.landcover_dict).any()):
            pred = ret.copy(deep=True)
            for i in range(len(self.landcover_dict)):
                np.place(pred.data,ret.data==i,self.landcover_dict[i])
            ret = pred
        return ret
            

    def predict_dataset(self,timeseries_ds):
        """predict a whole time series of observations and return a dataarray with matching
        shape"""
        
        try:
            times = timeseries_ds['time']
        except:
            return self.predict(timeseries_ds)



        try:
            for i in range(len(times)):
                sar_ds = timeseries_ds.isel(time=i)

                tree_xr = self.predict(sar_ds).expand_dims('time')

                cluster_xr = tree_xr if i == 0 else xr.concat([cluster_xr,tree_xr],dim='time')

        except:
            return self.predict(timeseries_ds)

        return cluster_xr
    

def tree_timeseries(timeseries_ds,treemodel,tmin=0,tmax=None):
    """predicc the pixel fractions in each landcover class for a labelled KMeans tree (treemodel) and SAR timeseries dataset (timeseries_ds).
    """
    nc = len(np.unique(treemodel.landcover_dict))
    
    if tmax is None:
        tmax = len(timeseries_ds.time)
    
    times = timeseries_ds['time'][tmin:tmax]
    
    timeseries = np.empty([tmax-tmin,nc])
    
    
    output_ds = treemodel.predict_dataset(timeseries_ds)
    
    for i in range(tmax-tmin):
        gm_output = output_ds.isel(time=i+tmin)
            
        timeseries[i] = [(gm_output == cat).sum() for cat in range(nc)]
        timeseries[i] = timeseries[i]/((~np.isnan(gm_output)).sum().data)
        
    return (times,timeseries)
    
    