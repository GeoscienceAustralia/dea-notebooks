# mosaic_COGs.py
"""
Generate Cloud Optimised GeoTIFF (COG) mosaics for DEA tiled products.

This module builds continental-scale mosaics by combining individual DEA tiles
into a single Cloud Optimised GeoTIFF using GDAL tools (`gdalbuildvrt`, `gdal_translate`).
It supports DEA's tiled product structure and naming conventions and can read from both
local disk and public S3 buckets (e.g., `dea-public-data` or `dea-public-data-dev`).

Input Format
------------
Input products must follow the DEA tiling convention:
`s3://dea-public-data/derivative/<product>/<version>/<tile path>/<year>--<freq>/<product>_<tile path>_<year>--<freq>_<dataset maturity>_<band>.tif` 

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

import s3fs
import os
import subprocess
import glob
import tempfile
import shutil
import click
import logging
from urllib.parse import urlparse
from datacube.utils.aws import configure_s3_access

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)


def _is_s3(path):
    """
    Determine whether output location is on S3.
    """
    uu = urlparse(path)
    return uu.scheme == "s3"


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
    list_tiles = None, # example ['x25y41', 'x25y41']
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

    if is_s3:
        fs = s3fs.S3FileSystem(anon=True) #s3fs.S3FileSystem(anon=aws_unsigned) 
        configure_s3_access(cloud_defaults=True, aws_unsigned=aws_unsigned)
        tiles_list = fs.glob(tiles_pattern)
    else:
        tiles_list = glob.glob(tiles_pattern, recursive=True)

    if list_tiles:
        xy_patterns = []
        for xy in list_tiles:
            xy_patterns.append(xy.replace('y','/y')) # i.e. from 'x25y41' to 'x25/y41'
        
        filtered_tiles = []
        for tile in tiles_list:
            if any(xy_pattern in tile for xy_pattern in xy_patterns):
                filtered_tiles.append(tile)

        tiles_list = filtered_tiles
        

    return tiles_list


def _get_vsicurlhttp_from_s3(s3_url):
    """
    Convert an S3 URL to a GDAL-compatible /vsicurl/ HTTPS path.
    """
    
    if "dea-public-data-dev/" in s3_url:
        return s3_url.replace(
            "dea-public-data-dev/",
            "/vsicurl/https://dea-public-data-dev.s3-ap-southeast-2.amazonaws.com/"
        )
    elif "dea-public-data/" in s3_url:
        return s3_url.replace(
            "dea-public-data/",
            "/vsicurl/https://data.dea.ga.gov.au/"
        )
    else:
        raise ValueError(f"Unexpected S3 URL structure: {s3_url}")



def make_cog_mosaics(
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
    compression_lvl,
    aws_unsigned,
    skip_existing,
    list_tiles = None,
):
    """
    Generate a COG mosaic for a given DEA tiles product.

    Parameters:
    ----------
    product : str
        The name of the DEA product (e.g., 'ga_ls_landcover_class_cyear_3').
    band : str
        The variable or band to extract.
    time : int or str
        The target time of the mosaic, year if annual summaries (e.g., 2023),
        year-month for seasonal (e.g., water observations nov_mar --> '2024-11')
    freq : str
        The frequency of the summary product (e.g.,P1Y).
    version : str
        Product version (e.g., '2-0-0').  
    dataset_maturity : str
        Dataset maturity stage. Usually: 'final'.        
    product_dir : str
        S3 directory for the product. Usually 's3://dea-public-data/derivative/',
        which is the DEA public bucket and derivates products folder,
        which corresponds with https://data.dea.ga.gov.au/derivative/ HTTPS endpoint. 
    output_dir : str
        local directory or s3 directory where to save ouptut. 
    cog_blocksize : int or str
        Size of COG tiles.
        Use 1024, unless there are specific reasons to use a different value.
    overview_count : int or str
        Number of image overviews to generate.
        Use 7 for 30m resolution products (like Landsat),
        use 8 for 10m resolution products (like Sentinel-2).
    overview_resampling : str
        gdal_translate resampling method used when building overviews. Use all capital letters
        - 'MODE' for categorical data (e.g., land cover),
        - 'BILINEAR' for continuous data,
        - 'NEAREST' for "narrow" continuos data with many no-data pixels (e.g., coastal products).
    compression_algo : str
        gdal_translate resampling algorithm. 
        Use 'ZSTD', unless there are specific reasons to use a different algorithm.
    compression_lvl : int or str
        Level of compression of output COG
        Use 9, unless there are specific reasons to use a different level.
    aws_unsigned : bool
        Whether to sign AWS requests for S3 access
    skip_existing : bool
        Wheter to skip generation if output already exists.
    list_tiles : list of strings
        List including tiles of interest to include in the output mosaic.
        For example: ['x25y41','x25y41'].
        Defaults to None --> use all tiles available.

    Notes:
    ------
    All other `gdal_translate` parameters
    are intentionally omitted in this function.
    These options should be standardized across all products,
    and are applied consistently as part of downstream processing.
    """

    # first log
    log = logging.getLogger(__name__)
    input_params = locals()
    run_id = f"[{product}] [{version}] [{time}] [{band}]"
    log.info(f"{run_id}: Using parameters {input_params}")

    # determine if input data is located on S3
    is_input_dir_s3 = _is_s3(product_dir)

    # Clean string to prepare for analysis
    product_dir = product_dir.replace("s3://", "")
    product_dir = product_dir.rstrip("/")
    log.info(f"{run_id}: Using input data product directory: {product_dir}")

    # Determine output directory and file path following naming convention
    # /derivative/<product_id>/<version>/continental_mosaics/<time>/<product_id>_mosaic_<time>_<band name>.tif
    output_dir = output_dir.rstrip("/")
    if _is_s3(output_dir):
        output_dir = f"{output_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        output_file_path = f"{output_dir}/{product}_mosaic_{time}--{freq}_{band}.tif"
        log.info(f"{run_id} - Output path: {output_file_path}")
    else:
        output_dir = os.path.join(output_dir, product, version, "continental_mosaics", f"{time}--{freq}")
        output_file_path = os.path.join(output_dir, f"{product}_mosaic_{time}--{freq}_{band}.tif")
        log.info(f"{run_id} - Output path: {output_file_path}")

    # check if output file already exists
    output_exists = False
    if _is_s3(output_file_path):
        fs = s3fs.S3FileSystem(anon=aws_unsigned)
        output_exists = fs.exists(output_file_path.replace("s3://", ""))
    else:
        output_exists = os.path.exists(output_file_path)

    if output_exists:
        if skip_existing:
            log.info(f"{run_id}: Output already exists at {output_file_path} and skip_existing=True. Skipping generation.")
            return
        else:
            log.warning(f"{run_id}: Output already exists at {output_file_path} but skip_existing=False. Overwriting.")
    else:
        log.info(f"{run_id}: Output does not exist. Proceeding with mosaic generation.")

    # get list of paths to tiles
    tiles_list = _get_tiles(product_dir, product,version, time, freq,dataset_maturity, band, is_input_dir_s3, aws_unsigned, list_tiles)
    
    # use /vsicurl/ path for `gdalbuildvrt` compatibility
    tiles_list = [_get_vsicurlhttp_from_s3(tile) for tile in tiles_list]
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
            
            # build VRT
            log.info(f"{run_id}: Building virtual raster (VRT)")
            try:
                subprocess.run(
                    ["gdalbuildvrt", vrt_name, "-input_file_list", file_list_name],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                log.error(f"{run_id}: gdalbuildvrt failed with error: {e}")
                raise

            # convert VRT to Cloud Optimized GeoTIFF (COG)
            log.info(f"{run_id}: Converting VRT to COG mosaic")
            try:
                subprocess.run(
                    [
                        "gdal_translate",
                        vrt_name,
                        output_name,
                        "-co", "NUM_THREADS=ALL_CPUS",                    # Parallelisation
                        "-of", "COG",                                     # Output format
                        "-co", "BIGTIFF=YES",                             # Allow large TIFFs
                        "-co", f"BLOCKSIZE={cog_blocksize}",              # Tiling
                        "-co", "OVERVIEWS=IGNORE_EXISTING",               # Force overview regen
                        "-co", f"OVERVIEW_RESAMPLING={overview_resampling}",# Resampling for overviews
                        "-co", f"OVERVIEW_COUNT={overview_count}",        # Number of overviews
                        "-co", f"COMPRESS={compression_algo}",            # Compression
                        "-co", f"LEVEL={compression_lvl}",                # Compression level
                        "-co", "PREDICTOR=YES",                           # Compression predictor
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                log.error(f"{run_id}: gdal_translate failed with error: {e}")
                raise

            # Copy output to S3
            if _is_s3(output_file_path):
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

            else: # copy locally to output folder
                os.makedirs(output_dir, exist_ok=True)
                log.info(f"{run_id}: Writing data locally: {output_file_path}")
                shutil.copy(output_name, output_file_path)

    else:
        log.info(f"{run_id}: No input tiles found")


@click.command()
@click.option(
    "--product",
    type=str,
    required=True,
    help="The name of the product to be mosaicked (e.g., 'ga_ls_landcover_class_cyear_3')."
)
@click.option(
    "--band",
    type=str,
    required=True,
    help="The variable or band to extract (e.g., 'level4')"
)
@click.option(
    "--time",
    type=str,
    required=True,
    help="The target time of the mosaic (e.g., '2022')."
)
@click.option(
    "--freq",
    type=str,
    required=True,
    help="The frequency of the summary product (e.g., 'P1Y')."
)
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version number of the product (e.g., '2-0-0')."
)
@click.option(
    "--dataset_maturity",
    type=str,
    default="final",
    show_default=True,
    help="Dataset maturity of the data to be mosaicked. Usually: 'final'."
)
@click.option(
    "--product_dir",
    type=str,
    default="s3://dea-public-data-dev/derivative/",
    show_default=True,
    help="The directory/location to read the tile COGs from; supports "
    "both local disk and S3 locations. E.g. 's3://dea-public-data/derivative/', "
    "corresponding to https://data.dea.ga.gov.au/derivative/."
)
@click.option(
    "--output_dir",
    type=str,
    required=True,
    help="Local or S3 directory where to save output. "
    "The function will add on `{product}/{version}/continental_mosaics/{time}--{freq}` "
)
@click.option(
    "--cog_blocksize",
    type=int,
    default=1024,
    show_default=True,
    help="Size of COG tiles."
         "Use 1024, unless there are specific reasons to use a different value."
)
@click.option(
    "--overview_count",
    type=int,
    required=True,
    help="Number of image overviews to generate. "
         "Use 7 for 30m resolution products (e.g., Landsat), "
         "or 8 for 10m resolution products (e.g., Sentinel-2)."
)
@click.option(
    "--overview_resampling",
    type=str,
    required=True,
    help="GDAL resampling method used for overviews. Use uppercase values: "
         "'MODE' for categorical data (e.g., land cover), "
         "'BILINEAR' for continuous data, "
         "'NEAREST' for sparse/narrow continuous data."
)
@click.option(
    "--compression_algo",
    type=str,
    default="ZSTD",
    show_default=True,
    help="gdal_translate resampling algorithm."
         "Use 'ZSTD', unless there are specific reasons to use a different algorithm."
)
@click.option(
    "--compression_lvl",
    type=int,
    default=9,
    show_default=True,
    help="Level of compression of output COG"
         "Use '9', unless there are specific reasons to use a different level."
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
    help="Skip generation if output already exists."
    "Defaults to False"
)
@click.option(
    "--list_tiles",
    type=str,
    required=False,
     help="Comma-separated list of tiles to include in the mosaic. Example: x25y41,x26y42. "
    "If omitted, all tiles will be used."
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
    compression_lvl,
    aws_unsigned,
    skip_existing,
    list_tiles=None,
):
    """
    CLI entry point for generating DEA COG mosaics from tiled datasets.
    Passes user inputs to the core mosaic generation function.
    """
    
    make_cog_mosaics(
        product, band, time, freq, version, dataset_maturity,
        product_dir, output_dir, cog_blocksize, overview_count,
        overview_resampling, compression_algo, compression_lvl,
        aws_unsigned, skip_existing, list_tiles
    )

if __name__ == "__main__":
    make_cog_mosaic_cli()