import pytest
import numpy as np
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point
from odc.geo.xr import assign_crs
from dea_tools.validation import random_sampling_xr


@pytest.fixture
def classified_da():
    """
    Create simple 10*10 datarray with random allocations of
    pixel values, and some NaNs
    """
    data = np.random.choice([1, 2, 3, np.nan], size=(10, 10), p=[0.2, 0.5, 0.25, 0.05])
    y = np.arange(10)
    x = np.arange(10)
    da = xr.DataArray(data, coords={"y": y, "x": x}, dims=("y", "x"))
    da = assign_crs(da, crs="EPSG:3577")
    return da


def test_sample_counts_by_strategy(classified_da):
    """
    Check all the various sampling options work as expected
    """
    # first check that samples are created.
    n = 10
    gdf = random_sampling_xr(classified_da, n=n, sampling="random")
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert not gdf.empty
    assert all(isinstance(geom, Point) for geom in gdf.geometry)

    # Strategy 'random' - N-samples should exactly match num requested
    assert len(gdf) == n, f"[random] Expected {n}, got {len(gdf_random)}"

    # Strategy 'stratified_random' - allow tolerance due to rounding or sparsity
    n_strat = 40
    gdf_strat = random_sampling_xr(
        classified_da, n=n_strat, sampling="stratified_random"
    )
    tolerance = 2
    assert (
        abs(len(gdf_strat) - n_strat) <= tolerance
    ), f"[stratified_random] Expected ~{n_strat}, got {len(gdf_strat)}"

    # Strategy 'equal_stratified_random' - may overshoot due to ceil(n / num_classes)
    n_equal = 30
    unique_classes = np.unique(classified_da.values[~np.isnan(classified_da.values)])
    num_classes = len(unique_classes)
    expected_min = n_equal
    expected_max = num_classes * int(np.ceil(n_equal / num_classes))
    gdf_equal = random_sampling_xr(
        classified_da, n=n_equal, sampling="equal_stratified_random"
    )
    actual_equal = len(gdf_equal)
    assert (
        expected_min <= actual_equal <= expected_max
    ), f"[equal_stratified_random] Expected between {expected_min}-{expected_max}, got {actual_equal}"

    # Strategy 'manual' - expect close to manual sum, allow 1 pixel difference
    manual_ratios = {1: 5, 2: 10, 3: 5}
    expected_manual_total = sum(manual_ratios.values())
    gdf_manual = random_sampling_xr(
        classified_da, sampling="manual", manual_class_ratios=manual_ratios
    )

    actual_manual = len(gdf_manual)
    assert (
        abs(actual_manual - expected_manual_total) <= 1
    ), f"[manual] Expected ~{expected_manual_total}, got {actual_manual}"


def test_stratified_random_proportional(classified_da):
    """
    Ensure proportions of samples returned are close to the proportions
    in the data.
    """
    gdf = random_sampling_xr(classified_da, n=40, sampling="stratified_random")
    counts = gdf["class"].value_counts()
    total = counts.sum()

    class_counts_in_da = np.unique(
        classified_da.values[~np.isnan(classified_da.values)], return_counts=True
    )

    da_proportions = {
        int(cls): count / sum(class_counts_in_da[1])
        for cls, count in zip(*class_counts_in_da)
    }

    sampled_proportions = {cls: count / total for cls, count in counts.items()}

    for cls in sampled_proportions:
        assert np.isclose(sampled_proportions[cls], da_proportions[cls], atol=0.02)


def test_oversample_error(classified_da):
    # Count how many valid pixels exist
    valid_pixel_count = np.isfinite(classified_da.values).sum()
    with pytest.raises(ValueError, match="more samples than available valid pixels"):
        random_sampling_xr(classified_da, n=valid_pixel_count + 10, sampling="random")
