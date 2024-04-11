# notebookapp_crophealth.py
'''
This file contains functions for loading and interacting with data in the
crop health notebook, inside the Real_world_examples folder.

Available functions:
    load_crophealth_data
    run_crophelath_app

Last modified: August 2023
'''

# Load modules
from ipyleaflet import (
    Map,
    GeoJSON,
    DrawControl,
    basemaps
)
import datetime as dt
import datacube
import matplotlib as mpl
import matplotlib.pyplot as plt
import rasterio
from rasterio.features import geometry_mask
import xarray as xr
from IPython.display import display
import warnings
import ipywidgets as widgets
import geopandas as gpd

# Load utility functions
import sys
sys.path.insert(1, '../Tools/')
from dea_tools.datahandling import load_ard
from dea_tools.spatial import transform_geojson_wgs_to_epsg
from dea_tools.bandindices import calculate_indices


def load_crophealth_data():
    """
    Loads Sentinel-2 analysis-ready data (ARD) product for the crop health
    case-study area. The ARD product is provided for the last year.
    Last modified: January 2020

    outputs
    ds - data set containing combined, masked data from Sentinel-2a and -2b.
    Masked values are set to 'nan'
    """
    
    # Suppress warnings
    warnings.filterwarnings('ignore')

    # Initialise the data cube. 'app' argument is used to identify this app
    dc = datacube.Datacube(app='Crophealth-app')

    # Specify latitude and longitude ranges
    latitude = (-24.974997, -24.995971)
    longitude = (152.429994, 152.395805)

    # Specify the date range
    # Calculated as today's date, subtract 90 days to match NRT availability
    # Dates are converted to strings as required by loading function below
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=365)

    time = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    # Construct the data cube query
    products = ["ga_s2am_ard_3", "ga_s2bm_ard_3"]
    
    query = {
        'x': longitude,
        'y': latitude,
        'time': time,
        'measurements': [
            'nbart_red',
            'nbart_green',
            'nbart_blue',
            'nbart_nir_1',
            'nbart_swir_2',
            'nbart_swir_3'
        ],
        'output_crs': 'EPSG:3577',
        'resolution': (-10, 10)
    }

    # Load the data and mask out bad quality pixels
    ds_s2 = load_ard(dc, products=products, min_gooddata=0.5, **query)

    # Calculate the normalised difference vegetation index (NDVI) across
    # all pixels for each image.
    # This is stored as an attribute of the data
    ds_s2 = calculate_indices(ds_s2, index='NDVI', collection='ga_s2_3')

    # Return the data
    return(ds_s2)


def run_crophealth_app(ds):
    """
    Plots an interactive map of the crop health case-study area and allows
    the user to draw polygons. This returns a plot of the average NDVI value
    in the polygon area.
    Last modified: January 2020
    
    inputs
    ds - data set containing combined, masked data from Sentinel-2a and -2b.
    Must also have an attribute containing the NDVI value for each pixel
    """
    
    # Suppress warnings
    warnings.filterwarnings('ignore')

    # Update plotting functionality through rcParams
    mpl.rcParams.update({'figure.autolayout': True})

    # Define the bounding box that will be overlayed on the interactive map
    # The bounds are hard-coded to match those from the loaded data
    geom_obj = {
        "type": "Feature",
        "properties": {
            "style": {
                "stroke": True,
                "color": 'red',
                "weight": 4,
                "opacity": 0.8,
                "fill": True,
                "fillColor": False,
                "fillOpacity": 0,
                "showArea": True,
                "clickable": True
            }
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [152.395805, -24.995971],
                    [152.395805, -24.974997],
                    [152.429994, -24.974997],
                    [152.429994, -24.995971],
                    [152.395805, -24.995971]
                ]
            ]
        }
    }

    # Create a map geometry from the geom_obj dictionary
    # center specifies where the background map view should focus on
    # zoom specifies how zoomed in the background map should be
    centroid = gpd.GeoDataFrame.from_features([geom_obj]).geometry.centroid
    loadeddata_center = centroid.y.item(), centroid.x.item()
    loadeddata_zoom = 14

    # define the study area map
    studyarea_map = Map(
        center=loadeddata_center,
        zoom=loadeddata_zoom,
        basemap=basemaps.Esri.WorldImagery
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
    instruction = widgets.Output(layout={'border': '1px solid black'})
    with instruction:
        print("Draw a polygon within the red box to view a plot of "
              "average NDVI over time in that area.")

    info = widgets.Output(layout={'border': '1px solid black'})
    with info:
        print("Plot status:")

    fig_display = widgets.Output(layout=widgets.Layout(
        width="50%",  # proportion of horizontal space taken by plot
    ))

    with fig_display:
        plt.ioff()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_ylim([-1, 1])

    colour_list = plt.rcParams['axes.prop_cycle'].by_key()['color']

    # Function to execute each time something is drawn on the map
    def handle_draw(self, action, geo_json):
        nonlocal polygon_number

        # Execute behaviour based on what the user draws
        if geo_json['geometry']['type'] == 'Polygon':

            info.clear_output(wait=True)  # wait=True reduces flicker effect
            with info:
                print("Plot status: polygon sucessfully added to plot.")

            # Convert the drawn geometry to pixel coordinates
            geom_selectedarea = transform_geojson_wgs_to_epsg(
                geo_json,
                EPSG=3577  # hard-coded to be same as case-study data
            )

            # Construct a mask to only select pixels within the drawn polygon
            mask = geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds.geobox.shape,
                transform=ds.geobox.affine,
                all_touched=False,
                invert=True
            )

            masked_ds = ds.NDVI.where(mask)
            masked_ds_mean = masked_ds.mean(dim=['x', 'y'], skipna=True)
            colour = colour_list[polygon_number % len(colour_list)]

            # Add a layer to the map to make the most recently drawn polygon
            # the same colour as the line on the plot
            studyarea_map.add_layer(
                GeoJSON(
                    data=geo_json,
                    style={
                        'color': colour,
                        'opacity': 1,
                        'weight': 4.5,
                        'fillOpacity': 0.0
                    }
                )
            )

            # add new data to the plot
            xr.plot.plot(
                masked_ds_mean,
                marker='*',
                color=colour,
                ax=ax
            )

            # reset titles back to custom
            ax.set_title("Average NDVI from Sentinel-2")
            ax.set_xlabel("Date")
            ax.set_ylabel("NDVI")

            # refresh display
            fig_display.clear_output(wait=True)  # wait=True reduces flicker effect
            with fig_display:
                display(fig)

            # Iterate the polygon number before drawing another polygon
            polygon_number = polygon_number + 1

        else:
            info.clear_output(wait=True)
            with info:
                print("Plot status: this drawing tool is not currently "
                      "supported. Please use the polygon tool.")

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
    ui = widgets.VBox([instruction,
                       widgets.HBox([studyarea_map, fig_display]),
                       info])
    display(ui)