import xarray
from datacube_stats.statistics import Percentile, Statistic
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd
from scipy import stats

class NDVIpercentile(Percentile):
    """
       NDVI percentiles of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `ndvi_PC_{q}`.

       :param q: list of percentiles to compute
       :param per_pixel_metadata: provenance metadata to attach to each pixel
       """

    def __init__(self, q, per_pixel_metadata=None):
        if isinstance(q, Sequence):
            self.qs = q
        else:
            self.qs = [q]

        super(NDVIpercentile, self).__init__(q, per_pixel_metadata=per_pixel_metadata)

    def compute(self, data):
        #`ndvi` for `(nir - red) / (nir + red)`
        # data['ndvi'] = (data.nir - data.red) / (data.nir + data.red)
        # data = data.drop(['nir','red'])
        ndvi = xarray.Dataset(data_vars={'ndvi': (data.nir - data.red) / (data.nir + data.red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))

        return Percentile(self.qs, per_pixel_metadata=self.per_pixel_metadata).compute(ndvi).assign_attrs(**data.attrs)
        # return xarray.Dataset(results, attrs=dict(crs=data.crs))

    def measurements(self, input_measurements):
        measurement_names = ['ndvi_PC_' + str(q) for q in self.qs]
        # print ([Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
        #         for m_name in measurement_names])
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]


class TCIpercentile(Percentile):
    """
       TCI percentiles of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `tcw_PC_{q}`.

       :param q: list of percentiles to compute
       :param per_pixel_metadata: provenance metadata to attach to each pixel
       """

    def __init__(self, q, category='wetness', coeffs=None, per_pixel_metadata=None):
        if isinstance(q, Sequence):
            self.qs = q
        else:
            self.qs = [q]

        self.category = category

        if coeffs is None:
            self.coeffs = {
                'brightness': {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524, 'nir': 0.5741,
                               'swir1': 0.3124, 'swir2': 0.2303},
                'greenness': {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934, 'nir': 0.7940,
                              'swir1': -0.0002, 'swir2': -0.1446},
                'wetness': {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102, 'nir': 0.1594,
                            'swir1': -0.6806, 'swir2': -0.6109}
            }
        else:
            self.coeffs = coeffs
        super(TCIpercentile, self).__init__(q, per_pixel_metadata=per_pixel_metadata)

    def compute(self, data):
        coeffs = self.coeffs
        bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        category = self.category
        #
        # results = {}
        # for cat in categories:
        #     data[cat] = sum([data[band] * coeffs[cat][band] for band in bands])
        #     results['pct_exceedance_' + cat] = \
        #         data[cat].where(data[cat] > thresholds[cat]).count(dim='time') / data[cat].count(dim='time')
        #
        #     results['mean_' + cat] = data[cat].mean(dim='time')
        #     results['std_' + cat] = data[cat].std(dim='time', keep_attrs=True, skipna=True)
        #     data = data.drop(cat)

        tci = sum([data[band] * coeffs[category][band] for band in bands])
        tci = xarray.Dataset(data_vars={'tcw': tcw},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))

        return Percentile(self.qs, per_pixel_metadata=self.per_pixel_metadata).compute(tci).assign_attrs(**data.attrs)
        # return xarray.Dataset(results, attrs=dict(crs=data.crs))

    def measurements(self, input_measurements):
        measurement_names = ['tci_' + self.category + '_PC_' + str(q) for q in self.qs]
        # print ([Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
        #         for m_name in measurement_names])
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]

class newTCWStats(Statistic):
    """
    Simple Tasseled Cap Wetness, Brightness and Greeness summary statistics.

    Based on the Crist 1985 RF coefficients
    You can provide your own coefficients, however at this stage it will run the same coefficients for all sensors.

    Default Tasseled Cap coefficient Values:
    brightness_coeff = {'blue':0.2043, 'green':0.4158, 'red':0.5524, 'nir':0.5741, 'swir1':0.3124, 'swir2':0.2303}
    greenness_coeff = {'blue':-0.1603, 'green':-0.2819, 'red':-0.4934, 'nir':0.7940, 'swir1':-0.0002, 'swir2':-0.1446}
    wetness_coeff = {'blue':0.0315, 'green':0.2021, 'red':0.3102, 'nir':0.1594, 'swir1':-0.6806, 'swir2':-0.6109}

    Default Thresholds used for calculating the percentage exceedance statistics for Brightness, Greenness and Wetness:
        brightness': 4000
        greenness': 600
        wetness': -600

    Outputs
    If you output as geotiff these will be your bands:
    Band1: pct_exceedance_brightness
    Band2: pct_exceedance_greenness
    Band3: pct_exceedance_wetness
    Band4: median_brightness
    Band5: median_greenness
    Band6: median_wetness
    Band7: std_brightness
    Band8: std_greenness
    Band9: std_wetness

    """

    def __init__(self, thresholds=None, coeffs=None):
        if thresholds is None:
            self.thresholds = {
                'brightness': 4000,
                'greenness': 700,
                'wetness': -600
            }
        else:
            self.thresholds = thresholds

        if coeffs is None:
            self.coeffs = {
                'brightness': {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524, 'nir': 0.5741,
                               'swir1': 0.3124, 'swir2': 0.2303},
                'greenness': {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934, 'nir': 0.7940,
                              'swir1': -0.0002, 'swir2': -0.1446},
                'wetness': {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102, 'nir': 0.1594,
                            'swir1': -0.6806, 'swir2': -0.6109}
            }
        else:
            self.coeffs = coeffs

    def compute(self, data):
        coeffs = self.coeffs
        thresholds = self.thresholds
        bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        categories = ['brightness', 'greenness', 'wetness']

        results = {}
        for cat in categories:
            data[cat] = sum([data[band] * coeffs[cat][band] for band in bands])
            results['pct_exceedance_' + cat] = \
                data[cat].where(data[cat] > thresholds[cat]).count(dim='time')/data[cat].count(dim='time')

            results['median_' + cat] = data[cat].median(dim='time', skipna=True)
            results['std_' + cat] = data[cat].std(dim='time', keep_attrs=True, skipna=True)
            data = data.drop(cat)

        data = data.drop(bands)

        return xarray.Dataset(results, attrs=dict(crs=data.crs))

    def measurements(self, input_measurements):
        measurement_names = [
            'pct_exceedance_brightness',
            'pct_exceedance_greenness',
            'pct_exceedance_wetness',
            'mean_brightness',
            'mean_greenness',
            'mean_wetness',
            'std_brightness',
            'std_greenness',
            'std_wetness']
        return [Measurement(name=m_name, dtype='float32', nodata=-1, units='1')
                for m_name in measurement_names]

