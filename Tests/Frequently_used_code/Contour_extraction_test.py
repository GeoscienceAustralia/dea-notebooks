import os
import pytest
from pathlib import Path
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / "How_to_guides" / "Contour_extraction.ipynb"


@pytest.fixture(scope="module")
def tb():
    
    # Update working directory to ensure relative links in notebooks work
    os.chdir(NB_DIR.parent)
    
    with testbook(NB_PATH, execute=True, timeout=180) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_z_values(tb):
    gdf = tb.ref("contours_gdf")
    assert "z_value" in gdf.columns
    assert gdf.z_value.to_list() == ["550", "600", "650"]


def test_location(tb):
    gdf = tb.ref("contours_gdf")
    assert "location" in gdf.columns
    assert gdf.location.to_list() == ["ACT", "ACT", "ACT"]


def test_time(tb):
    gdf = tb.ref("contours_s2_gdf")
    assert "time" in gdf.columns
    assert gdf.time.to_list() == ["2018-01-05", "2018-02-24"]
