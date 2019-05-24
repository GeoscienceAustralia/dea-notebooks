"""
Tests for the custom statistics functions

"""
from __future__ import absolute_import

import string
from datetime import datetime

import hypothesis.strategies as st
import numpy as np
import pytest
import xarray as xr


import datacube_stats.statistics

from datacube.model import Measurement
from datacube.utils.geometry import CRS
from datacube_stats.incremental_stats import mk_incremental_mean, mk_incremental_min, mk_incremental_sum, \
    mk_incremental_max, mk_incremental_counter
from datacube_stats.stat_funcs import nan_percentile, argpercentile, axisindex
from datacube_stats.statistics import NormalisedDifferenceStats, Percentile, WofsStats, TCWStats, \
    StatsConfigurationError, Medoid, GeoMedian
from .extra_stats import NDVIpercentile,
from .regression_stats import NDVIslope

FAKE_MEASUREMENT_INFO = {'dtype': 'int16', 'nodata': -1, 'units': '1'}


def test_nan_percentile():
    # create array of shape(5,100,100) - image of size 100x100 with 5 layers
    test_arr = np.random.randint(0, 10000, 50000).reshape(5, 100, 100).astype(np.float32)
    np.random.shuffle(test_arr)
    # place random NaNs
    random_nans = np.random.randint(0, 50000, 500).astype(np.float32)
    for r in random_nans:
        test_arr[test_arr == r] = np.NaN

    # Test with single q
    q = 45
    input_arr = np.array(test_arr, copy=True)
    std_np_func = np.nanpercentile(input_arr, q=q, axis=0)
    new_func = nan_percentile(input_arr, q=q)

    assert np.allclose(std_np_func, new_func)

    # Test with all qs
    qs = range(0, 100)
    input_arr = np.array(test_arr, copy=True)
    std_np_func = np.nanpercentile(input_arr, q=qs, axis=0)
    new_func = nan_percentile(input_arr, q=qs)

    assert np.allclose(std_np_func, new_func)


def test_argpercentile():
    # Create random Data
    test_arr = np.random.randint(0, 10000, 50000).reshape(5, 100, 100).astype(np.float32)
    np.random.shuffle(test_arr)
    # place random NaNs
    rand_nan = np.random.randint(0, 50000, 500).astype(np.float32)
    for r in rand_nan:
        test_arr[test_arr == r] = np.NaN

    np_result = np.nanpercentile(test_arr, q=25, axis=0, interpolation='nearest')
    argpercentile_result = axisindex(test_arr, argpercentile(test_arr, q=25, axis=0), axis=0)
    assert np.isclose(np_result, argpercentile_result).all()


def test_xarray_reduce():
    arr = np.random.random((100, 100, 5))
    dataarray = xr.DataArray(arr, dims=('x', 'y', 'time'))

    def reduction(in_arr, axis):
        assert axis == 2
        output = np.average(in_arr, axis)
        return output

    dataarray = dataarray.reduce(reduction, dim='time')

    assert dataarray.dims == ('x', 'y')


@pytest.mark.skipif(not hasattr(datacube_stats.statistics, 'NewGeomedianStatistic'),
                    reason='requires `pcm` module for new geomedian statistics')
def test_new_geometric_median():
    from datacube_stats.statistics import NewGeomedianStatistic

    arr = np.random.random((5, 100, 100))
    dataarray = xr.DataArray(arr, dims=('time', 'y', 'x'), coords={'time': list(range(5))})
    dataset = xr.Dataset(data_vars={'band1': dataarray, 'band2': dataarray})

    new_geomedian_stat = NewGeomedianStatistic()
    result = new_geomedian_stat.compute(dataset)

    assert isinstance(result, xr.Dataset)

    assert result.band1.dims == result.band2.dims == ('y', 'x')

    # The two bands had the same inputs, so should have the same result
    assert (result.band1 == result.band2).all()


def test_new_med_ndwi():
    medndwi = NormalisedDifferenceStats('green', 'nir', 'ndwi', stats=['median'])

    arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
    data_array_1 = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})
    arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
    data_array_2 = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})
    dataset = xr.Dataset(data_vars={'green': data_array_1, 'nir': data_array_2}, attrs={'crs': 'Fake CRS'})
    result = medndwi.compute(dataset)
    assert isinstance(result, xr.Dataset)
    assert 'crs' in result.attrs
    assert 'ndwi_median' in result.data_vars


def test_tcw_stats():
    tc_stats = TCWStats()
    bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
    data_vars = {}
    for band in bands:
        arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
        data_vars[band] = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                       coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})

    dataset = xr.Dataset(data_vars=data_vars, attrs={'crs': 'Fake CRS'})
    result = tc_stats.compute(dataset)
    assert isinstance(result, xr.Dataset)
    assert 'crs' in result.attrs
    assert 'pct_exceedance_wetness' in result.data_vars

def test_ndvi_percentiles():
    ndvi_stats = NDVIpercentile(q=50)
    bands = ['red', 'nir']
    data_vars = {}
    for band in bands:
        arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
        data_vars[band] = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                       coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})

    dataset = xr.Dataset(data_vars=data_vars, attrs={'crs': 'Fake CRS'})

    result = ndvi_stats.compute(dataset)
    assert isinstance(result, xr.Dataset)
    # print(result)
    # print(dataset)
    # print(dataset.ndvi.quantile(0.5, dim='time'))
    # print(np.nanpercentile(np.asarray(dataset.ndvi), 50, axis=0))
    assert 'crs' in result.attrs
    assert 'ndvi_PC_50' in result.data_vars

def test_ndvi_slope():
    ndvi_stats = NDVIslope
    bands = ['red', 'nir']
    data_vars = {}
    for band in bands:
        arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
        data_vars[band] = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                       coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})

    dataset = xr.Dataset(data_vars=data_vars, attrs={'crs': 'Fake CRS'})

    result = ndvi_stats.compute(dataset)
    assert isinstance(result, xr.Dataset)
    # print(result)
    # print(dataset)
    # print(dataset.ndvi.quantile(0.5, dim='time'))
    # print(np.nanpercentile(np.asarray(dataset.ndvi), 50, axis=0))
    assert 'crs' in result.attrs
    assert 'ndvi_PC_50' in result.data_vars


def test_masked_count():
    arr = np.random.randint(3, size=(5, 100, 100))
    da = xr.DataArray(arr, dims=('time', 'x', 'y'))

    from datacube_stats.statistics import MaskMultiCounter

    mc = MaskMultiCounter([{'name': 'test', 'mask': lambda x: x}])

    ds = xr.Dataset({'payload': da})
    result = mc.compute(ds)

    assert isinstance(result, xr.Dataset)


def test_new_med_std():
    stdndwi = NormalisedDifferenceStats('green', 'nir', 'ndwi', stats=['std'])
    arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
    data_array_1 = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})
    arr = np.random.uniform(low=-1, high=1, size=(5, 100, 100))
    data_array_2 = xr.DataArray(arr, dims=('time', 'y', 'x'),
                                coords={'time': list(range(5))}, attrs={'crs': 'Fake CRS'})
    dataset = xr.Dataset(data_vars={'green': data_array_1, 'nir': data_array_2}, attrs={'crs': 'Fake CRS'})
    result = stdndwi.compute(dataset)

    assert isinstance(result, xr.Dataset)
    assert 'ndwi_std' in result.data_vars


DatacubeCRSStrategy = st.sampled_from([CRS('EPSG:4326'), CRS('EPSG:3577'), CRS('EPSG:28354')])

