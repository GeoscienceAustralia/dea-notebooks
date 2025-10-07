import pytest
import numpy as np
from scipy import stats
import xarray as xr
import datacube
from datacube.utils.masking import mask_invalid_data
from dea_tools.temporal import xr_regression

@pytest.fixture()
def satellite_ds():
    # Connect to datacube
    dc = datacube.Datacube()

    # Load example satellite data around Broome tide gauge
    ds = dc.load(
        product="ga_ls8c_ard_3",
        measurements=["nbart_nir", "nbart_red"],
        x=(122.2183 - 0.01, 122.2183 + 0.01),
        y=(-18.0008 - 0.01, -18.0008 + 0.01),
        time=("2020-01", "2020-02"),
        resolution=(-200, 200),
        output_crs="EPSG:3577",  # Added here temporarily until NCI environment is updated to include load hints
        group_by="solar_day",
        skip_broken_datasets=True,
    )

    # Mask nodata
    ds = mask_invalid_data(ds)

    return ds


# Run test on different pixels and alternative hypotheses
@pytest.mark.parametrize(
    "x, y, alternative",
    [
        (0, 0, "two-sided"),
        (5, 10, "two-sided"),
        (0, 0, "less"),
        (5, 10, "less"),
        (0, 0, "greater"),
        (5, 10, "greater"),
    ],
)
def test_xr_regresssion(satellite_ds, x, y, alternative):
    # Calculate statistics using `xr_regression`
    stats_3d = xr_regression(x=satellite_ds.nbart_red, y=satellite_ds.nbart_nir, alternative=alternative)

    # Verify expected bands are in dataset
    assert "cov" in stats_3d.data_vars
    assert "cor" in stats_3d.data_vars
    assert "r2" in stats_3d.data_vars
    assert "slope" in stats_3d.data_vars
    assert "pvalue" in stats_3d.data_vars
    assert "stderr" in stats_3d.data_vars

    # Verify x and y coords are the same and that dataset does not have
    # a time dimension
    assert all(satellite_ds.x == stats_3d.x)
    assert "time" not in stats_3d.dims

    # Calculate statistics for a specific pixel using `scipy.stats`
    # and compare against `xr_regression`
    stats_1d = stats.linregress(
        x=satellite_ds.nbart_red.isel(x=x, y=y),
        y=satellite_ds.nbart_nir.isel(x=x, y=y),
        alternative=alternative,
    )
    assert np.isclose(stats_1d.rvalue, stats_3d.isel(x=x, y=y).cor)
    assert np.isclose(stats_1d.pvalue, stats_3d.isel(x=x, y=y).pvalue)
    assert np.isclose(stats_1d.intercept, stats_3d.isel(x=x, y=y).intercept)
    assert np.isclose(stats_1d.slope, stats_3d.isel(x=x, y=y).slope)
    assert np.isclose(stats_1d.stderr, stats_3d.isel(x=x, y=y).stderr)

    # Run `xr_regression` with x being 1D
    stats_3d_x1d = xr_regression(
        x=satellite_ds.nbart_red.isel(x=x, y=y),
        y=satellite_ds.nbart_nir,
        alternative=alternative,
    )

    assert np.isclose(stats_1d.rvalue, stats_3d_x1d.isel(x=x, y=y).cor)
    assert np.isclose(stats_1d.pvalue, stats_3d_x1d.isel(x=x, y=y).pvalue)
    assert np.isclose(stats_1d.intercept, stats_3d_x1d.isel(x=x, y=y).intercept)
    assert np.isclose(stats_1d.slope, stats_3d_x1d.isel(x=x, y=y).slope)
    assert np.isclose(stats_1d.stderr, stats_3d_x1d.isel(x=x, y=y).stderr)

    # Run `xr_regression` with y being 1D
    stats_3d_y1d = xr_regression(
        x=satellite_ds.nbart_red,
        y=satellite_ds.nbart_nir.isel(x=x, y=y),
        alternative=alternative,
    )

    assert np.isclose(stats_1d.rvalue, stats_3d_y1d.isel(x=x, y=y).cor)
    assert np.isclose(stats_1d.pvalue, stats_3d_y1d.isel(x=x, y=y).pvalue)
    assert np.isclose(stats_1d.intercept, stats_3d_y1d.isel(x=x, y=y).intercept)
    assert np.isclose(stats_1d.slope, stats_3d_y1d.isel(x=x, y=y).slope)
    assert np.isclose(stats_1d.stderr, stats_3d_y1d.isel(x=x, y=y).stderr)

    # Run `xr_regression` with both x and y being 1D
    stats_3d_1d = xr_regression(
        x=satellite_ds.nbart_red.isel(x=x, y=y),
        y=satellite_ds.nbart_nir.isel(x=x, y=y),
        alternative=alternative,
    )

    assert np.isclose(stats_1d.rvalue, stats_3d_1d.cor)
    assert np.isclose(stats_1d.pvalue, stats_3d_1d.pvalue)
    assert np.isclose(stats_1d.intercept, stats_3d_1d.intercept)
    assert np.isclose(stats_1d.slope, stats_3d_1d.slope)
    assert np.isclose(stats_1d.stderr, stats_3d_1d.stderr)


#test temporal-stats-----------------------------
from dea_tools.temporal import temporal_statistics

@pytest.fixture
def sample_da():
    """Simple 3D DataArray: dims (y, x, time) = (4, 3, 10)."""
    time = np.arange(10)
    y = np.arange(4)
    x = np.arange(3)
    data = np.random.rand(len(y), len(x), len(time)).astype(np.float32)

    da = xr.DataArray(
        data,
        coords={"y": y, "x": x, "time": time},
        dims=("y", "x", "time"),
    )
    return da


def test_mean_change_basic(sample_da):
    """Check basic functionality for a simple statistic (mean_change)."""
    ds = temporal_statistics(sample_da, stats=["mean_change"])

    # Should return a Dataset with one variable called 'mean_change'
    assert isinstance(ds, xr.Dataset)
    assert "mean_change" in ds.data_vars

    # The shape should match the spatial dimensions (y, x)
    assert ds["mean_change"].shape == (4, 3)

    # Values should be finite floats
    assert np.isfinite(ds["mean_change"].values).all()


def test_fourier_and_other_stats(sample_da):
    """Check handling of multi-stat combination including Fourier-based stats."""
    ds = temporal_statistics(sample_da, stats=["f_mean", "median_change"])

    # Expect 3 Fourier layers plus 1 median_change
    expected_vars = [
        "f_mean_n1",
        "f_mean_n2",
        "f_mean_n3",
        "median_change",
    ]
    for var in expected_vars:
        assert var in ds.data_vars, f"{var} missing in result"

    # Check that each variable has spatial dimensions only
    for var in expected_vars:
        assert ds[var].dims == ("y", "x")

    # Fourier outputs should have reasonable magnitudes (nonnegative)
    assert (ds["f_mean_n1"] >= 0).all()


def test_nan_mask_preserved(sample_da):
    """Ensure all-NaN pixels remain NaN in the output."""
    da = sample_da.copy()

    # Make one pixel entirely NaN across all time steps
    da[1, 2, :] = np.nan

    ds = temporal_statistics(da, stats=["mean_change", "abs_change"])

    # That pixel should still be NaN in *all* output layers
    for var in ds.data_vars:
        assert np.isnan(ds[var][1, 2]), f"{var} did not preserve NaN mask"







