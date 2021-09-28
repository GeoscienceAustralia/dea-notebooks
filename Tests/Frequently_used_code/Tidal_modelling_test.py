# import pytest
# from pathlib import Path
# from testbook import testbook

# TEST_DIR = Path(__file__).parent.parent.resolve()
# NB_DIR = TEST_DIR.parent
# NB_PATH = NB_DIR / "Frequently_used_code" / "Tidal_modelling.ipynb"


# @pytest.fixture(scope="module")
# def tb():
#     with testbook(NB_PATH, execute=True) as tb:
#         yield tb


# def test_ok(tb):
#     assert True  # ok


# def test_vars(tb):
#     ds = tb.ref("ds_tidal")
#     expected_vars = [
#         "nbart_red",
#         "nbart_green",
#         "nbart_blue",
#         "time",
#         "y",
#         "x",
#         "spatial_ref",
#         "tide_height",
#         "ebb_flow",
#     ]
#     for var in expected_vars:
#         assert var in ds.variables


# def test_stats(tb):
#     df = tb.ref("out_stats")
#     expected_stats = [
#         "tidepost_lat",
#         "tidepost_lon",
#         "observed_mean_m",
#         "all_mean_m",
#         "observed_min_m",
#         "all_min_m",
#         "observed_max_m",
#         "all_max_m",
#         "observed_range_m",
#         "all_range_m",
#         "spread",
#         "low_tide_offset",
#         "high_tide_offset",
#         "observed_slope",
#         "all_slope",
#         "observed_pval",
#         "all_pval",
#     ]
#     for stat in expected_stats:
#         assert stat in df
