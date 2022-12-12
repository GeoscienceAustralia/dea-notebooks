import pytest
from pathlib import Path
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / 'Frequently_used_code' / 'Using_load_ard.ipynb'


@pytest.fixture(scope='module')
def tb():
    with testbook(NB_PATH, execute=True, timeout=180) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_vars(tb):
    ds = tb.ref("ds")
    expected_vars = [
         'time',
         'y',
         'x',
         'spatial_ref',
         'nbart_red',
         'nbart_green',
         'nbart_blue']
    for var in expected_vars:
        assert var in ds.variables


def test_vars_s2(tb):
    ds_s2 = tb.ref("ds_s2")
    expected_vars = [
         'time',
         'y',
         'x',
         'spatial_ref',
         's2cloudless_prob']
    for var in expected_vars:
        assert var in ds_s2.variables


def test_vars_dask(tb):
    ds_dask = tb.ref("ds_dask")
    expected_vars = [
         'time',
         'y',
         'x',
         'spatial_ref',
         'nbart_red',
         'nbart_green',
         'nbart_blue']
    for var in expected_vars:
        assert var in ds_dask.variables


def is_dask(tb):    
    ds_dask = tb.ref("ds_dask")
    
    import dask
    assert dask.is_dask_collection(ds_dask)


def is_filtered(tb):    
    ds_s2 = tb.ref("ds_s2")
    ds_filtered = tb.ref("ds_filtered")

    assert len(ds_s2.time) > len(ds_filtered.time) 