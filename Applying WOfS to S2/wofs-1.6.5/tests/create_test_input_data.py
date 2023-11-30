import sys
from pathlib import Path

import xarray as xr
import yaml


def create_sample_file():
    in_dir = Path(sys.argv[1])
    out_file = sys.argv[2]

    fname = list(in_dir.glob('*.odc-metadata.yaml'))[0]

    with open(fname) as fin:
        doc = yaml.safe_load(fin)

    to_load = [(name, in_dir / details['path'])
               for name, details in doc['measurements'].items()
               if name.startswith('nbart') or 'fmask' in name]
    to_load = sorted(to_load, key=lambda tup: tup[1])

    def load_band(fname):
        data = xr.open_rasterio(fname)
        return data.squeeze().sel(x=slice(None, None, 200), y=slice(None, None, 200))

    data_vars = {name: load_band(fname) for name, fname in to_load}

    ds = xr.Dataset(data_vars)

    for dv in ds.data_vars.values():
        dv.attrs['nodata'] = dv.attrs['nodatavals']

    ds = ds.expand_dims({'time': [doc['properties']['datetime'].replace(tzinfo=None)]})

    ds.to_netcdf(out_file)


if __name__ == '__main__':
    create_sample_file()
