import datetime
import geopandas as gpd
import itertools
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import imageio
import shutil

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
        polygon_base_df = polygon_base_df.drop("index", axis=1)
        polygon_base_df.to_csv(export_csv, index_label ="date")

    return ds_wit, polygon_base_df

# this sorts the fractional cover values into their classes

def classify_pixel(pv, npv, bs):
    if pv > 2/3:
        return 8  # pv
    elif npv > 2/3:
        return 0  # ng
    elif bs > 2/3:
        return 4  # bs
    elif npv > 1/3 and bs > 1/3 and pv < 1/3:
        return 1  # ng_bs
    elif npv > 1/3 and pv > 1/3 and bs < 1/3:
        return 3  # ng_pv
    elif npv > 1/3 and pv < 1/3 and bs < 1/3:
        return 2  # ng_mix
    elif bs > 1/3 and pv > 1/3 and npv < 1/3:
        return 6  # bs_pv
    elif bs > 1/3 and pv < 1/3 and npv < 1/3:
        return 5  # bs_mix
    elif pv > 1/3 and npv < 1/3 and bs < 1/3:
        return 7  # pv_mix
    return -1 

def spatial_wit(ds):

    ds = ds.dropna(dim='time', how='all')

    fraction_sum = ds['pv'] + ds['npv'] + ds['bs']
    ds['pv'] = ds['pv'] / fraction_sum
    ds['npv'] = ds['npv'] / fraction_sum
    ds['bs'] = ds['bs'] / fraction_sum

    # Apply the classification function to the dataset across all time, y, x
    fc_class = xr.apply_ufunc(
    classify_pixel,
    ds['pv'], ds['npv'], ds['bs'],
    vectorize=True,
    )

    fc_class = fc_class.where(fc_class != -1, np.nan)

    # Add the new classification band to the dataset
    ds['fc_class'] = fc_class

    # this is a colour map for mapping fc only
    color_dict = {
        0: "#F1E8C9",  # ng
        1: "#C0AB86",  # ng_bs
        2: "#D6D2A7",  # ng_mix
        3: "#BCD495",  # ng_pv
        4: "#93724C",  # bs
        5: "#9C895D",  # bs_mix
        6: "#8F9C5C",  # bs_pv
        7: "#9DBD74",  # pv_mix
        8: "#8CC46B",  # pv
    }
    
    # Create a ListedColormap and a corresponding norm
    cmap = mcolors.ListedColormap([color_dict[i] for i in range(9)], name='fc_class_cmap')
    bounds = list(color_dict.keys()) + [len(color_dict)]  # Bounds for each color
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    
    # here we are making a brand new band called wetland that combines all the fc classes with the water and wet classes
    # i.e. water == 10, wet == 9, all other areas retain original fc class
    wetland = ds['fc_class'].where((ds['water'] == 0) | ds['water'].isnull(), 10)
    ds['wetland'] = wetland
    wetland = ds['wetland'].where((ds['wet'] == 0) | ds['wet'].isnull(), 9)
    ds['wetland'] = wetland

    class_labels = [
        "dry veg", "dry veg and bare mix", "dry mix", "dry veg and green veg",
        "bare soil", "bare soil mix", "bare soil and green veg", "green veg mix",
        "green veg", "wet", "water"
    ]
    
    # Define the colormap with your custom colors
    cmap = mcolors.ListedColormap([
        "#F1E8C9",  # ng
        "#C0AB86",  # ng_bs
        "#D6D2A7",  # ng_mix
        "#BCD495",  # ng_pv
        "#93724C",  # bs
        "#9C895D",  # bs_mix
        "#8F9C5C",  # bs_pv
        "#9DBD74",  # pv_mix
        "#8CC46B",  # pv
        "#6ce6f8", #wet
        "#676dca" # water
    ])
    
    # Create a BoundedNorm to ensure correct mapping of data to the colormap
    norm = mcolors.Normalize(vmin=0, vmax=10)

    # create a directory to save the frames
    os.makedirs("deawetlands_outputs", exist_ok=True)
    
    # if you want to save them all 
    for t in ds.time:
        wetland_time_step = ds['wetland'].sel(time=t)
        date_str = str(t.values)[:10]  # Extract date as string
        wetland_time_step.rio.to_raster(f"deawetlands_outputs/wetland_{date_str}.tif")

    # to make one big plot

    num_time_steps = ds.sizes['time']

    num_columns = min(num_time_steps, 20)

    num_rows = (num_time_steps + num_columns - 1) // num_columns  # Calculate the number of rows
    
    fig, axes = plt.subplots(num_rows, num_columns, figsize=(num_columns * 3, num_rows * 5))
    
    if num_rows == 1:
        axes = axes.reshape(1, num_columns)
    elif num_columns == 1:
        axes = axes.reshape(num_rows, 1)

    # Hide any unused axes
    for i in range(num_rows * num_columns):
        if i >= num_time_steps:
            fig.delaxes(axes.flatten()[i])
    
    for t in range(num_time_steps):
        time_step = ds['wetland'].isel(time=t)
        time_ns = ds['time'].isel(time=t).values.item()
        time_date = pd.to_datetime(time_ns, unit='ns')
        time_date_str = time_date.strftime('%d-%m-%Y')
        row_idx = t // num_columns 
        col_idx = t % num_columns
        cax = axes[row_idx, col_idx].imshow(time_step, cmap=cmap, norm=norm, interpolation='none')
        axes[row_idx, col_idx].set_title(f'{time_date_str}')
    
    plt.tight_layout()
    plt.savefig(f'deawetlands_outputs/wetland_time_steps.png', dpi=300)  

    # make a gif
    
    # loop through each time step, creating and saving a frame
    num_time_steps = ds.sizes['time']
    frames = []
    
    for t in range(num_time_steps):
        fig, ax = plt.subplots(figsize=(6, 6))  # adjust size as needed
        time_step = ds['wetland'].isel(time=t)
        
        time_ns = ds['time'].isel(time=t).values.item()
        time_date = pd.to_datetime(time_ns, unit='ns')
        time_date_str = time_date.strftime('%d-%m-%Y')
        
        cax = ax.imshow(time_step, cmap=cmap, norm=norm, interpolation='none')
        ax.set_title(f'Time: {time_date_str}')
        
        frame_path = f'deawetlands_outputs/wetland_{time_date_str}.png'
        plt.savefig(frame_path)
        frames.append(frame_path)
        plt.close(fig) 
        
    #make the gif
    output_path = f'deawetlands_outputs/wetland_animation.gif'
    with imageio.get_writer(output_path, mode='I', duration=0.7, loop=0) as writer:
        for frame_path in frames:
            image = imageio.imread(frame_path)
            writer.append_data(image)
    
    # print("GIF saved as 'wetland_animation.gif'")
    
    # clean up
    #for frame_path in frames:
    #    os.remove(frame_path)
    #shutil.rmtree("frames")

    return output_path