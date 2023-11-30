from datacube import Datacube

from wofs.wofls import woffles
import pytest

WATER = 136  # note, this is wrong.
NOT_WATER = 8


@pytest.mark.skip("Requires running ODC Database + Data")
@pytest.mark.parametrize("query,expected", [
    # Australian Parliament House, generally not water
    (dict(lat=(-35.308, -35.309), lon=(149.124, 149.125), time=('2016-01-10', '2016-01-14')), NOT_WATER),
    # Middle of Lake Burley Griffith. Water
    (dict(lat=(-35.295, -35.296), lon=(149.137, 149.138), time=('2016-01-10', '2016-01-14')), WATER),
])
def test_woffles(query, expected):
    dc = Datacube(app='test_wofls')

    bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']  # inputs needed from EO data)
    source = dc.load(product='ls8_nbar_albers', measurements=bands, **query)
    pq = dc.load(product='ls8_pq_albers', like=source)
    dsm = dc.load(product='dsm1sv10', like=source, time=('1900-01-01', '2100-01-01'), resampling='cubic')

    wofls_output = woffles(*(x.isel(time=0) for x in [source, pq, dsm]))

    assert (wofls_output == expected).all()
