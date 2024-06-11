import dask
import pytest
import datacube
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

from dea_tools.coastal import (
    model_tides,
    pixel_tides,
    tidal_tag,
    tidal_stats,
    glint_angle,
)
from dea_tools.validation import eval_metrics

GAUGE_X = 122.2183
GAUGE_Y = -18.0008
ENSEMBLE_MODELS = ["FES2014", "HAMTIDE11"]  # simplified for tests


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
    ],
    ids=["satellite_ds_epsg3577", "satellite_ds_epsg4326"],
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


@pytest.fixture()
def angle_metadata_ds():
    """
    Create a sample xarray.Dataset containing sun and satellite view
    angle data
    """

    # Create sample data as a dataframe
    df = pd.DataFrame(
        index=pd.Index(pd.date_range("2020", "2021", 2), name="time"),
        data=np.array([[22, 78, 99, 10], [21, 76, 280, 5]]),
        columns=[
            "oa_solar_zenith",
            "oa_solar_azimuth",
            "oa_satellite_azimuth",
            "oa_satellite_view",
        ],
    )

    # Convert to xarray to simulate data loaded from datacube
    return df.to_xarray()


# Run test for multiple input coordinates, CRSs and interpolation methods
@pytest.mark.parametrize(
    "x, y, crs, method",
    [
        (GAUGE_X, GAUGE_Y, "EPSG:4326", "bilinear"),  # WGS84, bilinear interp
        (GAUGE_X, GAUGE_Y, "EPSG:4326", "spline"),  # WGS84, spline interp
        (
            -1034913,
            -1961916,
            "EPSG:3577",
            "bilinear",
        ),  # Australian Albers, bilinear interp
    ],
)
def test_model_tides(measured_tides_ds, x, y, crs, method):
    # Run FES2014 tidal model for locations and timesteps in tide gauge data
    modelled_tides_df = model_tides(
        x=[x],
        y=[y],
        time=measured_tides_ds.time,
        crs=crs,
        method=method,
    )

    # Compare measured and modelled tides
    val_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_df.tide_m)

    # Test that modelled tides contain correct headings and have same
    # number of timesteps
    assert modelled_tides_df.index.names == ["time", "x", "y"]
    assert modelled_tides_df.columns.tolist() == ["tide_model", "tide_m"]
    assert len(modelled_tides_df.index) == len(measured_tides_ds.time)

    # Test that modelled tides meet expected accuracy
    assert val_stats["Correlation"] > 0.99
    assert val_stats["RMSE"] < 0.26
    assert val_stats["R-squared"] > 0.96
    assert abs(val_stats["Bias"]) < 0.20


# Run tests for one or multiple models, and long and wide format outputs
@pytest.mark.parametrize(
    "models, output_format",
    [
        (["FES2014"], "long"),
        (["FES2014"], "wide"),
        (["FES2014", "HAMTIDE11"], "long"),
        (["FES2014", "HAMTIDE11"], "wide"),
    ],
    ids=[
        "single_model_long",
        "single_model_wide",
        "multiple_models_long",
        "multiple_models_wide",
    ],
)
def test_model_tides_multiplemodels(measured_tides_ds, models, output_format):
    # Model tides for one or multiple tide models and output formats
    modelled_tides_df = model_tides(
        x=[GAUGE_X],
        y=[GAUGE_Y],
        time=measured_tides_ds.time,
        model=models,
        output_format=output_format,
    )

    if output_format == "long":
        # Verify output has correct columns
        assert modelled_tides_df.index.names == ["time", "x", "y"]
        assert modelled_tides_df.columns.tolist() == ["tide_model", "tide_m"]

        # Verify tide model column contains correct values
        assert modelled_tides_df.tide_model.unique().tolist() == models

        # Verify that dataframe has length of original timesteps multipled by
        # n models
        assert len(modelled_tides_df.index) == len(measured_tides_ds.time) * len(models)

    elif output_format == "wide":
        # Verify output has correct columns
        assert modelled_tides_df.index.names == ["time", "x", "y"]
        assert modelled_tides_df.columns.tolist() == models

        # Verify output has same length as orginal timesteps
        assert len(modelled_tides_df.index) == len(measured_tides_ds.time)


# Run tests for each unit, providing expected outputs
@pytest.mark.parametrize(
    "units, expected_range, expected_dtype",
    [("m", 10, "float32"), ("cm", 1000, "int16"), ("mm", 10000, "int16")],
    ids=["metres", "centimetres", "millimetres"],
)
def test_model_tides_units(measured_tides_ds, units, expected_range, expected_dtype):
    # Model tides
    modelled_tides_df = model_tides(
        x=[GAUGE_X],
        y=[GAUGE_Y],
        time=measured_tides_ds.time,
        output_units=units,
    )

    # Calculate tide range
    tide_range = modelled_tides_df.tide_m.max() - modelled_tides_df.tide_m.min()

    # Verify tide range and dtypes are as expected for unit
    assert np.isclose(tide_range, expected_range, rtol=0.01)
    assert modelled_tides_df.tide_m.dtype == expected_dtype


# Run test for each combination of mode, output format, and one or
# multiple tide models
@pytest.mark.parametrize(
    "mode, models, output_format",
    [
        ("one-to-many", ["FES2014"], "long"),
        ("one-to-one", ["FES2014"], "long"),
        ("one-to-many", ["FES2014"], "wide"),
        ("one-to-one", ["FES2014"], "wide"),
        ("one-to-many", ["FES2014", "HAMTIDE11"], "long"),
        ("one-to-one", ["FES2014", "HAMTIDE11"], "long"),
        ("one-to-many", ["FES2014", "HAMTIDE11"], "wide"),
        ("one-to-one", ["FES2014", "HAMTIDE11"], "wide"),
    ],
)
def test_model_tides_mode(mode, models, output_format):
    # Input params
    x = [122.14, 122.30, 122.12]
    y = [-17.91, -17.92, -18.07]
    times = pd.date_range("2020", "2021", periods=3)

    # Model tides
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        mode=mode,
        output_format=output_format,
        model=models,
    )

    if mode == "one-to-one":
        if output_format == "wide":
            # Should have the same number of rows as input x, y, times
            assert len(modelled_tides_df.index) == len(x)
            assert len(modelled_tides_df.index) == len(times)

            # Output indexes should match order of input x, y, times
            assert all(modelled_tides_df.index.get_level_values("time") == times)
            assert all(modelled_tides_df.index.get_level_values("x") == x)
            assert all(modelled_tides_df.index.get_level_values("y") == y)

        elif output_format == "long":
            # In "long" format, the number of x, y points multiplied by
            # the number of tide models
            assert len(modelled_tides_df.index) == len(x) * len(models)

            # Verify index values match expected x, y, time order
            assert all(
                modelled_tides_df.index.get_level_values("time")
                == np.tile(times, len(models))
            )
            assert all(
                modelled_tides_df.index.get_level_values("x") == np.tile(x, len(models))
            )
            assert all(
                modelled_tides_df.index.get_level_values("y") == np.tile(y, len(models))
            )

    if mode == "one-to-many":
        if output_format == "wide":
            # In "wide" output format, the number of rows should equal
            # the number of x, y points multiplied by timesteps
            assert len(modelled_tides_df.index) == len(x) * len(times)

            # TODO: Work out what order rows should be returned in in
            # "one-to-many" and "wide" mode

        elif output_format == "long":
            # In "long" output format, the number of rows should equal
            # the number of x, y points multiplied by timesteps and
            # the number of tide models
            assert len(modelled_tides_df.index) == len(x) * len(times) * len(models)

            # Verify index values match expected x, y, time order
            assert all(
                modelled_tides_df.index.get_level_values("time")
                == np.tile(times, len(x) * len(models))
            )
            assert all(
                modelled_tides_df.index.get_level_values("x")
                == np.tile(np.repeat(x, len(times)), len(models))
            )
            assert all(
                modelled_tides_df.index.get_level_values("y")
                == np.tile(np.repeat(y, len(times)), len(models))
            )


# Test ensemble modelling functionality
def test_model_tides_ensemble():
    # Input params
    x = [122.14, 144.910368]
    y = [-17.91, -37.919491]
    times = pd.date_range("2020", "2021", periods=2)

    # Default, only ensemble requested
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model="ensemble",
        ensemble_models=ENSEMBLE_MODELS,
    )

    assert modelled_tides_df.index.names == ["time", "x", "y"]
    assert modelled_tides_df.columns.tolist() == ["tide_model", "tide_m"]
    assert all(modelled_tides_df.tide_model == "ensemble")

    # Default, ensemble + other models requested
    models = ["FES2014", "HAMTIDE11", "ensemble"]
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        ensemble_models=ENSEMBLE_MODELS,
    )

    assert modelled_tides_df.index.names == ["time", "x", "y"]
    assert modelled_tides_df.columns.tolist() == ["tide_model", "tide_m"]
    assert set(modelled_tides_df.tide_model) == set(models)
    assert np.allclose(
        modelled_tides_df.tide_m,
        [
            -2.819,
            -1.850,
            -0.215,
            0.037,
            -2.623,
            -1.803,
            0.073,
            -0.069,
            -2.721,
            -1.826,
            -0.071,
            -0.0158,
        ],
        rtol=0.02,
    )

    # One-to-one mode
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        mode="one-to-one",
        ensemble_models=ENSEMBLE_MODELS,
    )

    assert modelled_tides_df.index.names == ["time", "x", "y"]
    assert modelled_tides_df.columns.tolist() == ["tide_model", "tide_m"]
    assert set(modelled_tides_df.tide_model) == set(models)

    # Wide mode, default
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        output_format="wide",
        ensemble_models=ENSEMBLE_MODELS,
    )

    # Check that expected models exist, and that ensemble is approx average
    # of other two models
    assert set(modelled_tides_df.columns) == set(models)
    assert np.allclose(
        0.5 * (modelled_tides_df.FES2014 + modelled_tides_df.HAMTIDE11),
        modelled_tides_df.ensemble,
    )

    # Wide mode, top n == 1
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        output_format="wide",
        ensemble_top_n=1,
        ensemble_models=ENSEMBLE_MODELS,
    )

    # Check that expected models exist, and that ensemble is equal to at
    # least one of the other models
    assert set(modelled_tides_df.columns) == set(models)
    assert all(
        (modelled_tides_df.FES2014 == modelled_tides_df.ensemble)
        | (modelled_tides_df.HAMTIDE11 == modelled_tides_df.ensemble)
    )

    # Check that correct model is the closest at each row
    closer_model = modelled_tides_df.apply(
        lambda row: (
            "FES2014"
            if abs(row["ensemble"] - row["FES2014"])
            < abs(row["ensemble"] - row["HAMTIDE11"])
            else "HAMTIDE11"
        ),
        axis=1,
    ).tolist()
    assert closer_model == ["FES2014", "HAMTIDE11", "FES2014", "HAMTIDE11"]

    # Check values are expected
    assert np.allclose(
        modelled_tides_df.ensemble, [-2.819, 0.0730, -1.850, -0.069], rtol=0.01
    )

    # Wide mode, custom functions
    ensemble_funcs = {
        "ensemble-best": lambda x: x["rank"] == 2,
        "ensemble-worst": lambda x: x["rank"] == 1,
        "ensemble-mean-top2": lambda x: x["rank"].isin([1, 2]),
        "ensemble-mean-weighted": lambda x: x["rank"],
        "ensemble-mean": lambda x: x["rank"] >= 0,
    }
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        output_format="wide",
        ensemble_func=ensemble_funcs,
        ensemble_models=ENSEMBLE_MODELS,
    )

    # Check that expected models exist, and that valid data is produced
    assert set(modelled_tides_df.columns) == set(
        [
            "FES2014",
            "HAMTIDE11",
            "ensemble-best",
            "ensemble-worst",
            "ensemble-mean-top2",
            "ensemble-mean-weighted",
            "ensemble-mean",
        ]
    )
    assert all(modelled_tides_df.notnull())

    # Long mode, custom functions
    modelled_tides_df = model_tides(
        x=x,
        y=y,
        time=times,
        model=models,
        output_format="long",
        ensemble_func=ensemble_funcs,
        ensemble_models=ENSEMBLE_MODELS,
    )

    # Check that expected models exist in "tide_model" column
    assert set(modelled_tides_df.tide_model) == set(
        [
            "FES2014",
            "HAMTIDE11",
            "ensemble-best",
            "ensemble-worst",
            "ensemble-mean-top2",
            "ensemble-mean-weighted",
            "ensemble-mean",
        ]
    )


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

    # Assert that high res and low res data have the same dims
    assert modelled_tides_ds.dims == modelled_tides_lowres.dims

    # Test through time at tide gauge

    # Create tide gauge point, and reproject to dataset CRS
    tide_gauge_point = gpd.points_from_xy(
        x=[GAUGE_X],
        y=[GAUGE_Y],
        crs="EPSG:4326",
    ).to_crs(satellite_ds.odc.geobox.crs)

    try:
        modelled_tides_gauge = modelled_tides_ds.sel(
            y=tide_gauge_point[0].y,
            x=tide_gauge_point[0].x,
            method="nearest",
        )
    except KeyError:
        modelled_tides_gauge = modelled_tides_ds.sel(
            latitude=tide_gauge_point[0].y,
            longitude=tide_gauge_point[0].x,
            method="nearest",
        )

    # Calculate accuracy stats
    gauge_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_gauge)

    # Assert pixel_tide outputs are accurate
    assert gauge_stats["Correlation"] > 0.99
    assert gauge_stats["RMSE"] < 0.26
    assert gauge_stats["R-squared"] > 0.96
    assert abs(gauge_stats["Bias"]) < 0.20

    # Test spatially for a single timestep at corners of array

    # Create test points, reproject to dataset CRS, and extract coords
    # as xr.DataArrays so we can select data from our array
    points = gpd.points_from_xy(
        x=[122.14438, 122.30304, 122.12964, 122.29235],
        y=[-17.91625, -17.92713, -18.07656, -18.08751],
        crs="EPSG:4326",
    ).to_crs(satellite_ds.odc.geobox.crs)
    x_coords = xr.DataArray(points.x, dims=["point"])
    y_coords = xr.DataArray(points.y, dims=["point"])

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


def test_pixel_tides_quantile(satellite_ds):
    # Model tides using `pixel_tides` and `calculate_quantiles`
    quantiles = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    modelled_tides_ds, modelled_tides_lowres = pixel_tides(
        satellite_ds, calculate_quantiles=quantiles
    )

    # Verify that outputs contain quantile dim and values match inputs
    assert modelled_tides_ds.dims == modelled_tides_lowres.dims
    assert "quantile" in modelled_tides_ds.dims
    assert "quantile" in modelled_tides_lowres.dims
    assert modelled_tides_ds["quantile"].values.tolist() == quantiles
    assert modelled_tides_lowres["quantile"].values.tolist() == quantiles

    # Verify tides are monotonically increasing along quantile dim
    # (in this case, axis=0)
    assert np.all(np.diff(modelled_tides_ds, axis=0) > 0)

    # Test results match expected results for a set of points across array

    # Create test points, reproject to dataset CRS, and extract coords
    # as xr.DataArrays so we can select data from our array
    points = gpd.points_from_xy(
        x=[122.14438, 122.30304, 122.12964, 122.29235],
        y=[-17.91625, -17.92713, -18.07656, -18.08751],
        crs="EPSG:4326",
    ).to_crs(satellite_ds.odc.geobox.crs)
    x_coords = xr.DataArray(points.x, dims=["point"])
    y_coords = xr.DataArray(points.y, dims=["point"])

    # Extract modelled tides for each point
    try:
        extracted_tides = modelled_tides_ds.sel(
            x=x_coords, y=y_coords, method="nearest"
        )
    except KeyError:
        extracted_tides = modelled_tides_ds.sel(
            longitude=x_coords, latitude=y_coords, method="nearest"
        )

    # Test if extracted tides match expected results (to within ~3 cm)
    expected_tides = np.array(
        [
            [-1.83, -1.98, -1.98, -2.07],
            [-1.38, -1.44, -1.44, -1.47],
            [-0.73, -0.78, -0.79, -0.82],
            [-0.38, -0.36, -0.36, -0.35],
            [0.49, 0.44, 0.44, 0.41],
            [1.58, 1.61, 1.62, 1.64],
        ]
    )
    assert np.allclose(extracted_tides.values, expected_tides, atol=0.03)


# Run test with quantile calculation off and on
@pytest.mark.parametrize("quantiles", [None, [0.0, 0.5, 1.0]])
def test_pixel_tides_multiplemodels(satellite_ds, quantiles):
    # Model tides using `pixel_tides` and multiple models
    models = ["FES2014", "HAMTIDE11"]
    modelled_tides_ds, modelled_tides_lowres = pixel_tides(
        satellite_ds, model=models, calculate_quantiles=quantiles
    )

    # Verify that outputs contain quantile dim and values match inputs
    assert modelled_tides_ds.dims == modelled_tides_lowres.dims
    assert "tide_model" in modelled_tides_ds.dims
    assert "tide_model" in modelled_tides_lowres.dims
    assert modelled_tides_ds["tide_model"].values.tolist() == models
    assert modelled_tides_lowres["tide_model"].values.tolist() == models

    # Verify that both model outputs are correlated
    assert (
        xr.corr(
            modelled_tides_ds.sel(tide_model="FES2014"),
            modelled_tides_ds.sel(tide_model="HAMTIDE11"),
        )
        > 0.98
    )


# Run test for different combinations of Dask chunking
@pytest.mark.parametrize(
    "dask_chunks",
    ["auto", (300, 300), (200, 300)],
)
def test_pixel_tides_dask(satellite_ds, dask_chunks):
    # Model tides with Dask compute turned off to return Dask arrays
    modelled_tides_ds, modelled_tides_lowres = pixel_tides(
        satellite_ds, dask_compute=False, dask_chunks=dask_chunks
    )

    # Verify output is Dask-enabled
    assert dask.is_dask_collection(modelled_tides_ds)

    # If chunks set to "auto", check output matches `satellite_ds` chunks
    if dask_chunks == "auto":
        assert modelled_tides_ds.chunks == satellite_ds.nbart_red.chunks

    # Otherwise, check output chunks match requested chunks
    else:
        output_chunks = tuple([i[0] for i in modelled_tides_ds.chunks[1:]])
        assert output_chunks == dask_chunks


# Run test pixel tides and ensemble modelling
def test_pixel_tides_ensemble(satellite_ds):
    # Model tides using `pixel_tides` and default ensemble model
    modelled_tides_ds, _ = pixel_tides(
        satellite_ds,
        model="ensemble",
        ensemble_models=ENSEMBLE_MODELS,
    )

    assert modelled_tides_ds.tide_model == "ensemble"

    # Model tides using `pixel_tides` and multiple models including
    # ensemble and custom IDW params
    models = ["FES2014", "HAMTIDE11", "ensemble"]
    modelled_tides_ds, _ = pixel_tides(
        satellite_ds,
        model=models,
        ensemble_models=ENSEMBLE_MODELS,
        k=10, 
        max_dist=20000,
    )

    assert "tide_model" in modelled_tides_ds.dims
    assert set(modelled_tides_ds.tide_model.values) == set(models)

    # Verify that all values are in equal to or between input model values
    min_vals = modelled_tides_ds.sel(tide_model=["FES2014", "HAMTIDE11"]).min(
        "tide_model"
    )
    max_vals = modelled_tides_ds.sel(tide_model=["FES2014", "HAMTIDE11"]).max(
        "tide_model"
    )
    assert (modelled_tides_ds.sel(tide_model=["ensemble"]) >= min_vals).all()
    assert (modelled_tides_ds.sel(tide_model=["ensemble"]) <= max_vals).all()

    # Model tides using `pixel_tides` and custom ensemble funcs
    ensemble_funcs = {
        "ensemble-best": lambda x: x["rank"] == 2,
        "ensemble-worst": lambda x: x["rank"] == 1,
        "ensemble-mean-top2": lambda x: x["rank"].isin([1, 2]),
        "ensemble-mean-weighted": lambda x: x["rank"],
        "ensemble-mean": lambda x: x["rank"] >= 0,
    }
    modelled_tides_ds, _ = pixel_tides(
        satellite_ds,
        model=models,
        ensemble_func=ensemble_funcs,
        ensemble_models=ENSEMBLE_MODELS,
    )

    assert set(modelled_tides_ds.tide_model.values) == set(
        [
            "FES2014",
            "HAMTIDE11",
            "ensemble-best",
            "ensemble-worst",
            "ensemble-mean-top2",
            "ensemble-mean-weighted",
            "ensemble-mean",
        ]
    )


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


def test_glint_angle(angle_metadata_ds):
    # Calculate glint angles
    glint_array = glint_angle(
        solar_azimuth=angle_metadata_ds.oa_solar_azimuth,
        solar_zenith=angle_metadata_ds.oa_solar_zenith,
        view_azimuth=angle_metadata_ds.oa_satellite_azimuth,
        view_zenith=angle_metadata_ds.oa_satellite_view,
    )

    # Verify values are expected
    assert np.allclose(glint_array, np.array([31.5297584, 16.5520374]))

    # Verify output as an xarray.DataArray
    assert isinstance(glint_array, xr.DataArray)
