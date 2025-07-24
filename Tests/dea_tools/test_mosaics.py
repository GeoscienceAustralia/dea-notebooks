import os
import rasterio
import pytest
import pathlib
import sys

from dea_tools.mosaics.mosaic_COGs import make_cog_mosaics
from dea_tools.mosaics.colour_scheme_VRTs import make_styling_vrt


def test_mosaic_vrt_creation_cat(tmp_path):
    mosaic_params = {
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
        "compression_level": 9,
        "aws_unsigned": True,
        "skip_existing": False,
        "list_tiles": ["x46y47", "x46y48"],
    }

    col_scheme_dir = "Supplementary_data/Colour_schemes"

    vrt_params = {
        "product": "ga_ls_landcover_class_cyear_3",
        "band": "level4",
        "time": "2024",
        "freq": "P1Y",
        "version": "2-0-0",
        "cog_dir": str(tmp_path),
        "output_dir": str(tmp_path),
        "col_scheme_dir": col_scheme_dir,
    }

    make_cog_mosaics(**mosaic_params)

    output_cog = os.path.join(
        mosaic_params["output_dir"],
        mosaic_params["product"],
        mosaic_params["version"],
        "continental_mosaics",
        f"{mosaic_params['time']}--{mosaic_params['freq']}",
        f"{mosaic_params['product']}_mosaic_{mosaic_params['time']}--{mosaic_params['freq']}_{mosaic_params['band']}.tif"
    )

    assert os.path.exists(output_cog), "Output COG not found"

    with rasterio.open(output_cog) as src:
        assert src.count == 1, "Expected 1 band in mosaic"
        assert src.crs is not None, "CRS missing"
        assert src.width > 0 and src.height > 0, "Invalid raster dimensions"
        assert src.read(1).any(), "No data read from mosaic file"

    make_styling_vrt(**vrt_params)

    output_vrt = os.path.join(
        vrt_params["output_dir"],
        vrt_params["product"],
        vrt_params["version"],
        "continental_mosaics",
        f"{vrt_params['time']}--{vrt_params['freq']}",
        f"{vrt_params['product']}_mosaic_{vrt_params['time']}--{vrt_params['freq']}_{vrt_params['band']}.vrt"
    )

    assert os.path.exists(output_vrt), "Output VRT not found"

    with rasterio.open(output_vrt) as vrt:
        assert vrt.count == 1, "Expected 1 band in VRT"
        assert vrt.crs is not None, "CRS missing"
        assert vrt.width > 0 and vrt.height > 0, "Invalid VRT dimensions"



def test_geomedian_rgb_mosaic_and_vrt(tmp_path):
    product = "ga_ls8cls9c_gm_cyear_3"
    version = "4-0-0"
    year = "2024"
    bands = ["nbart_red", "nbart_green", "nbart_blue"]
    list_tiles = ["x46y47", "x46y48"]

    # generate COGs for each RGB band
    for band in bands:
        make_cog_mosaics(
            product=product,
            band=band,
            time=year,
            freq="P1Y",
            version=version,
            dataset_maturity="final",
            product_dir="s3://dea-public-data/derivative/",
            output_dir=str(tmp_path),
            cog_blocksize=1024,
            overview_count=7,
            overview_resampling="BILINEAR",
            compression_algo="ZSTD",
            compression_level=9,
            aws_unsigned=True,
            skip_existing=False,
            list_tiles=list_tiles
        )

        output_cog = os.path.join(
            tmp_path,
            product,
            version,
            "continental_mosaics",
            f"{year}--P1Y",
            f"{product}_mosaic_{year}--P1Y_{band}.tif"
        )

        assert os.path.exists(output_cog), f"COG not found for {band}"

        with rasterio.open(output_cog) as src:
            assert src.count == 1
            assert src.crs is not None
            assert src.width > 0 and src.height > 0
            assert src.read(1).any(), f"No data in {band} band"

    make_styling_vrt(
        product=product,
        version=version,
        time=year,
        freq="P1Y",
        cog_dir=str(tmp_path),
        output_dir=str(tmp_path),
        r_channel_band="nbart_red",
        g_channel_band="nbart_green",
        b_channel_band="nbart_blue"
    )

    output_vrt = os.path.join(
        tmp_path,
        product,
        version,
        "continental_mosaics",
        f"{year}--P1Y",
        f"{product}_mosaic_{year}--P1Y_{'-'.join(bands)}.vrt"
    )

    assert os.path.exists(output_vrt), "RGB VRT not found"

    with rasterio.open(output_vrt) as vrt:
        assert vrt.count == 3, "Expected 3 bands in composite VRT"
        assert vrt.crs is not None, "CRS missing"
        assert vrt.width > 0 and vrt.height > 0, "Invalid VRT dimensions"
