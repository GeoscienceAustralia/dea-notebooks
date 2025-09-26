import pytest
import numpy as np
import pandas as pd
import xarray as xr

from dea_tools.coastal import glint_angle


@pytest.fixture()
def angle_metadata_ds():
    """
    Create a sample xarray.Dataset containing sun and satellite view
    angle data
    """

    # Create sample data as a dataframe
    df = pd.DataFrame(
        index=pd.Index(pd.date_range("2020", "2021", 2), name="time"),
        data=np.array([[22, 78, 99, 10], [21, 76, 280, 5]]),
        columns=[
            "oa_solar_zenith",
            "oa_solar_azimuth",
            "oa_satellite_azimuth",
            "oa_satellite_view",
        ],
    )

    # Convert to xarray to simulate data loaded from datacube
    return df.to_xarray()


def test_glint_angle(angle_metadata_ds):
    # Calculate glint angles
    glint_array = glint_angle(
        solar_azimuth=angle_metadata_ds.oa_solar_azimuth,
        solar_zenith=angle_metadata_ds.oa_solar_zenith,
        view_azimuth=angle_metadata_ds.oa_satellite_azimuth,
        view_zenith=angle_metadata_ds.oa_satellite_view,
    )

    # Verify values are expected
    assert np.allclose(glint_array, np.array([31.5297584, 16.5520374]))

    # Verify output as an xarray.DataArray
    assert isinstance(glint_array, xr.DataArray)
