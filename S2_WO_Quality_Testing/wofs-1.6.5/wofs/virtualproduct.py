import logging
from typing import Dict

import xarray as xr
from datacube.testutils.io import dc_read
from datacube.virtual import Transformation, Measurement
from xarray import Dataset

from wofs.wofls import woffles_ard, woffles_usgs_c2

WOFS_OUTPUT = [{
    'name': 'water',
    'dtype': 'uint8',
    'nodata': 1,
    'units': '1'
}, ]
_LOG = logging.getLogger(__file__)


def scale_usgs_collection2(data):
    """These are taken from the Fractional Cover scaling values"""
    return data.apply(scale_and_clip_dataarray, keep_attrs=True,
                      scale_factor=0.275, add_offset=-2000, 
                      clip_range=None, valid_range=(0, 10000))


def scale_and_clip_dataarray(dataarray: xr.DataArray, *, scale_factor=1, add_offset=0, clip_range=None,
                             valid_range=None, new_nodata=-999, new_dtype='int16'):
    orig_attrs = dataarray.attrs
    nodata = dataarray.attrs['nodata']

    mask = dataarray.data == nodata

    # add another mask here for if data > 10000 then also make that nodata
    dataarray = dataarray * scale_factor + add_offset

    if clip_range is not None:
        clip_min, clip_max = clip_range
        dataarray.clip(clip_min, clip_max)

    dataarray = dataarray.astype(new_dtype)

    dataarray.data[mask] = new_nodata
    if valid_range is not None:
        valid_min, valid_max = valid_range
        dataarray = dataarray.where(dataarray>= valid_min, new_nodata)
        dataarray = dataarray.where(dataarray<= valid_max, new_nodata)
    dataarray.attrs = orig_attrs
    dataarray.attrs['nodata'] = new_nodata

    return dataarray


def _to_xrds_coords(geobox):
    return {dim: coord.values for dim, coord in geobox.coordinates.items()}


class WOfSClassifier(Transformation):
    """ Applies the wofs algorithm to surface reflectance data.
    Requires bands named
    bands = ['nbart_blue', 'nbart_green', 'nbart_red', 'nbart_nir', 'nbart_swir_1', 'nbart_swir_2', 'fmask']

    Terrain buffer is specified in CRS Units (typically meters)

    Options include:
        dsm_path: a URI to a DSM, either S3:// or HTTPS:// work
        c2_scaling: handle the USGS's new scaling values, rescaling to the old way
        terrain_buffer:
    """

    def __init__(self, dsm_path=None, c2_scaling=False, terrain_buffer=0, dsm_no_data=-1000, ignore_dsm_no_data=False):
        self.dsm_path = dsm_path
        self.dsm_no_data = dsm_no_data
        self.c2_scaling = c2_scaling
        self.terrain_buffer = terrain_buffer
        self.ignore_dsm_no_data = ignore_dsm_no_data
        self.output_measurements = {m['name']: Measurement(**m) for m in WOFS_OUTPUT}
        if dsm_path is None:
            _LOG.warning('WARNING: Path or URL to a DSM is not set. Terrain shadow mask will not be calculated.')

    def measurements(self, input_measurements) -> Dict[str, Measurement]:
        return self.output_measurements

    def compute(self, data) -> Dataset:
        _LOG.info(data.geobox)
        _LOG.info(repr(data.geobox))

        if self.c2_scaling:
            # The C2 data need to be scaled
            orig_attrs = data.attrs
            spectral_data = data[
                ['nbart_blue', 'nbart_green', 'nbart_red', 'nbart_nir', 'nbart_swir_1', 'nbart_swir_2']
            ]
            mask_data = data[['fmask']]
            data = xr.merge([scale_usgs_collection2(spectral_data), mask_data])
            data.attrs = orig_attrs

        if self.dsm_path is not None:
            dsm = self._load_dsm(data.geobox.buffered(self.terrain_buffer, self.terrain_buffer))
        else:
            dsm = None

        wofs = []
        for time_idx in range(len(data.time)):
            if self.c2_scaling:
                # C2 wofls
                wofs.append(
                    woffles_usgs_c2(
                        data.isel(time=time_idx),
                        dsm,
                        dsm_no_data=self.dsm_no_data,
                        ignore_dsm_no_data=self.ignore_dsm_no_data
                    ).to_dataset(name='water')
                )
            else:
                wofs.append(
                    woffles_ard(
                        data.isel(time=time_idx),
                        dsm,
                        dsm_no_data=self.dsm_no_data,
                        ignore_dsm_no_data=self.ignore_dsm_no_data
                    ).to_dataset(name='water')
                )

        wofs = xr.concat(wofs, dim='time')
        wofs.attrs['crs'] = data.attrs['crs']
        return wofs

    def _load_dsm(self, gbox):
        # Data variable needs to be named elevation
        dsm = dc_read(self.dsm_path, gbox=gbox, resampling="bilinear")
        return xr.Dataset(
            data_vars={'elevation': (('y', 'x'), dsm)},
            coords=_to_xrds_coords(gbox),
            attrs={'crs': gbox.crs}
        )
