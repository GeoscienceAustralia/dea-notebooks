import pytest
import datacube
import pyproj
import pandas as pd
import xarray as xr

from dea_tools.coastal import model_tides, pixel_tides
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


@pytest.fixture()
def satellite_ds():
    """
    Load a sample timeseries of Landsat 8 data from datacube
    """
    # Connect to datacube
    dc = datacube.Datacube()

    # Load example satellite data around Broome tide gauge
    return dc.load(
        product="ga_ls8c_ard_3",
        x=(GAUGE_X - 0.08, GAUGE_X + 0.08),
        y=(GAUGE_Y - 0.08, GAUGE_Y + 0.08),
        time=("2020-01", "2020-02"),
        group_by="solar_day",
        dask_chunks={},
    )


def test_measured_vs_modelled_tides(measured_tides_ds):
    """
    Tests tides modelled by the `model_tides` function against measured
    data from the Broome ABSLMP tidal station:
    http://www.bom.gov.au/oceanography/projects/abslmp/data/data.shtml
    """
    # Run the FES2014 tidal model
    modelled_tides_df = model_tides(
        x=[GAUGE_X],
        y=[GAUGE_Y],
        time=measured_tides_ds.time,
    )

    # Compare measured and modelled outputs
    val_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_df.tide_m)

    # Test that outputs meet expected accuracy
    assert val_stats["Correlation"] > 0.99
    assert val_stats["RMSE"] < 0.26
    assert val_stats["R-squared"] > 0.98
    assert abs(val_stats["Bias"]) < 0.20


def test_pixel_tides(satellite_ds, measured_tides_ds):

    # Model tides
    modelled_tides_ds, modelled_tides_lowres = pixel_tides(satellite_ds)

    # Interpolate measured tide data to same timesteps
    measured_tides_ds = measured_tides_ds.interp(
        time=satellite_ds.time, method="linear"
    )

    # Extract tides for tide gauge location
    x, y = pyproj.Transformer.from_crs(
        "EPSG:4326", f"EPSG:{satellite_ds.odc.geobox.crs.to_epsg()}"
    ).transform(GAUGE_Y, GAUGE_X)
    modelled_tides_gauge = modelled_tides_ds.interp(y=y, x=x, method="linear")

    # Calculate stats
    gauge_stats = eval_metrics(x=measured_tides_ds.tide_m, y=modelled_tides_gauge)

    # Assert that modelled tides have the same coordinates as `satellite_ds`
    assert xr.align(measured_tides_ds, satellite_ds, join="exact")

    # Assert pixel_tide outputs are accurate
    assert gauge_stats["Correlation"] > 0.99
    assert gauge_stats["RMSE"] < 0.25
    assert gauge_stats["R-squared"] > 0.96
    assert abs(gauge_stats["Bias"]) < 0.20
