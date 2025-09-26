# cog.py
"""
Generate Cloud Optimised GeoTIFF (COG) mosaics for DEA tiled products.

This module builds continental-scale mosaics by combining individual DEA tiles
into a single Cloud Optimised GeoTIFF using GDAL tools (`gdalbuildvrt`, `gdal_translate`).
It supports DEA's tiled product structure and naming conventions and can read from both
local disk and public S3 buckets (e.g., `dea-public-data` or `dea-public-data-dev`).

Input Format
------------
Input products must follow the DEA Collection 3 naming conventions and file structure, e.g.:
`s3://dea-public-data/derivative/<product>/<version>/<tile path>/<year>--<freq>/<product>_<tile path>_<year>--<freq>_<dataset maturity>_<band>.tif`

For more information:
https://knowledge.dea.ga.gov.au/guides/reference/collection_3_naming/
https://knowledge.dea.ga.gov.au/guides/reference/collection_3_summary_grid/

Output Format
-------------
Mosaics are saved as:
`<output_dir>/<product>/<version>/continental_mosaics/<time>--<freq>/<product>_mosaic_<time>--<freq>_<band>.tif`

License: The code in this module is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one on
GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: July 2025
"""

import glob
import logging
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

import click
import s3fs
from odc.stac import configure_rio

from dea_tools.mosaics.utils import _is_s3, _get_vsicurlhttp_from_s3, _get_vsis3_from_s3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _get_tiles(
    product_dir,
    product,
    version,
    time,
    freq,
    dataset_maturity,
    band,
    is_s3,
    aws_unsigned,
    list_tiles=None,  # example ['x25y41', 'x25y41']
):
    """
    Search for matching tile files from local or S3 paths based on product metadata.
    Optionally filters to a subset of specified tiles (e.g., ['x25y41', 'x25y41']).
    """
    tiles_pattern = (
        f"{product_dir}/"
        f"{product}/"
        f"{version}/"
        "**/**/"
        f"{time}--{freq}/"
        f"{product}_*{time}--{freq}_{dataset_maturity}_{band}.tif"
    )

    # Return list of tiles on either S3 or local directory
    if is_s3:
        fs = s3fs.S3FileSystem(anon=True)
        configure_rio(cloud_defaults=True, aws={"aws_unsigned": aws_unsigned})
        tiles_list = fs.glob(tiles_pattern)
    else:
        tiles_list = glob.glob(tiles_pattern, recursive=True)

    # Optionally filter list of tiles if requested
    if list_tiles:
        xy_patterns = [xy.replace("y", "/y") for xy in list_tiles]  # i.e. from 'x25y41' to 'x25/y41'
        tiles_list = [tile for tile in tiles_list if any(xy in tile for xy in xy_patterns)]

    return tiles_list


def make_cog_mosaic(
    product,
    band,
    time,
    freq,
    version,
    dataset_maturity,
    product_dir,
    output_dir,
    cog_blocksize,
    overview_count,
    overview_resampling,
    compression_algo,
    compression_level,
    aws_unsigned,
    skip_existing,
    list_tiles=None,
    vsi_method="vsicurl",
):
    """
    Generate a COG mosaic for a given tiled DEA product.

    Products must follow the DEA Collection 3 naming
    conventions and file structure:
    https://knowledge.dea.ga.gov.au/guides/reference/collection_3_naming/
    https://knowledge.dea.ga.gov.au/guides/reference/collection_3_summary_grid/

    Parameters:
    ----------
    product : str
        The name of the DEA product (e.g. 'ga_ls_landcover_class_cyear_3').
    band : str
        The variable or band to extract.
    time : int or str
        The target time of the mosaic, year if annual summaries (e.g. '2023'),
        year-month for seasonal (e.g. water observations nov_mar --> '2024-11')
    freq : str
        The frequency of the summary product (e.g. 'P1Y').
    version : str
        Product version (e.g. '2-0-0').
    dataset_maturity : str
        Dataset maturity stage. Usually: 'final'.
    product_dir : str
        S3 directory for the product. Usually 's3://dea-public-data/derivative/',
        which is the DEA public bucket and derivates products folder,
        which corresponds with https://data.dea.ga.gov.au/derivative/
        HTTPS endpoint.
    output_dir : str
        local directory or s3 directory where to save output.
    cog_blocksize : int or str
        Size of internal COG tiling. Use 1024, unless there are specific reasons to
        use a different value.
    overview_count : int or str
        Number of image overviews to generate.
        Use 7 for 30 m resolution products (like Landsat),
        use 8 for 10 m resolution products (like Sentinel-2).
    overview_resampling : str
        GDAL resampling method used when building overviews.
        Options include (use all capital letters):
        - 'MODE' for categorical data (e.g. land cover),
        - 'BILINEAR' for continuous data,
        - 'NEAREST' for narrow continuous data with many nodata pixels (e.g., coastal products).
    compression_algo : str
        GDAL compression algorithm used for output COG.
        Use 'ZSTD', unless there are specific reasons to use a different algorithm.
    compression_level : int or str
        Level of compression of output COG.
        Use 9, unless there are specific reasons to use a different level.
    aws_unsigned : bool
        Whether to sign AWS requests for S3 access.
    skip_existing : bool
        Whether to skip generation if output already exists.
    list_tiles : list of strings, optional
        List including tiles of interest to include in the output mosaic.
        For example: ['x25y41', 'x25y41'].
        Defaults to None --> use all tiles available.
    vsi_method : str, optional
        Whether to use "/vsicurl/" for HTTPS-based URIs in the interim
        Virtual Raster ("vsicurl"), or "/vsis3/" for accessing data directly
        from AWS S3 ("vsis3"). Default is "vsicurl".

    Notes:
    ------
    All other `gdal_translate` parameters are intentionally
    omitted in this function. These options should be standardized
    across all products, and are applied consistently as part of
    downstream processing.
    """
    # first log
    log = logging.getLogger(__name__)
    input_params = locals()
    run_id = f"[{product}] [{version}] [{time}] [{band}]"
    log.info(f"{run_id}: Using parameters {input_params}")

    # Set product and output paths to plain strings
    # TODO: refactor code to use pathlib throughout
    product_dir = str(product_dir)
    output_dir = str(output_dir)

    # Determine if input data is located on S3
    is_input_dir_s3 = _is_s3(product_dir)
    is_out_dir_s3 = _is_s3(output_dir)

    # Clean string to prepare for analysis
    product_dir = product_dir.removeprefix("s3://")
    product_dir = product_dir.rstrip("/")
    log.info(f"{run_id}: Using input data product directory: {product_dir}")

    # Determine output directory and file path following naming convention
    # /derivative/<product_id>/<version>/continental_mosaics/<time>/<product_id>_mosaic_<time>_<band name>.tif
    output_dir = output_dir.rstrip("/")
    if is_out_dir_s3:
        output_dir = f"{output_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        output_file_path = f"{output_dir}/{product}_mosaic_{time}--{freq}_{band}.tif"
        log.info(f"{run_id} Output path: {output_file_path}")
    else:
        output_dir = os.path.join(output_dir, product, version, "continental_mosaics", f"{time}--{freq}")
        output_file_path = os.path.join(output_dir, f"{product}_mosaic_{time}--{freq}_{band}.tif")
        log.info(f"{run_id} Output path: {output_file_path}")

    # Check if output file already exists
    if is_out_dir_s3:
        fs = s3fs.S3FileSystem(anon=aws_unsigned)
        output_exists = fs.exists(output_file_path.removeprefix("s3://"))
    else:
        output_exists = os.path.exists(output_file_path)

    # If output exists, either skip processing or overwrite
    if output_exists:
        if skip_existing:
            log.info(
                f"{run_id}: Output already exists at {output_file_path} and skip_existing=True. Skipping generation."
            )
            return
        log.warning(f"{run_id}: Output already exists at {output_file_path} but skip_existing=False. Overwriting.")
    else:
        log.info(f"{run_id}: Output does not exist. Proceeding with mosaic generation.")

    # Get list of paths
    log.info(f"{run_id}: Finding data to mosaic")
    tiles_list = _get_tiles(
        product_dir,
        product,
        version,
        time,
        freq,
        dataset_maturity,
        band,
        is_input_dir_s3,
        aws_unsigned,
        list_tiles=list_tiles,
    )

    # Use /vsicurl/ or /vsis3/ path for `gdalbuildvrt` compatibility
    if vsi_method == "vsicurl":
        tiles_list = [_get_vsicurlhttp_from_s3(tile) for tile in tiles_list]
    elif vsi_method == "vsis3":
        tiles_list = [_get_vsis3_from_s3(tile) for tile in tiles_list]
    log.info(f"{run_id}: Number of tiles to mosaic: {len(tiles_list)}")

    if len(tiles_list) > 0:
        # Create a temporary directory to house files before syncing
        with tempfile.TemporaryDirectory() as temp_dir:
            log.info(f"{run_id}: Writing data to temporary folder: {temp_dir}")

            # Output paths for intermediate files
            file_list_name = os.path.join(temp_dir, f"{product}_{time}--{freq}_{band}_{version}.txt")
            vrt_name = os.path.join(temp_dir, f"{product}_{time}--{freq}_{band}_{version}.vrt")
            output_name = os.path.join(temp_dir, f"{product}_mosaic_{time}--{freq}_{band}.tif")

            # Write list of files to a temporary text file, so it can be
            # used as an input to `gdalbuildvrt`
            with open(file_list_name, "w") as f:
                for tile in tiles_list:
                    f.write(f"{tile}\n")

            # Build VRT that will subsequently be used to generate COG
            log.info(f"{run_id}: Building virtual raster (VRT)")
            try:
                subprocess.run(
                    ["gdalbuildvrt", vrt_name, "-input_file_list", file_list_name],
                    check=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                log.error(f"{run_id}: gdalbuildvrt failed with error: {e.stderr} {e.stdout}")
                raise

            # Convert VRT to Cloud Optimized GeoTIFF (COG)
            log.info(f"{run_id}: Converting VRT to COG mosaic")
            # fmt: off
            try:
                subprocess.run(
                    [
                        "gdal_translate",
                        vrt_name,
                        output_name,
                        "-co", "NUM_THREADS=ALL_CPUS",                        # Parallelisation
                        "-of", "COG",                                         # Output format
                        "-co", "BIGTIFF=YES",                                 # Allow large TIFFs
                        "-co", f"BLOCKSIZE={cog_blocksize}",                  # Tiling
                        "-co", "OVERVIEWS=IGNORE_EXISTING",                   # Force overview regen
                        "-co", f"OVERVIEW_RESAMPLING={overview_resampling}",  # Resampling for overviews
                        "-co", f"OVERVIEW_COUNT={overview_count}",            # Number of overviews
                        "-co", f"COMPRESS={compression_algo}",                # Compression
                        "-co", f"LEVEL={compression_level}",                  # Compression level
                        "-co", "PREDICTOR=YES",                               # Compression predictor
                    ],
                    check=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                log.error(f"{run_id}: gdal_translate failed with error: {e.stderr} {e.stdout}")
                raise
            # fmt: on

            # Copy output to S3
            if is_out_dir_s3:
                log.info(f"{run_id}: Writing COG to S3: {output_file_path}")

                subprocess.run(
                    [
                        "aws",
                        "s3",
                        "cp",
                        "--only-show-errors",
                        "--acl",
                        "bucket-owner-full-control",
                        str(output_name),
                        str(output_file_path),
                    ],
                    check=True,
                )

            # Copy locally to output folder
            else:
                log.info(f"{run_id}: Writing data locally: {output_file_path}")

                os.makedirs(output_dir, exist_ok=True)
                shutil.copy(output_name, output_file_path)

    else:
        log.info(f"{run_id}: No input tiles found")


@click.command()
@click.option(
    "--product",
    type=str,
    required=True,
    help="The name of the product to be mosaicked (e.g. 'ga_ls_landcover_class_cyear_3').",
)
@click.option(
    "--band",
    type=str,
    required=True,
    help="The variable or band to extract (e.g. 'level4')",
)
@click.option(
    "--time",
    type=str,
    required=True,
    help="The target time of the mosaic (e.g. '2022').",
)
@click.option(
    "--freq",
    type=str,
    required=True,
    help="The frequency of the summary product (e.g. 'P1Y').",
)
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version number of the product (e.g. '2-0-0').",
)
@click.option(
    "--dataset_maturity",
    type=str,
    default="final",
    show_default=True,
    help="Dataset maturity of the data to be mosaicked. Usually: 'final'.",
)
@click.option(
    "--product_dir",
    type=str,
    default="s3://dea-public-data-dev/derivative/",
    show_default=True,
    help="The directory/location to read the tile COGs from; supports "
    "both local disk and S3 locations. E.g. 's3://dea-public-data/derivative/', "
    "corresponding to https://data.dea.ga.gov.au/derivative/.",
)
@click.option(
    "--output_dir",
    type=str,
    required=True,
    help="Local or S3 directory where to save output. "
    "The function will add on `{product}/{version}/continental_mosaics/{time}--{freq}` ",
)
@click.option(
    "--cog_blocksize",
    type=int,
    default=1024,
    show_default=True,
    help="Size of internal COG tiling. Use 1024, unless there are specific reasons to use a different value.",
)
@click.option(
    "--overview_count",
    type=int,
    required=True,
    help="Number of image overviews to generate. "
    "Use 7 for 30m resolution products (e.g., Landsat), "
    "or 8 for 10m resolution products (e.g., Sentinel-2).",
)
@click.option(
    "--overview_resampling",
    type=str,
    required=True,
    help="GDAL resampling method used for overviews. Use uppercase values: "
    "'MODE' for categorical data (e.g., land cover), "
    "'BILINEAR' for continuous data, "
    "'NEAREST' for sparse/narrow continuous data.",
)
@click.option(
    "--compression_algo",
    type=str,
    default="ZSTD",
    show_default=True,
    help="GDAL compression algorithm used for output COG."
    "Use 'ZSTD', unless there are specific reasons to use a different algorithm.",
)
@click.option(
    "--compression_level",
    type=int,
    default=9,
    show_default=True,
    help="Level of compression of output COG. Use '9', unless there are specific reasons to use a different level.",
)
@click.option(
    "--aws_unsigned/--no-aws_unsigned",
    is_flag=True,
    default=True,
    help="Whether to sign AWS requests for S3 access. Defaults to "
    "True; can be set to False by passing `--no-aws_unsigned`.",
)
@click.option(
    "--skip_existing/--no-skip_existing",
    is_flag=True,
    default=False,
    show_default=True,
    help="Skip generation if output already exists.Defaults to False",
)
@click.option(
    "--list_tiles",
    type=str,
    required=False,
    help="Comma-separated list of tiles to include in the mosaic. Example: x25y41,x26y42. "
    "If omitted, all tiles will be used.",
)
def make_cog_mosaic_cli(
    product,
    band,
    time,
    freq,
    version,
    dataset_maturity,
    product_dir,
    output_dir,
    cog_blocksize,
    overview_count,
    overview_resampling,
    compression_algo,
    compression_level,
    aws_unsigned,
    skip_existing,
    list_tiles,
):
    """
    CLI entry point for generating DEA COG mosaics from tiled datasets.
    Passes user inputs to the core mosaic generation function.
    """
    # Convert string of tiles to list
    list_tiles = list_tiles.split(",") if list_tiles else None

    # Run analysis function
    make_cog_mosaic(
        product,
        band,
        time,
        freq,
        version,
        dataset_maturity,
        product_dir,
        output_dir,
        cog_blocksize,
        overview_count,
        overview_resampling,
        compression_algo,
        compression_level,
        aws_unsigned,
        skip_existing,
        list_tiles,
    )


if __name__ == "__main__":
    make_cog_mosaic_cli()
