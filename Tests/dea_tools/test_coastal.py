import pytest
import datacube
import pyproj
import numpy as np
import pandas as pd
import xarray as xr

from dea_tools.coastal import model_tides, pixel_tides, tidal_tag, tidal_stats
from dea_tools.validation import eval_metrics

GAUGE_X = 122.2183
GAUGE_Y = -18.0008


@pytest.fixture()
def measured_tides_ds():
    """
    Load measured sea level data from the Broome ABSLMP tidal station:
    http://www.bom.gov.au/oceanography/projects/abslmp/data/data.shtml
    """
    # Metadata for Broome ABSLMP tidal station:
    # http://www.bom.gov.au/oceanography/projects/abslmp/data/data.shtml
    ahd_offset = -5.322

    # Load measured tides from ABSLMP tide gauge data
    measured_tides_df = pd.read_csv(
        "Tests/data/IDO71013_2020.csv",
        index_col=0,
        parse_dates=True,
        na_values=-9999,
    )[["Sea Level"]]

    # Update index and column names
    measured_tides_df.index.name = "time"
    measured_tides_df.columns = ["tide_m"]

    # Apply station AHD offset
    measured_tides_df += ahd_offset

    # Return as xarray dataset
    return measured_tides_df.to_xarray()


# Create test data in different CRSs and resolutions
@pytest.fixture(
    params=[
        ("EPSG:3577", (-30, 30)),  # Australian Albers 30 m pixels
        ("EPSG:4326", (-0.00025, 0.00025)),  # WGS84, 0.0025 degree pixels
    ]
)
def satellite_ds(request):
    """
    Load a sample timeseries of Landsat 8 data from datacube
    """
    # Obtain CRS and resolution params
    crs, res = request.param

    # Connect to datacube
    dc = datacube.Datacube()

    # Load example satellite data around Broome tide gauge
    return dc.load(
        product="ga_ls8c_ard_3",
        x=(GAUGE_X - 0.08, GAUGE_X + 0.08),
        y=(GAUGE_Y - 0.08, GAUGE_Y + 0.08),
        time=("2020-01", "2020-02"),
        output_crs=crs,
        resolution=res,
        group_by="solar_day",
        dask_chunks={},
    )


# Run test for multiple input coordinates, CRSs and interpolation methods
@pytest.mark.parametrize(
    "x, y, epsg, method",
    [
        (GAUGE_X, GAUGE_Y, 4326, "bilinear"),  # WGS84, bilinear interp
        (GAUGE_X, GAUGE_Y, 4326, "spline"),  # WGS84, spline interp
        (-1034913, -1961916, 3577, "bilinear"),  # Australian Albers, spline interp
    ],
)
def test_model_tides(measured_tides_ds, x, y, epsg, method):
    # Run FES2014 tidal model for locations and timesteps in tide gauge data
    modelled_tides_df = model_tides(
        x=[x],
        y=[y],
        time=measured_tides_ds.time,
        epsg=epsg,
        method=method,
    )

    # Compare measured and modelled tides
    val_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_df.tide_m)

    # Test that modelled tides have same number of timesteps
    assert len(modelled_tides_df.index) == len(measured_tides_ds.time)

    # Test that modelled tides meet expected accuracy
    assert val_stats["Correlation"] > 0.99
    assert val_stats["RMSE"] < 0.26
    assert val_stats["R-squared"] > 0.96
    assert abs(val_stats["Bias"]) < 0.20


# Run tests for default and custom resolutions
@pytest.mark.parametrize("resolution", [None, "custom"])
def test_pixel_tides(satellite_ds, measured_tides_ds, resolution):
    # Use different custom resolution depending on CRS
    if resolution == "custom":
        resolution = 0.2 if satellite_ds.odc.geobox.crs.geographic else 10000

    # Model tides using `pixel_tides`
    modelled_tides_ds, modelled_tides_lowres = pixel_tides(
        satellite_ds, resolution=resolution
    )

    # Interpolate measured tide data to same timesteps
    measured_tides_ds = measured_tides_ds.interp(
        time=satellite_ds.time, method="linear"
    )

    # Assert that modelled tides have the same shape and dims as
    # arrays in `satellite_ds`
    assert modelled_tides_ds.shape == satellite_ds.nbart_red.shape
    assert modelled_tides_ds.dims == satellite_ds.nbart_red.dims

    # Test through time at tide gauge

    # Set up pyproj transformer to convert between coordinates
    reproject = pyproj.Transformer.from_crs(
        crs_from="EPSG:4326",
        crs_to=f"EPSG:{satellite_ds.odc.geobox.crs.to_epsg()}",
        always_xy=True,
    )

    # Extract tides through time for tide gauge location
    x, y = reproject.transform(GAUGE_X, GAUGE_Y)
    try:
        modelled_tides_gauge = modelled_tides_ds.sel(y=y, x=x, method="nearest")
    except KeyError:
        modelled_tides_gauge = modelled_tides_ds.sel(
            latitude=y, longitude=x, method="nearest"
        )

    # Calculate accuracy stats
    gauge_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_gauge)

    # Assert pixel_tide outputs are accurate
    assert gauge_stats["Correlation"] > 0.99
    assert gauge_stats["RMSE"] < 0.26
    assert gauge_stats["R-squared"] > 0.96
    assert abs(gauge_stats["Bias"]) < 0.20

    # Test spatially for a single timestep at corners of array

    # Reproject test point coordinates and create arrays
    x, y = reproject.transform(
        [122.14438, 122.30304, 122.12964, 122.29235],
        [-17.91625, -17.92713, -18.07656, -18.08751],
    )
    x_coords = xr.DataArray(x, dims=["point"])
    y_coords = xr.DataArray(y, dims=["point"])

    # Extract modelled tides for each corner
    try:
        extracted_tides = modelled_tides_ds.sel(
            x=x_coords, y=y_coords, time="2020-02-14", method="nearest"
        )
    except KeyError:
        extracted_tides = modelled_tides_ds.sel(
            longitude=x_coords, latitude=y_coords, time="2020-02-14", method="nearest"
        )

    # Test if extracted tides match expected results (to within ~3 cm)
    expected_tides = [-1.82249, -1.977088, -1.973618, -2.071242]
    assert np.allclose(extracted_tides.values, expected_tides, atol=0.03)


@pytest.mark.parametrize(
    "ebb_flow, swap_dims, tidepost_lat, tidepost_lon",
    [
        (False, False, None, None),  # Run with default settings
        (True, False, None, None),  # Run with ebb_flow on
        (False, True, None, None),  # Run with swap_dims on
        (False, False, GAUGE_Y, GAUGE_X),  # Run with custom tide posts
    ],
)
def test_tidal_tag(
    satellite_ds, measured_tides_ds, ebb_flow, swap_dims, tidepost_lat, tidepost_lon
):
    # Use tidal_tag to assign a "tide_m" variable to each observation
    tagged_tides_ds = tidal_tag(
        satellite_ds,
        ebb_flow=ebb_flow,
        swap_dims=swap_dims,
        tidepost_lat=tidepost_lat,
        tidepost_lon=tidepost_lon,
    )

    # Verify tide_m variable was added
    assert "tide_m" in tagged_tides_ds

    # Verify ebb_flow variable was added if requested
    if ebb_flow:
        assert "ebb_flow" in tagged_tides_ds

    if swap_dims:
        # Verify "tide_m" is now a dimension
        assert "tide_m" in tagged_tides_ds.dims

        # Test that "tide_m" dim is same length as satellite "time" dim
        assert len(tagged_tides_ds.tide_m) == len(satellite_ds.time)

        # Test that first value on "tide_m" dim is lower than last
        # (data should be sorted in increasing tide height order)
        assert (
            tagged_tides_ds.isel(tide_m=0).tide_m
            < tagged_tides_ds.isel(tide_m=-1).tide_m
        )

    else:
        # Test that tagged tides have same timesteps as satellite data
        assert len(tagged_tides_ds.tide_m.time) == len(satellite_ds.time)

        # Interpolate measured tide data to same timesteps
        measured_tides_ds = measured_tides_ds.interp(
            time=satellite_ds.time, method="linear"
        )

        # Compare measured and modelled tides
        val_stats = eval_metrics(x=measured_tides_ds.tide_m, y=tagged_tides_ds.tide_m)

        # Test that modelled tides meet expected accuracy
        assert val_stats["Correlation"] > 0.99
        assert val_stats["RMSE"] < 0.26
        assert val_stats["R-squared"] > 0.96
        assert abs(val_stats["Bias"]) < 0.20


# Run test for multiple modelled frequencies
@pytest.mark.parametrize(
    "modelled_freq",
    [
        ("2h"),  # Model tides every two hours
        ("120min"),  # Model tides every 120 minutes
    ],
)
def test_tidal_stats(satellite_ds, modelled_freq):
    # Calculate tidal stats
    tidal_stats_df = tidal_stats(satellite_ds, modelled_freq=modelled_freq)

    # Compare outputs to expected results (within 5% or 0.05 m)
    expected_results = pd.Series(
        {
            "tidepost_lat": -18.001,
            "tidepost_lon": 122.218,
            "observed_mean_m": -0.442,
            "all_mean_m": -0.005,
            "observed_min_m": -2.004,
            "all_min_m": -4.407,
            "observed_max_m": 1.625,
            "all_max_m": 4.305,
            "observed_range_m": 3.629,
            "all_range_m": 8.712,
            "spread": 0.417,
            "low_tide_offset": 0.276,
            "high_tide_offset": 0.308,
        }
    )
    assert np.allclose(tidal_stats_df, expected_results, atol=0.05)
