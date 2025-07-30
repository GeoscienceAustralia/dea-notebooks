# vrt.py
"""
Tools for applying colour schemes and generating GDAL VRTs for mosaics of
Digital Earth Australia (DEA) products, including single-band categorical
visualisations and three-band composites (e.g., RGB for true or false colour imagery).

In case of categorical data, colour schemes are loaded from JSON files
containing RGBA values and labels. The module supports DEA’s mosaic output
structure and naming conventions and can operate on mosaic files stored
locally or in the cloud (AWS's S3).

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


import json
import logging
import os
import shutil
import subprocess
import tempfile
import xml.dom.minidom
import xml.etree.ElementTree as ET

import click
import requests

from dea_tools.mosaics.utils import _is_s3, _file_exists_s3, _get_vsicurlhttp_from_s3, _clean_label_dict
from dea_tools.mosaics.styling import lc_styling


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _get_lc_colour_scheme(band, style_json_path=None):
    """
    Load land cover colour scheme dictionary and clean labels for use.
    
    Use style_json_path if needed to employ a colour scheme that 
    is external to dea-tools.
    """

    if style_json_path:
        with open(style_json_path, "r") as f:
            colour_dict = json.load(f)  
            # Convert keys to integers
            colour_dict = {int(k): v for k, v in colour_dict.items()}

    else:
        colour_dict = lc_styling[f"lc_{band}_colours"]

    colour_dict_cleaned = {}
    for key, value in colour_dict.items():
        r, g, b, a, label = value
        label = _clean_label_dict(label)
        colour_dict_cleaned[key] = (r, g, b, a, label)

    return colour_dict_cleaned


def _create_vrt_landcover(
    product,
    version,
    band,
    time,
    freq,
    cog_dir,
    output_dir,
    style_json_path=None,
):
    """
    Create a land cover VRT with colour scheme from COG input.

    Builds a VRT from a land cover mosaic, embeds colour palette,
    and saves output locally or to S3.

    The COG path in the VRT will relative to the VRT location for
    local COG directories, and absolute S3 paths for COGs on S3.
    """

    # first log
    log = logging.getLogger(__name__)
    input_params = locals()
    run_id = f"[{product}] [{version}] [{time}] [{band}]"
    log.info(
        f"Creating colour VRTs for Land Cover {run_id}: Using parameters {input_params}"
    )

    # Determine if COG or output directories are located on S3
    is_cog_dir_s3 = _is_s3(cog_dir)
    is_out_dir_s3 = _is_s3(output_dir)

    # get rgb of land cover classification values as a dictionary
    rgb_values = _get_lc_colour_scheme(band, style_json_path)

    # get input continental COG path
    cog_dir = cog_dir.rstrip("/")

    if is_cog_dir_s3:
        cog_dir = cog_dir.replace("s3://", "")
        cog_dir = cog_dir.rstrip("/")
        cog_dir = _get_vsicurlhttp_from_s3(cog_dir)

        cog_dir = f"{cog_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        input_path = f"{cog_dir}/{product}_mosaic_{time}--{freq}_{band}.tif"
        if _file_exists_s3(input_path):
            log.info(f"{run_id}: Identifying input data from S3 bucket: {input_path}")
        else:
            log.info(f"{run_id}: No COG input found")
            return
    else:
        cog_dir = os.path.join(
            cog_dir, product, version, "continental_mosaics", f"{time}--{freq}"
        )
        input_path = os.path.join(
            cog_dir, f"{product}_mosaic_{time}--{freq}_{band}.tif"
        )
        if os.path.exists(input_path):
            log.info(
                f"{run_id}: Identifying input data from local file system: {input_path}"
            )
        else:
            log.info(f"{run_id}: No COG input found")
            return

    # define ouptut VRT name following the standardised naming:
    # /derivative/<product_id>/<version>/continental_mosaics/<time>/<product_id>_mosaic_<time>_<VRT name>.vrt
    output_dir = output_dir.rstrip("/")
    if is_out_dir_s3:
        output_dir = (
            f"{output_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        )
        output_vrt = f"{output_dir}/{product}_mosaic_{time}--{freq}_{band}.vrt"
        log.info(f"{run_id} - Output path: {output_vrt}")
    else:
        output_dir = os.path.join(
            output_dir, product, version, "continental_mosaics", f"{time}--{freq}"
        )
        output_vrt = os.path.join(
            output_dir, f"{product}_mosaic_{time}--{freq}_{band}.vrt"
        )
        log.info(f"{run_id} - Output path: {output_vrt}")

    # Create a temporary directory to house files before syncing
    with tempfile.TemporaryDirectory() as temp_dir:
        log.info(f"{run_id}: Writing data to temporary folder: {temp_dir}")

        # Output paths for intermediate files
        temp_output_vrt = os.path.join(
            temp_dir, f"{product}_mosaic_{time}--{freq}_{band}.vrt"
        )

        # build base VRT
        try:
            subprocess.run(["gdalbuildvrt", temp_output_vrt, input_path], check=True)
        except subprocess.CalledProcessError as e:
            log.error(f"{run_id}: gdalbuildvrt failed with error: {e}")
            raise

        # modify the VRT XML
        log.info(f"{run_id}: Adding colour scheme to VRT")

        tree = ET.parse(temp_output_vrt)
        root = tree.getroot()

        # If COGs are not on S3, modify all <SourceFilename> elements to
        # keep only the filename (relative path)
        if not is_cog_dir_s3:
            for src in root.findall(".//SourceFilename"):
                full_path = src.text
                filename = os.path.basename(full_path)
                src.text = filename
                src.set("relativeToVRT", "1")

        band_node = root.find("VRTRasterBand")

        # insert ColorInterp
        interp = ET.SubElement(band_node, "ColorInterp")
        interp.text = "Palette"

        # add ColorTable
        color_table = ET.SubElement(band_node, "ColorTable")
        for i in range(256):
            if i in rgb_values:
                r, g, b, a, _ = rgb_values[i]
            else:
                r, g, b, a = 255, 255, 255, 0
            ET.SubElement(
                color_table,
                "Entry",
                {"c1": str(r), "c2": str(g), "c3": str(b), "c4": str(a)},
            )

        # add CategoryNames
        cat_names = ET.SubElement(band_node, "CategoryNames")
        for i in range(256):
            label = rgb_values[i][4] if i in rgb_values else "NA"
            ET.SubElement(cat_names, "Category").text = label

        # make xml more readable
        xml_str = ET.tostring(root, encoding="utf-8")
        formatted_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

        # remove overviews because they are already included in COGs
        filtered_lines = []
        for line in formatted_xml.splitlines():
            if "OverviewList resampling" not in line:
                filtered_lines.append(line)
        cleaned_xml = "\n".join(filtered_lines)

        with open(temp_output_vrt, "w", encoding="utf-8") as f:
            f.write(cleaned_xml)

        if is_out_dir_s3:  # Copy output to S3
            log.info(f"{run_id}: Writing VRT to S3: {output_vrt}")

            subprocess.run(
                [
                    "aws",
                    "s3",
                    "cp",
                    "--only-show-errors",
                    "--acl",
                    "bucket-owner-full-control",
                    str(temp_output_vrt),
                    str(output_vrt),
                ],
                check=True,
            )

        else:  # copy locally to output folder
            os.makedirs(
                os.path.dirname(output_vrt), exist_ok=True
            )  # technically it should always exist as it's the same of the continental COG
            log.info(f"{run_id}: Writing data locally: {output_vrt}")
            shutil.copy(temp_output_vrt, output_vrt)


def _create_vrt_3bands_comp(
    product,
    version,
    time,
    freq,
    cog_dir,
    output_dir,
    r_channel_band,
    g_channel_band,
    b_channel_band,
    vrt_name=None,
):
    """
    Create a three-band composite VRT from separate band COGs.

    Builds a multi-band VRT using specified red, green, and blue channels,
    and writes output locally or to S3.

    The COG path in the VRT will relative to the VRT location for
    local COG directories, and absolute S3 paths for COGs on S3.
    """

    # first log
    log = logging.getLogger(__name__)
    input_params = locals()
    run_id = f"[{product}] [{version}] [{time}] [{r_channel_band}] [{g_channel_band}] [{b_channel_band}]"
    log.info(
        f"Creating colour VRTs for Geomedian {run_id}: Using parameters {input_params}"
    )

    # Determine if COG or output directories are located on S3
    is_cog_dir_s3 = _is_s3(cog_dir)
    is_out_dir_s3 = _is_s3(output_dir)

    if is_cog_dir_s3:
        cog_dir = cog_dir.replace("s3://", "")
        cog_dir = cog_dir.rstrip("/")
        cog_dir = _get_vsicurlhttp_from_s3(cog_dir)

        cog_dir = f"{cog_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        input_path_r = f"{cog_dir}/{product}_mosaic_{time}--{freq}_{r_channel_band}.tif"
        input_path_g = f"{cog_dir}/{product}_mosaic_{time}--{freq}_{g_channel_band}.tif"
        input_path_b = f"{cog_dir}/{product}_mosaic_{time}--{freq}_{b_channel_band}.tif"

        if all(
            [
                _file_exists_s3(input_path_r),
                _file_exists_s3(input_path_g),
                _file_exists_s3(input_path_b),
            ]
        ):
            log.info(
                f"{run_id}: Identifying input data from S3 bucket:\n-{input_path_r}\n-{input_path_g}\n-{input_path_b}"
            )
        else:
            log.info(f"{run_id}: One or more input COGs not found")
            return
    else:
        cog_dir = os.path.join(
            cog_dir, product, version, "continental_mosaics", f"{time}--{freq}"
        )
        input_path_r = os.path.join(
            cog_dir, f"{product}_mosaic_{time}--{freq}_{r_channel_band}.tif"
        )
        input_path_g = os.path.join(
            cog_dir, f"{product}_mosaic_{time}--{freq}_{g_channel_band}.tif"
        )
        input_path_b = os.path.join(
            cog_dir, f"{product}_mosaic_{time}--{freq}_{b_channel_band}.tif"
        )
        if all(
            [
                os.path.exists(input_path_r),
                os.path.exists(input_path_g),
                os.path.exists(input_path_b),
            ]
        ):
            log.info(
                f"{run_id}: Identifying input data from local file system:\n-{input_path_r}\n-{input_path_g}\n-{input_path_b}"
            )
        else:
            log.info(f"{run_id}: One or more input COGs not found in local filesystem")
            return

    # define output VRT name following the standardised naming:
    # /derivative/<product_id>/<version>/continental_mosaics/<time>/<product_id>_mosaic_<time>_<VRT name>.vrt
    output_dir = output_dir.rstrip("/")
    vrt_name = (
        vrt_name if vrt_name else f"{r_channel_band}-{g_channel_band}-{b_channel_band}"
    )
    if is_out_dir_s3:
        output_dir = (
            f"{output_dir}/{product}/{version}/continental_mosaics/{time}--{freq}"
        )
        output_vrt = f"{output_dir}/{product}_mosaic_{time}--{freq}_{vrt_name}.vrt"
        log.info(f"{run_id} - Output path: {output_vrt}")
    else:
        output_dir = os.path.join(
            output_dir, product, version, "continental_mosaics", f"{time}--{freq}"
        )
        output_vrt = os.path.join(
            output_dir, f"{product}_mosaic_{time}--{freq}_{vrt_name}.vrt"
        )
        log.info(f"{run_id} - Output path: {output_vrt}")

    # Create a temporary directory to house files before syncing
    with tempfile.TemporaryDirectory() as temp_dir:
        log.info(f"{run_id}: Writing data to temporary folder: {temp_dir}")

        # Output paths for intermediate files
        temp_output_vrt = os.path.join(
            temp_dir,
            f"{product}_mosaic_{time}--{freq}_{r_channel_band}-{g_channel_band}-{b_channel_band}.vrt",
        )

        # build VRT with RGB bands
        try:
            subprocess.run(
                [
                    "gdalbuildvrt",
                    "-separate",
                    temp_output_vrt,
                    input_path_r,
                    input_path_g,
                    input_path_b,
                ],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            log.error(f"{run_id}: gdalbuildvrt failed with error: {e}")
            raise

        # modify the VRT XML
        tree = ET.parse(temp_output_vrt)
        root = tree.getroot()

        # If COGs are not on S3, modify all <SourceFilename> elements to
        # keep only the filename (relative path)
        if not is_cog_dir_s3:
            for src in root.findall(".//SourceFilename"):
                full_path = src.text
                filename = os.path.basename(full_path)
                src.text = filename
                src.set("relativeToVRT", "1")

        # make xml more readable
        xml_str = ET.tostring(root, encoding="utf-8")
        formatted_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

        # remove overviews as they are already in COGs
        filtered_lines = []
        for line in formatted_xml.splitlines():
            if "OverviewList resampling" not in line:
                filtered_lines.append(line)
        cleaned_xml = "\n".join(filtered_lines)

        # save modified VRT
        with open(temp_output_vrt, "w", encoding="utf-8") as f:
            f.write(cleaned_xml)

        if is_out_dir_s3:  # Copy output to S3
            log.info(f"{run_id}: Writing VRT to S3: {output_vrt}")

            subprocess.run(
                [
                    "aws",
                    "s3",
                    "cp",
                    "--only-show-errors",
                    "--acl",
                    "bucket-owner-full-control",
                    str(temp_output_vrt),
                    str(output_vrt),
                ],
                check=True,
            )

        else:  # copy locally to output folder
            os.makedirs(
                os.path.dirname(output_vrt), exist_ok=True
            )  # technically it should always exist as it's the same of the continental COG
            log.info(f"{run_id}: Writing data locally: {output_vrt}")
            shutil.copy(temp_output_vrt, output_vrt)


def make_styling_vrt(
    product,
    version,
    time,
    freq,
    cog_dir,
    output_dir,
    band=None,
    style_json_path=None,
    r_channel_band=None,
    g_channel_band=None,
    b_channel_band=None,
    vrt_name=None,
):
    """
    Create a virtual raster (VRT) for DEA products.

    If a single categorical band is specified, creates a categorical VRT with color scheme.
    If red, green, and blue bands are all provided, creates a three-band composite VRT.
    Raises error if input combinations are invalid.

    Parameters:
    -----------
    product : str
        DEA product name (e.g. 'ga_ls_landcover_class_cyear_3').
    version : str
        Product version (e.g. '2-0-0').
    time : int or str
        The target time of the mosaic, year if annual summaries (e.g. 2023),
        year-month for seasonal (e.g., water observations nov_mar --> '2024-11')
    freq : str
        The frequency of the summary product (e.g. P1Y).
    cog_dir : str
        Path to directory with continental COG. E.g. 's3://dea-public-data/derivative/'
    output_dir : str
        Local directory or s3 directory where to save ouptut.
    band : str, optional
        Band name (e.g. 'level4').
        Use None (default) if need a three-bands composite
    style_json_path : str, optional
        Path to json file containing custom colour schemes.
        The json file should be structured as a dictionary with 
        integer or string values as keys and [R,G,B,A,label] as values. 
        E.g. {"1":[255,255,255,0,"NA"]} for assigning a white colour 
        and "NA" label to raster values equal to 1.
        Use None (default) for using the default schemes in dea-tools.
    r_channel_band : str, optional
        Band to use in the RED channel for a three-bands composite.
        Use None (default) if need a single-band categorical view
    g_channel_band : str
        Band to use in the GREEN channel for a three-bands composite.
        Use None (default) if need a single-band categorical view
    b_channel_band : str, optional
        Band to use in the BLUE channel for a three-bands composite.
        Use None (default) if need a single-band categorical view
    vrt_name : str, optional
        An optional name used for the output VRT. If not provided,
        will default to {r_channel_band}-{g_channel_band}-{b_channel_band}.,
    """
    # Set product and output paths to plain strings
    # TODO: refactor code to use pathlib throughout
    cog_dir = str(cog_dir)
    output_dir = str(output_dir)

    if product == "ga_ls_landcover_class_cyear_3" and band:
        _create_vrt_landcover(
            product,
            version,
            band,
            time,
            freq,
            cog_dir,
            output_dir,
            style_json_path,
        )

    elif all([r_channel_band, g_channel_band, b_channel_band]):
        _create_vrt_3bands_comp(
            product,
            version,
            time,
            freq,
            cog_dir,
            output_dir,
            r_channel_band,
            g_channel_band,
            b_channel_band,
            vrt_name,
        )

    else:
        log = logging.getLogger(__name__)
        log.error(
            "INPUT ERROR: make sure product exists."
            "Define either --band for categorical single-band data, "
            "or ALL r g b channel bands for composites."
        )
        raise ValueError("Invalid input combination for VRT creation.")


@click.command()
@click.option(
    "--product",
    type=str,
    required=True,
    help="The name of the product to add colour to (e.g., 'ga_ls_landcover_class_cyear_3').",
)
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version number of the product (e.g., '2-0-0').",
)
@click.option("--time", type=str, required=True, help="The target time (e.g., '2022').")
@click.option(
    "--freq",
    type=str,
    required=True,
    help="The frequency of the summary product (e.g., 'P1Y').",
)
@click.option(
    "--cog_dir",
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
    "--band",
    type=str,
    required=False,
    help="The categorical data band to add the colour to (e.g., 'level4')",
)
@click.option(
    "--style_json_path",
    type=str,
    required=False,
    help="Path to json file containing custom colour schemes. "
    "The json file should be structured as a dictionary with "
    "integer or string values as keys and [R,G,B,A,label] as values. "
    "E.g. {'1':[255,255,255,0,'NA']} for assigning a white colour "
    "and 'NA' label to raster values equal to 1. "
    "Do not include this input if want to use the default schemes in dea-tools",
)
@click.option(
    "--r_channel_band",
    type=str,
    required=False,
    help="Band to use in the RED channel for RGB composite (e.g., 'nbart_red')",
)
@click.option(
    "--g_channel_band",
    type=str,
    required=False,
    help="Band to use in the GREEN channel for RGB composite e.g., 'nbart_green')",
)
@click.option(
    "--b_channel_band",
    type=str,
    required=False,
    help="Band to use in the BLUE channel for RGB composite e.g., 'nbart_blue')",
)
@click.option(
    "--vrt_name",
    type=str,
    required=False,
    help="An optional name used for the output three-band VRT. "
    "If not provided, will default to {r_channel_band}-{g_channel_band}-{b_channel_band}.",
)
def make_styling_vrt_cli(
    product,
    version,
    time,
    freq,
    cog_dir,
    output_dir,
    band=None,
    style_json_path=None,
    r_channel_band=None,
    g_channel_band=None,
    b_channel_band=None,
    vrt_name=None,
):
    """
    CLI entry point for creating VRT files with color schemes or composites.
    Passes user parameters to the main VRT creation function.
    """

    make_styling_vrt(
        product,
        version,
        time,
        freq,
        cog_dir,
        output_dir,
        band,
        style_json_path,
        r_channel_band,
        g_channel_band,
        b_channel_band,
        vrt_name,
    )


if __name__ == "__main__":
    make_styling_vrt_cli()