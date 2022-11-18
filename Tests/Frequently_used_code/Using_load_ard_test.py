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
         'nbart_green']
    for var in expected_vars:
        assert var in ds.variables
