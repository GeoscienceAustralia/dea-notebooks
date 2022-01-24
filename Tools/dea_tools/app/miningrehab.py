# notebookapp_miningrehab.py
'''
This file contains functions for loading and interacting with data in the
mining rehabilitation notebook, inside the Real_world_examples folder.

Available functions:
    load_miningrehab_data
    run_miningrehab_app

Last modified: September 2021
'''

# Load modules
from ipyleaflet import Map, GeoJSON, DrawControl, basemaps
import datetime as dt
import datacube
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import rasterio.features
import IPython
from IPython.display import display
import warnings
import ipywidgets as widgets
from datacube.utils import masking

# Load utility functions
import sys
sys.path.insert(1, '../Tools/')
from dea_tools.datahandling import wofs_fuser
from dea_tools.spatial import transform_geojson_wgs_to_epsg


def load_miningrehab_data():
    """
    Loads DEA Fractional Cover and Water Observations products for the mining
    case-study area.
    Last modified: July 2021

    outputs
    ds - data set containing masked Fractional Cover data from Landsat 8
    Masked values are set to 'nan'
    """
    
    # Suppress warnings
    warnings.filterwarnings("ignore")

    # Initialise the data cube. 'app' argument is used to identify this app
    dc = datacube.Datacube(app="mining-app")

    # Specify latitude and longitude ranges
    latitude = (-34.426512, -34.434517)
    longitude = (116.648123, 116.630731)

    # Specify the date range
    time = ("2015-06-01", "2018-06-30")

    # Construct the data cube query
    query = {
        "x": longitude,
        "y": latitude,
        "time": time,
        "output_crs": "EPSG:3577",
        "resolution": (-30, 30),
    }

    print("Loading DEA Fractional Cover")
    dataset_fc = dc.load(product="ga_ls_fc_3",
                         group_by='solar_day',
                         platform='landsat-8',
                         cloud_cover= (0, 10),
                         **query)

    print("Loading DEA Water Observations")
    dataset_wo = dc.load(product="ga_ls_wo_3",
                         group_by='solar_day',
                         platform='landsat-8',
                         fuse_func=wofs_fuser,
                         cloud_cover= (0, 10),
                         like=dataset_fc)

    # Match the data
    shared_times = np.intersect1d(dataset_fc.time, dataset_wo.time)
    ds_fc_matched = dataset_fc.sel(time=shared_times)
    ds_wo_matched = dataset_wo.sel(time=shared_times)

    # Mask FC
    dry_mask = masking.make_mask(ds_wo_matched, dry=True)

    # Get fractional masked fc dataset (as proportion of 1, rather than 100)
    ds_fc_masked = ds_fc_matched.where(dry_mask.water) / 100

    # Resample
    ds_resampled = ds_fc_masked  #.resample(time="3M").median()
    ds_resampled.attrs["crs"] = dataset_fc.crs

    # Return the data
    return ds_fc_masked


def run_miningrehab_app(ds):
    """
    Plots an interactive map of the mining case-study area and allows
    the user to draw polygons. This returns plots of the fractional cover value
    of bare soil, green vegetation and brown vegetation in the polygon area.
    Last modified: January 2020

    inputs
    ds - data set containing masked Fractional Cover data from Landsat 8
    """
    
    # Suppress warnings
    warnings.filterwarnings("ignore")

    # Update plotting functionality through rcParams
    mpl.rcParams.update({"figure.autolayout": True})

    # Define the bounding box that will be overlayed on the interactive map
    # The bounds are hard-coded to match those from the loaded data
    geom_obj = {
        "type": "Feature",
        "properties": {
            "style": {
                "stroke": True,
                "color": "red",
                "weight": 4,
                "opacity": 0.8,
                "fill": True,
                "fillColor": False,
                "fillOpacity": 0,
                "showArea": True,
                "clickable": True,
            }
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [116.630731, -34.434517],
                    [116.630731, -34.426512],
                    [116.648123, -34.426512],
                    [116.648123, -34.434517],
                    [116.630731, -34.434517],
                ]
            ],
        },
    }

    # Create a map geometry from the geom_obj dictionary
    # center specifies where the background map view should focus on
    # zoom specifies how zoomed in the background map should be
    centroid = gpd.GeoDataFrame.from_features([geom_obj]).geometry.centroid
    loadeddata_center = centroid.y.item(), centroid.x.item()
    loadeddata_zoom = 15

    # define the study area map
    studyarea_map = Map(
        layout=widgets.Layout(width="480px", height="600px"),
        center=loadeddata_center,
        zoom=loadeddata_zoom,
        basemap=basemaps.Esri.WorldImagery,
    )

    # define the drawing controls
    studyarea_drawctrl = DrawControl(
        polygon={"shapeOptions": {"fillOpacity": 0}},
        marker={},
        circle={},
        circlemarker={},
        polyline={},
    )

    # add drawing controls and data bound geometry to the map
    studyarea_map.add_control(studyarea_drawctrl)
    studyarea_map.add_layer(GeoJSON(data=geom_obj))

    # Index to count drawn polygons
    polygon_number = 0

    # Define widgets to interact with
    instruction = widgets.Output(layout={"border": "1px solid black"})
    with instruction:
        print(
            "Draw a polygon within the red box to view plots of "
            "the fractional cover values of bare, green and "
            "non-green cover for the area over time."
        )

    info = widgets.Output(layout={"border": "1px solid black"})
    with info:
        print("Plot status:")

    fig_display = widgets.Output(
        layout=widgets.Layout(
            width="50%"  # proportion of horizontal space taken by plot
        )
    )

    with fig_display:
        plt.ioff()
        fig, ax = plt.subplots(3, 1, figsize=(9, 9))

        for axis in ax:
            axis.set_ylim([0, 1])

    colour_list = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    # Function to execute each time something is drawn on the map
    def handle_draw(self, action, geo_json):
        nonlocal polygon_number

        #         info.clear_output(wait=True)  # wait=True reduces flicker effect
        #         with info:
        #             print("Plot status: entered handle draw")

        # Execute behaviour based on what the user draws
        if geo_json["geometry"]["type"] == "Polygon":

            # Convert the drawn geometry to pixel coordinates
            geom_selectedarea = transform_geojson_wgs_to_epsg(
                geo_json,
                EPSG=3577  # hard-coded to be same as case-study data
            )

            # Construct a mask to only select pixels within the drawn polygon
            mask = rasterio.features.geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds.geobox.shape,
                transform=ds.geobox.affine,
                all_touched=False,
                invert=True,
            )

            masked_ds = ds.where(mask)
            masked_ds_mean = masked_ds.mean(dim=["x", "y"], skipna=True)

            colour = colour_list[polygon_number % len(colour_list)]

            # Add a layer to the map to make the most recently drawn polygon
            # the same colour as the line on the plot
            studyarea_map.add_layer(
                GeoJSON(
                    data=geo_json,
                    style={
                        "color": colour,
                        "opacity": 1,
                        "weight": 4.5,
                        "fillOpacity": 0.0,
                    },
                )
            )

            # Add Fractional cover plots to app
            masked_ds_mean = masked_ds_mean.drop('spatial_ref')
            masked_ds_mean.bs.interpolate_na(dim="time", method="nearest").plot.line("-", ax=ax[0])
            masked_ds_mean.pv.interpolate_na(dim="time", method="nearest").plot.line("-", ax=ax[1])
            masked_ds_mean.npv.interpolate_na(dim="time", method="nearest").plot.line("-", ax=ax[2])

            # reset titles back to custom
            ax[0].set_ylabel("Bare soil")
            ax[1].set_ylabel("Green vegetation")
            ax[2].set_ylabel("Brown (i.e. non-green) vegetation")
            ax[0].set_xlabel("")
            ax[1].set_xlabel("")
            ax[2].set_xlabel(None)

            # refresh display
            fig_display.clear_output(wait=True)  # wait=True reduces flicker effect
            with fig_display:
                display(fig)

            # Update plot info
            info.clear_output(wait=True)  # wait=True reduces flicker effect
            with info:
                print("Plot status: polygon added to plot")

            # Iterate the polygon number before drawing another polygon
            polygon_number = polygon_number + 1

        else:
            info.clear_output(wait=True)
            with info:
                print(
                    "Plot status: this drawing tool is not currently "
                    "supported. Please use the polygon tool."
                )

    # call to say activate handle_draw function on draw
    studyarea_drawctrl.on_draw(handle_draw)

    with fig_display:
        # TODO: update with user friendly something
        display(widgets.HTML(""))

    # Construct UI:
    #  +-----------------------+
    #  | instruction           |
    #  +-----------+-----------+
    #  |  map      |  plot     |
    #  |           |           |
    #  +-----------+-----------+
    #  | info                  |
    #  +-----------------------+
    ui = widgets.VBox([instruction, widgets.HBox([studyarea_map, fig_display]), info])
    display(ui)