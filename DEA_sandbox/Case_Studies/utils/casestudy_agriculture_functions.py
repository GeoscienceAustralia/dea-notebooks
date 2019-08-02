# casestudy_agriculture_functions.py
'''
This file contains functions for loading and interacting with data in the
agriculture case-study notebook.

Available functions:
    load_agriculture_data
    run_agriculture_app

Last modified: May 2019
Authors: Caitlin Adams (FrontierSI)
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
import ogr
import matplotlib as mpl
import matplotlib.pyplot as plt
import rasterio
import xarray as xr
from IPython.display import display
import warnings
import ipywidgets as widgets

# Load utility functions
from utils.DEADataHandling import load_clearsentinel2
from utils.utils import transform_from_wgs_poly
from utils.BandIndices import calculate_indices


def load_agriculture_data():
    """
    Loads Sentinel-2 Near Real Time (NRT) product for the agriculture
    case-study area. The NRT product is provided for the last 90 days.
    Last modified: May 2019
    Author: Caitlin Adams (FrontierSI)

    outputs
    ds - data set containing combined, masked data from Sentinel-2a and -2b.
    Masked values are set to 'nan'
    """
    # Suppress warnings
    warnings.filterwarnings('ignore')

    # Initialise the data cube. 'app' argument is used to identify this app
    dc = datacube.Datacube(app='agriculture-app')

    # Specify latitude and longitude ranges
    latitude = (-24.974997, -24.995971)
    longitude = (152.429994, 152.395805)

    # Specify the date range
    # Calculated as today's date, subtract 90 days to match NRT availability
    # Dates are converted to strings as required by loading function below
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=90)

    time = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    # Construct the data cube query
    query = {
        'x': longitude,
        'y': latitude,
        'time': time,
        'output_crs': 'EPSG:3577',
        'resolution': (-10, 10)
    }

    # Specify the product measurments to load from Sentinel-2
    measurements = (
        'nbar_red',
        'nbar_green',
        'nbar_blue',
        'nbar_nir_1',
        'nbar_swir_2',
        'nbar_swir_3'
    )

    # Specify the minimum proportion of good quality pixels for an image.
    # The image will be excluded if masking results in fewer pixels than
    # the set proportion.
    # Setting this to 0.0 includes all images
    min_good_pixel_prop = 0.5

    # Load the data and mask out bad quality pixels
    ds_s2 = load_clearsentinel2(
        dc=dc,
        query=query,
        sensors=['s2a', 's2b'],
        product='nrt',
        bands_of_interest=measurements,
        masked_prop=min_good_pixel_prop
    )

    # Calculate the normalised difference vegetation index (NDVI) across
    # all pixels for each image.
    # This is stored as an attribute of the data
    ds_s2['ndvi'], description = calculate_indices(ds_s2, 'NDVI')

    # Return the data
    return(ds_s2)


def run_agriculture_app(ds):
    """
    Plots an interactive map of the agriculture case-study area and allows
    the user to draw polygons. This returns a plot of the average NDVI value
    in the polygon area.
    Last modified: May 2019
    Author: Caitlin Adams (FrontierSI)

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
    loadeddata_geometry = ogr.CreateGeometryFromJson(str(geom_obj['geometry']))
    loadeddata_center = [
        loadeddata_geometry.Centroid().GetY(),
        loadeddata_geometry.Centroid().GetX()
    ]
    loadeddata_zoom = 14

    # define the study area map
    studyarea_map = Map(
        center=loadeddata_center,
        zoom=loadeddata_zoom,
        basemap=basemaps.Esri.WorldImagery
    )

    # define the drawing controls
    studyarea_drawctrl = DrawControl(
        polygon={"shapeOptions": {"fillOpacity": 0}}
    )

    # add drawing controls and data bound geometry to the map
    studyarea_map.add_control(studyarea_drawctrl)
    studyarea_map.add_layer(GeoJSON(data=geom_obj))

    # Index to count drawn polygons
    global polygon_number
    polygon_number = 0

    # Define widgets to interact with
    instruction = widgets.Output(layout={'border': '1px solid black'})
    with instruction:
        print("Draw a polygon within the red box to view a plot of "
              "average NDVI over time in that area.")

    info = widgets.Output(layout={'border': '1px solid black'})
    with info:
        print("Plot status:")

    # Function to execute each time something is drawn on the map
    def handle_draw(self, action, geo_json):
        global polygon_number

        # Construct figure attributes
        plt.figure(0, figsize=(8, 5))
        plt.ylim([-1, 1])

        # Execute behaviour based on what the user draws
        if geo_json['geometry']['type'] == 'Polygon':

            info.clear_output()
            with info:
                print("Plot status: polygon sucessfully added to plot.")

            # Convert the drawn geometry to pixel coordinates
            geom_selectedarea = transform_from_wgs_poly(
                geo_json['geometry'],
                EPSGa=3577  # hard-coded to be same as case-study data
            )

            # Construct a mask to only select pixels within the drawn polygon
            mask = rasterio.features.geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds.geobox.shape,
                transform=ds.geobox.affine,
                all_touched=False,
                invert=True
            )

            masked_ds = ds.ndvi.where(mask)

            masked_ds_mean = masked_ds.mean(dim=['x', 'y'], skipna=True)

            # Get list of matplotlib colours for plotting
            colour_list = plt.rcParams['axes.prop_cycle'].by_key()['color']
            colour_index = polygon_number % len(colour_list)

            # Plot the data with data points marked
            xr.plot.plot(
                masked_ds_mean,
                marker='*',
                color=colour_list[colour_index]
            )
            plt.title("Average NDVI from Sentinel-2")
            plt.xlabel("Date")
            plt.ylabel("NDVI")

            # Add a layer to the map to make the most recently drawn polygon
            # the same colour as the line on the plot
            studyarea_map.add_layer(
                GeoJSON(data=geo_json,
                        style={
                            'color': colour_list[colour_index],
                            'opacity': 1,
                            'weight': 4.5,
                            'fillOpacity': 0.0
                        }
                        )
            )

            # Iterate the polygon number before drawing another polygon
            polygon_number = polygon_number + 1

        else:
            info.clear_output()
            with info:
                print("Plot status: this drawing tool is not currently "
                      "supported. Please use the polygon tool.")

    # call to say activate handle_draw function on draw
    studyarea_drawctrl.on_draw(handle_draw)

    # plot the map
    display(instruction)
    display(studyarea_map)
    display(info)
