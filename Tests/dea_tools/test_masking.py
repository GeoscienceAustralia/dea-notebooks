import pandas as pd
import pytest
import pystac_client

from dea_tools.masking import make_mask, create_mask_value, mask_to_dict

@pytest.fixture(scope="session")
def catalog():
    # DEA STAC endpoint
    return pystac_client.Client.open("https://explorer.dea.ga.gov.au/stac")

