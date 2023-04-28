import datacube
import pyproj
import pandas as pd
import xarray as xr

# import sys
# sys.path.insert(1, "../../Tools/")
from dea_tools.coastal import model_tides, pixel_tides
from dea_tools.validation import eval_metrics


def load_measured_tides():
    # Metadata for Broome ABSLMP tidal station:
    # http://www.bom.gov.au/oceanography/projects/abslmp/data/data.shtml
    y, x = -18.0008, 122.2183
    ahd_offset = -5.322

    # Load measured tides from ABSLMP tide gauge data
    measured_tides_df = pd.read_csv(
        "data/IDO71013_2020.csv",
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


def test_measured_vs_modelled_tides():
    """
    Tests tides modelled by the `model_tides` function against measured
    data from the Broome ABSLMP tidal station:
    http://www.bom.gov.au/oceanography/projects/abslmp/data/data.shtml
    """
    # Load tide gauge data
    measured_tides_df = load_measured_tides()

    # Run the FES2014 tidal model
    modelled_tides_df = model_tides(
        x=[122.2183],
        y=[-18.0008],
        time=measured_tides_df.time,
    )

    # Compare measured and modelled outputs
    val_stats = eval_metrics(x=measured_tides_df.tide_m, y=modelled_tides_df.tide_m)

    # Test that outputs meet expected accuracy
    assert val_stats["Correlation"] > 0.99
    assert val_stats["RMSE"] < 0.26
    assert val_stats["R-squared"] > 0.98
    assert abs(val_stats["Bias"]) < 0.20


def test_pixel_tides():
    dc = datacube.Datacube()

    ds = dc.load(
        product="ga_ls8c_ard_3",
        x=(122.154715, 122.300630),
        y=(-17.914642, -18.032868),
        time="2020",
        dask_chunks={},
    )

    # Model tides
    modelled_tides_highres, modelled_tides_lowres = pixel_tides(ds)

    # Load measured tides and select same timesteps
    measured_tides = load_measured_tides().tide_m.interp(time=ds.time, method="linear")

    # Extract tides for tide gauge location
    x, y = pyproj.Transformer.from_crs(
        "EPSG:4326", f"EPSG:{ds.odc.geobox.crs.to_epsg()}"
    ).transform(-18.0008, 122.2183)
    modelled_tides_gauge = modelled_tides_highres.interp(y=y, x=x, method="linear")

    # Extract tides for non-gauge location
    x, y = pyproj.Transformer.from_crs(
        "EPSG:4326", f"EPSG:{ds.odc.geobox.crs.to_epsg()}"
    ).transform(-17.92, 122.16)
    modelled_tides_other = modelled_tides_highres.interp(y=y, x=x, method="linear")

    # Calculate stats
    gauge_stats = eval_metrics(x=measured_tides, y=modelled_tides_gauge)
    other_stats = eval_metrics(x=measured_tides, y=modelled_tides_other)

    # Assert that modelled tides have the same coordinates as `ds`
    assert xr.align(modelled_tides_highres, ds, join="exact")

    # Assert pixel_tide outputs are accurate
    assert gauge_stats["Correlation"] > 0.99
    assert gauge_stats["RMSE"] < 0.25
    assert gauge_stats["R-squared"] > 0.98
    assert abs(gauge_stats["Bias"]) < 0.20

    # Verify that pixel_tide outputs are more accurate at tide gauge
    # than further away
    assert gauge_stats["RMSE"] < other_stats["RMSE"]
