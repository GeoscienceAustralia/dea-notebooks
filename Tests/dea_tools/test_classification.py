import pytest
import datacube
import numpy as np
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point
from pandas.testing import assert_frame_equal
from dea_tools.classification import collect_training_data

# --- feature function MUST be top level for multiprocessing ---
def feature_func(query):
    dc = datacube.Datacube(app="pytest_training_data")

    ds = dc.load(
        product="ga_ls8cls9c_gm_cyear_3",
        **query,
    )
    return ds

@pytest.fixture
def point_gdf():
    gdf = gpd.GeoDataFrame(
        {
            "class": [1, 2],
            "geometry": [
                Point(149.12, -35.30),
                Point(149.13, -35.31),
            ],
        },
        crs="EPSG:4326",
    )
    return gdf

@pytest.fixture
def dc_query():
    return {
        "time": ("2020"),
        "resolution": (-30, 30),
        "output_crs": "EPSG:3577",
    }

@pytest.fixture
def serial_result(point_gdf, dc_query):
    
    return collect_training_data(
        gdf=point_gdf,
        dc_query=dc_query,
        ncpus=1,
        feature_func=feature_func,
        field="class",
    )

@pytest.fixture
def parallel_result(point_gdf, dc_query):
    
    return collect_training_data(
        gdf=point_gdf,
        dc_query=dc_query,
        ncpus=2,
        feature_func=feature_func,
        field="class",
    )

def test_collect_training_data_serial(serial_result):
    assert not serial_result.empty

def test_collect_training_data_parallel(parallel_result):
    assert not parallel_result.empty

def test_serial_parallel_equivalent(
    serial_result,
    parallel_result,
):
    assert_frame_equal(
        serial_result,
        parallel_result
    )


