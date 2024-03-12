import pytest
import rioxarray
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

import datacube
from datacube.utils.masking import mask_invalid_data

from dea_tools.spatial import (
    subpixel_contours,
    xr_vectorize,
    xr_rasterize,
    xr_interpolate,
)
from dea_tools.validation import eval_metrics


@pytest.fixture(
    params=[
        None,  # Default WGS84
        "EPSG:3577",  # Australian Albers
        "EPSG:32756",  # UTM 56S
    ],
    ids=["dem_da_epsg4326", "dem_da_epsg3577", "dem_da_epsg32756"],
)
def dem_da(request):
    # Read elevation data from file
    raster_path = "Supplementary_data/Reprojecting_data/canberra_dem_250m.tif"
    da = rioxarray.open_rasterio(raster_path).squeeze("band")

    # Reproject if required
    crs = request.param
    if crs:
        # Reproject and mask out nodata
        da = da.odc.reproject(crs)
        da = da.where(da != da.nodata)

    return da


# Create test data in different CRSs and resolutions
@pytest.fixture(
    params=[
        ("EPSG:3577", (-30, 30)),  # Australian Albers 30 m pixels
        ("EPSG:4326", (-0.00025, 0.00025)),  # WGS84, 0.0025 degree pixels
    ],
    ids=["satellite_da_epsg3577", "satellite_da_epsg4326"],
)
def satellite_da(request):
    # Obtain CRS and resolution params
    crs, res = request.param

    # Connect to datacube
    dc = datacube.Datacube()

    # Load example satellite data around Broome tide gauge
    ds = dc.load(
        product="ga_ls8c_ard_3",
        measurements=["nbart_nir"],
        x=(122.2183 - 0.08, 122.2183 + 0.08),
        y=(-18.0008 - 0.08, -18.0008 + 0.08),
        time="2020-01",
        output_crs=crs,
        resolution=res,
        group_by="solar_day",
    )

    # Mask nodata
    ds = mask_invalid_data(ds)

    # Return single array
    return ds.nbart_nir


@pytest.fixture(
    params=[
        None,  # Default WGS84
        "EPSG:3577",  # Australian Albers
        "EPSG:32756",  # UTM 56S
    ],
    ids=[
        "categorical_da_epsg4326",
        "categorical_da_epsg3577",
        "categorical_da_epsg32756",
    ],
)
def categorical_da(request):
    # Read categorical raster from file
    raster_path = "Tests/data/categorical_raster.tif"
    da = rioxarray.open_rasterio(raster_path).squeeze("band")

    # Reproject if required
    crs = request.param
    if crs:
        # Reproject and mask out nodata
        da = da.odc.reproject(crs, resampling="nearest")

    return da


# Test set of points covering the extent of `dem_da`
@pytest.fixture()
def points_gdf():
    return gpd.GeoDataFrame(
        data={"z": [400, 800, 900, 1100, 1200, 1500]},
        geometry=gpd.points_from_xy(
            x=[149.06, 149.06, 149.10, 149.16, 149.20, 149.20],
            y=[-35.36, -35.22, -35.29, -35.29, -35.36, -35.22],
            crs="EPSG:4326",
        ),
    )


@pytest.mark.parametrize(
    "attribute_col, expected_col",
    [
        (None, "attribute"),  # Default creates a column called "attribute"
        ("testing", "testing"),  # Use custom output column name
    ],
)
def test_xr_vectorize(categorical_da, attribute_col, expected_col):
    # Vectorize data
    categorical_gdf = xr_vectorize(categorical_da, attribute_col=attribute_col)

    # Test correct columns are included
    assert expected_col in categorical_gdf
    assert "geometry" in categorical_gdf

    # Assert geometry
    assert isinstance(categorical_gdf, gpd.GeoDataFrame)
    assert (categorical_gdf.geometry.type.values == "Polygon").all()

    # Assert values
    assert len(categorical_gdf.index) >= 26
    assert len(categorical_gdf[expected_col].unique()) == len(np.unique(categorical_da))
    assert categorical_gdf.crs == categorical_da.odc.crs


def test_xr_vectorize_mask(categorical_da):
    # Vectorize data using a mask to remove non-1 values
    categorical_gdf = xr_vectorize(categorical_da, mask=categorical_da == 1)

    # Verify only values in array are 1
    assert (categorical_gdf.attribute == 1).all()


def test_xr_vectorize_output_path(categorical_da):
    # Vectorize and export to file
    categorical_gdf = xr_vectorize(categorical_da, output_path="testing.geojson")

    # Test that data on file is the same as original data
    assert gpd.read_file("testing.geojson").equals(categorical_gdf)


@pytest.mark.parametrize(
    "name",
    [
        None,  # Default does not rename output array
        "testing",  # Use custom output array name
    ],
)
def test_xr_rasterize(categorical_da, name):
    # Create vector to rasterize
    categorical_gdf = xr_vectorize(categorical_da)

    # Rasterize vector using attributes
    rasterized_da = xr_rasterize(
        gdf=categorical_gdf, da=categorical_da, attribute_col="attribute", name=name
    )

    # Assert that output is an xarray.DataArray
    assert isinstance(rasterized_da, xr.DataArray)

    # Assert that array has correct name
    assert rasterized_da.name == name

    # Assert that rasterized output is the same as original input after round trip
    assert np.allclose(rasterized_da, categorical_da)
    assert rasterized_da.odc.geobox.crs == categorical_da.odc.geobox.crs


def test_xr_rasterize_output_path(categorical_da):
    # Create vector to rasterize
    categorical_gdf = xr_vectorize(categorical_da)

    # Rasterize vector using attributes
    rasterized_da = xr_rasterize(
        gdf=categorical_gdf,
        da=categorical_da,
        attribute_col="attribute",
        output_path="testing.tif",
    )

    # Assert that output GeoTIFF data is same as input
    loaded_da = rioxarray.open_rasterio("testing.tif").squeeze("band")
    assert np.allclose(loaded_da, rasterized_da)


def test_subpixel_contours_dataseterror(dem_da):
    # Verify that function correctly raises error if xr.Dataset is passed
    with pytest.raises(ValueError):
        subpixel_contours(dem_da.to_dataset(name="test"), z_values=600)


@pytest.mark.parametrize(
    "z_values, expected",
    [
        (600, [600]),  # Single z-value, within DEM range
        ([600], [600]),  # Single z-value in list, within DEM range
        ([600, 700, 800], [600, 700, 800]),  # Multiple z, all within DEM range
        (0, []),  # Single z-value, outside DEM range
        ([0], []),  # Single z-value in list, outside DEM range
        ([0, 100, 200], []),  # Multiple z, all outside DEM range
        ([0, 700, 800], [700, 800]),  # Multiple z, some within DEM range
    ],
)
def test_subpixel_contours_dem(dem_da, z_values, expected):
    contours_gdf = subpixel_contours(dem_da, z_values=z_values)

    # Test correct columns are included
    assert "z_value" in contours_gdf
    assert "geometry" in contours_gdf

    # Test output is GeoDataFrame and all geometries are MultiLineStrings
    assert isinstance(contours_gdf, gpd.GeoDataFrame)
    assert (contours_gdf.geometry.type.values == "MultiLineString").all()

    # Verify that outputs are as expected
    assert contours_gdf.z_value.astype(int).to_list() == expected


@pytest.mark.parametrize(
    "z_values",
    [
        (0),  # Single z-value, all outside DEM range
        ([0]),  # Single z-value in list, all outside DEM range
        ([0, 100, 200]),  # Multiple z-values, all outside DEM range
    ],
)
def test_subpixel_contours_raiseerrors(dem_da, z_values):
    # Verify that function correctly raises error
    with pytest.raises(ValueError):
        subpixel_contours(dem_da, z_values=z_values, errors="raise")


@pytest.mark.parametrize(
    "min_vertices, expected_lines",
    [
        (2, [23, 25, 28]),  # Minimum 2 vertices; 23-28 linestrings expected
        (20, 5),  # Minimum 20 vertices; 5 linestrings expected
        (250, 1),  # Minimum 250 vertices; one linestring expected
    ],
)
def test_subpixel_contours_min_vertices(dem_da, min_vertices, expected_lines):
    contours_gdf = subpixel_contours(dem_da, z_values=600, min_vertices=min_vertices)

    # Check that number of individual linestrings match expected
    exploded_gdf = contours_gdf.geometry.explode(index_parts=False)
    assert np.isin(len(exploded_gdf.index), expected_lines)

    # Verify that minimum vertices are above threshold
    assert exploded_gdf.apply(lambda row: len(row.coords)).min() >= min_vertices


@pytest.mark.parametrize(
    "z_values, expected",
    [
        ([600, 700, 800], ["a", "b", "c"]),  # Valid data for a, b, c
        ([0, 700, 800], ["b", "c"]),  # Valid data for b, c
        ([0, 100, 800], ["c"]),  # Valid data for c only
        ([0, 100, 200], []),  # No valid data
    ],
)
def test_subpixel_contours_attribute_df(dem_da, z_values, expected):
    # Set up attribute dataframe (one row per elevation value above)
    attribute_df = pd.DataFrame({"foo": [1, 2, 3], "bar": ["a", "b", "c"]})

    contours_gdf = subpixel_contours(
        dem_da, z_values=z_values, attribute_df=attribute_df
    )

    # Verify correct columns are included in output
    assert "foo" in contours_gdf
    assert "bar" in contours_gdf
    assert "z_value" in contours_gdf
    assert "geometry" in contours_gdf

    # Verify that attributes are correctly included
    assert contours_gdf.bar.tolist() == expected


@pytest.mark.parametrize(
    "z_values, expected",
    [
        (3000, ["2020-01-04", "2020-01-13", "2020-01-20", "2020-01-29"]),
        (5000, ["2020-01-04", "2020-01-13", "2020-01-29"]),
        (7000, ["2020-01-04", "2020-01-13"]),
        (8000, ["2020-01-04"]),
    ],
)
def test_subpixel_contours_satellite_da(satellite_da, z_values, expected):
    contours_gdf = subpixel_contours(satellite_da, z_values=z_values)

    # Test correct columns are included
    assert "time" in contours_gdf
    assert "geometry" in contours_gdf

    # Test output is GeoDataFrame and all geometries are MultiLineStrings
    assert isinstance(contours_gdf, gpd.GeoDataFrame)
    assert (contours_gdf.geometry.type.values == "MultiLineString").all()

    # Verify that outputs are as expected
    assert contours_gdf.time.to_list() == expected


def test_subpixel_contours_multiple_z(satellite_da):
    # Verify that function correctly raises error multiple z values are
    # provided on inputs with multiple timesteps
    with pytest.raises(ValueError):
        subpixel_contours(satellite_da, z_values=[600, 700, 800])


def test_subpixel_contours_dim(satellite_da):
    # Rename dim to custom value
    satellite_da_date = satellite_da.rename({"time": "date"})

    # Verify that function correctly raises error if default dim of "time"
    # doesn't exist in the array
    with pytest.raises(KeyError):
        subpixel_contours(satellite_da_date, z_values=600)

    # Verify that function runs correctly if `dim="date"` is specified
    subpixel_contours(satellite_da_date, z_values=600, dim="date")


# def test_subpixel_contours_dem_crs(dem_da):
#     # Verify that an error is raised if data passed with no spatial ref/geobox
#     with pytest.raises(ValueError):
#         subpixel_contours(dem_da.drop_vars("spatial_ref"), z_values=700)

#     # Verify that no error is raised if we provide the correct CRS
#     subpixel_contours(dem_da.drop_vars("spatial_ref"), z_values=700, crs="EPSG:4326")


@pytest.mark.parametrize(
    "method",
    ["linear", "cubic", "nearest", "rbf", "idw"],
)
def test_xr_interpolate(dem_da, points_gdf, method):
    # Run interpolation and verify that pixel grids are the same and
    # output contains data
    interpolated_ds = xr_interpolate(
        dem_da,
        gdf=points_gdf,
        method=method,
        k=5,
    )
    assert interpolated_ds.odc.geobox == dem_da.odc.geobox
    assert "z" in interpolated_ds.data_vars
    assert interpolated_ds["z"].notnull().sum() > 0

    # Sample interpolated values at each point, and verify that
    # interpolated z values match our input z values
    xs = xr.DataArray(points_gdf.to_crs(dem_da.odc.crs).geometry.x, dims="z")
    ys = xr.DataArray(points_gdf.to_crs(dem_da.odc.crs).geometry.y, dims="z")
    sampled = interpolated_ds["z"].interp(x=xs, y=ys, method="nearest")
    val_stats = eval_metrics(points_gdf.z, sampled)
    assert val_stats.Correlation > 0.9
    assert val_stats.MAE < 10

    # Verify that a factor above 1 still returns expected results
    interpolated_ds_factor10 = xr_interpolate(
        dem_da,
        gdf=points_gdf,
        method=method,
        k=5,
        factor=10,
    )
    assert interpolated_ds_factor10.odc.geobox == dem_da.odc.geobox
    assert "z" in interpolated_ds_factor10.data_vars
    assert interpolated_ds_factor10["z"].notnull().sum() > 0

    # Verify that multiple columns can be processed, and that output
    # includes only numeric vars
    points_gdf["num_var"] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    points_gdf["obj_var"] = ["a", "b", "c", "d", "e", "f"]
    interpolated_ds_cols = xr_interpolate(
        dem_da,
        gdf=points_gdf,
        method=method,
        k=5,
    )
    assert "z" in interpolated_ds_cols.data_vars
    assert "num_var" in interpolated_ds_cols.data_vars
    assert "obj_var" not in interpolated_ds_cols.data_vars

    # Verify that specific columns can be selected
    interpolated_ds_cols2 = xr_interpolate(
        dem_da,
        gdf=points_gdf,
        columns=["num_var"],
        method=method,
        k=5,
    )
    assert "z" not in interpolated_ds_cols2.data_vars
    assert "num_var" in interpolated_ds_cols2.data_vars

    # Verify that error is raised if no numeric columns exist
    with pytest.raises(ValueError):
        xr_interpolate(
            dem_da,
            gdf=points_gdf,
            columns=["obj_var"],
            method=method,
            k=5,
        )

    # Verify that error is raised if `gdf` doesn't overlap with `ds`
    with pytest.raises(ValueError):
        xr_interpolate(
            dem_da,
            gdf=points_gdf.set_crs("EPSG:3577", allow_override=True),
            method=method,
            k=5,
        )

    # If IDW method, verify that k will fail if greater than points
    if method == "idw":
        with pytest.raises(ValueError):
            xr_interpolate(
                dem_da,
                gdf=points_gdf,
                method=method,
                k=10,
            )
