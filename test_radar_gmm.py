import pytest

from radar_gmm import *
import radar_functions as rf

import datacube

#@pytest.fixture
#def sar_ds():
dc = datacube.Datacube(config='radar.conf')
#load SAR data
#define the time period
qtime = ('2017-02-01', '2017-03-01')

query = {
             'time': qtime,
             'lat': (-12.70,-12.64),
             'long': (132.53,132.64)
             }

#load the raw SAR scenes
sardata = dc.load(product='s1_gamma0_scene_v2', group_by='solar_day', output_crs='EPSG:3577',resolution=(25,25), **query)

#Denoise and mask the radar data with the actual polygon - it will have been returned as a rectangle
sardata=sardata.where(sardata!=0)
clean=rf.denoise(sardata)

#drop scenes with a lot of NaN pixels
nanmask = ((np.isnan(clean).mean(dim = ['x','y'])) > 0.2).vv
valtimes = nanmask.where(~nanmask).dropna(dim='time')['time']

clean = clean.sel(time = valtimes)

#'vh_over_vv' channel
clean['vh_over_vv'] = clean.vh/clean.vv

#Take the natural logarithm of the backscatter to improve differentiation of dark areas
logclean = np.log(clean)
    
sar_ds = logclean

@pytest.fixture
def rkmm():
    return fit_kmeans(sar_ds.isel(time=0),n_components=5)

@pytest.fixture
def rgmm():
    return fit_gmm(sar_ds.isel(time=0),n_components=5)

def test_fit_gmm():
    rgmm = fit_gmm(sar_ds.isel(time=0),n_components=5)
    
    #check to see if the returned value has all the attributes of a fitted gaussian mixture
    
    assert rgmm is not None
    assert rgmm.means_ is not None
    assert rgmm.covariances_ is not None
    assert rgmm.means_.shape == (5,3)

def test_fit_kmeans():
    rkmm = fit_kmeans(sar_ds.isel(time=0),n_components=5)
    
    assert rkmm is not None
    assert rkmm.cluster_centers_ is not None
    assert rkmm.cluster_centers_.shape == (5,3)
    
def test_calc_gmm_classes_kmm(rkmm):
    class_xr = calc_gmm_classes(sar_ds.isel(time=1),rkmm)
    
    assert class_xr.time == sar_ds.isel(time=1).time
    assert class_xr.shape == sar_ds.isel(time=1).vv.shape
    assert class_xr.max() == 4
    assert class_xr.min() == 0
    
def test_calc_gmm_classes_gmm(rgmm):
    class_xr = calc_gmm_classes(sar_ds.isel(time=1),rgmm)
    
    assert class_xr.time == sar_ds.isel(time=1).time
    assert class_xr.shape == sar_ds.isel(time=1).vv.shape
    assert class_xr.max() == 4
    assert class_xr.min() == 0
    
#test that it works with no time dimension
def test_calc_gmm_classes_notime(rkmm):
    single_ds = sar_ds.mean(dim='time')
    class_xr = calc_gmm_classes(single_ds,rkmm)
    
    assert class_xr.shape == sar_ds.mean(dim='time').vv.shape
    assert class_xr.max() == 4
    assert class_xr.min() == 0
    
def test_gmm_dataset_kmm(rkmm):
    class_xr = gmm_dataset(sar_ds,rkmm)
    
    assert (class_xr.time == sar_ds.time).all()
    assert class_xr.shape == sar_ds.vv.shape
    assert class_xr.max() == 4
    assert class_xr.min() == 0
    
def test_gmm_dataset_gmm(rgmm):
    class_xr = gmm_dataset(sar_ds,rgmm)
    
    assert (class_xr.time == sar_ds.time).all()
    assert class_xr.shape == sar_ds.vv.shape
    assert class_xr.max() == 4
    assert class_xr.min() == 0

def test_calc_gmm_timeseries_gmm(rgmm):
    t,ts = calc_gmm_timeseries(sar_ds,rgmm)
    
    assert ts.shape == (len(sar_ds.time),5)
    assert ts.min()>=0
    assert ts.max()<=1
    
    assert (t == sar_ds.time).all()
    
def test_calc_gmm_timeseries_kmm(rkmm):
    t,ts = calc_gmm_timeseries(sar_ds,rkmm)
    
    assert ts.shape == (len(sar_ds.time),5)
    assert ts.min()>=0
    assert ts.max()<=1
    
    assert (t == sar_ds.time).all()
    
    