"""
Test some of the terrain masking functions
"""

import pytest
import hypothesis
from hypothesis import given
from hypothesis import strategies as st

from datacube.utils.geometry import CRS
from wofs.terrain import vector_to_crs

# Use slightly less than the projected boundary from
# https://spatialreference.org/ref/epsg/gda94-australian-albers/
points_3577 = st.tuples(st.integers(min_value=-5000000, max_value=-3000000),
                        st.integers(min_value=-1500000, max_value=2500000))

vectors = st.tuples(st.integers(min_value=-100, max_value=100),
                    st.integers(min_value=-100, max_value=100))

@hypothesis.settings(deadline=500)
@given(points_3577, vectors)
def test_vector_to_crs(orig_point, orig_vect):
    """
    Given a random point (in EPSG:3577) and vector, convert to EPSG:4326
    and back

    Ensure you get your starting values back (approximately)
    """
    inter_point, inter_vect = vector_to_crs(orig_point, orig_vect,
                                            original_crs=CRS('EPSG:3577'),
                                            destination_crs=CRS('EPSG:4326'))

    new_point, new_vect = vector_to_crs(inter_point, inter_vect,
                                        original_crs=CRS('EPSG:4326'),
                                        destination_crs=CRS('EPSG:3577'))

    assert orig_point == pytest.approx(new_point, abs=1e-6)
    assert orig_vect == pytest.approx(new_vect, abs=1e-6)
