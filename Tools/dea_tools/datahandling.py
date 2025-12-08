# datahandling.py
"""
Loading and manipulating Digital Earth Australia products and data
using the Open Data Cube and xarray.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one
on GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: December 2025
"""

from datetime import datetime, timezone

# Import required packages
import os
import warnings
import zipfile
from collections import Counter

import requests
import yaml
from yaml.loader import SafeLoader

import odc.stac
import pystac_client
import numpy as np
import odc.algo
import odc.geo.xr
import pandas as pd
import requests
import rioxarray
import sklearn.decomposition
import xarray as xr
from odc.algo import mask_cleanup
from odc.geo import BoundingBox
from scipy.ndimage import binary_dilation
from skimage.color import hsv2rgb, rgb2hsv
from skimage.exposure import match_histograms

from dea_tools.sar import apply_lee_filter

# Valid ARD product groups
VALID_PRODUCTS = {
    "ls": ["ga_ls5t_ard_3", "ga_ls7e_ard_3", "ga_ls8c_ard_3", "ga_ls9c_ard_3"],
    "s2": ["ga_s2am_ard_3", "ga_s2bm_ard_3", "ga_s2cm_ard_3"],
    # "s1": ["ga_s1_nrb_iw_vv_vh_0", "ga_s1_nrb_iw_hh_0", "ga_s1_nrb_iw_vv_0"],
}

# Landsat 7 cutoff date
LS7_CUTOFF = datetime(2003, 5, 31, tzinfo=timezone.utc)

# Custom flag defs
FLAGS_DEFINITIONS = {
    "oa_fmask": {
        "fmask": {
            "bits": [0, 1, 2, 3, 4, 5, 6, 7],
            "values": {
                "0": "nodata",
                "1": "valid",
                "2": "cloud",
                "3": "shadow",
                "4": "snow",
                "5": "water",
            },
            "description": "Fmask",
        }
    },
    "oa_s2cloudless_mask": {
        "s2cloudless_mask": {
            "bits": [0, 1, 2],
            "values": {
                "0": "nodata",
                "1": "valid",
                "2": "cloud",
            },
            "description": "s2cloudless mask",
        }
    },
}


def dea_stac_cfg(products: str | list) -> dict:
    """
    Create a STAC configuration dictionary for one or more DEA products.

    This function generates a configuration containing important
    attributes that are often missing from DEA's STAC metadata.
    The resulting dictionary can be passed directly to the
    `odc.stac.load` function via the `stac_cfg` parameter.

    The function reads DEA product definition YAML from DEA
    Explorer, and builds a dictionary containing:

    - Each band's data type (`dtype`)
    - Nodata values
    - Unit attributes
    - Band aliases

    Based on the `get_product_config` function from DE Africa Tools:
    https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/blob/main/Tools/deafrica_tools/get_config.py

    Parameters
    ----------
    products : str or list
        A Digital Earth Australia product ID (i.e. STAC collection)
        or list of product IDs.

    Returns
    -------
    dict
        A dictionary containing each product's pixel data type, nodata
        value, unit attribute, and band aliases.
    """
    # Convert product to a list if a single product string is provided
    if isinstance(products, str):
        products = [products]

    # Empty stac_cfg dictionary
    stac_cfg = {}

    # Iterate over each product
    for product in products:

        # Create URL for product
        url = f"https://explorer.dea.ga.gov.au/products/{product}.odc-product.yaml"

        # Download and parse the YAML file
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            raise ValueError(f"Invalid DEA product: '{product}'")

        product_def = yaml.load(resp.text, Loader=SafeLoader)

        # Build assets dictionary containing dtype, unit, nodata for each band
        assets = {
            m["name"]: {
                "data_type": m["dtype"],
                "unit": m["units"],
                "nodata": m["nodata"],
            }
            for m in product_def.get("measurements", [])
        }

        # Build alias dictionary
        aliases = {
            alias: m["name"]
            for m in product_def.get("measurements", [])
            for alias in m.get("aliases", [])
        }

        # Assemble config dictionary for product
        config = {"assets": assets}
        if aliases:
            config["aliases"] = aliases

        # Add to main stac_cfg dictionary
        stac_cfg[product] = config

    return stac_cfg


def _dc_query_only(**kw):
    """
    Remove load-only datacube parameters, the rest can be
    passed to Query/dc.find_datasets.

    Returns
    -------
    dict of query parameters
    """

    def _impl(
        measurements=None,
        output_crs=None,
        resolution=None,
        resampling=None,
        skip_broken_datasets=None,
        dask_chunks=None,
        fuse_func=None,
        align=None,
        datasets=None,
        progress_cbk=None,
        group_by=None,
        **query,
    ):
        return query

    return _impl(**kw)


def _stac_query_load(kwargs: dict) -> tuple[dict, dict]:
    """
    Split ``load_ard`` keyword arguments into query and load parameters.

    Also handles the consistent creation of a EPSG:4326 query
    bounding box used to search for data using `pystac_client.

    Parameters
    ----------
    kwargs : dict
        Keyword arguments passed through from ``load_ard``.

    Returns
    -------
    tuple
        A dictionary of query parameters (to pass to ``pystac_client``)
        and load parameters (to pass to ``odc-stac``).
    """

    # List of all valid odc.stac.load parameters
    valid_load_params = (
        "anchor",
        "bands",
        "bbox",
        "chunks",
        "crs",
        "driver",
        "dtype",
        "fail_on_error",
        "fuse_func",
        "geobox",
        "geopolygon",
        "groupby",
        "intersects",
        "kw",
        "lat",
        "lon",
        "like",
        "nodata",
        "patch_url",
        "pool",
        "preserve_original_order",
        "progress",
        "resampling",
        "resolution",
        "stac_cfg",
        "x",
        "y",
    )

    # Split out
    load_params = {k: v for k, v in kwargs.items() if k in valid_load_params}
    query_params = {k: v for k, v in kwargs.items() if k not in valid_load_params}

    # If a bounding box is provided, use directly
    if "bbox" in kwargs:
        query_params["bbox"] = kwargs["bbox"].to_crs("EPSG:4326")
        load_params["bbox"] = kwargs["bbox"]

    # If lon/lat are provided, convert to a bbox for querying
    elif "lon" in kwargs and "lat" in kwargs:
        query_params["bbox"] = BoundingBox.from_xy(
            x=kwargs["lon"], y=kwargs["lat"], crs="EPSG:4326"
        ).to_crs("EPSG:4326")

    # If x/y are provided, convert to bbox for querying
    # Use provided CRS if it exists, but convert to EPSG:4326 for querying
    elif "x" in kwargs and "y" in kwargs:
        crs = kwargs.get("crs", "EPSG:4326")
        query_params["bbox"] = BoundingBox.from_xy(
            x=kwargs["x"], y=kwargs["y"], crs=crs
        ).to_crs("EPSG:4326")

    # If a geobox is provided, convert to bbox for querying
    elif "geobox" in kwargs:
        query_params["bbox"] = kwargs["geobox"].boundingbox.to_crs("EPSG:4326")

    # If a dataset is provided via "like", convert to bbox for querying
    elif "like" in kwargs:
        query_params["bbox"] = kwargs["like"].odc.geobox.boundingbox.to_crs("EPSG:4326")

    # If a geopolygon is provided, pass actual geometry to "intersects" for querying
    elif "geopolygon" in kwargs:
        geopolygon = odc.stac._mdtools._normalize_geometry(kwargs["geopolygon"])
        query_params["intersects"] = geopolygon.to_crs("EPSG:4326")

    return query_params, load_params


def _common_bands(product_cfg: dict) -> tuple[dict, dict]:
    """
    Return a list of measurements/bands that are present in all products

    Returns
    -------
    List of band names
    """
    # Get sets of unique bands for each product
    asset_sets = [set(prod["assets"]) for prod in product_cfg.values()]

    # Find assets shared across all products
    return list(set.intersection(*asset_sets))


def _contiguity_fuser(dst: np.ndarray, src: np.ndarray) -> None:
    """
    Ensure contiguity data is properly combined by replacing
    pixels in `dst` that are either 0 (non-contiguous) or 255
    (nodata) with the corresponding value from `src`, propogating
    1 (valid contiguous data) if it exists.
    """
    np.copyto(dst, src, where=np.isin(dst, (255, 0)))


def _validate_ard_products(products: list[str]) -> str:
    """
    Validate and classify a list of Landsat, Sentinel-2,
    or Sentinel-1 products provided to `load_ard`.

    Parameters
    ----------
    products : list of str
        Product names to validate.

    Returns
    -------
    str
        One of "ls", "s2", "s1", "mixed".
    """
    # Valid products
    valid_products = {k: set(v) for k, v in VALID_PRODUCTS.items()}
    all_valid = {p for group in valid_products.values() for p in group}

    # Raise error if None or empty list of products is provided
    if products is None or products == []:
        raise ValueError(
            "Please pass a list of Landsat, Sentinel-2, or Sentinel-1 "
            f"Analysis Ready Data product names to `products`. Valid options are: {sorted(all_valid)}."
        )

    # Convert supported products to sets for easy validation
    input_products = set(products)

    # Validate all provided products
    invalid = [p for p in products if p not in all_valid]
    if invalid:
        raise ValueError(
            f"Invalid products: {sorted(invalid)}. Valid options are: {sorted(all_valid)}."
        )
    if input_products.issubset(valid_products["ls"]):
        return "ls"
    if input_products.issubset(valid_products["s2"]):
        return "s2"
    # if input_products.issubset(valid_products["s1"]):
    #     return "s1"
    if input_products.issubset(valid_products["ls"] | valid_products["s2"]):
        warnings.warn(
            "You have selected both Landsat and Sentinel-2 products. "
            "This can produce unexpected results as these products use "
            "the same names for different spectral bands (e.g. "
            "Landsat and Sentinel-2's 'nbart_swir_2'); use with caution."
        )
        return "mixed"

    # Catch combination of Sentinel-1 and optical sensors
    raise ValueError(
        "Loading a combination of Landsat/Sentinel-2 and Sentinel-1 products is not currently supported."
    )


def _configure_masking(
    cloud_mask: str,
    mask_contiguity: str | bool,
    fmask_categories: list[str],
    s2cloudless_categories: list[str],
    s1_mask_categories: list[str],
    product_type: str,
) -> tuple[str, list[str], str]:
    """
    Configure pixel quality and contiguity masking for ARD products.

    Parameters
    ----------
    cloud_mask : str
        Requested cloud mask.
    mask_contiguity : str or bool
        Requested contiguity mask.
    fmask_categories : list of int
        Requested pixel quality categories for Fmask.
    s2cloudless_categories : list of str
        Requested pixel quality categories for "s2cloudless".
    s1_mask_categories : list of str
        Requested pixel quality categories for Sentinel-1's "mask".
    product_type : str
        Product type, e.g., 'ls', 's2', 'mixed'.

    Returns
    -------
    pq_band : str
        Name of the pixel quality band to load.
    pq_categories : list of int
        Categories to use for pixel quality masking.
    contiguity_band : str
        Name of the contiguity band to load.
    """

    # Validate inputs
    if cloud_mask not in ("fmask", "s2cloudless"):
        raise ValueError(
            f"Unsupported cloud_mask '{cloud_mask}'. Must be 'fmask' or 's2cloudless'"
        )

    if mask_contiguity not in ("nbart", "nbar", True, False):
        raise ValueError(
            f"Unsupported mask_contiguity '{mask_contiguity}'. Must be 'nbart', 'nbar', True, or False."
        )

    if mask_contiguity & (product_type == "s1"):
        raise ValueError(
            "Contiguity masking is not supported for Sentinel-1 products. Use `mask_contiguity=False`."
        )

    # Determine contiguity band
    contiguity_band = (
        "oa_nbar_contiguity" if mask_contiguity == "nbar" else "oa_nbart_contiguity"
    )

    # If product type is "s1", set pq_band to "mask"
    if product_type == "s1":
        pq_band = "mask"
        pq_categories = s1_mask_categories

    # Otherwise, use either "fmask" or "s2cloudless"
    elif cloud_mask == "fmask":
        pq_band = "oa_fmask"
        pq_categories = fmask_categories
    elif cloud_mask == "s2cloudless":
        if product_type in ("ls", "mixed"):
            raise ValueError(
                "The Sentinel-2 's2cloudless' cloud mask is not available for "
                "Landsat products. Use `cloud_mask='fmask'`."
            )
        pq_band = "oa_s2cloudless_mask"
        pq_categories = s2cloudless_categories

    return pq_band, pq_categories, contiguity_band


def load_ard(
    dc,
    products,
    cloud_mask="fmask",
    min_gooddata=0.00,
    mask_pixel_quality=True,
    mask_filters=None,
    mask_contiguity=False,
    fmask_categories=["valid", "snow", "water"],
    s2cloudless_categories=["valid"],
    s1_mask_categories=["valid"],
    ls7_slc_off=True,
    apply_speckle_filter=False,
    convert_db=False,
    dtype="auto",
    verbose=True,
    **kwargs,
):
    """  
    Load multiple Geoscience Australia Landsat or Sentinel-2 Analysis Ready Data (ARD) products.

    This function supports automated pixel-quality/cloud masking,
    filtering to retain only good-quality observations (e.g. non-cloudy
    or non-shadowed), and advanced features such as selectively dropping
    Landsat 7 SLC-off acquisitions.
    
    Only DEA ARD products are supported. For non-ARD datasets (e.g.
    DEA Water Observations), use ``odc-stac`` or ``dc.load`` instead.
    
    Supported Landsat ARD products    
        * ga_ls5t_ard_3
        * ga_ls7e_ard_3
        * ga_ls8c_ard_3
        * ga_ls9c_ard_3
    
    Supported Sentinel-2 ARD products    
        * ga_s2am_ard_3
        * ga_s2bm_ard_3
        * ga_s2cm_ard_3
        
    Pixel-quality masking uses Fmask for Landsat and Sentinel-2, and
    s2cloudless for Sentinel-2.    

    Last modified: December 2025

    Parameters
    ----------
    dc : STAC catalogue or datacube Datacube object
        The data catalogue used to load data from. Can be either a
        STAC catalog (e.g. ``catalog = pystac_client.Client()``),
        or a datacube instance (e.g. ``dc = datacube.Datacube()``).
        If a STAC catalog is provided, data will be loaded using
        ``odc-stac``.
    products : list
        A list of product names to load. Valid options are
        ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3', 'ga_ls9c_ard_3']
        for Landsat, ['ga_s2am_ard_3', 'ga_s2bm_ard_3', 'ga_s2cm_ard_3']
        for Sentinel-2.
    cloud_mask : string, optional
        The cloud mask used for masking Landsat and Sentinel-2 data. This
        is used for both masking out poor quality pixels (e.g. clouds) if
        ``mask_pixel_quality=True``, and for calculating the
        ``min_gooddata`` percentage when dropping cloudy or low quality
        satellite observations. Two cloud masks are supported:
            * ``'fmask'`` (default; Landsat and Sentinel-2)
            * ``'s2cloudless'`` (Sentinel-2 only)
    min_gooddata : float, optional
        The minimum percentage of good quality pixels required for a
        satellite observation to be loaded. Defaults to 0.00 which will
        return all observations regardless of pixel quality (set to e.g.
        0.99 to return only observations with more than 99% good quality
        pixels).
    mask_pixel_quality : str or bool, optional
        Whether to mask out poor quality pixels (for example, clouds or shadows).
        Good quality pixels are defined by values passed to the ``fmask_categories``,
        ``s2cloudless_categories`` or ``s1_mask_categories`` parameters.
        Set to False to turn off pixel quality masking completely. Poor quality
        pixels will be set to NaN if  ``dtype='auto'``, or be set to the data's
        native nodata value (usually -999) if ``dtype='native'`` (see ``dtype``
        below for more details).
    mask_filters : iterable of tuples, optional
        Iterable tuples of morphological operations - ("<operation>", <radius>)
        to apply to the inverted pixel quality mask, where:
        operation: string; one of these morphological operations:
            * ``'dilation'`` = Expands poor quality pixels/clouds outwards
            * ``'erosion'``  = Shrinks poor quality pixels/clouds inwards
            * ``'closing'``  = Remove small holes in clouds by expanding then shrinking poor quality pixels
            * ``'opening'``  = Remove small or narrow clouds by shrinking then expanding poor quality pixels
        radius: int,
        e.g. ``mask_filters=[('erosion', 5), ("opening", 2), ("dilation", 2)]``
    mask_contiguity : str or bool, optional
        Whether to mask out Landsat or Sentinel-2 pixels that are missing
        data in any band (i.e. "non-contiguous" pixels). This can be important
        for generating clean composite datasets. The default False will
        not apply contiguity masking.
        If loading NBART data, set:
            * ``mask_contiguity='nbart'`` (or ``mask_contiguity=True``)
        If loading NBAR data, specify:
            * ``mask_contiguity='nbar'``
        Non-contiguous pixels will be set to NaN if ``dtype='auto'``, or
        set to the data's native nodata value if ``dtype='native'`` (see
        'dtype' below).
    fmask_categories : list, optional
        A list of Fmask cloud mask categories to consider as good
        quality pixels if ``mask_pixel_quality=True``, or when filtering by
        ``min_gooddata``. Defaults to ``['valid', 'snow', 'water']``; all
        other Fmask categories (e.g. 'cloud', 'shadow', 'nodata') will be
        treated as low quality pixels. Choose from: 'nodata', 'valid', 'cloud',
        'shadow', 'snow', and 'water'.
    s2cloudless_categories : list, optional
        A list of s2cloudless cloud mask categories to consider as good
        quality pixels if ``mask_pixel_quality=True``, or when filtering by
        ``min_gooddata``. Defaults to ``['valid']``; all other s2cloudless
        categories ('cloud', 'nodata') will be treated as low quality pixels.
        Choose from: 'nodata', 'valid', or 'cloud'.
    ls7_slc_off : bool, optional
        An optional boolean indicating whether to include data from
        after the Landsat 7 SLC failure (i.e. SLC-off). Defaults to
        True, which keeps all Landsat 7 observations > May 31 2003.
    apply_speckle_filter : bool or int, optional
        Whether to apply Lee speckle filtering to Sentinel-1 backscatter
        bands (e.g. 'HH_gamma0', 'VV_gamma0', 'VH_gamma0', 'HV_gamma0').
        If True, a Lee filter of radius 7 will be applied; pass an integer
        to specify a custom radius.
    convert_db : bool, optional
        Whether to convert Sentinel-1 backscatter bands (e.g. 'HH_gamma0',
        'VV_gamma0', 'VH_gamma0', 'HV_gamma0') from linear gamma0 to
        decibels.
    dtype : string, optional
        Controls the data type/dtype that layers are coerced to after
        loading. Valid values include 'native', 'auto', and 'float{16|32|64}'.
        When 'auto' is used, Landsat and Sentinel-2 data will be
        converted to `float32` if masking is used, otherwise data will
        be returned in the native data type of the data. Be aware that
        if Landsat and Sentinel-2 data is loaded in its native dtype,
        nodata and masked pixels will be returned with the data's native
        nodata value (typically -999), not NaN.
     verbose : bool, optional
        If True, print progress statements during loading.
    **kwargs :
        A set of keyword arguments to `odc.stac.load` or `dc.load` that define
        the spatiotemporal query and load parameters used to extract data.
        Keyword arguments can either be listed directly in ``load_ard`` like
        any other parameter (e.g. ``resampling='bilinear'``), or by passing
        in a query kwarg dictionary (e.g. ``**query``). Keywords depend on the
        approach being used for loading (STAC or datacube): see the ``odc.stac.load``
        documentation: https://odc-stac.readthedocs.io/en/latest/_api/odc.stac.load.html
        or ``dc.load`` documentation for all possible options:
        https://datacube-core.readthedocs.io/en/latest/api/indexed-data/generate/datacube.Datacube.load.html

    Returns
    -------
    combined_ds : xarray.Dataset
        An xarray.Dataset containing only satellite observations with
        a proportion of good quality pixels greater than `min_gooddata`.

    Examples
    --------
    Load available ARD data from multiple Landsat collections:
    
    >>> ds = load_ard(
    ...     dc=catalog,
    ...     products=["ga_ls8c_ard_3", "ga_ls9c_ard_3"],
    ...     bands=["nbart_green", "nbart_red", "nbart_blue"],
    ...     lon=(149.06, 149.17),
    ...     lat=(-35.27, -35.32),
    ...     datetime="2025-06-27/2025-07-20",
    ...     groupby="solar_day",
    ... )    
    """
    # Convert products to a list if it is passed as a string
    products = [products] if isinstance(products, str) else products

    # Validate input products against supported and classify type
    product_type = _validate_ard_products(products)

    # Get basic details about each product
    product_cfg = dea_stac_cfg(products=products)

    ########################
    # odc-stac or datacube #
    ########################

    if isinstance(dc, pystac_client.client.Client):
        if verbose:
            print("Loading data with STAC")
        method = "stac"
        chunks_param = "chunks"
        bands_param = "bands"

        # If no stac_cfg in kwargs, use sensible defaults
        stac_cfg = kwargs.pop("stac_cfg", product_cfg)

        # Raise helpful errors to assist with transition to STAC
        dc_to_stac_errors = {
            "dask_chunks": "chunks",
            "measurements": "bands",
            "output_crs": "crs",
            "time": "datetime='2000/2001' (instead of time=('2000','2001'))",
            "group_by": "groupby",
        }

        for wrong, correct in dc_to_stac_errors.items():
            if wrong in kwargs:
                raise ValueError(
                    f"When loading with STAC, `{wrong}` is not valid. "
                    f"Please use `{correct}` instead."
                )

        # STAC requires resolution as a single integer
        if "resolution" in kwargs and isinstance(kwargs["resolution"], tuple):
            raise ValueError(
                "When loading with STAC, provide `resolution` as a single value "
                "(e.g., `resolution=30`) instead of a tuple "
                "(e.g., `resolution=(-30, 30)`)."
            )

    else:
        if verbose:
            print("Loading data with datacube")
        method = "datacube"
        chunks_param = "dask_chunks"
        bands_param = "measurements"

        # Raise meaningful errors for any STAC-style kwargs
        stac_to_dc_errors = {
            "chunks": "dask_chunks",
            "bands": "measurements",
            "crs": "output_crs",
            "datetime": "time=('2000','2001')",
            "groupby": "group_by",
        }

        for wrong, correct in stac_to_dc_errors.items():
            if wrong in kwargs:
                raise ValueError(
                    f"When loading with datacube, `{wrong}` is not valid. "
                    f"Please use `{correct}` instead."
                )

        # STAC-style 'resolution' (single int) vs datacube expects tuple
        if "resolution" in kwargs and not isinstance(kwargs["resolution"], tuple):
            raise ValueError(
                "When loading with datacube, `resolution` must be a tuple "
                "(e.g., `resolution=(-30, 30)`) rather than a single value."
            )

    #########
    # Setup #
    #########

    # Configure required pixel quality and contiguity masking params
    pq_band, pq_categories, contiguity_band = _configure_masking(
        cloud_mask=cloud_mask,
        mask_contiguity=mask_contiguity,
        fmask_categories=fmask_categories,
        s2cloudless_categories=s2cloudless_categories,
        s1_mask_categories=s1_mask_categories,
        product_type=product_type,
    )

    # To ensure that the categorical PQ/contiguity masking bands are
    # loaded using nearest neighbour resampling, we need to add these to
    # the resampling kwarg if it exists and is not already "nearest".
    # This only applies if a string resampling method is supplied;
    # if a resampling dictionary (e.g. `resampling={'*': 'bilinear',
    # 'oa_fmask': 'mode'}` is passed instead we assume the user wants
    # to select custom resampling methods for each of their bands.
    resampling = kwargs.get("resampling")

    if isinstance(resampling, str) and resampling not in (None, "nearest"):
        kwargs["resampling"] = {
            "*": resampling,
            pq_band: "nearest",
            contiguity_band: "nearest",
        }

    # We extract and deal with dask chunks separately as every
    # function call uses dask internally regardless of whether the user
    # sets dask chunks themselves
    dask_chunks = kwargs.pop(chunks_param, None)

    # Create a list of requested measurements/bands so that we can eventually
    # return only the measurements/bands the user originally asked for
    requested_measurements = kwargs.pop(bands_param, None)

    # Copy our measurements/bands list so we can temporarily append extra PQ
    # and/or contiguity masking bands when loading our data
    measurements = requested_measurements.copy() if requested_measurements else None

    # Deal with "load all" case: pick a set of bands that are common
    # across requested products
    if measurements is None:
        measurements = _common_bands(product_cfg)

    # Deal with edge case where user supplies alias for PQ/contiguity
    # by stripping PQ/contiguity masks of their "oa_" prefix
    else:
        contiguity_band = (
            contiguity_band.replace("oa_", "")
            if contiguity_band.replace("oa_", "") in measurements
            else contiguity_band
        )
        pq_band = (
            pq_band.replace("oa_", "")
            if pq_band.replace("oa_", "") in measurements
            else pq_band
        )

    # Use custom fuse function to ensure contiguity is combined correctly
    # when grouping data by solar day. Without this, contiguity data from
    # neighbouring images is pasted semi-randomly over each other,
    # producing artefacts in the output.
    kwargs["fuse_func"] = {contiguity_band: _contiguity_fuser}

    # If measurements/bands are specified but do not include PQ or
    # contiguity variables, add these to list
    if pq_band not in measurements:
        measurements.append(pq_band)
    if mask_contiguity and contiguity_band not in measurements:
        measurements.append(contiguity_band)

    # Get list of data and mask bands so that we can later exclude
    # mask bands from being masked themselves
    data_bands = [
        band for band in measurements if band not in (pq_band, contiguity_band)
    ]
    mask_bands = [band for band in measurements if band not in data_bands]

    ######################
    # Load with odc-stac #
    ######################

    if method == "stac":

        # Split params into query params (passed to `pystac_client`
        # and load params (passed to `odc-stac`)
        query, load = _stac_query_load(kwargs)

        # Search the STAC catalog for all items matching the query
        if verbose:
            print(
                f"Searching STAC for {', '.join(products)} data (ignoring SLC-off observations)"
                if not ls7_slc_off
                else f"Searching STAC for {', '.join(products)} data"
            )
        query_result = dc.search(collections=products, **query)
        item_list = list(query_result.items())

        # Raise exception if no datasets are returned
        if len(item_list) == 0:
            raise ValueError(
                "No data available for query: ensure that "
                "the products specified have data for the "
                "time and location requested"
            )

        # Remove Landsat 7 SLC-off observations if ls7_slc_off=False
        if not ls7_slc_off:
            item_list = [
                i
                for i in item_list
                if i.properties.get("platform") != "landsat-7"
                or i.datetime < LS7_CUTOFF
            ]

        # Note we always load using dask here so that we can lazy load data
        # before filtering by `min_gooddata`
        ds = odc.stac.load(
            item_list,
            bands=measurements,
            chunks={} if dask_chunks is None else dask_chunks,
            stac_cfg=stac_cfg,
            **load,
        )

        # Manually set missing flag definitions that are not provided via STAC
        # TODO: Find a more STAC native way of doing this
        ds[pq_band] = ds[pq_band].assign_attrs(
            flags_definition=FLAGS_DEFINITIONS[pq_band]
        )

    ######################
    # Load with datacube #
    ######################

    elif method == "datacube":

        # Pull out query params only to pass to dc.find_datasets
        query = _dc_query_only(**kwargs)

        # Extract list of datasets for each product using query params
        dataset_list = []

        # Get list of datasets for each product
        if verbose:
            print("Finding datasets")
        for product in products:
            # Obtain list of datasets for product
            if verbose:
                print(
                    f"    {product} (ignoring SLC-off observations)"
                    if not ls7_slc_off and product == "ga_ls7e_ard_3"
                    else f"    {product}"
                )
            datasets = dc.find_datasets(product=product, **query)

            # Remove Landsat 7 SLC-off observations if ls7_slc_off=False
            if not ls7_slc_off and product == "ga_ls7e_ard_3":
                datasets = [d for d in datasets if d.time.begin < LS7_CUTOFF]

            # Add any returned datasets to list
            dataset_list.extend(datasets)

        # Raise exception if no datasets are returned
        if len(dataset_list) == 0:
            raise ValueError(
                "No data available for query: ensure that "
                "the products specified have data for the "
                "time and location requested"
            )

        # Note we always load using dask here so that we can lazy load data
        # before filtering by `min_gooddata`
        ds = dc.load(
            datasets=dataset_list,
            measurements=measurements,
            dask_chunks={} if dask_chunks is None else dask_chunks,
            **kwargs,
        )

    # return ds

    ################################
    # Apply Sentinel-1 corrections #
    ################################

    if product_type == "s1":
        # Select backscatter bands containing HH, VV, VH, or HV
        backscatter_bands = [
            b for b in ds.data_vars if any(pol in b for pol in ("HH", "VV", "VH", "HV"))
        ]

        # Applee Lee filter with default 7 radius
        if apply_speckle_filter:
            radius = 7 if apply_speckle_filter is True else int(apply_speckle_filter)
            if verbose:
                print(
                    f"Applying speckle filter (radius={radius}) to bands {backscatter_bands}"
                )
            for band in backscatter_bands:
                ds[band] = apply_lee_filter(ds[band], size=radius)

        # Convert to decibels (clipping to ensure finite values are returned)
        # Xarray will drop important attributes by default, so tell it not to
        if convert_db:
            if verbose:
                print(f"Converting {backscatter_bands} to decibels")
            for band in backscatter_bands:
                with xr.set_options(keep_attrs=True):
                    ds[band] = 10 * np.log10(ds[band].clip(min=1e-6))
                    ds[band].attrs["units"] = "decibel power"

    ####################
    # Filter good data #
    ####################

    # Calculate pixel quality mask
    # TEMPORARY hack to invert mask until s1 "mask" layer is updated to add a "valid" category
    if (pq_band == "mask") & (pq_categories == ["valid"]):
        pq_mask = odc.algo.fmask_to_bool(
            ds[pq_band],
            categories=["shadow", "layover", "shadow and layover", "invalid sample"],
            invert=True,
        )
    else:
        pq_mask = odc.algo.fmask_to_bool(ds[pq_band], categories=pq_categories)

    # The good data percentage calculation has to load all pixel quality
    # data, which can be slow. If the user has chosen no filtering
    # by using the default `min_gooddata = 0`, we can skip this step
    # completely to save processing time
    if min_gooddata > 0.0:
        # Compute good data for each observation as % of total pixels
        if verbose:
            print(f"Counting good quality pixels for each time step using {cloud_mask}")
        data_perc = pq_mask.sum(axis=[1, 2], dtype="int32") / (
            pq_mask.shape[1] * pq_mask.shape[2]
        )
        keep = (data_perc >= min_gooddata).persist()

        # Filter by `min_gooddata` to drop low quality observations
        total_obs = len(ds.time)
        ds = ds.sel(time=keep)
        pq_mask = pq_mask.sel(time=keep)

        if verbose:
            print(
                f"Filtering to {len(ds.time)} out of {total_obs} "
                f"time steps with at least {min_gooddata:.1%} "
                f"good quality pixels"
            )

    # Morphological filtering on cloud masks
    if (mask_filters is not None) & mask_pixel_quality:
        if verbose:
            print(
                f"Applying morphological filters to pixel quality mask: {mask_filters}"
            )

        pq_mask = ~mask_cleanup(~pq_mask, mask_filters=mask_filters)

    ###############
    # Apply masks #
    ###############

    # Create a combined mask to hold both pixel quality and contiguity.
    # This is more efficient than creating multiple dask tasks for
    # similar masking operations.
    mask = None

    # Add pixel quality mask to combined mask
    if mask_pixel_quality:
        if verbose:
            print(f"Applying {cloud_mask} pixel quality/cloud mask")

        mask = pq_mask

    # Add contiguity mask to combined mask
    if mask_contiguity:
        if verbose:
            print(f"Applying contiguity mask ({contiguity_band})")

        cont_mask = ds[contiguity_band] == 1

        # If mask already has data if mask_pixel_quality == True,
        # multiply with cont_mask to perform a logical 'or' operation
        # (keeping only pixels good in both)
        mask = cont_mask if mask is None else mask * cont_mask

    # Split into data/masks bands, as conversion to float and masking
    # should only be applied to data bands
    ds_data = ds[data_bands]
    ds_masks = ds[mask_bands]

    # Apply mask if provided
    if mask is not None:
        ds_data = odc.algo.keep_good_only(ds_data, where=mask)

    # Resolve dtype if set to "auto"
    if dtype == "auto":
        dtype = (
            "native"
            if product_type == "s1"
            else "native" if mask is None else "float32"
        )

    # Convert dtype if required
    if dtype != "native":
        ds_data = (
            ds_data.astype(dtype)
            if product_type == "s1"
            else odc.algo.to_float(ds_data, dtype=dtype)
        )

    # Put data and mask bands back together
    attrs = ds.attrs
    ds = xr.merge([ds_data, ds_masks])
    ds.attrs.update(attrs)

    ###############
    # Return data #
    ###############

    # Drop bands not originally requested by user
    if requested_measurements:
        ds = ds[requested_measurements]

    # If user supplied dask chunks, return data as a dask array
    # without actually loading it into memory
    if dask_chunks is not None:
        if verbose:
            print(f"Returning {len(ds.time)} time steps as a dask array")
        return ds
    if verbose:
        print(f"Loading {len(ds.time)} time steps")
    return ds.compute()


def mostcommon_crs(dc, product, query):
    """
    Takes a given query and returns the most common CRS for observations
    returned for that spatial extent. This can be useful when your study
    area lies on the boundary of two UTM zones, forcing you to decide
    which CRS to use for your `output_crs` in `dc.load`.

    Parameters
    ----------
    dc : datacube Datacube object
        The Datacube to connect to, i.e. `dc = datacube.Datacube()`.
        This allows you to also use development datacubes if required.
    product : str
        A product name (or list of product names) to load CRSs from.
    query : dict
        A datacube query including x, y and time range to assess for the
        most common CRS

    Returns
    -------
    epsg_string : str
        An EPSG string giving the most common CRS from all datasets
        returned by the query above

    """

    # Find list of datasets matching query for either product or
    # list of products
    if isinstance(product, list):
        matching_datasets = []
        for i in product:
            matching_datasets.extend(dc.find_datasets(product=i, **query))
    else:
        matching_datasets = dc.find_datasets(product=product, **query)

    # Extract all CRSs
    crs_list = [str(i.crs) for i in matching_datasets]

    # If CRSs are returned
    if len(crs_list) > 0:
        # Identify most common CRS
        crs_counts = Counter(crs_list)
        crs_mostcommon = crs_counts.most_common(1)[0][0]

        # Warn user if multiple CRSs are encountered
        if len(crs_counts.keys()) > 1:
            warnings.warn(
                f"Multiple UTM zones {list(crs_counts.keys())} "
                f"were returned for this query. Defaulting to "
                f"the most common zone: {crs_mostcommon}",
                UserWarning,
            )

        return crs_mostcommon

    raise ValueError(
        f"No CRS was returned as no data was found for "
        f"the supplied product ({product}) and query. "
        f"Please ensure that data is available for "
        f"{product} for the spatial extents and time "
        f"period specified in the query (e.g. by using "
        f"the Data Cube Explorer for this datacube "
        f"instance)."
    )


def download_unzip(url, output_dir=None, remove_zip=True):
    """
    Downloads and unzips a .zip file from an external URL to a local
    directory.

    Parameters
    ----------
    url : str
        A string giving a URL path to the zip file you wish to download
        and unzip
    output_dir : str, optional
        An optional string giving the directory to unzip files into.
        Defaults to None, which will unzip files in the current working
        directory
    remove_zip : bool, optional
        An optional boolean indicating whether to remove the downloaded
        .zip file after files are unzipped. Defaults to True, which will
        delete the .zip file.

    """

    # Get basename for zip file
    zip_name = os.path.basename(url)

    # Raise exception if the file is not of type .zip
    if not zip_name.endswith(".zip"):
        raise ValueError(
            f"The URL provided does not point to a .zip "
            f"file (e.g. {zip_name}). Please specify a "
            f"URL path to a valid .zip file"
        )

    # Download zip file
    print(f"Downloading {zip_name}")
    r = requests.get(url)
    with open(zip_name, "wb") as f:
        f.write(r.content)

    # Extract into output_dir
    with zipfile.ZipFile(zip_name, "r") as zip_ref:
        zip_ref.extractall(output_dir)
        print(f"Unzipping output files to: {output_dir if output_dir else os.getcwd()}")

    # Optionally cleanup
    if remove_zip:
        os.remove(zip_name)


def wofs_fuser(dest, src):
    """
    Fuse two WOfS water measurements represented as ``ndarray``s.

    Note: this is a copy of the function located here:
    https://github.com/GeoscienceAustralia/digitalearthau/blob/develop/digitalearthau/utils.py
    """
    empty = (dest & 1).astype(bool)
    both = ~empty & ~((src & 1).astype(bool))
    dest[empty] = src[empty]
    dest[both] |= src[both]


def dilate(array, dilation=10, invert=True):
    """
    Dilate a binary array by a specified nummber of pixels using a
    disk-like radial dilation.

    By default, invalid (e.g. False or 0) values are dilated. This is
    suitable for applications such as cloud masking (e.g. creating a
    buffer around cloudy or shadowed pixels). This functionality can
    be reversed by specifying `invert=False`.

    Parameters
    ----------
    array : array
        The binary array to dilate.
    dilation : int, optional
        An optional integer specifying the number of pixels to dilate
        by. Defaults to 10, which will dilate `array` by 10 pixels.
    invert : bool, optional
        An optional boolean specifying whether to invert the binary
        array prior to dilation. The default is True, which dilates the
        invalid values in the array (e.g. False or 0 values).

    Returns
    -------
    An array of the same shape as `array`, with valid data pixels
    dilated by the number of pixels specified by `dilation`.
    """

    y, x = np.ogrid[
        -dilation : (dilation + 1),
        -dilation : (dilation + 1),
    ]

    # disk-like radial dilation
    kernel = (x * x) + (y * y) <= (dilation + 0.5) ** 2

    # If invert=True, invert True values to False etc
    if invert:
        array = ~array

    return ~binary_dilation(
        array.astype(bool), structure=kernel.reshape((1,) + kernel.shape)
    )


def paths_to_datetimeindex(paths, string_slice=(0, 10)):
    """
    Helper function to generate a Pandas datetimeindex object
    from dates contained in a file path string.

    Parameters
    ----------
    paths : list of strings
        A list of file path strings that will be used to extract times
    string_slice : tuple
        An optional tuple giving the start and stop position that
        contains the time information in the provided paths. These are
        applied to the basename (i.e. file name) in each path, not the
        path itself. Defaults to (0, 10).

    Returns
    -------
    datetime : pandas.DatetimeIndex
        A pandas.DatetimeIndex object containing a 'datetime64[ns]' derived
        from the file paths provided by `paths`.
    """

    date_strings = [os.path.basename(i)[slice(*string_slice)] for i in paths]
    return pd.to_datetime(date_strings)


def _select_along_axis(values, idx, axis):
    other_ind = np.ix_(*[np.arange(s) for s in idx.shape])
    sl = other_ind[:axis] + (idx,) + other_ind[axis:]
    return values[sl]


def first(array: xr.DataArray, dim: str, index_name: str = None) -> xr.DataArray:
    """
    Finds the first occuring non-null value along the given dimension.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to reduce by finding the first
        non-null value.

    Returns
    -------
    reduced : xr.DataArray
        An array of the first non-null values.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension where
        the last value was found.
    """

    axis = array.get_axis_num(dim)
    idx_first = np.argmax(~pd.isnull(array), axis=axis)
    reduced = array.reduce(_select_along_axis, idx=idx_first, axis=axis)
    reduced[dim] = array[dim].isel({dim: xr.DataArray(idx_first, dims=reduced.dims)})
    if index_name is not None:
        reduced[index_name] = xr.DataArray(idx_first, dims=reduced.dims)
    return reduced


def last(array: xr.DataArray, dim: str, index_name: str = None) -> xr.DataArray:
    """
    Finds the last occuring non-null value along the given dimension.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to reduce by finding the last non-null
        value.
    index_name : str, optional
        If given, the name of a coordinate to be added containing the
        index of where on the dimension the nearest value was found.

    Returns
    -------
    reduced : xr.DataArray
        An array of the last non-null values.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension where
        the last value was found.
    """

    axis = array.get_axis_num(dim)
    rev = (slice(None),) * axis + (slice(None, None, -1),)
    idx_last = -1 - np.argmax(~pd.isnull(array)[rev], axis=axis)
    reduced = array.reduce(_select_along_axis, idx=idx_last, axis=axis)
    reduced[dim] = array[dim].isel({dim: xr.DataArray(idx_last, dims=reduced.dims)})
    if index_name is not None:
        reduced[index_name] = xr.DataArray(idx_last, dims=reduced.dims)
    return reduced


def nearest(
    array: xr.DataArray, dim: str, target, index_name: str = None
) -> xr.DataArray:
    """
    Finds the nearest values to a target label along the given
    dimension, for all other dimensions.

    E.g. For a DataArray with dimensions ('time', 'x', 'y'):
    ``nearest_array = nearest(array, 'time', '2017-03-12')``

    will return an array with the dimensions ('x', 'y'), with non-null
    values found closest for each (x, y) pixel to that location along
    the time dimension.

    The returned array will include the 'time' coordinate for each x,y
    pixel that the nearest value was found.

    Parameters
    ----------
    array : xr.DataArray
         The array to search.
    dim : str
        The name of the dimension to look for the target label.
    target : same type as array[dim]
        The value to look up along the given dimension.
    index_name : str, optional
        If given, the name of a coordinate to be added containing the
        index of where on the dimension the nearest value was found.

    Returns
    -------
    nearest_array : xr.DataArray
        An array of the nearest non-null values to the target label.
        The `dim` dimension will be removed, and replaced with a coord
        of the same name, containing the value of that dimension closest
        to the given target label.
    """

    before_target = slice(None, target)
    after_target = slice(target, None)

    da_before = array.sel({dim: before_target})
    da_after = array.sel({dim: after_target})

    da_before = last(da_before, dim, index_name) if da_before[dim].shape[0] else None
    da_after = first(da_after, dim, index_name) if da_after[dim].shape[0] else None

    if da_before is None and da_after is not None:
        return da_after
    if da_after is None and da_before is not None:
        return da_before

    target = array[dim].dtype.type(target)
    is_before_closer = abs(target - da_before[dim]) < abs(target - da_after[dim])
    nearest_array = xr.where(is_before_closer, da_before, da_after, keep_attrs=True)
    nearest_array[dim] = xr.where(
        is_before_closer, da_before[dim], da_after[dim], keep_attrs=True
    )

    if index_name is not None:
        nearest_array[index_name] = xr.where(
            is_before_closer,
            da_before[index_name],
            da_after[index_name],
            keep_attrs=True,
        )

    return nearest_array


def parallel_apply(ds, dim, func, use_threads=False, *args, **kwargs):
    """
    Applies a custom function in parallel along the dimension of an
    xarray.Dataset or xarray.DataArray.

    The function can be any function that can be applied to an
    individual xarray.Dataset or xarray.DataArray (e.g. data for a
    single timestep). The function should also return data in
    xarray.Dataset or xarray.DataArray format.

    This function is useful as a simple method for parallising code
    that cannot easily be parallised using Dask.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        xarray data with a dimension `dim` to apply the custom function
        along.
    dim : string
        The dimension along which the custom function will be applied.
    func : function
        The function that will be applied in parallel to each array
        along dimension `dim`. The first argument passed to this
        function should be the array along `dim`.
    use_threads : bool, optional
        Whether to use threads instead of processes for parallelisation.
        Defaults to False, which means it'll use multi-processing.
        In brief, the difference between threads and processes is that threads
        share memory, while processes have separate memory.
    *args :
        Any number of arguments that will be passed to `func`.
    **kwargs :
        Any number of keyword arguments that will be passed to `func`.

    Returns
    -------
    xarray.Dataset
        A concatenated dataset containing an output for each array
        along the input `dim` dimension.
    """

    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
    from functools import partial
    from itertools import repeat

    from tqdm import tqdm

    # Use threads or processes
    Executor = ThreadPoolExecutor if use_threads else ProcessPoolExecutor

    with Executor as executor:
        # Update func to add kwargs
        func = partial(func, **kwargs)

        # Apply func in parallel
        groups = [group for (i, group) in ds.groupby(dim)]
        to_iterate = (groups, *(repeat(i, len(groups)) for i in args))
        out_list = list(tqdm(executor.map(func, *to_iterate), total=len(groups)))

    # Combine to match the original dataset
    return xr.concat(out_list, dim=ds[dim])


def _apply_weights(da, band_weights):
    """
    Apply weights from a dictionary to the bands of a
    multispectral xarray.DataArray.  Raises a ValueError if any
    bands in `da` are not present in the `band_weights` dictionary.

    Parameters
    ----------
    da : xarray.DataArray object
        DataArray containing multispectral data. The dataarray
        should contain a "variable" dimension that corresponds
        to the different bands of the data.
    band_weights : dict
        Mapping of band names to weights to be applied. The keys
        of the dictionary should be the names of the bands in the
        "variable" dimension of `da`, and the values should be
        the weights to be applied to each band.

    Returns
    -------
    xarray.DataArray object
        DataArray with weights applied to the bands.
    """

    # Identify any bands without weights, and raise an
    # error if they exist
    bands_without_weights = set(da["variable"].values) - set(band_weights.keys())
    if len(bands_without_weights) > 0:
        raise ValueError(
            f"The following multispectral bands are missing from the "
            f"`band_weights` dictionary: {bands_without_weights}.\n"
            f"Ensure that weights are supplied for all multispectral "
            f"bands in `ds`, or set `band_weights=None`."
        )

    # Create xr.DataArray with weights for each variable
    # along the "variable" dimension
    weights_da = xr.DataArray(
        data=list(band_weights.values()),
        coords={"variable": list(band_weights.keys())},
        dims="variable",
    )

    # Apply weights
    return da.weighted(weights_da)


def _brovey_pansharpen(ds, pan_band, band_weights=None):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the Brovey transform (with optional per-band weights).

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    band_weights : dict, optional
        Mapping of band names to weights to be applied to each band when
        calculating the sum of all multispectral bands. The keys of
        the dictionary should be the names of the bands, and the values
        should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting `band_weights=None`
        will use a simple unweighted sum.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Create new dataarrays with and without pan band
    da_nopan = ds.drop(pan_band).to_array()
    da_pan = ds[pan_band]

    # Calculate weighted sum
    if band_weights is not None:
        da_total = _apply_weights(da_nopan, band_weights).sum(dim="variable")
    else:
        da_total = da_nopan.sum(dim="variable")

    # Perform Brovey Transform in form of: band / total * panchromatic
    da_pansharpened = da_nopan / da_total * da_pan
    return da_pansharpened.to_dataset("variable")


def _esri_pansharpen(ds, pan_band, band_weights=None):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the ESRI transform (with optional per-band weights).

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    band_weights : dict, optional
        Mapping of band names to weights to be applied to each band when
        calculating the mean of all multispectral bands. The keys of
        the dictionary should be the names of the bands, and the values
        should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting `band_weights=None`
        will use a simple unweighted mean.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """
    # Create new dataarrays with and without pan band
    da_nopan = ds.drop(pan_band).to_array()
    da_pan = ds[pan_band]

    # Calculate weighted sum
    if band_weights is not None:
        da_mean = _apply_weights(da_nopan, band_weights).mean(dim="variable")
    else:
        da_mean = da_nopan.mean(dim="variable")

    # Calculate adjustment and apply to multispectral bands
    adj = da_pan - da_mean
    da_pansharpened = da_nopan + adj
    return da_pansharpened.to_dataset("variable")


def _simple_mean_pansharpen(ds, pan_band):
    """
    Perform pansharpening on multiple timesteps of a multispectral
    dataset using the Simple Mean transform.

    Source: https://pro.arcgis.com/en/pro-app/latest/help/analysis/
            raster-functions/fundamentals-of-pan-sharpening-pro.htm

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """

    # Create new dataarrays with and without pan band
    ds_nopan = ds.drop(pan_band)
    da_pan = ds[pan_band]

    # Take mean of pan band and RGBs
    return (ds_nopan + da_pan) / 2.0


def _hsv_timestep_pansharpen(ds_i, pan_band):
    """
    Perform pansharpening on a single timestep of a multispectral
    dataset using the Hue Saturation Value (HSV) transform.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """
    # Squeeze out any single dimensions
    ds_i = ds_i.squeeze()

    # Convert to an xr.DataArray and move "variable" to end
    da_i = ds_i.to_array().transpose(..., "variable")

    # Create new dataarrays with and without pan band
    da_i_nopan = da_i.drop(pan_band, dim="variable")
    da_i_pan = da_i.sel(variable=pan_band)

    # Convert to HSV colour space
    hsv = rgb2hsv(da_i_nopan)

    # Replace value (lightness) channel with pan band data
    hsv[:, :, 2] = da_i_pan.values

    # Convert back to RGB colour space
    pansharped_array = hsv2rgb(hsv)

    # Add back into original array, reshape and return dataframe
    da_i_nopan[:] = pansharped_array
    return da_i_nopan.to_dataset("variable")


def _pca_timestep_pansharpen(ds_i, pan_band, pca_rescaling="histogram"):
    """
    Perform pansharpening on a single timestep of a multispectral
    dataset using the principal component analysis (PCA) transform.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing multispectral and panchromatic bands.
    pan_band : str
        Name of the panchromatic band in the dataset.
    pca_rescaling : str, optional
        Method to use for rescaling pan band to more closely match the
        distribution of values in the first PCA component. "simple"
        scales the pan band values to more closely match the first PCA
        component by subtracting the mean of the pan band values from
        each value, scaling the resulting values by the ratio of the
        standard deviations of the first PCA component and the pan band,
        and adding back the mean of the first PCA component.
        "histogram" uses a histogram matching technique to adjust the
        pan band values so that the resulting histogram more closely
        matches the histogram of the first PCA component.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        Pansharpened dataset with the same dimensions as the input dataset.
    """
    # Squeeze out any single dimensions
    ds_i = ds_i.squeeze()

    # Reshape to 2D by stacking x and y dimensions to prepare it
    # as an input to PCA. Drop NA rows as these are not supported
    # by `pca.fit_transform`.
    da_2d = (
        ds_i.to_array()
        .stack(pixel=("y", "x"))
        .transpose("pixel", "variable")
        .dropna(dim="pixel")
    )

    # Create new dataarrays with and without pan band
    da_2d_nopan = da_2d.drop(pan_band, dim="variable")
    da_2d_pan = da_2d.sel(variable=pan_band)

    # Apply PCA transformation
    pca = sklearn.decomposition.PCA()
    pca_array = pca.fit_transform(da_2d_nopan)

    # Rescale pan band to more closely match the first PCA component
    if pca_rescaling == "simple":
        pca_array[:, 0] = (da_2d_pan.values - da_2d_pan.values.mean()) * (
            pca_array[:, 0].std() / da_2d_pan.values.std()
        ) + pca_array[:, 0].mean()
    elif pca_rescaling == "histogram":
        pca_array[:, 0] = match_histograms(da_2d_pan.values, pca_array[:, 0])

    # Apply reverse PCA transform to restore multispectral array
    pansharped_array = pca.inverse_transform(pca_array)

    # Add back into original array, reshape and return dataframe
    da_2d_nopan[:] = pansharped_array
    return da_2d_nopan.unstack("pixel").to_dataset("variable")


def xr_pansharpen(
    ds,
    transform,
    pan_band="nbart_panchromatic",
    return_pan=False,
    output_dtype=None,
    parallelise=False,
    band_weights={"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2},
    pca_rescaling="histogram",
):
    """
    Apply pan-sharpening to multispectral satellite data with one
    or more timesteps. The following pansharpening transforms are
    currently supported:

    - Brovey ("brovey"), with optional band weighting
    - ESRI ("esri"), with optional band weighting
    - Simple mean ("simple mean")
    - PCA ("pca")
    - HSV ("hsv"), similar to IHS

    Note: Pan-sharpening transforms do not necessarily maintain
    the spectral integrity of the input satellite data, and may
    be more suitable for visualisation than quantitative work.

    Parameters
    ----------
    ds : xarray.Dataset
        An xarrray dataset containing the three input multispectral
        bands, and a panchromatic band. This dataset should have
        already been resampled to the spatial resolution of the
        panchromatic band (15 m for Landsat). Due to differences in
        the electromagnetic spectrum covered by the panchromatic band,
        Landsat 8 and 9 data should be supplied with 'blue', 'green',
        and 'red' multispectral bands, while Landsat 7 should be
        supplied with 'green', 'red' and 'NIR'.
    transform : string
        The pansharpening transform to apply to the data. Valid options
        include "brovey", "esri", "simple mean", "pca", "hsv".
    pan_band : string, optional
        The name of the panchromatic band that will be used to
        pansharpen the multispectral data.
    return_pan : bool, optional
        Whether to return the panchromatic band in the output dataset.
        Defaults to False.
    output_dtype : string or numpy.dtype, optional
        The dtype used for the output values. Defaults to the input
        dtype of the multispectral bands in ``ds``.
    parallelise: bool, optional
        Whether to parallelise transformations across multiple cores.
        Used for PCA and HSV transforms that are applied to each
        timestep in ``ds`` individually; defaults to False.
    band_weights : dict, optional
        Used for the Brovey and ESRI transforms. Mapping of band
        names to weights to be applied to each band when calculating
        the sum (Brovey) or mean (ESRI) of all multispectral bands.
        The keys of the dictionary should be the names of the bands,
        and the values should be the weights to apply to each band, e.g.:
        ``{"nbart_red": 0.4, "nbart_green": 0.4, "nbart_blue": 0.2}``.
        The default accounts for Landsat 8 and 9's pan band only
        partially overlapping with the blue band; this may not be
        suitable for all applications. Setting ``band_weights=None``
        will use a simple unweighted sum (for the Brovey transform)
        or unweighted mean (for the ESRI transform).
    pca_rescaling : str, optional
        Used for the PCA transform. The method to use for rescaling
        pan band to more closely match the distribution of values
        in the first PCA component. "simple" scales the pan band
        values to more closely match the first PCA component by
        subtracting the mean of the pan band values from each value,
        scaling the resulting values by the ratio of the standard
        deviations of the first PCA component and the pan band, and
        adding back the mean of the first PCA component.
        "histogram" uses a histogram matching technique to adjust the
        pan band values so that the resulting histogram more closely
        matches the histogram of the first PCA component.

    Returns
    -------
    ds_pansharpened : xarray.Dataset
        An xarrray dataset containing the three pansharpened input
        multispectral bands and optionally the panchromatic band
        (if `return_pan=True`).
    """

    # Assert whether pan band exists in the dataset
    if pan_band not in ds.data_vars:
        raise ValueError(
            f"The specified panchromatic band '{pan_band}' cannot be found in `ds`. "
            f"Specify a panchromatic band name that exists in the dataset using `pan_band=...`."
        )

    # Assert whether exactly three multispectral bands are included in `ds`
    n_multi = len(ds.drop(pan_band).data_vars)
    if n_multi != 3:
        raise ValueError(
            f"`ds` should contain exactly three multispectral bands (not "
            f"including the panchromatic band). However, {n_multi} "
            f"multispectral bands were found: {list(ds.drop(pan_band).data_vars)}. "
        )

    # Define dict linking functions to each transform
    transform_dict = {
        "brovey": _brovey_pansharpen,
        "esri": _esri_pansharpen,
        "simple mean": _simple_mean_pansharpen,
        "pca": _pca_timestep_pansharpen,
        "hsv": _hsv_timestep_pansharpen,
    }

    # If Brovey, ESRI or Simple Mean pansharpening is specified, apply to
    # entire `xr.Dataset` in one go (with optional weights for Brovey, ESRI)
    if transform in ("brovey", "esri", "simple mean"):
        print(f"Applying {transform.capitalize()} pansharpening")
        extra_params = (
            {"band_weights": band_weights} if transform in ("brovey", "esri") else {}
        )
        ds_pansharpened = transform_dict[transform](
            ds,
            pan_band=pan_band,
            **extra_params,
        )

    # Otherwise, apply PCA or HSV pansharpening to each
    # timestep in the `xr.Dataset` using `.apply`
    elif transform in ("pca", "hsv"):
        extra_params = {"pca_rescaling": pca_rescaling} if transform == "pca" else {}

        # Apply pansharpening to all timesteps in data in parallel
        if ("time" in ds.dims) and parallelise:
            print(f"Applying {transform.upper()} pansharpening in parallel")
            ds_pansharpened = parallel_apply(
                ds,
                "time",
                transform_dict[transform],
                pan_band,
                *extra_params.values(),  # TODO: Update once `parallel_apply` supports kwargs
            )

        # Apply pansharpening to all timesteps in data sequentially
        elif ("time" in ds.dims) and not parallelise:
            print(f"Applying {transform.upper()} pansharpening")
            ds_pansharpened = ds.groupby("time").apply(
                transform_dict[transform],
                pan_band=pan_band,
                **extra_params,
            )

        # Otherwise, apply func directly if only one timestep
        else:
            print(f"Applying {transform.upper()} pansharpening")
            ds_pansharpened = transform_dict[transform](
                ds, pan_band=pan_band, **extra_params
            )

    else:
        raise ValueError(
            f"Unsupported value '{transform}' passed to `method`. Please provide one of {list(transform_dict.keys())}."
        )

    # Optionally insert pan band back into dataset
    if return_pan:
        ds_pansharpened[pan_band] = ds[pan_band]

    # Return data in original or requested dtype
    return ds_pansharpened.astype(
        ds.to_array().dtype if output_dtype is None else output_dtype
    )


def load_reproject(
    path,
    how,
    resolution="auto",
    tight=False,
    resampling="nearest",
    chunks={"x": 2048, "y": 2048},
    bands=None,
    masked=True,
    reproject_kwds=None,
    **kwargs,
):
    """
    Load and reproject part of a raster dataset into a given GeoBox or
    custom CRS/resolution.

    Parameters
    ----------
    path : str
        Path to the raster dataset to be loaded and reprojected.
    how : GeoBox, str or int
        How to reproject the raster. Can be a GeoBox or a CRS (e.g.
        "ESPG:XXXX" string or integer).
    resolution : str or int, optional
        The resolution to reproject the raster dataset into if `how` is
        a CRS, by default "auto". Supports:
        - "same" use exactly the same resolution as the input raster
        - "fit" use center pixel to determine required scale change
        - "auto" uses the same resolution on the output if CRS units are the same between source and destination; otherwise "fit"
        - Else, a specific resolution in the units of the output crs
    tight : bool, optional
         By default output pixel grid is adjusted to align pixel edges
         to X/Y axis, suppling tight=True produces an unaligned geobox.
    resampling : str, optional
        Resampling method to use when reprojecting data, by default
        "nearest", supports all standard GDAL options ("average",
        "bilinear", "min", "max", "cubic" etc).
    chunks : dict, optional
        The size of the Dask chunks to load the data with, by default
        {"x": 2048, "y": 2048}.
    bands : str or list, optional
        Bands to optionally filter to when loading data.
    masked : bool, optional
        Whether to mask the data by its nodata value, by default True.
    reproject_kwds : dict, optional
        Additional keyword arguments to pass to the `.odc.reproject()`
        method, by default None.
    **kwargs : dict
        Additional keyword arguments to be passed to the
        `rioxarray.open_rasterio` function.

    Returns
    -------
    xarray.Dataset
        The reprojected raster dataset.
    """
    # Use empty kwds if not provided
    reproject_kwds = {} if reproject_kwds is None else reproject_kwds

    # Load data with rasterio
    da = rioxarray.open_rasterio(
        filename=path,
        masked=masked,
        chunks=chunks,
        **kwargs,
    )

    # Optionally filter to bands
    if bands is not None:
        da = da.sel(band=bands)

    # Reproject into GeoBox
    da = da.odc.reproject(
        how=how,
        resolution=resolution,
        tight=tight,
        resampling=resampling,
        dst_nodata=np.nan if masked else None,
        **reproject_kwds,
    )

    # Squeeze if only one band
    return da.squeeze()


def stac_collections(catalog: pystac_client.Client, products: list[str]) -> pd.DataFrame:
    """
    Summarise key spatial and temporal metadata for a list of STAC collections.

    Parameters
    ----------
    catalog : pystac_client.Client
        An open STAC catalog or API endpoint.
    products : list of str
        Collection IDs to summarise.

    Returns
    -------
    pandas.DataFrame
        A table indexed by product ID, including:
        - description : Collection description
        - bbox : Spatial extent as minx, miny, maxx, maxy
        - start_date : Start date of temporal extent
        - end_date : End date of temporal extent
        - license : Collection licence string
    """
    rows = []
    for p in products:
        # Search STAC for collection name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            c = catalog.get_collection(p)

        # Get spatial and temporal regions
        s = c.extent.spatial.bboxes[0]
        t = c.extent.temporal.intervals[0]

        # Convert to human readable
        rows.append({
            "product": p,
            "description": c.description,
            "bbox": f"{s[0]:.2f}, {s[1]:.2f}, {s[2]:.2f}, {s[3]:.2f}",
            "start_date": t[0].date(),
            "end_date": t[1].date() if t[1] else None,
            "license": c.license,
        })

    # Return as dataframe with product index, sorted by start date
    return pd.DataFrame(rows).set_index("product").sort_values("start_date")


def stac_assets(catalog: pystac_client.Client, products: list[str]) -> pd.DataFrame:
    """
    Summarise the assets in a STAC collection/product.

    Assets are listed from the first item found in the list
    of products.
    
    Parameters
    ----------
    catalog : pystac_client.Client
        An open STAC catalog or API endpoint.
    products : list of str
        Collection IDs to load an item from.

    Returns
    -------
    pandas.DataFrame
        A table where each row describes one asset.
    """
    # Search the STAC catalog for an item
    query = catalog.search(
        collections=products,
        max_items=1,
    )
    
    # Convert to a list
    item = list(query.items())[0]
    
    rows = []

    for name, asset in item.assets.items():
        
        # Asset-level fields
        roles = ", ".join(asset.roles) if asset.roles else None
        
        # eo:bands extension (if present)
        bands = asset.extra_fields.get("eo:bands") or asset.extra_fields.get("bands")
        if bands:
            # Try to extract meaningful summaries from bands list
            band_names = ", ".join([b.get("name", "") for b in bands])
            band_units = ", ".join([b.get("unit", "") for b in bands])
        else:
            band_names = None
            band_units = None
        
        # Common spatial metadata (if present)
        nodata = asset.extra_fields.get("nodata")
        dtype = asset.extra_fields.get("type") or asset.extra_fields.get("dtype")

        rows.append(
            dict(
                asset=name,
                roles=roles,
                band_names=band_names,

                # Not currently supported, but hopefully soon
                # band_units=band_units,
                # nodata=nodata,
                # dtype=dtype,
            )
        )
    
    return pd.DataFrame(rows).set_index("asset")