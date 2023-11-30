from pathlib import Path

import xarray as xr
import yaml
from datacube.virtual import construct

from wofs.virtualproduct import WOfSClassifier


def test_virtualproduct():
    # Load sample surface reflectance data
    sr_data = xr.open_dataset(Path(__file__).parent / 'sample_c3_sr.nc', mask_and_scale=False)
    # and munge to make look more like data loaded by ODC
    sr_data = sr_data.rename({'oa_fmask': 'fmask'})
    sr_data.attrs['crs'] = 'EPSG:32754'
    del sr_data.coords['band']

    for dv in sr_data.data_vars.values():
        dv.attrs['nodata'] = dv.attrs['nodatavals']

    transform = WOfSClassifier()
    wofl = transform.compute(sr_data)

    sample = xr.open_dataset(Path(__file__).parent / 'sample_wofl.nc', mask_and_scale=False)

    assert sample.equals(wofl)


def foo():
    # measurements: [green, red, nir, swir1, swir2]
    virtual_product_defn = yaml.safe_load('''
    transform: wofs.virtualproduct.Wofs
    input:
        product: ls8_ard
        measurements: [nbart_blue, nbart_green, nbart_red, nbart_nir, nbart_swir_1, nbart_swir_2, fmask]
    ''')
    virtual_product = construct(**virtual_product_defn)

    # [odc_conf_test] -
    # db_hostname: agdcdev-db.nci.org.au
    # db_port: 6432
    # db_database: odc_conf_test

    # [ard_interop] - collection upgrade DB
    # db_hostname: agdcstaging-db.nci.org.au
    # db_port:     6432
    # db_database: ard_interop

    dc = datacube.Datacube(env="odc_conf_test")

    vdbag = virtual_product.query(dc=dc, id='be43b7ce-c421-4c16-826d-a508f3e3d984')

    box = virtual_product.group(vdbag, output_crs='EPSG:28355', resolution=(-25, 25))

    virtual_product.output_measurements(vdbag.product_definitions)

    data = virtual_product.fetch(box, dask_chunks=dict(x=1000, y=1000))

    print(data)

    # crash!
    # done = data.compute()
