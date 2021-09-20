from pathlib import Path

import os
import pytest
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / "Frequently_used_code" / "Generating_composites.ipynb"

# Update working directory to ensure relative links in notebooks work
os.chdir("..")


@pytest.fixture(scope="module")
def tb():
    with testbook(NB_PATH, execute=True) as tb:
        yield tb


def test_ok(tb):
    assert True  # ok


def test_no_time(tb):
    ds_median = tb.ref("ds_median")
    ds_mean = tb.ref("ds_mean")
    da_min = tb.ref("da_min")
    da_max = tb.ref("da_max")
    da_before = tb.ref("da_before")
    da_after = tb.ref("da_after")
    da_nearest = tb.ref("da_nearest")
    assert "time" not in ds_median.dims
    assert "time" not in ds_mean.dims
    assert "time" not in da_min.dims
    assert "time" not in da_max.dims
    assert "time" not in da_before.dims
    assert "time" not in da_after.dims
    assert "time" not in da_nearest.dims


def test_resampled_median(tb):
    ds = tb.ref("ds_resampled_median")
    assert "time" in ds.dims
    assert len(ds.time) == 3


def test_groupby_median(tb):
    ds = tb.ref("ds_groupby_season")
    assert "season" in ds.dims
    assert len(ds.season) == 4


def test_resampled_mean(tb):
    ds = tb.ref("ds_resampled_mean")
    assert "time" in ds.dims
    assert len(ds.time) == 3
