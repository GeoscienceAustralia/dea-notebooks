import xarray
from datacube_stats.statistics import Percentile, Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np

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
        ndvi = xarray.Dataset(data_vars={'ndvi': (data.nir - data.red) / (data.nir + data.red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))

        return Percentile(self.qs, per_pixel_metadata=self.per_pixel_metadata).compute(ndvi).assign_attrs(**data.attrs)


    def measurements(self, input_measurements):
        measurement_names = ['ndvi_PC_' + str(q) for q in self.qs]
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]


class TCIpercentile(Percentile):
    """
       TCI percentiles of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `tci_PC_{q}`.

       :param q: list of percentiles to compute
       :param per_pixel_metadata: provenance metadata to attach to each pixel
       """

    def __init__(self, q, category='wetness', coeffs=None,
                 per_pixel_metadata=None,
                 minimum_valid_observations=0):
        if isinstance(q, Sequence):
            self.qs = q
        else:
            self.qs = [q]

        self.category = category

        if coeffs is None:
            self.coeffs = {
                'brightness': {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524, 'nir': 0.5741,
                               'swir1': 0.3124, 'swir2': 0.2303,'nbart_blue': 0.2043,
                               'nbart_green': 0.4158, 'nbart_red': 0.5524, 'nbart_nir_1': 0.5741,
                               'nbart_swir_2': 0.3124, 'nbart_swir_3': 0.2303},
                'greenness': {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934, 'nir': 0.7940,
                              'swir1': -0.0002, 'swir2': -0.1446, 'nbart_blue': -0.1603,
                              'nbart_green': -0.2819, 'nbart_red': -0.4934, 'nbart_nir_1': 0.7940,
                              'nbart_swir_2': -0.0002, 'nbart_swir_3': -0.1446},
                'wetness': {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102, 'nir': 0.1594,
                            'swir1': -0.6806, 'swir2': -0.6109, 'nbart_blue': 0.0315,
                            'nbart_green': 0.2021, 'nbart_red': 0.3102, 'nbart_nir_1': 0.1594,
                            'nbart_swir_2': -0.6806, 'nbart_swir_3': -0.6109}
            }
        else:
            self.coeffs = coeffs

        self.var_name = f'TC{category[0].upper()}'
        self.per_pixel_metadata = per_pixel_metadata
        super(TCIpercentile, self).__init__(q, per_pixel_metadata=per_pixel_metadata,
                                            minimum_valid_observations =minimum_valid_observations)

    def compute(self, data):
        print(data)
        tci_var = []
        for var in data.data_vars:
            nodata = getattr(data[var], 'nodata', -1)
            data[var] = data[var].where(data[var] > nodata)
            tci_var.append(data[var] * self.coeffs[self.category][var])
        tci_var = sum(tci_var)
        #print(tci_var)
        #tci_var = tci_var.fillna(-9999)

        print(tci_var)
        tci = xarray.Dataset(data_vars={self.var_name: tci_var.astype('float32')},
                             coords=data.coords,
                             attrs=dict(crs=data.crs))
        tci[self.var_name].attrs['nodata'] = -9999
        tci[self.var_name].attrs['units'] = 1
        return Percentile(self.qs, per_pixel_metadata=self.per_pixel_metadata).compute(tci).assign_attrs(**data.attrs)

    # def compute(self, data):
    #     coeffs = self.coeffs
    #     bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
    #     category = self.category
    #     tci_var = []
    #     for var in data.data_vars:
    #         nodata = getattr(data[var], 'nodata', -1)
    #         data[var] = data[var].where(data[var] > nodata)
    #         tci_var.append(data[var] * self.coeffs[self.category][var])
    #     tci_var = sum(tci_var)
    #     tci_var = sum([data[band] * coeffs[category][band] for band in bands])
    #
    #     tci = xarray.Dataset(data_vars={self.var_name: tci_var},
    #                           coords=data.coords,
    #                           attrs=dict(crs=data.crs))
    #     tci[self.var_name].attrs['nodata'] = -9999
    #     tci[self.var_name].attrs['units'] = 1

        # return Percentile(self.qs, per_pixel_metadata=self.per_pixel_metadata).compute(tci).assign_attrs(**data.attrs)

    def measurements(self, input_measurements):
        measurement_names = [self.var_name + '_PC_' + str(q) for q in self.qs]
        renamed = [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]
        return PerBandIndexStat(per_pixel_metadata=self.per_pixel_metadata).measurements(renamed)

