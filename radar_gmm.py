#Gaussian Mixture Model tools for radar project, including some generic plotting code

#Richard Taylor 2019

from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import xarray as xr
import itertools
from scipy import linalg
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
ma = np.ma

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

#gmm model fitter
def fit_gmm(sar_ds, n_components=4):
    #prepare the sar data in a format that suits the model
    gm_input = _sklearn_flatten(sar_ds)
    
    #pad the list with zeros to force a cluster at or near (0,0) [i.e. open water]
    #gm_input = np.concatenate((gm_input,[[0,0]]*1500))
    
    #fit the model to the data and return the fitted model
    return GaussianMixture(n_components=n_components).fit(gm_input)


def fit_kmeans(sar_ds, n_components=4):
    km_input = _sklearn_flatten(sar_ds)
    
    #pad the list with zeros to force a cluster at or near (0,0) [i.e. open water]
    
    return KMeans(n_clusters=n_components).fit(km_input)

#plot gmm classes for one step of dataset
def plot_gmm_classes(sar_ds,gmm,**kwargs):
    #predict
    plottable = calc_gmm_classes(sar_ds,gmm)
    
    #plot
    plottable.plot(**kwargs)
    

#return the class predictions on a single scene
def calc_gmm_classes(sar_ds,gmm):
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
    except:
        pass
    
    return plottable


#'private' method to convert the sar data to a format suitable for fitting and
#predicting with sklearn
def _sklearn_flatten(sar_ds):
    stacked_sar = sar_ds.stack(z=['x','y'])
    
    stacked_vv = stacked_sar.vv.to_masked_array()
    stacked_vh = stacked_sar.vh.to_masked_array()

    stacked_both = np.stack((stacked_vv,stacked_vh),axis=-1)
    return stacked_both[np.logical_and(~stacked_vv.mask,~stacked_vh.mask)]

#method to convert the flat output of a scikit-learn predict call to an xarray
#with compatible shape to the original input
def _reshape(output,sar_ds):
    
    stacked_sar = sar_ds.stack(z=['x','y'])
    
    stacked_vv = stacked_sar.vv.to_masked_array()
    stacked_vh = stacked_sar.vh.to_masked_array()
    
    maskclusters = ma.empty(np.shape(stacked_vv))

    maskclusters[np.logical_and(~stacked_vv.mask,~stacked_vh.mask)] = output
    maskclusters.mask = ~np.logical_and(~stacked_vv.mask,~stacked_vh.mask)

    #same coords as the original stacked DataArray
    coords = stacked_sar['z']

    cluster_xr = xr.DataArray(maskclusters, coords={'z':coords},dims=['z'])

    return cluster_xr.unstack().transpose('y','x')


#method to plot timeseries for each gmm class

def plot_gmm_timeseries(timeseries_ds,gmm):

    times,timeseries = calc_gmm_timeseries(timeseries_ds,gmm)
    
    for cat in range(nc):
        plt.plot(times,timeseries[:,cat])
    plt.show()
    return (times,timeseries)

#method to calculate the timeseries (without plotting)
def calc_gmm_timeseries(timeseries_ds,gmm,tmin=None,tmax=None):

    
    if tmax is None:
        times = timeseries_ds['time']
        tmax = len(times)
    if tmin is None:
        tmin = 0

    times = timeseries_ds['time'][tmin:tmax]
    
    try:
        nc=gmm.n_components
    except:
        nc=gmm.n_clusters
        
    timeseries = np.empty([tmax-tmin,nc])
    
    
    for i in range(tmax-tmin):
        sar_ds = timeseries_ds.isel(time=i+tmin)
        gm_input = _sklearn_flatten(sar_ds)
        gm_output = gmm.predict(gm_input)
        timeseries[i] = [(gm_output == cat).sum() for cat in range(nc)]
        timeseries[i] = timeseries[i]/len(gm_output)
        
    return (times,timeseries)
    
#make a new dataset with the GMM/KMM classes instead of SAR reflectance

def gmm_dataset(timeseries_ds,gmm):
    times = timeseries_ds['time']

    try:
        nc=gmm.n_components
    except:
        nc=gmm.n_clusters
    
    for i in range(len(times)):
        sar_ds = timeseries_ds.isel(time=i)
        gm_input = _sklearn_flatten(sar_ds)
        gm_output = gmm.predict(gm_input)
        gm_xr = _reshape(gm_output,sar_ds).expand_dims('time')
        
        gm_xr['time'] = [np.datetime64(times[i]['time'].data)]
        
        cluster_xr = gm_xr if i == 0 else xr.concat([cluster_xr,gm_xr],dim='time')
        
                
    return cluster_xr
    