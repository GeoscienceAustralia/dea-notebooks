import os
import rasterio
import pytest
import pathlib
import sys
sys.path.insert(1, '../../Tools/')
from dea_tools.mosaics.mosaic_COGs import make_mosaic_cogs
from dea_tools.mosaics.colour_scheme_VRTs import create_vrt  

@pytest.fixture
def mosaic_test_params(tmp_path):
    return {
        "product": "ga_ls_landcover_class_cyear_3",
        "band": "level4",
        "time": "2024",
        "freq": "P1Y",
        "version": "2-0-0",
        "dataset_maturity": "final",
        "product_dir": "s3://dea-public-data/derivative/",
        "output_dir": str(tmp_path),
        "cog_blocksize": 1024,
        "overview_count": 7,
        "overview_resampling": "MODE",
        "compression_algo": "ZSTD",
        "compression_lvl": 9,
        "aws_unsigned": True,
        "skip_existing": False,
        "list_tiles": ["x46y47", "x46y48"],  
    }


@pytest.fixture
def vrt_test_params_categorical(tmp_path):
    #relative path to test python script
    col_scheme_dir = pathlib.Path(__file__).parent.parent.parent / "Supplementary_data" / "Colour_schemes"
    return {
        "product": "ga_ls_landcover_class_cyear_3",
        "band": "level4",
        "time": "2024",
        "freq": "P1Y",
        "version": "2-0-0",
        "cog_dir": str(tmp_path),
        "output_dir": str(tmp_path),
        "col_scheme_dir": str(col_scheme_dir.resolve()),
    }

        
def test_mosaic_vrt_creation(mosaic_test_params, vrt_test_params_categorical):
    make_mosaic_cogs(**mosaic_test_params)

    output_cog = os.path.join(
        mosaic_test_params["output_dir"],
        mosaic_test_params["product"],
        mosaic_test_params["version"],
        "continental_mosaics",
        f"{mosaic_test_params['time']}--{mosaic_test_params['freq']}",
        f"{mosaic_test_params['product']}_mosaic_{mosaic_test_params['time']}--{mosaic_test_params['freq']}_{mosaic_test_params['band']}.tif"
    )

    # assert mosaic COG created
    assert os.path.exists(output_cog), "Output COG not found"

    # try open file and validate raster integrity
    with rasterio.open(output_cog) as src:
        assert src.count == 1, "Expected 1 band in mosaic"
        assert src.crs is not None, "CRS missing"
        assert src.width > 0 and src.height > 0, "Invalid raster dimensions"
        data = src.read(1)
        assert data.any(), "No data read from mosaic file"

    create_vrt(**vrt_test_params_categorical)

    output_vrt_cat = os.path.join(
        vrt_test_params_categorical["output_dir"],
        vrt_test_params_categorical["product"],
        vrt_test_params_categorical["version"],
        "continental_mosaics",
        f"{vrt_test_params_categorical['time']}--{vrt_test_params_categorical['freq']}",
        f"{vrt_test_params_categorical['product']}_mosaic_{vrt_test_params_categorical['time']}--{vrt_test_params_categorical['freq']}_{vrt_test_params_categorical['band']}.vrt"
    )

    # assert mosaic COG created
    assert os.path.exists(output_vrt_cat), "Output VRT not found"


