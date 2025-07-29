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

Last modified: July 2025
"""

from math import sqrt

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .spatial import add_geobox


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
        stats_dict.update({
            "Regression p-value": lin_reg.pvalue,
            "Regression intercept": lin_reg.intercept,
            "Regression standard error": lin_reg.stderr,
        })

    # Return as
    return pd.Series(stats_dict).round(round)


def xr_random_sampling(
    da,
    n=None,
    sampling="stratified_random",
    manual_class_ratios=None,
    oversample_factor=5,
    out_fname=None,
    verbose=True,
):
    """
    Efficient and scalable random sampling of a 2D classified xarray.DataArray.
    Returns a GeoDataFrame of point samples based on specified sampling strategy.

    Parameters
    ----------
    da : xarray.DataArray
        A classified 2-dimensional xarray.DataArray
    n : int
        Total number of points to sample. Ignored if providing
        a dictionary of {class:numofpoints} to 'manual_class_ratios'
    sampling : str, optional
        The sampling strategy to use. Options include:
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
    manual_class_ratios : dict, optional
        If setting sampling to 'manual', the provide a dictionary
        of type {'class': numofpoints} mapping the number of points
        to generate for each class.
    oversample_factor : float, optional (default=5)
        A multiplier used to increase the number of random candidate pixels
        initially drawn when sampling very large classes (>1 billion pixels).
        For such large classes, the function randomly samples a subset of
        pixel coordinates and checks which ones match the target class.
        To reduce the chance of undersampling, `oversample_factor` controls
        how many candidate coordinates are initially drawn.
        For example, if 100 samples are required and `oversample_factor=5`,
        500 random (x, y) coordinates will be sampled first. Only those matching
        the class will be retained and then randomly subsampled down to the desired
        number of samples. If too few valid matches are found, a warning is issued.
        Increasing this value can improve success rates when sampling sparse or
        spatially fragmented classes in large datasets, at the cost of more memory
        and computation.
    out_fname : str, optional
        If providing a filepath name, e.g 'sample_points.geojson', the
        function will export a geojson (or shapefile) of the sampling
        points to file.
    verbose: bool, optional (default=True)
        If True, print statements will track progress and print warnings

    Returns
    -------
    geopandas.GeoDataFrame

    """
    # perform checks on the inputs
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
        raise ValueError("Input DataArray must not have more than two dimensions")

    if not isinstance(da, xr.DataArray):
        raise ValueError("This function only accepts xarray.DataArrays as input")

    # Ensure da has a .odc.* accessor using odc.geo.
    da = add_geobox(da)

    # Obtain spatial dim names
    y_dim, x_dim = da.odc.spatial_dims

    # grab data as numpy arrays and count classes
    data = da.values

    unique_classes, class_counts = np.unique(data[~np.isnan(data)], return_counts=True)

    unique_classes = unique_classes.astype(int)

    # store our samples in a list
    samples = []

    if sampling == "random":
        # first check num of samples doesn't exceed pixels
        total_valid = (~np.isnan(data)).sum()
        if n > total_valid:
            raise ValueError("Requested more samples than available valid pixels.")

        if verbose:
            print(f"Sampling {n} points")

        # determine flat indices of the non-Nans
        flat_indices = np.flatnonzero(~np.isnan(data))

        # sample the flat indices
        sampled = np.random.choice(flat_indices, size=n, replace=False)

        # get coords and class values from sample indices
        for idx in sampled:
            y, x = np.unravel_index(idx, data.shape)
            y_val = da[y_dim].values[y]
            x_val = da[x_dim].values[x]
            cls = data[y, x]
            samples.append((y_val, x_val, int(cls)))

    elif sampling in ["stratified_random", "equal_stratified_random", "manual"]:
        if sampling == "equal_stratified_random":
            # divide n by the number of classes
            n_per_class = int(np.ceil(n / len(unique_classes)))
            class_sample_sizes = dict.fromkeys(unique_classes, n_per_class)

        elif sampling == "stratified_random":
            # calculate relative proportions of classes.
            proportions = class_counts / class_counts.sum()
            class_sample_sizes = {cls: int(np.round(n * prop)) for cls, prop in zip(unique_classes, proportions)}

        elif sampling == "manual":
            if not isinstance(manual_class_ratios, dict):
                raise ValueError("Must provide manual_class_ratios for manual sampling.")

            class_sample_sizes = {int(k): int(v) for k, v in manual_class_ratios.items()}

        for cls in class_sample_sizes:
            sample_size = class_sample_sizes[cls]

            if verbose:
                print(f"Class {cls}: sampling {sample_size} points")

            class_count = (data == cls).sum()

            if class_count > 1e9:  # For v. large classes, sample random coords first and check matches
                # Try oversampling until we get enough
                n_try = int(sample_size * oversample_factor)
                rand_x = np.random.choice(np.arange(len(da.x)), n_try, replace=False)

                rand_y = np.random.choice(np.arange(len(da.y)), n_try, replace=False)

                # find matches with class id
                match = data[rand_y, rand_x] == cls
                rand_y, rand_x = rand_y[match], rand_x[match]

                # check if matches is less than requested sample size
                #  and return samples with a warning
                if len(rand_y) < sample_size:
                    if verbose:
                        print(
                            f"Warning: insufficient matches for class {cls}, "
                            f"try increasing oversampling. Returning {len(rand_y)} matches"
                        )

                    idx = np.random.choice(np.arange(len(rand_y)), size=len(rand_y), replace=False)
                    for i in idx:
                        y = da[y_dim].values[rand_y[i]]
                        x = da[x_dim].values[rand_x[i]]
                        samples.append((y, x, cls))

                else:
                    # If more matches than samples, then randomly sample the matches so we get the
                    # the right number of samples.
                    idx = np.random.choice(np.arange(len(rand_y)), size=sample_size, replace=False)
                    for i in idx:
                        y = da[y_dim].values[rand_y[i]]
                        x = da[x_dim].values[rand_x[i]]
                        samples.append((y, x, cls))

            else:
                # if class size is less than a billion, then sample class mask
                class_mask = data == cls
                flat_indices = np.flatnonzero(class_mask)

                # Check if enough pixels exist
                if flat_indices.size < sample_size:
                    if verbose:
                        print(f"Warning: not enough pixels in class {cls} for given sample size, skipping")
                    continue

                # Randomly sample from those flat indices
                sampled = np.random.choice(flat_indices, size=sample_size, replace=False)

                # Convert flat indices to (y, x), then to coordinates
                for idx in sampled:
                    y_idx, x_idx = np.unravel_index(idx, data.shape)
                    y = da[y_dim].values[y_idx]
                    x = da[x_dim].values[x_idx]
                    samples.append((y, x, cls))

    if len(samples) == 0:
        raise RuntimeError("No samples collected. Check input conditions.")

    # Add samples to geodataframe
    df = pd.DataFrame(samples, columns=["y", "x", "class"])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y), crs=f"EPSG:{da.odc.crs.epsg}")
    gdf = gdf.drop(["x", "y"], axis=1)

    if out_fname:
        gdf.to_file(out_fname)

    return gdf
