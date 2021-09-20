import pytest
from pathlib import Path
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent

NB_PATH = NB_DIR / "Frequently_used_code" / "Calculating_band_indices.ipynb"


@pytest.fixture(scope="module")
def tb():
    with testbook(NB_PATH, execute=True) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_vars_ndvi(tb):
    ds = tb.ref("ds_ndvi")
    expected_vars = [
        "time",
        "y",
        "x",
        "spatial_ref",
        "nbart_red",
        "nbart_blue",
        "nbart_green",
        "nbart_nir",
        "nbart_swir_1",
        "nbart_swir_2",
        "ndvi",
        "NDVI",
    ]
    for var in expected_vars:
        assert var in ds.variables


def test_vars_multi(tb):
    ds = tb.ref("ds_multi")
    expected_vars = [
        "time",
        "y",
        "x",
        "spatial_ref",
        "nbart_red",
        "nbart_blue",
        "nbart_green",
        "nbart_nir",
        "nbart_swir_1",
        "nbart_swir_2",
        "ndvi",
        "NDVI",
        "NDWI",
        "MNDWI",
    ]
    for var in expected_vars:
        assert var in ds.variables


def test_vars_drop(tb):
    ds = tb.ref("ds_multi")
    expected_vars = ["time", "y", "x", "spatial_ref", "NDVI", "NDWI", "MNDWI"]
    for var in expected_vars:
        assert var in ds.variables


def test_vars_ds(tb):
    ds = tb.ref("ds")
    expected_vars = ["time", "y", "x", "spatial_ref", "ndvi", "TCW"]
    for var in expected_vars:
        assert var in ds.variables
