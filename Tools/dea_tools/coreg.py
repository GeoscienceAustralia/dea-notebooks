import os
import rasterio.coords
import rasterio
import pandas as pd
import shutil
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
import numpy as np
import imageio
import cv2 as cv
from typing import Union
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from shapely import box
from pathlib import Path
from typing import Literal
import time
from subprocess import run
import shlex
from typing import Any
import warnings
from arosics import COREG_LOCAL

flip_img = lambda img: np.moveaxis(img, 0, -1)


def adjust_resolutions(
    dataset_paths: list[str],
    output_paths: list[str],
    resampling_resolution: str = "lower",
) -> tuple:
    """
    Adjusts the resolutions for two or more datasets with different ones. Rounding errors might cause a slightly different output resolutions.

    Parameters
    ----------
    dataset_paths : list[str]
        List of paths to the datasets to be adjusted.
    output_paths : list[str]
        List of paths where the adjusted datasets will be saved.
    resampling_resolution : str, optional
        The resolution to which the datasets should be resampled if their resolutions are different.
        Can be either "lower" or "higher", by default "lower".
    """
    ps_x = []
    ps_y = []

    for ds in dataset_paths:
        raster = rasterio.open(ds)
        raster_px_size = abs(raster.profile["transform"].a)
        raster_py_size = abs(raster.profile["transform"].e)
        ps_x.append(raster_px_size)
        ps_y.append(raster_py_size)

    if resampling_resolution == "lower":
        ref_res_x = max(ps_x)
        ref_res_y = max(ps_y)
    else:
        ref_res_x = min(ps_x)
        ref_res_y = min(ps_y)

    scale_factors = []
    for sx, sy in zip(ps_x, ps_y):
        scale_factors.append(
            [
                sy / ref_res_y,
                sx / ref_res_x,
            ]
        )

    transforms = []
    for i, ds in enumerate(dataset_paths):
        transforms.append(downsample_dataset(ds, scale_factors[i], output_paths[i])[1])

    return [[abs(t.a), abs(t.e), t] for t in transforms], scale_factors


def reproject_tif(
    src_path: Path | str,
    dst_path: Path | str,
    dst_crs: str,
    resampling: Resampling = Resampling.bilinear,
    verbose: bool = True,
) -> None:
    """Reprojects a raster file to a new coordinate reference system (CRS) and saves it to a new file.

    Parameters
    ----------
    src_path : : Path | str
        Path to the source raster file to be reprojected.
    dst_path : : Path | str
        Destination path where the reprojected raster file will be saved.
    dst_crs : : str
        Destination coordinate reference system in a format recognized by rasterio (e.g., "EPSG:4326").
    resampling : Resampling, optional
        Resampling method to use during reprojection. Defaults to Resampling.bilinear.
    verbose : bool, optional
        If True, print detailed information about the reprojection process. Defaults to True.
    """

    with rasterio.open(src_path) as src:
        if verbose:
            print(f"reprojecting from {src.crs} to {dst_crs}")
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            {"crs": dst_crs, "transform": transform, "width": width, "height": height}
        )

        if verbose:
            print(f"saving - {dst_path}")
        with rasterio.open(dst_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling,
                )
    return None


def stream_scene(
    geotiff_file: str | Path,
    aws_session: rasterio.session.AWSSession | None = None,
    metadata_only: bool = False,
    scale_factor: float | list[float] | None = None,
    resolution: float | list[float] | None = None,
    reshape_method: Resampling = Resampling.bilinear,
    round_transform: bool = True,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Streams a GeoTIFF scene from a cloud storage using rasterio.

    Parameters
    ----------
    geotiff_file : str | Path
        Remote path to the GeoTIFF file, e.g. "s3://bucket/path/to/file.tif"
    aws_session : rasterio.session.AWSSession | None, optional
        AWS session for authentication, by default None
    metadata_only : bool, optional
        Only retrieve metadata without reading the data, by default False
    scale_factor: float | list[float] | None, optional
        Desired output scale factor for the streamed data, (h, w) if list, by default None
    resolution: float | list[float] | None, optional
        Desired output resolution in raster units for the streamed data, (h, w) if list, overrides `scale_factor`, by default None
    reshape_method: Resampling, optional
        Resampling method used for reshaping the streamed data, by default Resampling.bilinear
    round_transform: bool, optional
        If True, round the transform parameters to the nearest integer, by default True
    """

    def get_data(gtif, sclf, res, meta_only, roundtrans):
        with rasterio.open(gtif) as geo_fp:
            prof = geo_fp.profile
            bnds = geo_fp.bounds
            gcrs = geo_fp.crs
            dtype = prof["dtype"]
            if res is not None:
                if type(res) == float:
                    res = [res] * 2
                sclf = [
                    abs(geo_fp.transform.e) / res[0],
                    abs(geo_fp.transform.a) / res[1],
                ]
            if sclf is not None:
                if type(sclf) == float:
                    sclf = [sclf] * 2
                stream_out_shape = (
                    int(prof["height"] * sclf[0]),
                    int(prof["width"] * sclf[1]),
                )
                transform = geo_fp.transform * geo_fp.transform.scale(
                    (geo_fp.width / stream_out_shape[1]),
                    (geo_fp.height / stream_out_shape[0]),
                )
                if roundtrans:
                    transform = rasterio.Affine(
                        np.round(transform.a).tolist(),
                        transform.b,
                        transform.c,
                        transform.d,
                        np.round(transform.e).tolist(),
                        transform.f,
                    )
                prof.update(
                    transform=transform,
                    width=stream_out_shape[1],
                    height=stream_out_shape[0],
                    dtype=dtype,
                )

            if meta_only:
                scn = None
            else:
                if sclf is None:
                    scn = geo_fp.read()
                else:
                    scn = geo_fp.read(
                        out_shape=(geo_fp.count, *stream_out_shape),
                        resampling=reshape_method,
                    )

        return scn, prof, bnds, gcrs

    if aws_session is not None:
        with rasterio.Env(aws_session):
            scene, profile, bounds, crs = get_data(
                geotiff_file, scale_factor, resolution, metadata_only, round_transform
            )
    else:
        scene, profile, bounds, crs = get_data(
            geotiff_file, scale_factor, resolution, metadata_only, round_transform
        )

    return scene, {"profile": profile, "bounds": bounds, "crs": crs}


def downsample_dataset(
    dataset_path: str,
    scale_factor: Union[float, list[float]] = 1.0,
    output_file: str = "",
    enhance_function=None,
    force_shape: tuple = (),  # (height, width)
    readjust_origin: bool = False,
    round_resolution: bool = False,
    masked_data: bool = False,
) -> tuple:
    """
    Downsamples the output data and returns the new downsampled data and its new affine transformation according to `scale_factor`
    The output shape could also be forced using `forced_shape` parameter.

    Parameters
    ----------
    dataset_path : str
        Path to the dataset to be downsampled.
    scale_factor : float or list[float], optional
        Scale factor for downsampling. If a single float is provided, it will be applied to both dimensions (height, width).
        If a list of two floats is provided, they will be applied to the height and width respectively.
        Defaults to 1.0 (no downsampling).
    output_file : str, optional
        Path to save the downsampled dataset. If not provided, the data will not be saved to a file.
    enhance_function : callable, optional
        A function to enhance the data after downsampling. It should accept a numpy array and return a modified numpy array.
        Defaults to None (no enhancement).
    force_shape : tuple, optional
        A tuple specifying the desired output shape (height, width). If provided, the output data will be forced to this shape.
        If empty, the output shape will be calculated based on the scale factor.
    readjust_origin : bool, optional
        If True, the origin of the affine transformation will be readjusted after downsampling.
        Defaults to False.
    round_resolution : bool, optional
        If True, the pixel size in the affine transformation will be rounded to the nearest integer.
        Defaults to False.
    masked_data : bool, optional
        If True, reads the data as a masked array to handle nodata values. Defaults to False.

    Returns
    -------
    tuple
        A tuple containing:
        - data: numpy array of the downsampled data.
        - transform: rasterio.Affine object representing the new affine transformation.
    """
    with rasterio.open(dataset_path) as dataset:
        # resample data to target shape
        if type(scale_factor) == float:
            scale_factor = [scale_factor] * 2
        if len(force_shape) != 0:
            output_shape = force_shape
        else:
            output_shape = (
                int(dataset.height * scale_factor[0]),
                int(dataset.width * scale_factor[1]),
            )
        data = dataset.read(
            out_shape=(
                dataset.count,
                *output_shape,
            ),
            resampling=Resampling.bilinear,
            masked=masked_data,
        )

        if enhance_function is not None:
            data = enhance_function(data)

        # scale image transform
        transform = dataset.transform * dataset.transform.scale(
            (dataset.width / data.shape[-1]), (dataset.height / data.shape[-2])
        )

        if round_resolution:
            transform = rasterio.Affine(
                np.round(transform.a).tolist(),
                transform.b,
                transform.c,
                transform.d,
                np.round(transform.e).tolist(),
                transform.f,
            )

        if len(force_shape) != 0:
            scale_factor = [
                force_shape[0] / dataset.height,
                force_shape[1] / dataset.width,
            ]

        if readjust_origin:
            transform = readjust_origin_for_new_pixel_size(transform, *scale_factor)

        profile = dataset.profile
        profile.update(
            transform=transform,
            width=data.shape[2],
            height=data.shape[1],
            dtype=data.dtype,
        )

    if output_file != "":
        with rasterio.open(output_file, "w", **profile) as ds:
            for i in range(0, profile["count"]):
                ds.write(data[i], i + 1)

    return data, transform if len(force_shape) == 0 else (transform, scale_factor)


def find_overlap(
    dataset_1: str,
    dataset_2: str,
    return_images: bool = False,
    return_pixels: bool = False,
    resampling_resolution: str = "lower",
    output_dir: str = "",
) -> tuple:
    """
    Crude overlap finder for two overlapping scenes. (finds the bounding box around the overlapping area.
    A better way is to straighten the images and then find the overlap and then revert the transform.)

    Parameters
    ----------
    dataset_1 : str
        Path to the first dataset.
    dataset_2 : str
        Path to the second dataset.
    return_images : bool, optional
        If True, returns the images of the overlapping area, by default False.
    return_pixels : bool, optional
        If True, returns the pixel coordinates of the overlapping area, by default False.
    resampling_resolution : str, optional
        The resolution to which the datasets should be resampled if their resolutions are different.
        Can be either "lower" or "higher", by default "lower".
    output_dir : str, optional
        Directory to save overlapping area files if needed, by default "".
        If provided, `return_pixels` and `return_images` will be set to True.

    Returns
    -------
    tuple
        A tuple containing:
        - The bounding box of the overlapping area as a rasterio.coords.BoundingBox object.
        - If `return_images` is True, a tuple containing:
            - The mosaiced image as a numpy array.
            - The overlapping area of the mosaiced image.
            - The overlapping area of the first dataset.
            - The overlapping area of the second dataset.
        - Scale factors for each dataset if their resolutions were adjusted.
    """
    raster_1 = rasterio.open(dataset_1)
    raster_2 = rasterio.open(dataset_2)

    bounds_1 = raster_1.bounds
    bounds_2 = raster_2.bounds

    if return_images:
        return_pixels = True

    if output_dir != "":
        return_images = True
        return_pixels = True
        os.makedirs(output_dir, exist_ok=True)
        overlapping_bounds_real = box(*bounds_1).intersection(box(*bounds_2)).bounds
        real_left = overlapping_bounds_real[0]
        real_top = overlapping_bounds_real[3]
        overlap_profile = raster_1.profile

    scale_factors = [[1.0, 1.0]] * 2
    if return_pixels:
        raster_1_px_size = abs(raster_1.profile["transform"].a)
        raster_1_py_size = abs(raster_1.profile["transform"].e)

        raster_2_px_size = abs(raster_2.profile["transform"].a)
        raster_2_py_size = abs(raster_2.profile["transform"].e)

        if (raster_1_px_size != raster_2_px_size) or (
            raster_1_py_size != raster_2_py_size
        ):

            os.makedirs("temp", exist_ok=True)
            outputs = adjust_resolutions(
                [dataset_1, dataset_2],
                ["temp/scaled_raster_1.tif", "temp/scaled_raster_2.tif"],
                resampling_resolution,
            )
            dataset_1 = "temp/scaled_raster_1.tif"
            dataset_2 = "temp/scaled_raster_2.tif"

            (
                (raster_1_px_size, raster_1_py_size, _),
                (
                    raster_2_px_size,
                    raster_2_py_size,
                    _,
                ),
            ), scale_factors = outputs

        min_left = min(bounds_1.left, bounds_2.left)
        max_top = max(bounds_1.top, bounds_2.top)

        res_x = [raster_1_px_size, raster_2_px_size]
        res_y = [raster_1_py_size, raster_2_py_size]
        selected_res_x = max(res_x) if resampling_resolution == "lower" else min(res_x)
        selected_res_y = max(res_y) if resampling_resolution == "lower" else min(res_y)

        bounds_1 = rasterio.coords.BoundingBox(
            int((bounds_1.left - min_left) / selected_res_x),
            int((max_top - bounds_1.bottom) / selected_res_y),
            int((bounds_1.right - min_left) / selected_res_x),
            int((max_top - bounds_1.top) / selected_res_y),
        )

        bounds_2 = rasterio.coords.BoundingBox(
            int((bounds_2.left - min_left) / selected_res_x),
            int((max_top - bounds_2.bottom) / selected_res_y),
            int((bounds_2.right - min_left) / selected_res_x),
            int((max_top - bounds_2.top) / selected_res_y),
        )

    overlap_left = max(bounds_1.left, bounds_2.left)
    overlap_bottom = (
        min(bounds_1.bottom, bounds_2.bottom)
        if return_pixels
        else max(bounds_1.bottom, bounds_2.bottom)
    )
    overlap_right = min(bounds_1.right, bounds_2.right)
    overlap_top = (
        max(bounds_1.top, bounds_2.top)
        if return_pixels
        else min(bounds_1.top, bounds_2.top)
    )

    x_condition = (overlap_right - overlap_left) > 0
    y_condition = (
        (overlap_bottom - overlap_top) > 0
        if return_pixels
        else (overlap_top - overlap_bottom) > 0
    )

    assert x_condition and y_condition, "The provided scenes do not overlap."

    overlap_in_mosaic = rasterio.coords.BoundingBox(
        overlap_left, overlap_bottom, overlap_right, overlap_top
    )

    mosaic = None
    mosaic_overlap = None
    raster_overlap_1 = None
    raster_overlap_2 = None

    if return_images:
        mosaic, warps, _ = make_mosaic([dataset_1, dataset_2], return_warps=True)
        mosaic_overlap = mosaic[
            overlap_in_mosaic.top : overlap_in_mosaic.bottom,
            overlap_in_mosaic.left : overlap_in_mosaic.right,
        ]
        raster_overlap_1 = warps[0][
            overlap_in_mosaic.top : overlap_in_mosaic.bottom,
            overlap_in_mosaic.left : overlap_in_mosaic.right,
        ]
        raster_overlap_2 = warps[1][
            overlap_in_mosaic.top : overlap_in_mosaic.bottom,
            overlap_in_mosaic.left : overlap_in_mosaic.right,
        ]

    shutil.rmtree("temp", ignore_errors=True)

    if output_dir != "":
        overlap_profile.update(
            {
                "height": raster_overlap_1.shape[0],
                "width": raster_overlap_1.shape[1],
                "transform": rasterio.Affine(
                    raster_1.profile["transform"].a,
                    raster_1.profile["transform"].b,
                    real_left,
                    raster_1.profile["transform"].d,
                    raster_1.profile["transform"].e,
                    real_top,
                ),
            }
        )
        if overlap_profile["count"] == 1:
            raster_overlap_1 = np.expand_dims(raster_overlap_1, axis=2)
            raster_overlap_2 = np.expand_dims(raster_overlap_2, axis=2)
        with rasterio.open(
            os.path.join(output_dir, os.path.basename(dataset_1)),
            "w",
            **overlap_profile,
        ) as dst:
            for i in range(overlap_profile["count"]):
                dst.write(raster_overlap_1[:, :, i], i + 1)
        with rasterio.open(
            os.path.join(output_dir, os.path.basename(dataset_2)),
            "w",
            **overlap_profile,
        ) as dst:
            for i in range(overlap_profile["count"]):
                dst.write(raster_overlap_2[:, :, i], i + 1)
        raster_overlap_1 = np.squeeze(raster_overlap_1)
        raster_overlap_2 = np.squeeze(raster_overlap_2)

    return (
        overlap_in_mosaic,
        (
            mosaic,
            mosaic_overlap,
            raster_overlap_1,
            raster_overlap_2,
        ),
        scale_factors,
    )


def make_mosaic(
    dataset_paths: list[str],
    offset_x: int = 0,
    offset_y: int = 0,
    return_warps: bool = False,
    resampling_resolution: str = "lower",
    mosaic_output_path: str = "",
    return_profile_only: bool = False,
    cv_flags: int = cv.INTER_NEAREST,
    output_type: str = "uint8",
    nodata: int | float | None = None,
    force_crs: Literal["auto"] | str | None = "auto",
    no_affine: bool = False,
) -> tuple:
    """
    Creates a mosaic of overlapping scenes. Offsets will be added to the size of the final mosaic if specified.
    NOTE: dataset ground resolutions should be the same. Use `resolution_adjustment` flag to fix the unequal resolutions.

    Parameters
    ----------
    dataset_paths : list[str]
        List of paths to the datasets to be mosaiced.
    offset_x : int, optional
        Offset to be added to the width of the mosaic, by default 0.
    offset_y : int, optional
        Offset to be added to the height of the mosaic, by default 0.
    return_warps : bool, optional
        If True, returns the warped images of the mosaiced datasets, by default False.
    resampling_resolution : str, optional
        The resolution to which the datasets will be adjusted if `resolution_adjustment` is True.
        Can be either "lower" or "higher", by default "lower".
    mosaic_output_path : str, optional
        If provided, the mosaic will be saved to this path. If not provided, the mosaic will not be saved.
    return_profile_only : bool, optional
        If True, returns only the real world profiles of the mosaic instead of the new transforms in pixels.
        Defaults to False.
    cv_flags : int, optional
        OpenCV flags for the warping process. Defaults to `cv.INTER_NEAREST`.
    output_type : str, optional
        The data type of the output mosaic. Defaults to "uint8". Other options could be "uint16", "float32", etc.
    nodata : int | float | None, optional
        The nodata value to be used for masking.
    force_crs : Literal["auto"] | dict | None, optional
        If "auto", the function will try to determine the CRS from the datasets.
        If None, the CRS will not be forced. Defaults to "auto".
        If a str, the function will use the provided CRS information. The provided CRS should be in the form of an EPSG code (e.g., "EPSG:4326").
    no_affine: bool, optional
        Does not perform affine transformation and assumes the images are already geo-referenced.

    Returns
    -------
    tuple
        A tuple containing:
        - The mosaiced image as a numpy array.
        - A list of warped images if `return_warps` is True, otherwise an empty list.
        - A list of new transforms for each dataset or the real world profiles if `return_profile_only` is True.
    """

    ps_x = []
    ps_y = []
    rasters = []
    transforms = []
    boundss = []
    original_boundss = []
    crs_numbers = []
    first_crs = rasterio.open(dataset_paths[0]).crs
    if first_crs is None:
        force_crs = None
    else:
        if type(force_crs) == str and force_crs != "auto":
            first_crs_data = force_crs
        else:
            first_crs_data = f"EPSG:{first_crs.to_epsg()}"

    for p in dataset_paths:
        with rasterio.open(p, "r") as raster:
            raster_crs = raster.crs
            if raster_crs is not None:
                crs_numbers.append(raster.crs.to_epsg())

    if type(force_crs) == str and force_crs != "auto":
        print(f"Using provided CRS information: {force_crs}")
    elif len(crs_numbers) != 0 and np.any(np.diff(crs_numbers) != 0):
        if force_crs is None:
            warnings.warn(
                "Datasets have different CRS. The mosaicing process might fail with discrepancies in CRS information."
            )
        else:
            warnings.warn(
                f"Datasets have different CRS. The first CRS: {first_crs}, will be used for the mosaicing process."
            )
    else:
        force_crs = None

    for p in dataset_paths:
        raster_path = p
        with rasterio.open(raster_path, "r") as raster:
            raster_crs = raster.crs
        if raster_crs is None:
            warnings.warn(f"Dataset {p} does not have a CRS.")
        else:
            if force_crs == "auto" or type(force_crs) == str:
                os.makedirs("temp/reproject", exist_ok=True)
                new_p = f"temp/reproject/{os.path.basename(p)}"
                reproject_tif(p, new_p, first_crs_data, verbose=False)
                raster_path = new_p
            elif force_crs is not None:
                raise ValueError(
                    "force_crs should be either 'auto' or None. Please check the documentation."
                )

        raster = rasterio.open(raster_path)
        raster_crs = raster.crs
        boundss.append(raster.bounds)
        original_boundss.append(raster.bounds)
        transform = raster.transform
        ps_x.append(abs(transform.a))
        ps_y.append(abs(transform.e))
        rasters.append(raster)
        transforms.append(transform)

    selected_res_x = max(ps_x) if resampling_resolution == "lower" else min(ps_x)
    selected_res_y = max(ps_y) if resampling_resolution == "lower" else min(ps_y)
    ps_x_condition = all(round(ps) == round(ps_x[0]) for ps in ps_x)
    ps_y_condition = all(round(ps) == round(ps_y[0]) for ps in ps_y)
    if not (ps_x_condition and ps_y_condition):
        print(
            """Ground resolutions are different for datasets. The mosaicing process might fail if adding large datasets.
              Please use `resolution_adjustment` flag first if you encounter memory related issues."""
        )

    lefts = []
    rights = []
    tops = []
    bottoms = []
    original_tops = []
    original_lefts = []
    for i, bounds in enumerate(boundss):
        lefts.append(bounds.left)
        rights.append(bounds.right)
        tops.append(bounds.top)
        bottoms.append(bounds.bottom)
        original_tops.append(original_boundss[i].top)
        original_lefts.append(original_boundss[i].left)

    min_left = min(lefts)
    min_bottom = min(bottoms)
    max_right = max(rights)
    max_top = max(tops)

    max_original_top = max(original_tops)
    min_original_left = min(original_lefts)

    new_shape = (
        int((max_top - min_bottom) / selected_res_y) + offset_y,
        int((max_right - min_left) / selected_res_x) + offset_x,
    )

    new_transforms = []
    for i, t in enumerate(transforms):
        orig_x = boundss[i].left
        orig_y = boundss[i].top
        new_transforms.append(
            np.array(
                [
                    [
                        t.a / selected_res_x,
                        abs(t.b / t.e),
                        (orig_x - min_left) / selected_res_x,
                    ],
                    [
                        t.d / t.a,
                        abs(t.e / selected_res_y),
                        (max_top - orig_y) / selected_res_y,
                    ],
                ]
            )
        )

    if no_affine:
        new_shape = rasters[0].shape
    mosaic = np.zeros((*new_shape, 3)).astype(output_type)
    warps = []
    masks = []
    for i, rs in enumerate(rasters):
        img = flip_img(rs.read())
        if no_affine:
            imgw = img.copy()
        else:
            imgw = cv.warpAffine(
                img,
                new_transforms[i],
                (new_shape[1], new_shape[0]),
                flags=cv_flags,
            )

        if len(imgw.shape) == 2:
            idx = np.where(imgw != 0)
            for i in range(0, 3):
                mosaic[idx[0], idx[1], i] = imgw[idx[0], idx[1]]
        else:
            if imgw.shape[2] == 1:
                warnings.warn(
                    "WARNING: Single channel image detected. Converting to 3 channels."
                )
                imgw = cv.merge([imgw] * 3)
            elif imgw.shape[2] == 2:
                warnings.warn(
                    "WARNING: Two channel image detected. Converting to 3 channels."
                )
                imgw = cv.merge(
                    [
                        imgw[:, :, 0],
                        imgw[:, :, 1],
                        imgw[:, :, 0],
                    ]
                )

            idx = np.where(cv.cvtColor(imgw, cv.COLOR_BGR2GRAY) != 0)
            mosaic[idx[0], idx[1], :] = imgw[idx[0], idx[1], :]

        if return_warps:
            warp = np.zeros_like(imgw).astype(output_type)
            if len(imgw.shape) == 2:
                warp[idx[0], idx[1]] = imgw[idx[0], idx[1]]
            else:
                warp[idx[0], idx[1], :] = imgw[idx[0], idx[1], :]
            warps.append(warp)

    if os.path.exists("temp/reproject"):
        shutil.rmtree("temp/reproject", ignore_errors=True)

    mosaic_profile = rasterio.open(dataset_paths[0]).profile

    mosaic_profile["height"] = new_shape[0]
    mosaic_profile["width"] = new_shape[1]
    mosaic_profile["count"] = 3
    mosaic_profile["transform"] = rasterio.Affine(
        selected_res_x, 0.0, min_left, 0.0, -selected_res_y, max_top
    )
    original_mosaic_profile = mosaic_profile.copy()
    original_mosaic_profile["transform"] = rasterio.Affine(
        selected_res_x, 0.0, min_original_left, 0.0, -selected_res_y, max_original_top
    )
    original_mosaic_profile["dtype"] = output_type
    if first_crs is not None:
        mosaic_profile["crs"] = first_crs
        original_mosaic_profile["crs"] = first_crs

    if mosaic_output_path != "":
        print("Writing mosaic file.")
        with rasterio.open(mosaic_output_path, "w", **mosaic_profile) as ds:
            for i in range(0, 3):
                ds.write(mosaic[:, :, i], i + 1)

    if nodata is not None:
        mosaic_profile["nodata"] = nodata
        original_mosaic_profile["nodata"] = nodata

    return (
        mosaic,
        warps,
        (
            (mosaic_profile, original_mosaic_profile)
            if return_profile_only
            else new_transforms
        ),
    )


def filter_features(
    ref_points: np.ndarray,
    tgt_points: np.ndarray,
    ref_img: np.ndarray,
    tgt_img: np.ndarray,
    bounding_shape: tuple,
    dists: np.ndarray,
    dist_thresh: Union[None, int, float] = None,
    lower_of_dist_thresh: Union[None, int, float] = None,
    target_info: Union[None, tuple] = None,
    directional_filtering: bool = False,
) -> tuple:
    """Filters the reference and target points based on distance thresholds and image validity.

    Parameters
    ----------
    ref_points : np.ndarray
        Array of reference points to be filtered.
    tgt_points : np.ndarray
        Array of target points to be filtered.
    ref_img : np.ndarray
        Reference image corresponding to the reference points.
    tgt_img : np.ndarray
        Target image corresponding to the target points.
    bounding_shape : tuple
        Shape of the bounding box for the images, used to validate points.
    dists : np.ndarray
        Array of distances corresponding to the reference and target points.
    dist_thresh : Union[None, int, float], optional
        Threshold for filtering points based on distance, by default None
    lower_of_dist_thresh : Union[None, int, float], optional
        Lower threshold for filtering points based on distance, by default None
    target_info : Union[None, tuple], optional
        Information about the target, used for logging if no valid features are found, by default None
    directional_filtering : bool, optional
        If True, distance filtering is done per direction, by default False

    Returns
    -------
    tuple
        Filtered reference and target points as numpy arrays.
        If no valid features are found, returns (None, None).
    """

    if dist_thresh != None:
        if directional_filtering:
            print("Applying directional filtering to feature points...")
            dists = np.abs(ref_points - tgt_points)
            dists_x = dists[:, 0]
            dists_y = dists[:, 1]
            if lower_of_dist_thresh != None:
                upper_idx_x = np.squeeze(dists_x) < dist_thresh
                lower_idx_x = np.squeeze(dists_x) > lower_of_dist_thresh
                filter_idx_x = np.where(np.logical_and(upper_idx_x, lower_idx_x))

                upper_idx_y = np.squeeze(dists_y) < dist_thresh
                lower_idx_y = np.squeeze(dists_y) > lower_of_dist_thresh
                filter_idx_y = np.where(np.logical_and(upper_idx_y, lower_idx_y))
            else:
                filter_idx_x = np.where(np.squeeze(dists_x) < dist_thresh)
                filter_idx_y = np.where(np.squeeze(dists_y) < dist_thresh)

            filter_idx = np.intersect1d(filter_idx_x, filter_idx_y)
        else:
            if lower_of_dist_thresh != None:
                upper_idx = np.squeeze(dists) < dist_thresh
                lower_idx = np.squeeze(dists) > lower_of_dist_thresh
                filter_idx = np.where(np.logical_and(upper_idx, lower_idx))
            else:
                filter_idx = np.where(np.squeeze(dists) < dist_thresh)
        ref_good = np.squeeze(ref_points)[filter_idx]
        tgt_good = np.squeeze(tgt_points)[filter_idx]

        valid_idx = np.all(
            (
                tgt_good[:, 0] >= 0,
                tgt_good[:, 1] >= 0,
                tgt_good[:, 0] < bounding_shape[1],
                tgt_good[:, 1] < bounding_shape[0],
            ),
            axis=0,
        )

        ref_good = ref_good[valid_idx]
        tgt_good = tgt_good[valid_idx]

        points = ref_good.astype("int")
        invalid_idx_ref = np.where(ref_img[points[:, 1], points[:, 0]] == 0)
        points = tgt_good.astype("int")
        invalid_idx_tgt = np.where(tgt_img[points[:, 1], points[:, 0]] == 0)
        invalid_idx = set(
            np.hstack([invalid_idx_ref, invalid_idx_tgt]).ravel().tolist()
        )
        valid_idx = np.array(list(set(range(0, len(ref_good))) - invalid_idx))

        if len(valid_idx) == 0:
            info_str = ""
            if target_info is not None:
                info_str = f"For target {target_info[0]} ({target_info[1]}), "
            print(info_str + "All features removed as outliers.")
            return None, None

        tgt_good = np.expand_dims(tgt_good[valid_idx], axis=0)
        ref_good = np.expand_dims(ref_good[valid_idx], axis=0)
    else:
        tgt_good = np.expand_dims(tgt_points, axis=0)
        ref_good = np.expand_dims(ref_points, axis=0)

    return ref_good, tgt_good


def find_cells(
    img: np.ndarray, points: np.ndarray, window_size: tuple, invert_points: bool = False
) -> list[np.ndarray]:
    """Finds grid cells around the given points in the image.
    Parameters
    ----------
    img : np.ndarray
        The input image.
    points : np.ndarray
        The points around which to find the grid cells.
    window_size : tuple
        The size of the grid cells.
    invert_points : bool, optional
        If True, inverts the points to (y, x) format, by default False
    Returns
    -------
    list
        List of grid cells as numpy arrays.
    """
    if invert_points:
        points = np.column_stack([points[:, 1], points[:, 0]])
    h = img.shape[0]
    w = img.shape[1]
    cells = []
    sx = window_size[0] // 2
    sy = window_size[1] // 2
    for p in points:
        l_h = p[0] - sx
        u_h = p[0] + sx
        l_w = p[1] - sy
        u_w = p[1] + sy
        h_range = (np.clip(l_h, 0, l_h), np.clip(u_h, u_h, h))
        w_range = (np.clip(l_w, 0, l_w), np.clip(u_w, u_w, w))
        cells.append(img[h_range[0] : h_range[1], w_range[0] : w_range[1]])
    return cells


def find_corrs_shifts(
    ref_img: np.ndarray,
    tgt_img: np.ndarray,
    ref_points: np.ndarray,
    tgt_points: np.ndarray,
    corr_win_size: tuple = (25, 25),
    signal_power_thresh: float = 0.9,
    drop_unbound: bool = True,
    invert_points: bool = True,
    valid_num_points=10,
) -> tuple:
    """Filters the reference and target points based on phase correlation of the grid cells around the points.

    Parameters
    ----------
    ref_img : np.ndarray
        Reference image corresponding to the reference points.
    tgt_img : np.ndarray
        Target image corresponding to the target points.
    ref_points : np.ndarray
        Reference points to be filtered.
    tgt_points : np.ndarray
        Target points to be filtered.
    corr_win_size : tuple, optional
        Window size for calculating phase correlation aroung a feature point, by default (25, 25)
    signal_power_thresh : float, optional
        Phase correlation signal threshold for filtering points, by default 0.9
    drop_unbound : bool, optional
        Drop out og bound points, by default True
    invert_points : bool, optional
        invert points to (y, x) format, by default True
    valid_num_points : int, optional
        Valid number of points to be found, if fewer points are found, the function will return the original points, by default 10

    Returns
    -------
    tuple
        Filtered reference and target points as numpy arrays.
        If no valid features are found, returns (ref_points, tgt_points).
    """

    ref_points_temp = ref_points.copy().astype("int")
    tgt_points_temp = tgt_points.copy().astype("int")

    ref_cells = find_cells(
        ref_img,
        ref_points_temp,
        corr_win_size,
        invert_points,
    )
    tgt_cells = find_cells(
        tgt_img,
        tgt_points_temp,
        corr_win_size,
        invert_points,
    )

    if drop_unbound:
        valid_idx = []
        final_ref_cells = []
        final_tgt_cells = []
        for idx, (ref, tgt) in enumerate(zip(ref_cells, tgt_cells)):
            if ref.shape == tgt.shape:
                final_ref_cells.append(ref)
                final_tgt_cells.append(tgt)
                valid_idx.append(idx)
        ref_points = ref_points[valid_idx]
        tgt_points = tgt_points[valid_idx]
    else:
        final_ref_cells = ref_cells
        final_tgt_cells = tgt_cells

    corrs = []
    corr_shifts = []
    valid_idx = []
    warning = False
    for idx, (ref, tgt) in enumerate(zip(final_ref_cells, final_tgt_cells)):
        try:
            corr = cv.phaseCorrelate(np.float32(tgt), np.float32(ref), None)
            corrs.append(corr[1])
            corr_shifts.append(corr[0])
            valid_idx.append(idx)
        except Exception as e:
            warning = True

    ref_points = ref_points[valid_idx]
    tgt_points = tgt_points[valid_idx]

    if warning:
        print(
            "WARNING: Phase correlation filtering failed for some of the gird cells. This might be due to the size of the cells or the image data type."
        )

    valid_idx = np.where(np.array(corrs) > signal_power_thresh)

    if len(valid_idx[0]) < valid_num_points:
        has_s = " was" if len(valid_idx[0]) == 1 else "s were"
        print(
            f"WARNING: {len(valid_idx[0])} point{has_s} found with the given correlation threshold (fewer than accepted {valid_num_points}), turning off phase correlation filter..."
        )
        return ref_points, tgt_points, np.array(corr_shifts)

    return (
        ref_points[valid_idx],
        tgt_points[valid_idx],
        np.array(corr_shifts)[valid_idx],
    )


def warp_affine_dataset(
    dataset: Union[str, np.ndarray],
    output_path: str = "",
    translation_x: float = 0.0,
    translation_y: float = 0.0,
    rotation_angle: float = 0.0,
    scale: float = 1.0,
    write_new_transform: bool = False,  # if writing to an output file, changes the transform of the profile instead of shifting image pixels.
    affine_matrix: np.ndarray = None,
) -> np.ndarray:
    """
    Transforms the dataset accroding to given translation, rotation and scale params and writes it to the `output_path` file.

    Parameters
    ----------
    dataset : Union[str, np.ndarray]
        The input dataset to be transformed. Can be a file path or a numpy array.
    output_path : str, optional
        The path to save the transformed dataset. If empty, the transformed image will not be saved
    translation_x : float, optional
        The translation in the x direction, by default 0.0
    translation_y : float, optional
        The translation in the y direction, by default 0.0
    rotation_angle : float, optional
        The rotation angle in degrees, by default 0.0
    scale : float, optional
        The scale factor for the image, by default 1.0
    write_new_transform : bool, optional
        If True, the new affine transformation will be written to the output file's profile.
        If False, the image pixels will be shifted according to the translation parameters, by default False
    affine_matrix : np.ndarray, optional
        A 2x3 affine transformation matrix. If provided, this matrix will be used for the transformation instead of calculating it from translation, rotation, and scale parameters.

    Returns
    -------
    np.ndarray
        The transformed image as a numpy array.
        If `output_path` is provided, the transformed image will also be saved to that path
    """
    if type(dataset) == str:
        raster = rasterio.open(dataset)
        img = flip_img(raster.read()).copy()
    else:
        img = dataset
    img_centre = (img.shape[1] // 2, img.shape[0] // 2)
    rotation_mat = cv.getRotationMatrix2D(img_centre, rotation_angle, scale)
    translation_mat = np.array([[1.0, 0.0, translation_x], [0.0, 1.0, translation_y]])
    affine_transform = np.matmul(
        rotation_mat, np.vstack([translation_mat, np.array([0, 0, 1])])
    )
    if affine_matrix is not None:
        affine_transform = affine_matrix
    warped_img = cv.warpAffine(img, affine_transform, (img.shape[1], img.shape[0]))

    if (type(dataset) == str) and (output_path != ""):
        profile = raster.profile
        if write_new_transform:
            profile["transform"] = rasterio.Affine(*affine_transform.ravel())
            with rasterio.open(output_path, "w", **profile) as ds:
                for i in range(0, profile["count"]):
                    ds.write(img[:, :, i], i + 1)
        else:
            with rasterio.open(output_path, "w", **profile) as ds:
                if profile["count"] == 1:
                    ds.write(warped_img, 1)
                else:
                    for i in range(0, profile["count"]):
                        ds.write(warped_img[:, :, i], i + 1)

    return warped_img


def make_difference_gif(
    images_list: list[str],
    output_path: str,
    titles_list: list[str] = [],
    scale_factor: float = -1.0,
    mosaic_scenes: bool = False,
    mosaic_offsets_x: int = 0,
    mosaic_offsets_y: int = 0,
    fps: int = 3,
    font_scale: float = 1.5,
    thickness: int = 3,
    color: tuple = (255, 0, 0),
    origin: tuple = (5, 50),
) -> None:
    """Makes a GIF from a list of images with titles and optional scaling.

    Parameters
    ----------
    images_list : list[str]
        List of image file paths to be included in the GIF.
    output_path : str
        Output path for the generated GIF.
    titles_list : list[str], optional
        List of titles for each image, by default []
    scale_factor : float, optional
        Scale factor for downsampling the images, by default -1.0
    mosaic_scenes : bool, optional
        Flag to indicate if the images should be mosaiced, by default False
    mosaic_offsets_x : int, optional
        Offset mosaic size in the x direction for the mosaic, by default 0
    mosaic_offsets_y : int, optional
        Offset mosaic size in the y direction for the mosaic, by default 0
    fps : int, optional
        Frames per second for the GIF, by default 3
    font_scale : float, optional
        Size of the font for titles, by default 1.5
    thickness : int, optional
        Thickness of the text for titles, by default 3
    color : tuple, optional
        Color of the text for titles, by default (255, 0, 0)
    origin : tuple, optional
        Origin point for the text placement, by default (5, 50)
    """
    os.makedirs("temp", exist_ok=True)
    temp_paths = [os.path.join("temp", os.path.basename(f)) for f in images_list]

    if scale_factor != -1.0:
        for i, p in enumerate(temp_paths):
            downsample_dataset(images_list[i], scale_factor, p)
    else:
        temp_paths = images_list

    if len(titles_list) > 0:
        assert len(titles_list) == len(
            images_list
        ), "Length of provided list of titles does not match the number of images."
    else:
        titles_list = [os.path.splitext(os.path.basename(f))[0] for f in images_list]

    images = []
    font = cv.FONT_HERSHEY_SIMPLEX
    if mosaic_scenes:
        _, warps, _ = make_mosaic(
            temp_paths,
            mosaic_offsets_x,
            mosaic_offsets_y,
            return_warps=True,
        )
        for i, warp in enumerate(warps):
            cv.putText(
                warp,
                titles_list[i],
                origin,
                font,
                font_scale,
                color,
                thickness,
                cv.LINE_AA,
            )
            images.append(warp)
    else:
        temp_images = []
        transforms = []
        for i, p in enumerate(temp_paths):
            img_raster = rasterio.open(p)
            transforms.append(img_raster.profile["transform"])
            img = img_raster.read()
            img = flip_img(img).copy().astype("uint8")
            if (len(img.shape) == 3) and (img.shape[2] == 1):
                img = img[:, :, 0]
            temp_images.append(img)

        for i, img in enumerate(temp_images):
            cv.putText(
                img,
                titles_list[i],
                origin,
                font,
                font_scale,
                color,
                thickness,
                cv.LINE_AA,
            )
            images.append(img)

    imageio.mimwrite(output_path, images, loop=0, fps=fps)
    shutil.rmtree("temp", ignore_errors=True)
    return None


def co_register(
    reference: Union[str, np.ndarray],
    targets=Union[
        str, np.ndarray, list[str], list[np.ndarray], list[Union[str, np.ndarray]]
    ],
    number_of_iterations: int = 30,
    termination_eps: float = 0.03,
    of_params: dict = dict(
        # params for ShiTomasi corner detection
        feature_params=dict(
            maxCorners=20000,
            qualityLevel=0.1,
            minDistance=10,
            blockSize=15,
        ),
        # Parameters for lucas kanade optical flow
        lk_params=dict(
            winSize=(25, 25),
            maxLevel=1,
        ),
    ),
    output_path: str = "",
    export_outputs: bool = True,
    fps: int = 3,
    of_dist_thresh: Union[None, int, float] = 2,  # pixels
    phase_corr_filter: bool = True,
    phase_corr_signal_thresh: float = 0.9,
    phase_corr_valid_num_points=10,
    rethrow_error: bool = False,
    resampling_resolution: str = "lower",
    laplacian_kernel_size: Union[None, int, list] = None,
    laplacian_for_targets_ids: list | None = None,
    lower_of_dist_thresh: Union[None, int, float] = None,
    band_number: Union[None, int] = None,
    no_export_when_any_failed: bool = False,
    affine_transform_targets: bool = False,
    directional_filtering: bool = False,
    no_ransac: bool = False,
    shift_method: Literal["mean", "median", "affine"] = "mean",
    big_shifts_mode: bool = False,
    big_shifts_corr_win_size: tuple = (256, 256),
) -> tuple:
    """
    Co-registers the target images to the reference image using optical flow and phase correlation.

    Parameters
    ----------
    reference: Union[str, np.ndarray]
        Path to the reference image or a numpy array of the reference image.
    targets: Union[str, np.ndarray, list[str], list[np.ndarray], list[Union[str, np.ndarray]]]
        Path to the target image(s) or a numpy array of the target image(s). Can be a single image or a list of images.
    number_of_iterations: int, Optional
        Number of iterations for the optical flow algorithm, by default 30.
    termination_eps: float, Optional
        Termination epsilon for the optical flow algorithm, by default 0.03.
    of_params: dict, Optional
        Parameters for the optical flow algorithm, by default dict(
            feature_params=dict(maxCorners=20000, qualityLevel=0.1, minDistance=10, blockSize=15),
            lk_params=dict(winSize=(25, 25), maxLevel=1),
        ).
    output_path: str, Optional
        Path to save the output images, by default "" (no output).
    export_outputs: bool, Optional
        Whether to export the output images, by default True.
    fps: int, Optional
        Frames per second for the GIF, by default 3.
    of_dist_thresh: Union[None, int, float], Optional
        Distance threshold for the optical flow points, by default 2 (pixels).
    phase_corr_filter: bool, Optional
        Whether to apply phase correlation filtering, by default True.
        In big shifts mode, it acts as a local phase correlation operator to evaluate local shifts in tie points. Turning this off in big shifts mode switched the local phase correlation to a global one.
    phase_corr_signal_thresh: float, Optional
        Signal threshold for the phase correlation filtering, by default 0.9.
    phase_corr_valid_num_points: int, Optional
        Minimum number of valid points for the phase correlation filtering, by default 10.
    rethrow_error: bool, Optional
        Whether to rethrow errors during the co-registration process, by default False.
    resampling_resolution: str, Optional
        Resolution for resampling the images, by default "lower". Can be "lower" or "higher".
    laplacian_kernel_size: Union[None, int, list], Optional
        Kernel size for the Laplacian filter, by default None (no filtering). If a list is provided, it will be applied to each target image.
    laplacian_for_targets_ids: list | None, Optional
        List of target image indices for which to apply the Laplacian filter, by default None (apply to all targets).
    lower_of_dist_thresh: Union[None, int, float], Optional
        Lower distance threshold for filtering the points, by default None (no lower threshold).
    band_number: Union[None, int], Optional
        Band number to use for the target images, by default None (use all bands). If specified, it will select the band from the target images.
    no_export_when_any_failed: bool, Optional
        If True, no output will be exported if any target image fails to co-register, by default False.
    affine_transform_targets: bool, Optional
        If True, applies the affine transformation to the target images instead of translation by mean shifts, by default False.
    directional_filtering: bool, Optional
        If True, filters distance per direction (x and y) instead of Euclidean distance, by default False.
    no_ransac: bool, Optional
        If True, skips the RANSAC step for outlier removal, by default False.
    shift_method: Literal["mean", "median", "affine"], Optional
        Method for calculating shifts. "mean" for mean shifts, "median" for median shifts, "affine" for affine transformation, by default "mean".
    big_shifts_mode: bool, Optional
        If True, enables big shifts mode for handling large displacements, by default False.
    big_shifts_corr_win_size: tuple, Optional
        Window size for phase correlation in big shifts mode, by default (256, 256).

    Returns
    -------
    tuple
        A tuple containing list of aligned target images, shifts applied to each target image, and IDs of the processed target images.

    Raises
    ------
    Exception
        If an error occurs during the co-registration process and `rethrow_error` is True,
        the error will be rethrown.
    """

    run_start = full_start = time.time()

    criteria = (
        cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT,
        number_of_iterations,
        termination_eps,
    )

    if (type(targets) == str) or (type(targets) == np.ndarray):
        targets = [targets]

    ref_raster = rasterio.open(reference)
    tgt_profiles = []
    for tgt in targets:
        tgt_raster = rasterio.open(tgt)
        tgt_profiles.append(tgt_raster.profile)

    ref_transform = ref_raster.profile["transform"]
    tgt_transforms = [profile["transform"] for profile in tgt_profiles]
    all_transforms = [ref_transform] + tgt_transforms
    ref_width = ref_raster.profile["width"]
    ref_height = ref_raster.profile["height"]
    tgt_widths = [profile["width"] for profile in tgt_profiles]
    tgt_heights = [profile["height"] for profile in tgt_profiles]
    all_widths = [ref_width] + tgt_widths
    all_heights = [ref_height] + tgt_heights

    transform_condition = len(set(all_transforms)) > 1
    shape_condition = (len(set(all_widths)) > 1) or (len(set(all_heights)) > 1)
    use_overlap = transform_condition or shape_condition
    if use_overlap:
        print("Using overlapping regions of the reference and target images.")
        tgt_imgs = []
        tgt_origs = []
        ref_imgs = []
        scale_factors = []
        for i, tgt in enumerate(targets):
            tgt_origs.append(flip_img(rasterio.open(tgt).read().copy().astype("uint8")))
            _, (_, _, ref_overlap, tgt_overlap), scale_facrtors_temp = find_overlap(
                reference, tgt, True, resampling_resolution=resampling_resolution
            )

            scale_factors.append(scale_facrtors_temp[1])

            if len(ref_overlap.shape) > 2:
                if ref_overlap.shape[2] == 1:
                    ref_overlap = ref_overlap[:, :, 0]
                else:
                    if band_number is not None:
                        ref_overlap = ref_overlap[:, :, band_number]
                    else:
                        ref_overlap = cv.cvtColor(ref_overlap, cv.COLOR_BGR2GRAY)

            if len(tgt_overlap.shape) > 2:
                if tgt_overlap.shape[2] == 1:
                    tgt_overlap = tgt_overlap[:, :, 0]
                else:
                    if band_number is not None:
                        tgt_overlap = tgt_overlap[:, :, band_number]
                    else:
                        tgt_overlap = cv.cvtColor(tgt_overlap, cv.COLOR_BGR2GRAY)

            ref_imgs.append(ref_overlap)
            tgt_imgs.append(tgt_overlap)
    else:
        scale_factors = [[1.0, 1.0]] * len(targets)
        if type(reference) == str:
            ref_img = flip_img(ref_raster.read().copy())
            if ref_img.shape[2] == 1:
                ref_img = ref_img[:, :, 0]
            else:
                if band_number is not None:
                    ref_img = ref_img[:, :, band_number]
                else:
                    ref_img = cv.cvtColor(ref_img, cv.COLOR_BGR2GRAY)
        else:
            if len(reference.shape) == 2:
                ref_img = reference
            else:
                if band_number is not None:
                    ref_img = ref_img[:, :, band_number]
                else:
                    ref_img = cv.cvtColor(reference, cv.COLOR_BGR2GRAY)
        ref_img = ref_img.astype("uint8")

        tgt_imgs = []
        tgt_origs = []
        for tgt in targets:
            if type(tgt) == str:
                tgt_raster = rasterio.open(tgt)
                img = flip_img(tgt_raster.read().copy())
                tgt_origs.append(img.astype("uint8"))
                if img.shape[2] == 1:
                    img = img[:, :, 0]
                else:
                    if band_number is not None:
                        img = img[:, :, band_number]
                    else:
                        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                tgt_imgs.append(img.astype("uint8"))
            else:
                if len(tgt.shape) == 2:
                    tgt_imgs.append(tgt.astype("uint8"))
                else:
                    tgt_imgs.append(cv.cvtColor(tgt, cv.COLOR_BGR2GRAY).astype("uint8"))
                tgt_origs.append(tgt.astype("uint8"))

    ref_imgs_temp = []
    if laplacian_kernel_size is not None:
        if laplacian_for_targets_ids is None:
            laplacian_for_targets_ids = list(range(len(tgt_imgs)))
        if use_overlap:
            for ref_img in ref_imgs:
                ref_imgs_temp.append(
                    cv.Laplacian(ref_img, cv.CV_8U, ksize=laplacian_kernel_size)
                )
            grey_refs = ref_imgs.copy()
            ref_imgs = ref_imgs_temp.copy()
            ref_imgs_temp = None
        else:
            grey_ref = ref_img.copy()
            ref_img_laplacian = cv.Laplacian(
                ref_img, cv.CV_8U, ksize=laplacian_kernel_size
            )

    tgt_imgs_temp = []
    if laplacian_kernel_size is not None:
        for i, tgt_img in enumerate(tgt_imgs):
            if i in laplacian_for_targets_ids:
                tgt_imgs_temp.append(
                    cv.Laplacian(tgt_img, cv.CV_8U, ksize=laplacian_kernel_size)
                )
            else:
                tgt_imgs_temp.append(tgt_img.copy())
        tgt_imgs = tgt_imgs_temp.copy()
        tgt_imgs_temp = None

    if export_outputs:
        if (type(reference) != str) or (any(type(el) != str for el in targets)):
            print(
                "To generate output GeoTiffs or GIF animation all inputs should be string paths to input scenes. Setting related flags to False."
            )
            export_outputs = False
            os.makedirs(output_path, exist_ok=True)

    tgt_aligned_list = []
    processed_tgt_images = []
    processed_output_images = []
    shifts = []
    process_ids = []
    all_successful = True

    if export_outputs:
        aligned_output_dir = os.path.join(output_path, "Aligned")
        os.makedirs(aligned_output_dir, exist_ok=True)
    for i, tgt_img in enumerate(tgt_imgs):
        if use_overlap:
            ref_img = ref_imgs[i]

        if laplacian_kernel_size is not None:
            if i not in laplacian_for_targets_ids:
                if use_overlap:
                    ref_img = grey_refs[i]
                else:
                    ref_img = grey_ref
            else:
                if use_overlap:
                    ref_img = ref_imgs[i]
                else:
                    ref_img = ref_img_laplacian
                print("Applying Laplacian filter...")

        try:
            use_corr_shifts = False
            if big_shifts_mode:
                corr_shifts = cv.phaseCorrelate(
                    np.float32(tgt_img), np.float32(ref_img), None
                )[0]

                if any([abs(cs) > of_dist_thresh for cs in corr_shifts]):
                    print(
                        f"For target {i} ({os.path.basename(targets[i])}), calculating large shifts using phase correlation..."
                    )
                    print(
                        f"Initial shifts from phase correlation => x: {corr_shifts[0]}, y: {corr_shifts[1]} pixels."
                    )
                    use_corr_shifts = True

            p0 = cv.goodFeaturesToTrack(
                ref_img, mask=None, **of_params["feature_params"]
            )
            p1, st, _ = cv.calcOpticalFlowPyrLK(
                ref_img,
                tgt_img,
                p0,
                None,
                **of_params["lk_params"],
                criteria=criteria,
            )
            dists = np.linalg.norm(p1[st == 1] - p0[st == 1], axis=1)

            print(
                f"For target {i} ({os.path.basename(targets[i])}), found {len(p0[st == 1])} initial features."
            )
            print("Filtering features based on distance...")

            ref_good, tgt_good = filter_features(
                p0[st == 1],
                p1[st == 1],
                ref_img,
                tgt_img,
                tgt_img.shape,
                dists,
                of_dist_thresh,
                lower_of_dist_thresh,
                (i, os.path.basename(targets[i])),
                directional_filtering,
            )

            if tgt_good is None:
                print(
                    f"For target {i} ({os.path.basename(targets[i])}), couldn't find valid features for target or reference. Skipping this target.\n"
                )
                all_successful = False
                continue
            if tgt_good.shape[1] < 4:
                print(
                    f"""For target {i} ({os.path.basename(targets[i])}), couldn't find enough good features for target or reference. Num features: {tgt_good.shape[0]}\n"""
                )
                all_successful = False
                continue

            ref_good_temp = ref_good.copy()[0, :, :]
            tgt_good_temp = tgt_good.copy()[0, :, :]

            if not no_ransac:
                _, inliers = cv.estimateAffine2D(tgt_good, ref_good)
                print("Applying RANSAC filter....")
                ref_good_temp = ref_good_temp[inliers.ravel().astype(bool)]
                tgt_good_temp = tgt_good_temp[inliers.ravel().astype(bool)]

            if len(tgt_good_temp) == 0:
                print(
                    f"For target {i} ({os.path.basename(targets[i])}), no valid features found after RANSAC filtering.\n"
                )
                all_successful = False
                continue

            if phase_corr_filter:
                print(f"Applying phase correlation filter...")
                ref_good_temp, tgt_good_temp, corr_shifts = find_corrs_shifts(
                    ref_img,
                    tgt_img,
                    ref_good_temp,
                    tgt_good_temp,
                    (
                        big_shifts_corr_win_size
                        if use_corr_shifts
                        else of_params["lk_params"]["winSize"]
                    ),
                    phase_corr_signal_thresh,
                    valid_num_points=phase_corr_valid_num_points,
                )

            if use_corr_shifts:
                if not phase_corr_filter:
                    corr_shifts = np.array([corr_shifts] * len(tgt_good_temp))
                ref_good_temp = tgt_good_temp.copy() + corr_shifts

            if shift_method == "affine":
                affine_matrix, _ = cv.estimateAffine2D(tgt_good_temp, ref_good_temp)
                shift_x = np.float64(affine_matrix[0, 2])
                shift_y = np.float64(affine_matrix[1, 2])
            elif shift_method == "median":
                shift_x, shift_y = np.median(ref_good_temp - tgt_good_temp, axis=0)
            else:
                shift_x, shift_y = np.mean(ref_good_temp - tgt_good_temp, axis=0)

            num_features = ref_good_temp.shape[0]

            print(
                f"For target {i} ({os.path.basename(targets[i])}), Num features: {num_features}"
            )

            print(
                f"For target {i} ({os.path.basename(targets[i])}), shifts => x: {shift_x / scale_factors[i][1]}, y: {shift_y / scale_factors[i][0]} pixels.\n"
            )

            if shift_x == np.inf:
                print(
                    f"No valid shifts found for target {i} ({os.path.basename(targets[i])})\n"
                )
                all_successful = False
                continue

            shifts.append(
                (shift_x / scale_factors[i][1], shift_y / scale_factors[i][0])
            )

            if affine_transform_targets:
                tgt_good_temp[:, 0] = tgt_good_temp[:, 0] / scale_factors[i][1]
                tgt_good_temp[:, 1] = tgt_good_temp[:, 1] / scale_factors[i][0]
                ref_good_temp[:, 0] = ref_good_temp[:, 0] / scale_factors[i][1]
                ref_good_temp[:, 1] = ref_good_temp[:, 1] / scale_factors[i][0]
                affine_matrix, _ = cv.estimateAffine2D(tgt_good_temp, ref_good_temp)

            process_ids.append(i)

            if export_outputs:
                out_path = os.path.join(
                    aligned_output_dir, os.path.basename(targets[i])
                )
                warp_affine_dataset(
                    targets[i],
                    out_path,
                    translation_x=shift_x / scale_factors[i][1],
                    translation_y=shift_y / scale_factors[i][0],
                    affine_matrix=affine_matrix if affine_transform_targets else None,
                )
                processed_tgt_images.append(targets[i])
                processed_output_images.append(out_path)

        except Exception as e:
            print(
                f"Algorithm did not converge for target {i} ({os.path.basename(targets[i])}) {'for the reason below:' if rethrow_error else ''}\n"
            )
            if rethrow_error:
                raise
            else:
                all_successful = False
                print(e)

    run_time = time.time() - run_start

    if export_outputs and (all_successful or not no_export_when_any_failed):
        generate_results_from_raw_inputs(
            reference,
            processed_output_images,
            processed_tgt_images,
            output_dir=output_path,
            shifts=shifts,
            run_time=run_time,
            target_ids=process_ids,
            gif_fps=fps,
        )

    full_time = time.time() - full_start
    print(f"Run time: {run_time} seconds")
    print(f"Total time: {full_time} seconds")

    return tgt_aligned_list, shifts, process_ids


def generate_results_from_raw_inputs(
    ref_image: str,
    processed_output_images: list[str],
    tgt_images: list[str],
    output_dir: str,
    shifts: list[tuple],
    run_time: float,
    output_name: str = "output",
    target_ids: list | None = None,
    gif_fps: int = 3,
) -> None:
    """Generates results from raw inputs by creating GIFs and CSV files.

    Parameters
    ----------
    ref_image : str
        Reference image path.
    processed_output_images : list[str]
        List of processed output image paths.
    tgt_images : list[str]
        List od raw target image paths.
    output_dir : str
        Output directory where results will be saved.
    shifts : list[tuple]
        List of shifts applied to the images, each shift is a tuple of (x_shift, y_shift).
    run_time : float
        Runtime of the processing in seconds.
    output_name : str, optional
        Name of the output files, by default "output".
    target_ids : list | None, optional
        Ids of the processed target images, by default None.
    gif_fps : int, optional
        Frames per second for the output GIFs, by default 3. If set to 0, no GIFs will be created.

    Returns
    -------
    None
    """

    if target_ids is not None:
        assert len(target_ids) == len(
            processed_output_images
        ), "target_ids should be the same length as processed_output_images"
    else:
        target_ids = list(range(len(processed_output_images)))

    os.makedirs(output_dir, exist_ok=True)

    tgt_aligned_list = []
    ref_imgs = []
    for tgt in processed_output_images:
        _, (_, _, ref_overlap, tgt_overlap), _ = find_overlap(ref_image, tgt, True)
        ref_imgs.append(ref_overlap)
        tgt_aligned_list.append(tgt_overlap)

    datasets_paths = [ref_image] + processed_output_images
    ssims_aligned = [
        np.round(ssim(ref_imgs[id], tgt_aligned_list[id], win_size=3), 3)
        for id in range(len(tgt_aligned_list))
    ]
    mse_aligned = [
        np.round(mse(ref_imgs[id], tgt_aligned_list[id]), 3)
        for id in range(len(tgt_aligned_list))
    ]
    zncc_aligned = [
        np.round(zncc(ref_imgs[id], tgt_aligned_list[id]), 3)
        for id in range(len(tgt_aligned_list))
    ]

    target_titles = [f"target_{str(i)}" for i in target_ids]

    if gif_fps != 0:
        datasets_titles = ["Reference"] + [
            f"{target_title}, ssim:{ssim_score}, mse:{mse_score}, zncc:{zncc_score}"
            for target_title, ssim_score, mse_score, zncc_score in zip(
                target_titles, ssims_aligned, mse_aligned, zncc_aligned
            )
        ]

        output_path = os.path.join(output_dir, f"{output_name}.gif")
        if os.path.isfile(output_path):
            os.remove(output_path)

        make_difference_gif(
            datasets_paths,
            output_path,
            datasets_titles,
            mosaic_scenes=True,
            fps=gif_fps,
        )

    tgt_raw_list = []
    ref_imgs = []
    for tgt in tgt_images:
        _, (_, _, ref_overlap, tgt_overlap), _ = find_overlap(ref_image, tgt, True)
        ref_imgs.append(ref_overlap)
        tgt_raw_list.append(tgt_overlap)

    datasets_paths = [ref_image] + tgt_images
    ssims_aligned_raw = [
        np.round(ssim(ref_imgs[id], tgt_raw_list[id], win_size=3), 3)
        for id in range(len(tgt_raw_list))
    ]
    mse_aligned_raw = [
        np.round(mse(ref_imgs[id], tgt_raw_list[id]), 3)
        for id in range(len(tgt_raw_list))
    ]
    zncc_aligned_raw = [
        np.round(zncc(ref_imgs[id], tgt_raw_list[id]), 3)
        for id in range(len(tgt_raw_list))
    ]

    if gif_fps != 0:
        datasets_titles = ["Reference"] + [
            f"{target_title}, ssim:{ssim_score}, mse:{mse_score}, zncc:{zncc_score}"
            for target_title, ssim_score, mse_score, zncc_score in zip(
                target_titles, ssims_aligned_raw, mse_aligned_raw, zncc_aligned_raw
            )
        ]

        output_path = os.path.join(output_dir, f"{output_name}_raw.gif")
        if os.path.isfile(output_path):
            os.remove(output_path)

        make_difference_gif(
            datasets_paths,
            output_path,
            datasets_titles,
            mosaic_scenes=True,
            fps=gif_fps,
        )

    output_path = os.path.join(output_dir, f"{output_name}.csv")
    if os.path.isfile(output_path):
        os.remove(output_path)

    out_ssim_df = pd.DataFrame(
        zip(
            target_titles,
            ssims_aligned_raw,
            mse_aligned_raw,
            zncc_aligned_raw,
            ssims_aligned,
            mse_aligned,
            zncc_aligned,
            [np.round(run_time, 2).tolist()] * len(target_titles),
            [
                tuple([np.round(el.tolist(), 3).tolist() for el in shift])
                for shift in shifts
            ],
        ),
        columns=[
            "Title",
            "SSIM Raw",
            "MSE Raw",
            "ZNCC Raw",
            "SSIM Aligned",
            "MSE Aligned",
            "ZNCC Aligned",
            "Run Time",
            "Shifts",
        ],
        index=None,
    )
    out_ssim_df.to_csv(output_path, encoding="utf-8")

    return None


def karios(
    ref_image: str,
    tgt_images: list[str],
    output_dir: str,
    karios_executable: str = "karios",
    fps: int = 3,
    scan_big_shifts: bool = False,
) -> tuple:
    """Runs Karios coregistration on the provided reference and target images.

    Parameters
    ----------
    ref_image : str
        Path to the reference image.
    tgt_images : list[str]
        List of target image paths to be coregistered with the reference image.
    output_dir : str
        Output directory where the aligned images will be saved.
    karios_executable : str
        Path to the Karios executable. Default is 'karios'.
    fps : int, optional
        Frames per second for the output GIFs, by default 3.
    scan_big_shifts : bool, optional
        Whether to scan for big shifts, by default False.

    Returns
    -------
    tuple
        Dictionary of shifts and list of processed target IDs.
    """
    os.makedirs(output_dir, exist_ok=True)
    tgt_images_copy = tgt_images.copy()
    run_start = full_start = time.time()
    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    ref_profile = rasterio.open(ref_image).profile
    tgt_profiles = [rasterio.open(t).profile for t in tgt_images_copy]
    ds_profiles = tgt_profiles.copy()
    ref_images = [ref_image] * len(tgt_images_copy)

    for i, tgt_profile in enumerate(tgt_profiles):
        downsample = False
        if tgt_profile["height"] != ref_profile["height"]:
            print(
                f"Target image {tgt_images_copy[i]} has different height than reference image {ref_image}"
            )
            downsample = True
        if tgt_profile["width"] != ref_profile["width"]:
            print(
                f"Target image {tgt_images_copy[i]} has different width than reference image {ref_image}"
            )
            downsample = True
        if downsample:
            os.makedirs(f"{output_dir}/downsampled", exist_ok=True)
            find_overlap(
                ref_image,
                tgt_images_copy[i],
                output_dir=f"{output_dir}/downsampled/tgt_{i}",
            )
            tgt_images_copy[i] = os.path.join(
                f"{output_dir}/downsampled/tgt_{i}",
                os.path.basename(tgt_images_copy[i]),
            )
            ds_profiles[i] = rasterio.open(tgt_images_copy[i]).profile
            ref_images[i] = os.path.join(
                f"{output_dir}/downsampled/tgt_{i}", os.path.basename(ref_images[i])
            )

    log_file = f"{output_dir}/karios.log"
    if os.path.isfile(log_file):
        os.remove(log_file)
    for i, tgt_image in enumerate(tgt_images_copy):
        try:
            cmd = f"{karios_executable} process {tgt_image} {ref_images[i]} --out {output_dir} --log-file-path {log_file} "
            if scan_big_shifts:
                cmd += "--enable-large-shift-detection "
            print(f"Running {cmd}")
            run(shlex.split(cmd))
        except Exception as e:
            print(f"Error running karios for {tgt_image}: {e}")
            continue

    shutil.rmtree(temp_dir, ignore_errors=True)
    tgt_images_copy = tgt_images.copy()

    scene_names = []
    shifts = []
    target_ids = []
    for i, tgt_image in enumerate(tgt_images_copy):
        line_found = False
        mean_e_found = False
        mean_n_found = False
        shift_x = 0.0
        shift_y = 0.0
        with open(log_file, "r") as f:
            for line in f:
                if (os.path.basename(tgt_image) in line) and ("Process" in line):
                    line_found = True
                if line_found:
                    if scan_big_shifts:
                        if "Large offset found:" in line:
                            splits = line.strip().split()
                            if splits[-4] != "nan" or splits[-1] != "nan":
                                scene_names.append(tgt_images[i])
                                shifts.append(
                                    [
                                        -float(splits[-1].replace("]", "")),
                                        -float(splits[-2].replace("[", "")),
                                    ]
                                )
                                target_ids.append(i)
                            break
                    else:
                        if "Easting displacement (meter):" in line:
                            mean_e_found = True
                        if mean_e_found and "Mean :" in line:
                            splits = line.strip().split(" ")
                            if splits[2] != "nan":
                                shift_x = float(splits[2])
                            mean_e_found = False
                        if "Northing displacement (meter):" in line:
                            mean_n_found = True
                        if mean_n_found and "Mean :" in line:
                            splits = line.strip().split(" ")
                            if splits[2] != "nan":
                                shift_y = float(splits[2])
                            mean_n_found = False
                            scene_names.append(tgt_images[i])
                            shifts.append(
                                [
                                    shift_x / abs(ds_profiles[i]["transform"].a),
                                    shift_y / abs(ds_profiles[i]["transform"].e),
                                ]
                            )
                            target_ids.append(i)
                            break

    shifts_dict = {}
    for f, sh in zip(scene_names, shifts):
        shifts_dict[f] = sh

    os.makedirs(f"{output_dir}/Aligned", exist_ok=True)
    processed_output_images = []
    processed_tgt_images = []
    final_shifts = []
    for key in list(shifts_dict.keys()):
        output_path = os.path.join(f"{output_dir}/Aligned", os.path.basename(key))
        shift_x, shift_y = shifts_dict[key]
        warp_affine_dataset(
            key, output_path, translation_x=shift_x, translation_y=shift_y
        )
        processed_output_images.append(output_path)
        processed_tgt_images.append(key)
        final_shifts.append((np.float64(shift_x), np.float64(shift_y)))

    run_time = time.time() - run_start
    generate_results_from_raw_inputs(
        ref_image,
        processed_output_images,
        processed_tgt_images,
        output_dir=output_dir,
        shifts=final_shifts,
        run_time=run_time,
        target_ids=target_ids,
        gif_fps=fps,
    )
    full_time = time.time() - full_start
    print(f"Run time: {run_time} seconds")
    print(f"Total time: {full_time} seconds")

    return shifts_dict, target_ids


def arosics(
    ref_image: str,
    tgt_images: list[str],
    output_dir: str,
    max_points: int = None,
    r_b4match: int = 1,
    s_b4match: int = 1,
    max_iter: int = 5,
    max_shift: int = 5,
    grid_res: int = 250,
    min_reliability: int = 30,
    tieP_filter_level: int = 3,
    rs_max_outlier: float = 10,
    rs_tolerance: float = 2.5,
    existing_ref_image: str | None = None,
    existing_tgt_images: list[str] | None = None,
    fps: int = 3,
) -> tuple:
    """Runs AROSICS coregistration on the provided reference and target images.

    Parameters
    ----------
    ref_image : str
        Reference image path.
    tgt_images : list[str]
        List of target image paths to be coregistered with the reference image.
    output_dir : str
        Output directory where the aligned images will be saved.
    max_points : int, optional
        MAx number of points to be used for coregistration, by default None
    r_b4match : int, optional
        Reference band number for matching, by default 1
    s_b4match : int, optional
        Target band number for matching, by default 1
    max_iter : int, optional
        Max number of iterations for coregistration, by default 5
    max_shift : int, optional
        Maximum allowed shift in pixels, by default 5
    grid_res : int, optional
        Local grid resolution in pixels, by default 250
    min_reliability : int, optional
        Minimum tie point reliability percentage, by default 30
    tieP_filter_level : int, optional
        Tie point filter level, by default 3
    rs_max_outlier : float, optional
        Maximum outlier ratio for robust statistics, by default 10
    rs_tolerance : float, optional
        Tolerance for robust statistics, by default 2.5
    existing_ref_image : str | None, optional
        Existing reference image to force reference bounding box, by default None
    existing_tgt_images : list[str] | None, optional
        Existing target images to force target bounding boxes, by default None
    fps : int, optional
        Frames per second for the output GIFs, by default 3.

    Returns
    -------
    tuple
        List of shifts applied to each target image in the format [(shift_x, shift_y), ...] and
        List of target IDs corresponding to the shifts.
    """
    os.makedirs(output_dir, exist_ok=True)
    run_start = full_start = time.time()
    tgt_images_copy = tgt_images.copy()
    local_outputs = [
        os.path.join(
            f"{output_dir}/Aligned",
            os.path.basename(tgt),
        )
        for tgt in tgt_images_copy
    ]
    os.makedirs(f"{output_dir}/Aligned", exist_ok=True)

    processed_output_images = []
    processed_tgt_images = []
    target_ids = []
    shifts = []
    print(f"Reference image: {ref_image}")
    for i, tgt_image in enumerate(tgt_images_copy):
        print(f"Coregistering {tgt_image}")
        coreg_local = COREG_LOCAL(
            im_ref=ref_image,
            im_tgt=tgt_image,
            grid_res=grid_res,
            max_points=max_points,
            path_out=local_outputs[i],
            fmt_out="GTIFF",
            nodata=(0.0, 0.0),
            r_b4match=r_b4match,
            s_b4match=s_b4match,
            align_grids=True,
            max_iter=max_iter,
            max_shift=max_shift,
            ignore_errors=True,
            min_reliability=min_reliability,
            tieP_filter_level=tieP_filter_level,
            rs_max_outlier=rs_max_outlier,
            rs_tolerance=rs_tolerance,
            footprint_poly_ref=(
                None
                if existing_ref_image is None
                else box(*rasterio.open(existing_ref_image).bounds).wkt
            ),
            footprint_poly_tgt=(
                None
                if existing_tgt_images is None
                else box(*rasterio.open(existing_tgt_images[i]).bounds).wkt
            ),
        )
        try:
            coreg_local.correct_shifts()
            if not coreg_local.success:
                print(f"Coregistration was not successfull for {tgt_image}.")
                if os.path.isfile(local_outputs[i]):
                    print(f"Removing the corresponding output: {local_outputs[i]}")
                    os.remove(local_outputs[i])
            else:
                if existing_tgt_images is not None:
                    tgt_image = existing_tgt_images[i]
                    warp_affine_dataset(
                        tgt_image,
                        local_outputs[i],
                        translation_x=coreg_local.coreg_info["mean_shifts_px"]["x"],
                        translation_y=coreg_local.coreg_info["mean_shifts_px"]["y"],
                    )

                processed_output_images.append(local_outputs[i])
                processed_tgt_images.append(tgt_image)
                target_ids.append(i)
                shifts.append(
                    (
                        coreg_local.coreg_info["mean_shifts_px"]["x"],
                        coreg_local.coreg_info["mean_shifts_px"]["y"],
                    )
                )
        except:
            print(f"Coregistration was not successfull for {tgt_image}.")
            if os.path.isfile(local_outputs[i]):
                print(f"Removing the corresponding output: {local_outputs[i]}")
                os.remove(local_outputs[i])

    if existing_ref_image is not None:
        ref_image = existing_ref_image
    run_time = time.time() - run_start
    generate_results_from_raw_inputs(
        ref_image,
        processed_output_images,
        processed_tgt_images,
        output_dir=output_dir,
        shifts=shifts,
        run_time=run_time,
        target_ids=target_ids,
        gif_fps=fps,
    )
    full_time = time.time() - full_start
    print(f"Run time: {run_time} seconds")
    print(f"Total time: {full_time} seconds")

    return shifts, target_ids


def coreg(
    reference: str,
    targets: list[str],
    output_dir: str,
    method: Literal["co_register", "karios", "arosics"] = "co_register",
    **kwargs,
) -> tuple:
    """
    Wrapper for the co-registration functions.

    Parameters
    ----------
    reference : str
        Path to the reference image.
    targets : list[str]
        List of paths to the target images.
    method : Literal["co_register", "karios", "arosics"]
        The method to use for co-registration.
    **kwargs
        Additional keyword arguments to pass to the `method` function.
    """

    method = method.lower()
    if method == "co_register":
        _, shifts, target_ids = co_register(
            reference,
            targets,
            output_path=output_dir,
            **kwargs,
            no_export_when_any_failed=True,
        )

        failed_targets = [i for i in range(len(targets)) if i not in target_ids]

        if len(failed_targets) > 0:
            print("Re-running co-registration with Laplacian filter for failed targets")
            print("\r")

            shutil.rmtree(output_dir, ignore_errors=True)

            _, shifts, target_ids = co_register(
                reference,
                targets,
                output_path=output_dir,
                **kwargs,
                laplacian_kernel_size=kwargs.get("laplacian_kernel_size", 5),
                laplacian_for_targets_ids=failed_targets,
            )
    elif method == "karios":
        shifts, target_ids = karios(
            reference,
            targets,
            output_dir,
            **kwargs,
        )
    elif method == "arosics":
        shifts, target_ids = arosics(
            reference,
            targets,
            output_dir,
            **kwargs,
        )
    else:
        raise ValueError(
            f"Method {method} not recognized. Use 'co_register', 'karios', or 'arosics'."
        )
    return shifts, target_ids


def zncc(template: np.ndarray, image_patch: np.ndarray) -> float:
    """
    Calculates the Zero-Normalized Cross-Correlation (ZNCC) between a template
    and an image patch.

    Parameters
    ----------
    template : np.ndarray
        The template image or signal.
    image_patch : np.ndarray
        The image patch or signal to compare with the template.

    Returns
    -------
        float: The ZNCC score, a scalar value between -1 and 1.
               1 indicates a perfect match, -1 indicates a perfect mismatch,
               and 0 indicates no correlation.
    """

    # Ensure inputs are NumPy arrays
    template = np.array(template, dtype=np.float64)
    image_patch = np.array(image_patch, dtype=np.float64)

    # Check if the dimensions match
    if template.shape != image_patch.shape:
        raise ValueError("Template and image patch must have the same dimensions.")

    # Subtract the mean from both the template and the image patch
    template_mean_subtracted = template - np.mean(template)
    image_patch_mean_subtracted = image_patch - np.mean(image_patch)

    # Calculate the standard deviation of both
    template_std = np.std(template)
    image_patch_std = np.std(image_patch)

    # Handle cases where standard deviation is zero to avoid division by zero
    if template_std == 0 or image_patch_std == 0:
        return 0.0  # Or handle as an error depending on desired behavior

    # Calculate the ZNCC score
    numerator = np.sum(template_mean_subtracted * image_patch_mean_subtracted)
    denominator = (
        template_std * image_patch_std * template.size
    )  # template.size is equivalent to N in the formula

    return numerator / denominator


