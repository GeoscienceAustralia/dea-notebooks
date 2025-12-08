import pandas as pd
import pytest
import pystac_client

from dea_tools.datahandling import stac_collections, stac_assets


@pytest.fixture(scope="session")
def catalog():
    # DEA STAC endpoint
    return pystac_client.Client.open("https://explorer.dea.ga.gov.au/stac")


@pytest.mark.parametrize(
    "products",
    [
        "ga_s2am_ard_3",                          # single product
        ["ga_s2am_ard_3", "ga_ls8c_ard_3"],       # multiple products
    ],
)
def test_stac_collections(catalog, products):
    df = stac_collections(catalog, products)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    # Check index contains all products
    prod_list = [products] if isinstance(products, str) else products
    assert set(df.index) == set(prod_list)

    # Expected columns exist
    for col in ["description", "bbox", "start_date", "end_date", "license"]:
        assert col in df.columns


@pytest.mark.parametrize(
    "products",
    [
        "ga_s2am_ard_3",
        ["ga_s2am_ard_3", "ga_s2bm_ard_3"],
    ],
)
def test_stac_assets(catalog, products):
    df = stac_assets(catalog, products)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert isinstance(df.index, pd.MultiIndex)
    assert list(df.index.names) == ["product", "asset"]

    # Check index includes all products
    prod_list = [products] if isinstance(products, str) else products
    prod_index = df.index.get_level_values("product")

    for p in prod_list:
        assert p in prod_index

    # Columns that should always be present
    for col in ["roles", "band_names", "nodata", "dtype"]:
        assert col in df.columns
