from pathlib import Path

import pytest
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent

NB_PATH = NB_DIR / "Frequently_used_code" / "Rasterize_vectorize.ipynb"


@pytest.fixture(scope="module")
def tb():
    with testbook(NB_PATH, execute=True) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_geometry(tb):
    gdf = tb.ref("gdf")
    assert "geometry" in gdf.columns


def test_shape(tb):
    ds = tb.ref("water_bodies_again")
    assert len(ds.x) == 2789
    assert len(ds.y) == 2443
