import pytest
from pathlib import Path
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / "DEA_datasets" / "DEA_Sentinel2_Surface_Reflectance.ipynb"


@pytest.fixture(scope="module")
def tb():
    with testbook(NB_PATH, execute=True, timeout=180) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


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
        "oa_s2cloudless_mask",
        "oa_s2cloudless_prob"
    ]
    for var in expected_vars:
        assert var in ds.variables

def is_filtered(tb):
    ds = tb.ref("ds")
    ds_noncloudy = tb.ref("ds_noncloudy")

    assert len(ds.time) > len(ds_noncloudy.time)
