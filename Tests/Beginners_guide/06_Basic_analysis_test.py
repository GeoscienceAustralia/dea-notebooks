from pathlib import Path

import pytest
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent

NB_PATH = NB_DIR / 'Beginners_guide' / '06_Basic_analysis.ipynb'


@pytest.fixture(scope='module')
def tb():
    with testbook(NB_PATH, execute=True) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_shape(tb):
    ds = tb.ref("ds")
    expected_vars = [
        'time',
         'y',
         'x',
         'spatial_ref',
         'nbart_red',
         'nbart_blue',
         'nbart_green',
         'nbart_nir_1']
    for var in expected_vars:
        assert var in ds.variables
