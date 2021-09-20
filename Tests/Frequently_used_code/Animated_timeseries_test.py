from pathlib import Path

import os
import pytest
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / "Frequently_used_code" / "Animated_timeseries.ipynb"

# Update working directory to ensure relative links in notebooks work
os.chdir("..")


@pytest.fixture(scope="module")
def tb():
    with testbook(NB_PATH, execute=True) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_cols(tb):
    gdf = tb.ref("poly_gdf")
    expected_cols = ["attribute",
                     "area",
                     "geometry",
                     "color",
                     "start_time",
                     "end_time"]
    for col in expected_cols:
        assert col in gdf.columns


def test_vars(tb):
    ds = tb.ref("ds")
    expected_vars = [
        "time",
        "y",
        "x",
        "spatial_ref",
        "nbart_red",
        "nbart_green",
        "nbart_blue",
        "nbart_nir_1",
        "nbart_swir_2",
        "NDWI"
    ]
    for var in expected_vars:
        assert var in ds.variables
