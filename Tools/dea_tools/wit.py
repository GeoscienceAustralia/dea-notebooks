import datetime
import geopandas as gpd
import itertools
import numpy as np
import pandas as pd
import xarray as xr

import datacube

import sys

sys.path.insert(1, "../Tools/")
import dea_tools.bandindices
import dea_tools.datahandling
from dea_tools.spatial import xr_rasterize
from dea_tools.dask import create_local_dask_cluster
import dea_tools.wetlands
import dea_tools.wit

# Create local dask cluster to improve data load time
client = create_local_dask_cluster(return_client=True)

def WIT_drill(
    gdf,
    time,
    #min_gooddata=0.85,
    #resample_frequency=None,
    export_csv=None,
    dask_chunks=None,
    verbose=False,
    verbose_progress=False,
):

    # add geom to dc query dict
    if isinstance(gdf, datacube.utils.geometry._base.Geometry):
        gdf = gpd.GeoDataFrame({"col1": ["name"], "geometry": gdf.geom}, crs=gdf.crs)
    geom = datacube.utils.geometry.Geometry(geom=gdf.iloc[0].geometry, crs=gdf.crs)
    #query = {"geopolygon": geom, "time": time}

    dc = datacube.Datacube(app="DEA_Wetlands_Insight_Tool")

    if verbose_progress:
        print("Loading Landsat data")

    # Define which spectral bands are being used in the analysis
    bands = [
        f"nbart_{band}" for band in ("blue", "green", "red", "nir", "swir_1", "swir_2")
    ]
    
    # Load Landsat 5, 7 and 8 data. Not including Landsat 7 SLC off period (31-05-2003 to 06-04-2022).
    ds_ls = dea_tools.datahandling.load_ard(
        dc,
        products=["ga_ls8c_ard_3", "ga_ls7e_ard_3", "ga_ls5t_ard_3"],
        ls7_slc_off=False,
        measurements=bands,
        geopolygon=geom,
        output_crs="EPSG:3577",
        resolution=(-30, 30),
        resampling={"fmask": "nearest", "*": "bilinear"},
        time=time,
        group_by="solar_day",
        dask_chunks={"time":1, "x": 2048, "y": 2048},
    )
    
    # Load into memory using Dask
    ds_ls.load()

    # create polygon mask
    poly_mask = xr_rasterize(gdf.iloc[[0]], ds_ls)
    ds_ls = ds_ls.where(poly_mask)
        
    ds_wo = dc.load(
    "ga_ls_wo_3", resampling="nearest", group_by="solar_day", like=ds_ls, dask_chunks={"time":1, "x": 2048, "y": 2048}
    )
    ds_fc = dc.load(
        "ga_ls_fc_3", resampling="nearest", group_by="solar_day", like=ds_ls, dask_chunks={"time":1, "x": 2048, "y": 2048}
    )
    
    # Load data into memory
    ds_wo.load()
    ds_fc.load()

    missing = set()
    for t1, t2 in itertools.product(
        [ds_fc.time.values, ds_wo.time.values, ds_ls.time.values], repeat=2
    ):
        missing_ = set(t1) - set(t2)
        missing |= missing_
    
    ds_fc = ds_fc.sel(time=[t for t in ds_fc.time.values if t not in missing])
    ds_ls = ds_ls.sel(time=[t for t in ds_ls.time.values if t not in missing])
    ds_wo = ds_wo.sel(time=[t for t in ds_wo.time.values if t not in missing])
    
    
    tcw = dea_tools.bandindices.calculate_indices(
        ds_ls, index="TCW", collection="ga_ls_3", normalise=False, drop=True, inplace=False
    )
    
    bs = ds_fc.bs / 100
    pv = ds_fc.pv / 100
    npv = ds_fc.npv / 100

    rast_names = ["pv", "npv", "bs", "wet", "water"]
    output_rast = {n: xr.zeros_like(bs) for n in rast_names}
    
    output_rast["bs"].values[:] = bs
    output_rast["pv"].values[:] = pv
    output_rast["npv"].values[:] = npv
    
    # Rasterise the shapefile where poly is the vector data and pv is the xarray template
    poly_raster = xr_rasterize(gdf, pv) > 0
    
    # Mask includes No data, Non contiguous data, Cloud shadow, Cloud, and water.
    # See https://knowledge.dea.ga.gov.au/notebooks/DEA_products/DEA_Water_Observations/#Understanding-WOs-bit-flags for more detail.
    mask = (ds_wo.water & 0b01100011) == 0
    mask &= poly_raster
    
    # Set open water to water present and classified as water as per Water Observations and bit flags
    open_water = ds_wo.water & (1 << 7) > 0
    
    # Set wet pixels where not masked and above threshold of -350
    wet = tcw.where(mask).TCW > -350
    
    # Adding wet and water values to output raster
    
    # TCW
    output_rast["wet"].values[:] = wet.values.astype(float)
    for name in rast_names[:3]:
        output_rast[name].values[wet.values] = 0
    
    # WO
    output_rast["water"].values[:] = open_water.values.astype(float)
    for name in rast_names[:4]:
        output_rast[name].values[open_water.values] = 0
    
    # Masking again
    ds_wit = xr.Dataset(output_rast).where(mask)


    # Calculate percentage missing
    pc_missing = (~mask).where(poly_raster).mean(dim=["x", "y"])
    
    ds_wit = ds_wit.where(pc_missing < 0.1)
    
    # Convert ds_wit: XArray.Dataset to polygon_base_df: pandas.DataFrame
    
    polygon_base_df = pd.DataFrame()
    polygon_base_df["date"] = ds_wit.time.values
    
    for band in rast_names:
        polygon_base_df[band] = ds_wit[band].mean(dim=["x", "y"])
    
    polygon_base_df = dea_tools.wetlands.normalise_wit(polygon_base_df)

    if export_csv:
        if verbose:
            print("exporting csv: " + export_csv)
        polygon_base_df.to_csv(export_csv, index_label="Datetime")

    return polygon_base_df