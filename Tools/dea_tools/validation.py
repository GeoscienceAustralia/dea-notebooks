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

Last modified: August 2026
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
        stats_dict.update(
            {
                "Regression p-value": lin_reg.pvalue,
                "Regression intercept": lin_reg.intercept,
                "Regression standard error": lin_reg.stderr,
            }
        )

    # Return as
    return pd.Series(stats_dict).round(round)


def xr_random_sampling(
    da,
    n=None,
    sampling="stratified_random",
    manual_class_ratios=None,
    min_sample_size=None,
    oversample_factor=5,
    random_seed=None,
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
    min_sample_size : int, optional
        Only used when sampling="stratified_random'. If provided,
        this will ensure that each class has at least this number
        of samples, even if the proportional allocation (based on relative area)
        would otherwise be smaller. Classes with fewer available pixels
        than the requested sample size will still be capped at the number of
        available pixels (i.e. a warning will still be raised if
        there aren't enough pixels to sample).
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
    random_seed : int | None, optional
        Controls the random number generation for reproducibility.
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

    # --- Setup local RNG ---
    # random_seed=None → entropy; int → reproducible
    rng = np.random.default_rng(random_seed)

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
        sampled = rng.choice(flat_indices, size=n, replace=False)

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
            class_sample_sizes = {
                cls: int(np.round(n * prop))
                for cls, prop in zip(unique_classes, proportions)
            }

            # ensure minimum sample size per class
            if min_sample_size is not None:
                for cls in class_sample_sizes:
                    if class_sample_sizes[cls] < min_sample_size:
                        if verbose:
                            print(
                                f"Class {cls}: increasing sample size from {class_sample_sizes[cls]} to {min_sample_size}."
                            )
                        class_sample_sizes[cls] = min_sample_size

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

            if verbose:
                print(f"Class {cls}: sampling {sample_size} points")

            class_count = (data == cls).sum()

            if (
                class_count > 1e9
            ):  # For v. large classes, sample random coords first and check matches
                # Try oversampling until we get enough
                n_try = int(sample_size * oversample_factor)

                rand_x = rng.choice(np.arange(len(da.x)), n_try, replace=False)
                rand_y = rng.choice(np.arange(len(da.y)), n_try, replace=False)

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
                    idx = rng.choice(
                        np.arange(len(rand_y)), size=len(rand_y), replace=False
                    )

                    for i in idx:
                        y = da[y_dim].values[rand_y[i]]
                        x = da[x_dim].values[rand_x[i]]
                        samples.append((y, x, cls))

                else:
                    # If more matches than samples, then randomly sample the matches so we get the
                    # the right number of samples.
                    idx = rng.choice(
                        np.arange(len(rand_y)), size=sample_size, replace=False
                    )

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
                        print(
                            f"Warning: not enough pixels in class {cls} for given sample size, skipping"
                        )
                    continue

                # Randomly sample from those flat indices
                sampled = rng.choice(flat_indices, size=sample_size, replace=False)

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
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.x, df.y), crs=f"EPSG:{da.odc.crs.epsg}"
    )
    gdf = gdf.drop(["x", "y"], axis=1)

    if out_fname:
        gdf.to_file(out_fname)

    return gdf


def confusion_matrix_accuracy(
    df: pd.DataFrame,
    ref_col: str,
    pred_col: str,
    class_names: list = None,
    class_order: list = None,
):
    """
    Computes a confusion matrix using a reference (ground truth)
    column and a predicted column from a pandas DataFrame
    It extends the standard confusion matrix by including:
        - Producer's accuracy (per-class recall; 1 - omission error)
        - User's accuracy (per-class precision; 1 - commission error)
        - Overall accuracy

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    ref_col : str
        Reference/ground-truth column.
    pred_col : str
        Predicted class column.
    class_names : sequence, optional
        Class names corresponding to integer labels.
        Example:
            class_names=["Water", "Forest", "Urban"]

        implies:
            0 -> Water
            1 -> Forest
            2 -> Urban

    class_order : sequence, optional
        Explicit ordering of classes. Useful when not all
        classes occur in the data.

    Returns
    -------
    pandas.DataFrame
        A confusion matrix with counts, producer's accuracy, user's accuracy,
        and overall accuracy. Rows represent actual classes, columns
        represent predicted classes, with additional rows/columns for metrics.

    """

    # Determine classes
    if class_order is None:
        classes = sorted(set(df[ref_col].dropna()) | set(df[pred_col].dropna()))
    else:
        classes = list(class_order)

    # Create crosstab
    cm = pd.crosstab(
        pd.Categorical(df[ref_col], categories=classes),
        pd.Categorical(df[pred_col], categories=classes),
        rownames=["Actual"],
        colnames=["Predicted"],
        margins=True,
    )

    # Producer's accuracy
    producer_acc = []

    for cls in classes:
        row_total = cm.loc[cls, "All"]

        if row_total > 0:
            producer_acc.append(cm.loc[cls, cls] / row_total * 100)
        else:
            producer_acc.append(np.nan)

    producer_acc.append(np.nan)

    cm["Producer's"] = producer_acc

    # User's accuracy
    users_acc = {}

    for cls in classes:
        col_total = cm.loc["All", cls]

        if col_total > 0:
            users_acc[cls] = cm.loc[cls, cls] / col_total * 100
        else:
            users_acc[cls] = np.nan

    users_acc["All"] = np.nan

    overall_accuracy = (
        np.trace(cm.loc[classes, classes].values) / cm.loc["All", "All"] * 100
    )

    users_acc["Producer's"] = overall_accuracy

    cm.loc["User's"] = users_acc

    # Rename total
    cm = cm.rename(
        columns={"All": "Total"},
        index={"All": "Total"},
    )

    # Replace integer labels with names if requested
    if class_names is not None:

        label_map = {label: name for label, name in zip(classes, class_names)}

        cm = cm.rename(
            index=label_map,
            columns=label_map,
        )

    # Replace meaningless cells nans
    cm.loc["User's", "Total"] = np.nan
    cm.loc["Total", "Producer's"] = np.nan

    return cm.round(2)


def estimate_olofsson_area(
    confusion_df: pd.DataFrame,
    map_area_df: pd.DataFrame,
    class_col: str = "class",
    area_col: str = "map_area",
    rows_are_reference: bool = True,
    z: float = 1.96,
    clip_ci: bool = True,
):
    """
    Estimate class areas and 95% uncertainty intervals following
    Olofsson et al. (2014), for stratified random sampling where map
    classes are the strata.

    Recommeded to be used in conjuction with "confusion_matrix_accuracy"

    Parameters
    ----------
    confusion_df : pandas.DataFrame
        Confusion/error matrix containing sample counts.
        The core class-by-class counts are extracted using the class
        labels in map_area_df.

        Recommeded to use dea-tools.validation.confusion_matrix_accucary for
        passing in this parameter.

        If rows_are_reference=True, rows are reference/actual classes
        and columns are map/predicted classes, as in many sklearn-style
        or validation summary matrices.

        If rows_are_reference=False, rows are map/predicted classes
        and columns are reference/actual classes, which is the orientation
        used in Olofsson et al. notation.
    map_area_df : pandas.DataFrame
        DataFrame containing class labels and mapped areas. The mapped
        areas can be pixel counts, hectares, square kilometres, etc.
        Output areas will be in the same units as area_col.
    class_col : str, default "class"
        Column in map_area_df containing class labels.
    area_col : str, default "map_area"
        Column in map_area_df containing mapped class areas.
    rows_are_reference : bool, default True
        Whether rows of confusion_df are reference/actual classes and
        columns are map/predicted classes.
    z : float, default 1.96
        Normal quantile for the confidence interval. Use 1.96 for an
        95% interval.
    clip_ci : bool, default True
        If True, lower confidence bounds are clipped to 0 and upper bounds
        are clipped to total mapped area.

    Returns
    -------
    results : pandas.DataFrame
        One row per class with mapped area, estimated reference area,
        standard error, and confidence interval.

    """

    # Validate and prepare map areas
    if class_col not in map_area_df.columns:
        raise ValueError(f"map_area_df must contain class column '{class_col}'.")

    if area_col not in map_area_df.columns:
        raise ValueError(f"map_area_df must contain area column '{area_col}'.")

    areas = (
        map_area_df[[class_col, area_col]].dropna(subset=[class_col, area_col]).copy()
    )
    areas[class_col] = areas[class_col].astype(str)
    areas[area_col] = pd.to_numeric(areas[area_col], errors="raise")

    if (areas[area_col] < 0).any():
        raise ValueError("Mapped areas must be non-negative.")

    if areas[class_col].duplicated().any():
        duplicates = areas.loc[areas[class_col].duplicated(), class_col].tolist()
        raise ValueError(f"Duplicate class labels in map_area_df: {duplicates}")

    classes = areas[class_col].tolist()
    map_area = areas.set_index(class_col)[area_col].astype(float)

    total_area = map_area.sum()
    if total_area <= 0:
        raise ValueError("Total mapped area must be greater than zero.")

    W = map_area / total_area

    # Ensure confusion matrix and map-areas have same classes
    cm = confusion_df.copy()
    cm.index = cm.index.map(str)
    cm.columns = cm.columns.map(str)

    missing_rows = sorted(set(classes) - set(cm.index))
    missing_cols = sorted(set(classes) - set(cm.columns))

    if missing_rows or missing_cols:
        raise ValueError(
            "Could not find all class labels in the confusion matrix. "
            f"Missing rows: {missing_rows}. Missing columns: {missing_cols}."
        )

    # Extract only class rows and class columns, dropping totals and accuracy columns
    count_matrix = cm.loc[classes, classes].apply(pd.to_numeric, errors="raise")

    # Olofsson notation expects rows=map classes and columns=reference classes.
    if rows_are_reference:
        count_matrix_map_reference = count_matrix.T
    else:
        count_matrix_map_reference = count_matrix.copy()

    count_matrix_map_reference = count_matrix_map_reference.astype(float)
    count_matrix_map_reference.index.name = "map_class"
    count_matrix_map_reference.columns.name = "reference_class"

    if (count_matrix_map_reference < 0).any().any():
        raise ValueError("Confusion matrix counts must be non-negative.")

    # Compute Olofsson area-proportion matrix (these are the sums of the
    # reference labels per-class)
    n_i = count_matrix_map_reference.sum(axis=1)

    if (n_i <= 0).any():
        empty = n_i[n_i <= 0].index.tolist()
        raise ValueError(
            "Each mapped class stratum must have at least one validation sample. "
            f"No samples found for: {empty}"
        )

    # Divide the reference sums by per-class counts
    # p_raw_ij = n_ij / n_i
    p_raw = count_matrix_map_reference.div(n_i, axis=0)

    # create the area-prortion matrix by multiplying by the class-weights
    # p_hat_ij = W_i * n_ij / n_i
    area_proportion_matrix = p_raw.mul(W, axis=0)
    area_proportion_matrix.index.name = "map_class"
    area_proportion_matrix.columns.name = "reference_class"

    # Estimated reference class proportions are the column totals.
    estimated_area_proportion = area_proportion_matrix.sum(axis=0)

    # Standard errors and confidence intervals
    se_prop = pd.Series(index=classes, dtype=float)

    # Eq. 10 requires at least two validation samples in every map stratum.
    invalid_classes = n_i[n_i <= 1].index.tolist()
    if invalid_classes:
        raise ValueError(
            "At least two samples per mapped class are required to estimate "
            "the stratified variance. Classes with n_i <= 1: "
            f"{invalid_classes}"
        )

    for klass in classes:
        # Estimated proportion of reference class k within each map stratum
        # p_ik = n_ik / n_i
        p_ik = p_raw[klass]

        # Eq. 10 (Olofsson et al., 2014):
        # Var(p̂_.k) = Σ_i [ W_i² × p_ik × (1 - p_ik) / (n_i - 1) ]
        # where:
        #   W_i   = proportion of total mapped area in map class i
        #   p_ik  = proportion of validation samples in map class i
        #           belonging to reference class k
        #   n_i   = number of validation samples in map class i
        variance_terms = W**2 * p_ik * (1.0 - p_ik) / (n_i - 1.0)

        variance_proportion = variance_terms.sum()
        se_prop.loc[klass] = np.sqrt(variance_proportion)

    # calculate for each class the area and confidences
    estimated_area = estimated_area_proportion * total_area
    se_area = se_prop * total_area
    ci_half_width = z * se_area
    ci_lower = estimated_area - ci_half_width
    ci_upper = estimated_area + ci_half_width

    if clip_ci:
        ci_lower = ci_lower.clip(lower=0)
        ci_upper = ci_upper.clip(upper=total_area)

    mapped_area = map_area.loc[classes]
    mapped_area_proportion = W.loc[classes]

    # return a pandas dataframe
    results = pd.DataFrame(
        {
            "class": classes,
            "mapped_area": mapped_area.values,
            "mapped_area_proportion": mapped_area_proportion.values,
            "estimated_area": estimated_area.loc[classes].values,
            "estimated_area_proportion": estimated_area_proportion.loc[classes].values,
            "standard_error_area": se_area.loc[classes].values,
            "standard_error_proportion": se_prop.loc[classes].values,
            "ci_lower": ci_lower.loc[classes].values,
            "ci_upper": ci_upper.loc[classes].values,
            "ci_half_width": ci_half_width.loc[classes].values,
        }
    )

    return results
