import matplotlib

matplotlib.use("Agg")

import numpy as np
import xarray as xr
import pytest
import matplotlib.pyplot as plt
from odc.geo.xr import assign_crs

from dea_tools.plotting import rgb


@pytest.fixture
def rgb_dataset():
    """A small synthetic 3-band dataset with a length-2 `time` dim."""
    nt, ny, nx = 2, 8, 10
    rng = np.random.default_rng(0)
    bands = ["nbart_red", "nbart_green", "nbart_blue"]
    ds = xr.Dataset(
        {b: (("time", "y", "x"), rng.integers(0, 3000, (nt, ny, nx)).astype("int16")) for b in bands},
        coords={
            "time": np.arange(nt),
            "y": np.linspace(-2e6, -2.001e6, ny),
            "x": np.linspace(1e6, 1.001e6, nx),
        },
    )
    return assign_crs(ds, crs="EPSG:3577")


def test_rgb_titles_single_composite(rgb_dataset):
    """Regression test for #1334: a single composite (no index dim) with
    custom titles must not raise (previously `AttributeError: 'AxesImage'
    object has no attribute 'axs'`). `rgb()` returns None and sets the
    title on the current axes."""
    composite = rgb_dataset.isel(time=0)
    rgb(composite, titles=["2021"])
    assert plt.gca().get_title() == "2021"
    plt.close("all")


def test_rgb_titles_single_index(rgb_dataset):
    """Regression test for #1334: selecting a single observation via
    `index=0` with custom titles must not raise."""
    rgb(rgb_dataset, index=0, titles=["2021"])
    assert plt.gca().get_title() == "2021"
    plt.close("all")


def test_rgb_titles_faceted(rgb_dataset):
    """The faceted path (multiple indices) must continue to work with a
    list of titles."""
    rgb(rgb_dataset, index=[0, 1], titles=["a", "b"])
    titles = {ax.get_title() for ax in plt.gcf().axes if ax.get_title()}
    assert titles == {"a", "b"}
    plt.close("all")


def test_rgb_titles_bare_string(rgb_dataset):
    """A bare string `titles` on a single panel should set the whole
    string as the title (not the first character via list-indexing)."""
    composite = rgb_dataset.isel(time=0)
    rgb(composite, titles="2021")
    assert plt.gca().get_title() == "2021"
    plt.close("all")
