# import pytest
# from pathlib import Path
# from testbook import testbook

# TEST_DIR = Path(__file__).parent.parent.resolve()
# NB_DIR = TEST_DIR.parent
# NB_PATH = NB_DIR / "Frequently_used_code" / "Exporting_GeoTIFFs.ipynb"


# @pytest.fixture(scope="module")
# def tb():
#     with testbook(NB_PATH, execute=True) as tb:
#         yield tb


# def test_ok(tb):
#     assert True  # ok


# def test_dims(tb):
#     da = tb.ref("singleband_masked")
#     expected_dims = ["y", "x"]
#     for dim in expected_dims:
#         assert dim in da.dims

        
# def test_no_nodata(tb):
#     da = tb.ref("singleband_masked")
#     assert 'nodata' not in da.attrs