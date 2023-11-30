import dask.array as da
import numpy as np
import pytest
import xarray as xr
from affine import Affine

from datacube.utils.geometry import GeoBox, CRS
from wofs.virtualproduct import WOfSClassifier


def test_nodata_bit_setting(sample_data):
    """

    If no-data bit (bit 1) is set, all other bits should be 0. -- Recommendation from Norman Mueller.
    """

    classifier = WOfSClassifier()

    wofl = classifier.compute(sample_data)
    wofl = wofl.compute()
    wofl = wofl.water.data.reshape(-1)

    values_with_nodata_bit_set = wofl[np.bitwise_and(wofl, 1) == 1]
    assert wofl.dtype == np.dtype('uint8')
    assert (values_with_nodata_bit_set == 1).all()


@pytest.fixture(params=[np, da], ids=["numpy", "dask.array"])
def sample_data(request):
    """Load sample Surface reflectance and QA data"""
    required_bands = ['nbart_blue', 'nbart_green', 'nbart_red', 'nbart_nir', 'nbart_swir_1', 'nbart_swir_2', 'fmask']

    test_data = xr.Dataset(
        {
            name: (['time', 'y', 'x'],
                   request.param.arange(0, 2 ** 16, dtype='uint16').reshape((1, 256, 256)),
                   {'nodata': 0})
            for name in required_bands
        }, attrs={
            'geobox': GeoBox(256, 256, Affine(0.01, 0.0, 139.95,
                                              0.0, -0.01, -49.05), CRS('EPSG:3577')),
            'crs': CRS('EPSG:3577')
        }, coords={
            'time': np.array(['2000-01-01'], dtype='datetime64')
        })
    test_data.fmask.attrs['flags_definition'] = {
        'nodata': {'bits': 0, 'values': {0: False, 1: True}},
        'valid_aerosol': {'bits': 1, 'values': {0: 'not_valid', 1: 'valid'}},
        'water': {'bits': 2, 'values': {0: 'not_water', 1: 'water'}},
        'cloud_or_cirrus': {'bits': 3, 'values': {0: 'not_cloud_or_cirrus',
                                                  1: 'cloud_or_cirrus'}},
        'cloud_shadow': {'bits': 4,
                         'values': {0: 'not_cloud_shadow', 1: 'cloud_shadow'}},
        'interpolated_aerosol': {'bits': 5,
                                 'values': {0: 'not_aerosol_interpolated',
                                            1: 'aerosol_interpolated'}},
        'aerosol_level': {'bits': [6, 7],
                          'values': {0: 'climatology', 1: 'low', 2: 'medium',
                                     3: 'high'}}}
    return test_data
