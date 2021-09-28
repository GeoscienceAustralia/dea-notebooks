# import pytest
# from pathlib import Path
# from testbook import testbook

# TEST_DIR = Path(__file__).parent.parent.resolve()
# NB_DIR = TEST_DIR.parent
# NB_PATH = NB_DIR / "Frequently_used_code" / "Polygon_drill.ipynb"


# @pytest.fixture(scope="module")
# def tb():
#     with testbook(NB_PATH, execute=True) as tb:
#         yield tb


# def test_ok(tb):
#     assert True  # ok


# def test_geometry(tb):
#     gdf = tb.ref("polygon_to_drill")
#     assert "geometry" in gdf.columns


# def test_vars(tb):
#     ds = tb.ref("data")
#     expected_vars = [
#         "time",
#         "y",
#         "x",
#         "spatial_ref",
#         "nbart_red",
#         "nbart_green",
#         "nbart_blue",
#     ]
#     for var in expected_vars:
#         assert var in ds.variables


# def test_shape(tb):
#     ds = tb.ref("mask")
#     assert len(ds.x) == 97
#     assert len(ds.y) == 120


# def test_masked(tb):
#     ds = tb.ref("data_masked")
#     assert ds.nbart_red.isnull().any().item()
