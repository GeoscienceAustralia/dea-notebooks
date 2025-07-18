import os
import tempfile
import rasterio
import pytest
from mosaic_COGs import make_mosaic_cogs, create_vrt  

@pytest.fixture
def test_params(tmp_path):
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

def test_make_mosaic_and_validate(test_params):
    make_mosaic_cogs(**test_params)

    output_file = os.path.join(
        test_params["output_dir"],
        test_params["product"],
        test_params["version"],
        "continental_mosaics",
        f"{test_params['time']}--{test_params['freq']}",
        f"{test_params['product']}_mosaic_{test_params['time']}--{test_params['freq']}_{test_params['band']}.tif"
    )

    # assert mosaic COG created
    assert os.path.exists(output_file), "Output COG not found"

    # try open file and validate raster integrity
    with rasterio.open(output_file) as src:
        assert src.count == 1, "Expected 1 band in mosaic"
        assert src.crs is not None, "CRS missing"
        assert src.width > 0 and src.height > 0, "Invalid raster dimensions"
        data = src.read(1)
        assert data.any(), "No data read from mosaic file"
        
def test_vrt_creation(tmp_path):
    make_mosaic_cogs(**test_params)

    mosaic_path = os.path.join(
        test_params["output_dir"],
        test_params["product"],
        test_params["version"],
        "continental_mosaics",
        f"{test_params['time']}--{test_params['freq']}",
        f"{test_params['product']}_mosaic_{test_params['time']}--{test_params['freq']}_{test_params['band']}.tif"
    )


    # ADD CODE TO ACTUALLY TEST CREAT_VRT function

