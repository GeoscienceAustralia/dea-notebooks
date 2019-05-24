
from datacube_stats.statistics import Statistic
from datacube.model import Measurement
import numpy as np
from scipy import stats, signal
import xarray as xr

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, signal
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, signal


def lag_linregress_3D(x, y, lagx=0, lagy=0):
    """
    Input: Two xr.Datarrays of any dimensions with the first dim being time.
    Thus the input data could be a 1D time series, or for example, have three dimensions (time,lat,lon).
    Datasets can be provied in any order, but note that the regression slope and intercept will be calculated
    for y with respect to x.
    Output: Covariance, correlation, regression slope and intercept, p-value, and standard error on regression
    between the two datasets along their aligned time dimension.
    Lag values can be assigned to either of the data, with lagx shifting x, and lagy shifting y, with the specified lag amount.
    """
    # 1. Ensure that the data are properly alinged to each other. and check time field
    x, y = xr.align(x, y)
    if 'month' in y.dims:
        groupby = 'month'
    elif 'dayofyear' in y.dims:
        groupby = 'dayofyear'
    elif 'year' in y.dims:
        groupby = 'year'

    # 2. Add lag information if any, and shift the data accordingly
    if lagx != 0:
        # If x lags y by 1, x must be shifted 1 step backwards.
        # But as the 'zero-th' value is nonexistant, xr assigns it as invalid (nan). Hence it needs to be dropped
        x = x.shift(time=-lagx).dropna(dim='time')
        # Next important step is to re-align the two datasets so that y adjusts to the changed coordinates of x
        x, y = xr.align(x, y)

    if lagy != 0:
        y = y.shift(time=-lagy).dropna(dim='time')
        x, y = xr.align(x, y)

    # 3. Compute data length, mean and standard deviation along time axis for further use:
    # n     = x.shape[0]

    n = y.notnull().sum(dim=groupby)  # this allows the code to cope with nans

    xmean = x.mean(axis=0)
    ymean = y.mean(axis=0)
    xstd = x.std(axis=0)
    ystd = y.std(axis=0)

    # 4. Compute covariance along time axis
    cov = np.sum((x - xmean) * (y - ymean), axis=0) / (n)

    # 5. Compute correlation along time axis
    cor = cov / (xstd * ystd)

    # 6. Compute regression slope and intercept:
    slope = cov / (xstd ** 2)
    intercept = ymean - xmean * slope

    # 7. Compute P-value and standard error
    # Compute t-statistics
    tstats = cor * np.sqrt(n - 2) / np.sqrt(1 - cor ** 2)
    stderr = slope / tstats

    from scipy.stats import t
    pval = t.sf(tstats, n - 2) * 2
    pval = xr.DataArray(pval, dims=cor.dims, coords=cor.coords)

    return cov, cor, slope, intercept, pval, stderr

def linregress_3D(x, y):
    """
    Input: Two xr.Datarrays of any dimensions with the first dim being time.
    Thus the input data could be a 1D time series, or for example, have three dimensions (time,lat,lon).
    Datasets can be provied in any order, but note that the regression slope and intercept will be calculated
    for y with respect to x.
    Output: Covariance, correlation, regression slope and intercept, p-value, and standard error on regression
    between the two datasets along their aligned time dimension.
    Lag values can be assigned to either of the data, with lagx shifting x, and lagy shifting y, with the specified lag amount.
    """
    # 1. Ensure that the data are properly alinged to each other. and check time field
    x, y = xr.align(x, y)

    # 2. check time field
    if 'month' in y.dims:
        groupby = 'month'
    elif 'dayofyear' in y.dims:
        groupby = 'dayofyear'
    elif 'year' in y.dims:
        groupby = 'year'

    # 3. Compute data length, mean and standard deviation along time axis for further use:
    # n     = x.shape[0]

    n = y.notnull().sum(dim=groupby)  # this allows the code to cope with nans

    xmean = x.mean(axis=0)
    ymean = y.mean(axis=0)
    xstd = x.std(axis=0)
    ystd = y.std(axis=0)

    # 4. Compute covariance along time axis
    cov = np.sum((x - xmean) * (y - ymean), axis=0) / (n)

    # 5. Compute correlation along time axis
    cor = cov / (xstd * ystd)

    # 6. Compute regression slope and intercept:
    slope = cov / (xstd ** 2)
    intercept = ymean - xmean * slope

    # 7. Compute P-value and standard error
    # Compute t-statistics
    tstats = cor * np.sqrt(n - 2) / np.sqrt(1 - cor ** 2)
    stderr = slope / tstats

    from scipy.stats import t
    pval = t.sf(tstats, n - 2) * 2
    pval = xr.DataArray(pval, dims=cor.dims, coords=cor.coords)

    return xr.DataArray([slope, intercept, cor**2, pval, stderr])

class NDVIslope(Statistic):
    """
       NDVI percentiles of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `ndvi_PC_{q}`.

       :param months: list of monthsto include for the regression calc
       :param groupby: the time range by which to group the data
       """

    def __init__(self, months=None, groupby='month'):
        # if months is None:
        #     #self.months = list(range(1, 13, 1))
        #     self.months = None
        # else:
        self.months = months
        self.groupby = groupby

    def compute(self, data):
        data = data.sortby('time')
        # pernan is a filtration level - scenes with more nans than this per scene are removed
        pernan = 0.80
        data = data.dropna('time', thresh=int(
            pernan * len(data.x) * len(data.y)))
        def dry_vals(sensor_data, months):
            '''calculates dry season or wet season values'''
            if sensor_data is not None:
                dry_data = sensor_data.sel(time=np.in1d(sensor_data.time.dt.month, months))
                return dry_data
            else:
                return None

        if self.months is not None:
            data = dry_vals(data, self.months)

        ndvi = xr.Dataset(data_vars={'ndvi': (data.nir - data.red) / (data.nir + data.red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))
        data=None

        if self.groupby =='month':
            averaged_data = ndvi.groupby('time.month').mean(dim='time')
        else:
            averaged_data = ndvi.groupby('time.dayofyear').mean(dim='time')

        # define a function to compute a linear trend of a timeseries
        def linear_trend_day(x):
            pf = stats.linregress(x.dayofyear, x)
            return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])

        def linear_trend_month(x):
            pf = stats.linregress(x.month, x)
            return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])

        # def linear_trend_day(x):
        #     mask = ~np.isnan(x)
        #     if len(x[mask]) > 1:
        #         pf = stats.linregress(x.dayofyear[mask], x[mask])
        #         return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])
        #     else:
        #         pf = [np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]
        #         # we need to return a dataarray or else xarray's groupby won't be happy
        #         return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])
        #
        # def linear_trend_month(x):
        #     mask = ~np.isnan(x)
        #     if len(x[mask]) > 1:
        #         pf = stats.linregress(x.month[mask], x[mask])
        #         return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])
        #     else:
        #         pf = [np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]
        #         # we need to return a dataarray or else xarray's groupby won't be happy
        #         return xr.DataArray([pf[0], pf[1], pf[2] ** 2, pf[3], pf[4]])

        # stack lat and lon into a single dimension called allpoints
        averaged_data_pos = averaged_data.where(averaged_data >= 0)
        da_dropped = averaged_data_pos.drop(['x', 'y'])
        # stack lat and lon into a single dimension called allpoints
        stacked = da_dropped.stack(allpoints=['x', 'y'])
        # apply the function over allpoints to calculate the trend at each point
        if self.groupby == 'month':
            trend = stacked.ndvi.groupby('allpoints').apply(linear_trend_month)
        else:
            trend = stacked.ndvi.groupby('allpoints').apply(linear_trend_day)

        # unstack back to lat lon coordinates
        trend_unstacked = trend.unstack('allpoints').T
        trend_dataset = trend_unstacked.to_dataset(dim="dim_0").rename({0: 'slope', 1: 'intercept',
                                                                        2: 'r_squared', 3: 'p_value',
                                                                        4: 'std_err'})
        trend_dataset.coords['y'] = averaged_data_pos.coords['y']
        trend_dataset.coords['x'] = averaged_data_pos.coords['x']
        return trend_dataset

    def measurements(self, input_measurements):
        measurement_names = ['slope', 'intercept', 'r_squared','p_value','std_err']
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]



class NDVIregression(Statistic):
    """
       NDVI regression of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `ndvi_PC_{q}`.

       :param months: list of monthsto include for the regression calc
       :param groupby: the time range by which to group the data
       """

    def __init__(self, months=None, groupby='month'):
        self.months = months
        self.groupby = groupby

    def compute(self, data):
        crs = data.crs
        data = data.sortby('time')
        # pernan is a filtration level - scenes with more nans than this per scene are removed
        pernan = 0.80
        data = data.dropna('time', thresh=int(
            pernan * len(data.x) * len(data.y)))
        def dry_vals(sensor_data, months):
            '''calculates dry season or wet season values'''
            if sensor_data is not None:
                dry_data = sensor_data.sel(time=np.in1d(sensor_data.time.dt.month, months))
                return dry_data
            else:
                return None

        if self.months is not None:
            data = dry_vals(data, self.months)

        ndvi = xr.Dataset(data_vars={'ndvi': (data.nir - data.red) / (data.nir + data.red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))
        data=None
        mean_ndvi = ndvi.ndvi.mean(dim='time')
        if self.groupby =='month':
            averaged_data = ndvi.groupby('time.month').mean(dim='time')
        elif self.groupby =='dayofyear':
            averaged_data = ndvi.groupby('time.dayofyear').mean(dim='time')
        elif self.groupby == 'year':
            averaged_data = ndvi.groupby('time.year').mean(dim='time')

        start_ndvi= averaged_data.ndvi[0, :, :]
        end_ndvi = averaged_data.ndvi[-1, :, :]

        #averaged_data = averaged_data.where(averaged_data >= 0)
        min_date = averaged_data[self.groupby].min()
        averaged_data['ts'] = (averaged_data.ndvi/averaged_data.ndvi) * (averaged_data[self.groupby]-min_date)

        cov, cor, slope, intercept, pval, stderr = lag_linregress_3D(averaged_data.ts, averaged_data.ndvi)

        averaged_data = averaged_data.drop([self.groupby])
        start_ndvi = start_ndvi.drop([self.groupby])
        end_ndvi = end_ndvi.drop([self.groupby])

        trend_dataset = xr.Dataset(data_vars={'slope_ndvi': slope,
                                        'intercept_ndvi': intercept,
                                        'r_squared_ndvi': cor**2,
                                        'p_value_ndvi': pval,
                                        'std_err_ndvi': stderr,
                                        'mean_ndvi': mean_ndvi,
                                        'start_ndvi': start_ndvi,
                                        'end_ndvi': end_ndvi},
                                        coords=averaged_data.coords,
                                        attrs=dict(crs=crs))

        return trend_dataset

    def measurements(self, input_measurements):
        measurement_names = ['slope_ndvi', 'intercept_ndvi', 'r_squared_ndvi','p_value_ndvi','std_err_ndvi',
                             'mean_ndvi', 'start_ndvi', 'end_ndvi']
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]

class TCIregression(Statistic):
    """
       Tasselled Cap regression of observations through time.
       The different percentiles are stored in the output as separate bands.
       The q-th percentile of a band is named `ndvi_PC_{q}`.

       :param months: list of monthsto include for the regression calc
       :param groupby: the time range by which to group the data
       """

    def __init__(self, months=None, groupby='month', category='wetness', coeffs=None):
        self.months = months
        self.groupby = groupby

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

    def compute(self, data):
        crs = data.crs
        coeffs = self.coeffs
        bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        category = self.category
        data = data.sortby('time')

        # pernan is a filtration level - scenes with more nans than this per scene are removed
        pernan = 0.80
        data = data.dropna('time', thresh=int(
            pernan * len(data.x) * len(data.y)))
        def dry_vals(sensor_data, months):
            '''calculates dry season or wet season values'''
            if sensor_data is not None:
                dry_data = sensor_data.sel(time=np.in1d(sensor_data.time.dt.month, months))
                return dry_data
            else:
                return None

        if self.months is not None:
            data = dry_vals(data, self.months)

        tci = sum([data[band] * coeffs[category][band] for band in bands])

        tci = xr.Dataset(data_vars={'tci': tci},
                             coords=data.coords,
                             attrs=dict(crs=data.crs))
        tc_mean = tci.tci.mean(dim='time')
        data = None

        if self.groupby =='month':
            averaged_data = tci.groupby('time.month').mean(dim='time')
        elif self.groupby =='dayofyear':
            averaged_data = tci.groupby('time.dayofyear').mean(dim='time')
        elif self.groupby == 'year':
            averaged_data = tci.groupby('time.year').mean(dim='time')

        start_tci= averaged_data.tci[0, :, :]
        end_tci = averaged_data.tci[-1, :, :]

        #averaged_data = averaged_data.where(averaged_data >= 0)
        averaged_data['ts'] = (averaged_data.tci/averaged_data.tci) * averaged_data[self.groupby]

        cov, cor, slope, intercept, pval, stderr = lag_linregress_3D(averaged_data.ts, averaged_data.tci)
        averaged_data = averaged_data.drop([self.groupby])
        start_tci = start_tci.drop([self.groupby])
        end_tci = end_tci.drop([self.groupby])
        suffix = '_tc' + self.category[0]
        trend_dataset = xr.Dataset(data_vars={'slope'+ suffix: slope,
                                              'intercept' + suffix: intercept,
                                              'r_squared' + suffix: cor**2,
                                              'p_value' + suffix: pval,
                                              'std_err' + suffix: stderr,
                                              'mean' + suffix: tc_mean,
                                              'start' + suffix: start_tci,
                                              'end' + suffix: end_tci},
                                   coords=averaged_data.coords,
                                   attrs=dict(crs=crs))

        return trend_dataset

    def measurements(self, input_measurements):
        suffix = '_tc' + self.category[0]
        measurement_names = ['slope'+ suffix, 'intercept'+ suffix, 'r_squared'+ suffix,
                             'p_value'+ suffix,'std_err'+ suffix,'mean' + suffix,'start'+ suffix,'end' + suffix]
        return [Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
                for m_name in measurement_names]


