# validation.py
"""
Tools for validating outputs and producing accuracy assessment metrics.

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

Last modified: April 2023
"""

import numpy as np
import pandas as pd
import xarray as xr
import odc.geo.xr
from math import sqrt
from scipy import stats
import geopandas as gpd
from odc.geo.xr import assign_crs
from shapely.geometry import Point
from sklearn.metrics import mean_absolute_error, mean_squared_error


def eval_metrics(x, y, round=3, all_regress=False):
    """
    Calculate a set of common statistical metrics
    based on two input actual and predicted vectors.

    These include:
        - Pearson correlation
        - Root Mean Squared Error
        - Mean Absolute Error
        - R-squared
        - Bias
        - Linear regression parameters (slope,
          p-value, intercept, standard error)

    Parameters
    ----------
    x : numpy.array
        An array providing "actual" variable values
    y : numpy.array
        An array providing "predicted" variable values
    round : int
        Number of decimal places to round each metric
        to. Defaults to 3
    all_regress : bool
        Whether to return linear regression p-value,
        intercept and standard error (in addition to
        only regression slope). Defaults to False

    Returns
    -------
    A pandas.Series containing calculated metrics
    """

    # Create dataframe to drop na
    xy_df = pd.DataFrame({"x": x, "y": y}).dropna()

    # Compute linear regression
    lin_reg = stats.linregress(x=xy_df.x, y=xy_df.y)

    # Calculate statistics
    stats_dict = {
        "Correlation": xy_df.corr().iloc[0, 1],
        "RMSE": sqrt(mean_squared_error(xy_df.x, xy_df.y)),
        "MAE": mean_absolute_error(xy_df.x, xy_df.y),
        "R-squared": lin_reg.rvalue**2,
        "Bias": (xy_df.y - xy_df.x).mean(),
        "Regression slope": lin_reg.slope,
    }

    # Additional regression params
    if all_regress:
        stats_dict.update(
            {
                "Regression p-value": lin_reg.pvalue,
                "Regression intercept": lin_reg.intercept,
                "Regression standard error": lin_reg.stderr,
            }
        )

    # Return as
    return pd.Series(stats_dict).round(round)


def random_sampling(
    da, n=None,
    sampling="stratified_random",
    manual_class_ratios=None,
    out_fname=None,
    oversample_factor=5
):
    """
    Efficient and scalable random sampling of a 2D classified xarray.DataArray.
    Returns a GeoDataFrame of point samples based on specified sampling strategy.

    Params:
    -------
    da: xarray.DataArray
        A classified 2-dimensional xarray.DataArray
    n: int
        Total number of points to sample. Ignored if providing
        a dictionary of {class:numofpoints} to 'manual_class_ratios'
    sampling: str
        'stratified_random' = Create points that are randomly
        distributed within each class, where each class has a
        number of points proportional to its relative area.
        'equal_stratified_random' = Create points that are randomly
        distributed within each class, where each class has the
        same number of points.
        'random' = Create points that are randomly distributed
        throughout the image.
        'manual' = user definined, each class is allocated a
        specified number of points, supply a manual_class_ratio
        dictionary mapping number of points to each class
    manual_class_ratios: dict
        If setting sampling to 'manual', the provide a dictionary
        of type {'class': numofpoints} mapping the number of points
        to generate for each class.
    out_fname: str
        If providing a filepath name, e.g 'sample_points.shp', the
        function will export a shapefile/geojson of the sampling
        points to file.

    Output
    ------
    GeoPandas.Dataframe

    """

    if sampling not in [
        "stratified_random",
        "equal_stratified_random",
        "random",
        "manual",
    ]:
        raise ValueError(
            "Sampling strategy must be one of 'stratified_random', 'equal_stratified_random', 'random', or 'manual'"
        )

    if "time" in da.dims:
        raise ValueError("Input DataArray must not have a 'time' dimension.")

    if len(da.dims) > 2:
        raise ValueError(
            "Input DataArray must not have more than two dimensions")

    if not isinstance(da, xr.DataArray):
        raise ValueError(
            "This function only accepts xarray.DataArrays as input")

    # Standardize spatial dims
    x_names = ["x", "longitude", "lon"]
    y_names = ["y", "latitude", "lat"]
    x_dim = next((dim for dim in da.dims if dim.lower() in x_names), None)
    y_dim = next((dim for dim in da.dims if dim.lower() in y_names), None)
    if x_dim is None or y_dim is None:
        raise ValueError(
            f"Could not infer spatial dimensions. Found dims: {da.dims}")
    da = da.rename({x_dim: "x", y_dim: "y"})

    #grab data as numpy arrays and count classes
    data = da.values
    unique_classes, class_counts = np.unique(
        data[~np.isnan(data)], return_counts=True)
    unique_classes = unique_classes.astype(int)

    samples = []

    def unravel_sample(flat_idx):
        y_idx, x_idx = np.unravel_index(flat_idx, data.shape)
        return da["y"].values[y_idx], da["x"].values[x_idx]

    if sampling == "random":
        total_valid = (~np.isnan(data)).sum()
        if n > total_valid:
            raise ValueError(
                "Requested more samples than available valid pixels.")
        print(f"Sampling {n} points")
        flat_indices = np.flatnonzero(~np.isnan(data))
        sampled = np.random.choice(flat_indices, size=n, replace=False)
        for idx in sampled:
            y, x = np.unravel_index(idx, data.shape)
            y_val = da["y"].values[y]
            x_val = da["x"].values[x]
            cls = data[y, x]
            samples.append((y_val, x_val, int(cls)))

    elif sampling in ["stratified_random", "equal_stratified_random", "manual"]:
        if sampling == "equal_stratified_random":
            n_per_class = int(np.ceil(n / len(unique_classes)))
            class_sample_sizes = {cls: n_per_class for cls in unique_classes}
        elif sampling == "stratified_random":
            proportions = class_counts / class_counts.sum()
            class_sample_sizes = {
                cls: int(np.round(n * prop))
                for cls, prop in zip(unique_classes, proportions)
            }
        elif sampling == "manual":
            if not isinstance(manual_class_ratios, dict):
                raise ValueError(
                    "Must provide manual_class_ratios for manual sampling."
                )
            class_sample_sizes = {
                int(k): int(v) for k, v in manual_class_ratios.items()
            }

        for cls in class_sample_sizes:
            sample_size = class_sample_sizes[cls]
            print(f"Class {cls}: sampling {sample_size} points")

            class_mask = data == cls
            class_count = class_mask.sum()
            if (
                class_count > 1e9
            ):  # For v. large classes, sample random coords first and check matches
                # Try oversampling until we get enough
                n_try = int(sample_size * oversample_factor)
                rand_x = np.random.choice(
                    np.arange(len(da.x)), n_try, replace=False)
                
                rand_y = np.random.choice(
                    np.arange(len(da.y)), n_try, replace=False)
                
                match = data[rand_y, rand_x] == cls
                rand_y, rand_x = rand_y[match], rand_x[match]
                if len(rand_y) < sample_size:
                    print(f"Warning: insufficient matches for class {cls}, "
                          f"try increasing oversampling. Returning {len(rand_y)-1} matches")

                    idx = np.random.choice(np.arange(len(rand_y)), size=len(rand_y) - 1, replace=False)
                    for i in idx:
                        y = da["y"].values[rand_y[i]]
                        x = da["x"].values[rand_x[i]]
                        samples.append((y, x, cls))

                else:
                    idx = np.random.choice(np.arange(len(rand_y)), size=sample_size, replace=False)
                    for i in idx:
                        y = da["y"].values[rand_y[i]]
                        x = da["x"].values[rand_x[i]]
                        samples.append((y, x, cls))

            else:
                flat_idx = np.argwhere(class_mask).squeeze()
                if flat_idx.size < sample_size:
                    print(
                        f"Warning: not enough pixels in class  {cls} for given sample size, skipping")
                    continue
                picked = np.random.choice(
                    flat_idx.shape[0], sample_size, replace=False)
                ys, xs = flat_idx[picked].T
                for y_i, x_i in zip(ys, xs):
                    y = da["y"].values[y_i]
                    x = da["x"].values[x_i]
                    samples.append((y, x, cls))

    if len(samples) == 0:
        raise RuntimeError("No samples collected. Check input conditions.")

    df = pd.DataFrame(samples, columns=["y", "x", "class"])
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.x, df.y), crs=f"EPSG:{da.odc.crs.epsg}"
    )
    gdf = gdf.drop(["x", "y"], axis=1)

    if out_fname:
        gdf.to_file(out_fname)

    return gdf
