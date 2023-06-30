# -*- coding: utf-8 -*-
"""
Satellite imagery animation widget, which can be used to interactively 
produce animations for multiple DEA products.
"""

# Import required packages
import fiona
import sys
import datacube
import warnings
import matplotlib.pyplot as plt
from datacube.utils.geometry import CRS
from ipyleaflet import (
    WMSLayer,
    basemaps,
    basemap_to_tiles,
    Map,
    DrawControl,
    WidgetControl,
    SearchControl,
    Marker,
    LayerGroup,
    LayersControl,
    GeoData,
)
from traitlets import Unicode
from ipywidgets import (
    GridspecLayout,
    Button,
    Layout,
    HBox,
    VBox,
    HTML,
    Output,
)
import json
import itertools
import numpy as np
import geopandas as gpd
from io import BytesIO
import ipywidgets as widgets
import datetime
from skimage import exposure
from skimage.filters import unsharp_mask

from datacube.utils import masking
from datacube.utils.geometry import Geometry
from datacube.utils.masking import mask_invalid_data
import dea_tools.app.widgetconstructors as deawidgets
from dea_tools.dask import create_local_dask_cluster
from dea_tools.spatial import reverse_geocode

import warnings
warnings.filterwarnings("ignore")

# WMS params and satellite style bands
sat_params = {
    "Landsat": {
        "products": [
            "ga_ls5t_ard_3",
            "ga_ls7e_ard_3",
            "ga_ls8c_ard_3",
            "ga_ls9c_ard_3",
        ],
        "styles": {
            "True colour": ("true_colour", ["nbart_red", "nbart_green", "nbart_blue"]),
            "False colour": (
                "false_colour",
                ["nbart_swir_1", "nbart_nir", "nbart_green"],
            ),
        },
    },
    "Sentinel-2": {
        "products": [
            "ga_s2am_ard_3",
            "ga_s2bm_ard_3",
        ],
        "styles": {
            "True colour": ("simple_rgb", ["nbart_red", "nbart_green", "nbart_blue"]),
            "False colour": (
                "infrared_green",
                ["nbart_swir_2", "nbart_nir_1", "nbart_green"],
            ),
        },
    },
    "Sentinel-2 and Landsat": {
        "products": [
            "ga_s2am_ard_3",
            "ga_s2bm_ard_3",
            "ga_ls5t_ard_3",
            "ga_ls7e_ard_3",
            "ga_ls8c_ard_3",
            "ga_ls9c_ard_3",
        ],
        "styles": {
            "True colour": ("simple_rgb", ["nbart_red", "nbart_green", "nbart_blue"]),
            "False colour": (
                "infrared_green",
                ["nbart_common_swir_1", "nbart_common_nir", "nbart_green"],
            ),
        },
    },
}


def make_box_layout():
    return Layout(
        #         border='solid 1px black',
        margin="0px 10px 10px 0px",
        padding="5px 5px 5px 5px",
        width="100%",
        height="100%",
    )


def create_expanded_button(description, button_style):
    return Button(
        description=description,
        button_style=button_style,
        layout=Layout(width="auto", height="auto"),
    )


def update_map_layers(self, update_basemap=False):
    """
    Updates map to add new DEA layers, styles or basemap when selected
    using menu options. Triggers data reload by resetting load params
    and output arrays.
    """

    # Clear data load params to trigger data re-load
    self.timeseries_ds = None
    self.load_params = None
    self.query_params = None

    if update_basemap:

        # Clear all layers and add basemap
        self.map_layers.clear_layers()
        self.map_layers.add_layer(self.basemap)


def extract_data(self):

    # Connect to datacube database
    dc = datacube.Datacube(app="Exporting satellite images")

    # Configure local dask cluster
    client = create_local_dask_cluster(return_client=True, display_client=True)

    # Convert to geopolygon
    geopolygon = Geometry(geom=self.gdf_drawn.geometry[0], crs=self.gdf_drawn.crs)

    # Create query after adjusting interval time to UTC by
    # adding a UTC offset of -10 hours. This results issues
    # on the east coast of Australia where satelite overpasses
    # can occur on either side of 24:00 hours UTC
    start_date = np.datetime64(self.start_date) - np.timedelta64(10, "h")
    end_date = np.datetime64(self.end_date) + np.timedelta64(14, "h")
    self.query_params = {
        "time": (str(start_date), str(end_date)),
        "geopolygon": geopolygon,
    }

    # Find matching datasets
    dss = [
        dc.find_datasets(product=i, **self.query_params)
        for i in sat_params[self.dealayer]["products"]
    ]
    dss = list(itertools.chain.from_iterable(dss))

    # If data is found
    if len(dss) > 0:

        # Get CRS
        crs = str(dss[0].crs)

        self.load_params = {
            "measurements": sat_params[self.dealayer]["styles"][self.style][1],
            "resolution": (-self.resolution, self.resolution),
            "output_crs": crs,
            "group_by": "solar_day",
            "dask_chunks": {"time": 1, "x": 2048, "y": 2048},
            "resampling": {"*": "bilinear", "oa_fmask": "nearest", "fmask": "nearest"},
            "skip_broken_datasets": True,
        }

        # Load data
        from dea_tools.datahandling import load_ard

        timeseries_ds = load_ard(
            dc=dc,
            products=sat_params[self.dealayer]["products"],
            min_gooddata=1.0 - (self.max_cloud_cover / 100),
            ls7_slc_off=False,
            mask_pixel_quality=self.cloud_mask,
            **self.load_params,
            **self.query_params,
        )

        # Set invalid nodata pixels to NaN
        timeseries_ds = mask_invalid_data(timeseries_ds)

        # If resampling freq specified
        if self.resample_freq:
            print(f"\nResampling data to {self.resample_freq} frequency")
            timeseries_ds = timeseries_ds.resample(time=self.resample_freq).median()

        # load into memory
        timeseries_ds.load()

    # Else if no data is returned, return None
    else:
        timeseries_ds = None

    # Close down the dask client
    #     client.shutdown()
    client.close()

    return timeseries_ds


def plot_data(self, fname):

    # Data to plot
    to_plot = self.timeseries_ds

    # If rolling median specified
    if self.rolling_median:
        with self.status_info:
            print(
                f"\nApplying rolling median ({self.rolling_median_window} timesteps window)"
            )
        to_plot = to_plot.rolling(
            time=int(self.rolling_median_window), center=True, min_periods=1
        ).median()

    # Raise by power to dampen bright features and enhance dark.
    # Raise vmin and vmax by same amount to ensure proper stretch
    if self.power < 1.0:
        with self.status_info:
            print(f"\nApplying power transformation ({self.power})")
        to_plot = to_plot ** self.power

    # Apply unsharp masking to enhance overall dynamic range,
    # and improve fine scale detail
    if self.unsharp_mask:
        with self.status_info:
            print(
                f"\nApplying unsharp masking with {self.unsharp_mask_radius} "
                f"radius and {self.unsharp_mask_amount} amount"
            )
        from skimage.exposure import rescale_intensity

        funcs_list = [
            rescale_intensity,
            lambda x: unsharp_mask(
                x, radius=self.unsharp_mask_radius, amount=self.unsharp_mask_amount
            ),
        ]
    else:
        funcs_list = None

    from dea_tools.plotting import xr_animation

    xr_animation(
        output_path=fname,
        ds=to_plot.dropna(dim="time", how="all"),
        show_text="",
        bands=sat_params[self.dealayer]["styles"][self.style][1],
        interval=self.interval,
        width_pixels=self.width,
        show_gdf=deacoastlines_overlay(to_plot) if self.deacoastlines else None,
        gdf_kwargs={"linewidth": 3},
        percentile_stretch=(self.vmin, self.vmax),
        image_proc_funcs=funcs_list,
        show_date="%Y" if self.resample_freq == "1Y" else "%b %Y",
        annotation_kwargs={"fontsize": 75},
    )

    # Add plot preview below map and finish
    plt.show()
    with self.status_info:
        print(f"\nImage successfully exported to:\n{fname}.")


def deacoastlines_overlay(ds):

    import geopandas as gpd
    import pandas as pd
    import matplotlib
    from shapely.geometry import box, Point
    from dea_tools.coastal import get_coastlines

    # Get bounding box of data
    xmin, ymin, xmax, ymax = ds.geobox.geographic_extent.boundingbox
    bounds = [xmin, ymin, xmax, ymax]

    # Load data
    deacl_gdf = get_coastlines(bbox=bounds)

    # Clip to extent of satellite data
    bbox = gpd.GeoDataFrame(geometry=[ds.geobox.extent.geom], crs=ds.geobox.crs)
    deacl_gdf = gpd.overlay(deacl_gdf, bbox.to_crs(deacl_gdf.crs))
    deacl_gdf = deacl_gdf.dissolve("year")  # values("year", ascending=True)

    # Apply colours
    norm = matplotlib.colors.Normalize(vmin=0, vmax=len(deacl_gdf.index))
    cmap = matplotlib.cm.get_cmap("inferno")
    rgba = cmap(norm(deacl_gdf.reset_index().index))
    deacl_gdf["color"] = list(rgba)
    deacl_gdf["start_time"] = pd.to_datetime(deacl_gdf.index) + pd.DateOffset(months=0)
    deacl_gdf = deacl_gdf.sort_index()

    if len(deacl_gdf.index) > 0:
        return deacl_gdf
    else:
        return None


class animation_app(HBox):
    def __init__(self):
        super().__init__()

        ######################
        # INITIAL ATTRIBUTES #
        ######################

        # Basemap
        self.basemap_list = [
            ("ESRI World Imagery", basemap_to_tiles(basemaps.Esri.WorldImagery)),
            ("Open Street Map", basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)),
        ]
        self.basemap = self.basemap_list[0][1]

        # Satellite data
        end_date = datetime.datetime.today()
        start_date = datetime.datetime(
            year=end_date.year - 3, month=end_date.month, day=end_date.day
        )
        self.start_date = start_date.strftime("%Y-%m-%d")
        self.end_date = end_date.strftime("%Y-%m-%d")
        self.dealayer_list = [
            ("Landsat", "Landsat"),
            ("Sentinel-2", "Sentinel-2"),
            ("Sentinel-2 and Landsat", "Sentinel-2 and Landsat")
        ]
        self.dealayer = self.dealayer_list[0][1]

        # Styles
        self.styles_list = ["True colour", "False colour"]
        self.style = self.styles_list[0]

        # Analysis params
        self.resolution = 30
        self.vmin = 0.01
        self.vmax = 0.99
        self.power = 1.0
        self.output_list = [("MP4", "mp4"), ("GIF", "gif")]
        self.output_format = self.output_list[0][1]
        self.rolling_median = False
        self.rolling_median_window = 20
        self.unsharp_mask = False
        self.unsharp_mask_radius = 20
        self.unsharp_mask_amount = 0.3
        self.max_size = False
        self.width = 900
        self.interval = 100
        self.cloud_mask = False
        self.max_cloud_cover = 20
        self.resample_list = [
            ("None", False),
            ("Monthly", "1M"),
            ("Quarterly", "Q-DEC"),
            ("Yearly", "1Y"),
        ]
        self.resample_freq = self.resample_list[0][1]
        self.deacoastlines = False

        # Drawing params
        self.target = None
        self.action = None
        self.gdf_drawn = None

        # Data load params
        self.timeseries_ds = None
        self.load_params = None
        self.query_params = None

        ##################
        # HEADER FOR APP #
        ##################

        # Create the Header widget
        header_title_text = (
            "<h3>Digital Earth Australia satellite imagery animations</h3>"
        )
        instruction_text = (
            "<p>Select the desired satellite data, imagery date range "
            "and image style, then zoom in and draw a rectangle to "
            "select an area export as a satellite imagery time-series "
            "animation.</p>"
        )
        self.header = deawidgets.create_html(f"{header_title_text}{instruction_text}")
        self.header.layout = make_box_layout()

        #####################################
        # HANDLER FUNCTION FOR DRAW CONTROL #
        #####################################

        # Define the action to take once something is drawn on the map
        def update_geojson(target, action, geo_json):

            # Get data from action
            self.action = action

            # Clear data load params to trigger data re-load
            self.timeseries_ds = None
            self.load_params = None
            self.query_params = None

            # Convert data to geopandas
            json_data = json.dumps(geo_json)
            binary_data = json_data.encode()
            io = BytesIO(binary_data)
            io.seek(0)
            gdf = gpd.read_file(io)
            gdf.crs = "EPSG:4326"

            # Convert to Albers and compute area
            gdf_drawn_albers = gdf.copy().to_crs("EPSG:3577")
            m2_per_ha = 10000
            area = gdf_drawn_albers.area.values[0] / m2_per_ha
            polyarea_label = "Total area of satellite data to extract"
            polyarea_text = f"<b>{polyarea_label}</b>: {area:.2f} ha</sup>"

            # Test area size
            if self.max_size:
                confirmation_text = (
                    '<span style="color: #33cc33"> '
                    "<b>(Overriding maximum size limit; use with caution as may lead to memory issues)</b></span>"
                )
                self.header.value = (
                    header_title_text
                    + instruction_text
                    + polyarea_text
                    + confirmation_text
                )
                self.gdf_drawn = gdf
            elif area <= 50000:
                confirmation_text = (
                    '<span style="color: #33cc33"> '
                    "<b>(Area to extract falls within "
                    "recommended 50000 ha limit)</b></span>"
                )
                self.header.value = (
                    header_title_text
                    + instruction_text
                    + polyarea_text
                    + confirmation_text
                )
                self.gdf_drawn = gdf
            else:
                warning_text = (
                    '<span style="color: #ff5050"> '
                    "<b>(Area to extract is too large, "
                    "please select an area less than 50000 "
                    "ha)</b></span>"
                )
                self.header.value = (
                    header_title_text + instruction_text + polyarea_text + warning_text
                )
                self.gdf_drawn = None

        ###########################
        # WIDGETS FOR APP OUTPUTS #
        ###########################

        self.status_info = Output(layout=make_box_layout())
        self.output_plot = Output(layout=make_box_layout())

        #########################################
        # MAP WIDGET, DRAWING TOOLS, WMS LAYERS #
        #########################################

        # Create drawing tools
        desired_drawtools = ["rectangle"]
        draw_control = deawidgets.create_drawcontrol(desired_drawtools)

        # Begin by displaying an empty layer group, and update the group with desired WMS on interaction.
        self.map_layers = LayerGroup(layers=())
        self.map_layers.name = "Map Overlays"

        # Create map widget
        self.m = deawidgets.create_map(map_center=(-33.96, 151.20), zoom_level=13)
        self.m.layout = make_box_layout()

        # Add tools to map widget
        self.m.add_control(draw_control)
        self.m.add_control(SearchControl(
        position="topleft",
        url='https://nominatim.openstreetmap.org/search?format=json&q={s}',
        zoom=13, # 'Village / Suburb' level zoom
        marker=Marker(draggable=False)
        ))
        self.m.add_layer(self.map_layers)

        # Update all maps to starting defaults
        update_map_layers(self, update_basemap=True)

        ############################
        # WIDGETS FOR APP CONTROLS #
        ############################

        # Create parameter widgets
        dropdown_basemap = deawidgets.create_dropdown(
            self.basemap_list, self.basemap_list[0][1]
        )
        dropdown_dealayer = deawidgets.create_dropdown(
            self.dealayer_list, self.dealayer_list[0][1]
        )
        dropdown_output = deawidgets.create_dropdown(
            self.output_list, self.output_list[0][1]
        )
        date_picker_start = deawidgets.create_datepicker(
            value=start_date,
        )
        date_picker_end = deawidgets.create_datepicker(
            value=end_date,
        )
        dropdown_styles = deawidgets.create_dropdown(
            self.styles_list, self.styles_list[0]
        )
        slider_percentile = widgets.FloatRangeSlider(
            value=[0.01, 0.99],
            min=0,
            max=1,
            step=0.001,
            description="",
            layout={"width": "85%"},
        )
        run_button = create_expanded_button("Generate animation", "info")

        floatslider_max_cloud_cover = widgets.IntSlider(
            value=20,
            min=0,
            max=100,
            step=1,
            description="",
            layout={"width": "85%"},
        )

        checkbox_rolling_median = deawidgets.create_checkbox(
            self.rolling_median,
            "Apply rolling median to produce smooth, cloud-free animations",
            layout={"width": "85%"},
        )
        text_rolling_median_window = widgets.IntText(
            value=20,
            step=1,
            description="Rolling window (timesteps)",
            layout={
                "width": "85%",
                "margin": "0px",
                "padding": "0px",
                "display": "none",
            },
        )

        # Expandable advanced section
        text_interval = widgets.IntText(
            value=100, description="", step=50, layout={"width": "95%"}
        )
        text_resolution = widgets.FloatText(
            value=30,
            description="",
            layout={"width": "95%", "margin": "0px", "padding": "0px"},
        )
        text_width = widgets.IntText(
            value=900, description="", step=50, layout={"width": "95%"}
        )
        dropdown_resampling = deawidgets.create_dropdown(
            self.resample_list,
            self.resample_freq,
            description="",
            layout={"width": "95%"},
        )
        checkbox_cloud_mask = deawidgets.create_checkbox(
            self.cloud_mask, "Mask out cloudy pixels", layout={"width": "95%"}
        )
        slider_power = widgets.FloatSlider(
            value=1.0,
            min=0.01,
            max=1.0,
            step=0.01,
            description="",
            layout={"width": "95%"},
        )
        checkbox_unsharp_mask = deawidgets.create_checkbox(
            self.unsharp_mask, "Enable", layout={"width": "95%"}
        )
        text_unsharp_mask_radius = widgets.FloatText(
            value=20,
            step=1,
            description="Radius",
            layout={
                "width": "95%",
                "margin": "0px",
                "padding": "0px",
                "display": "none",
            },
        )
        text_unsharp_mask_amount = widgets.FloatText(
            value=0.3,
            step=0.1,
            description="Amount",
            layout={
                "width": "95%",
                "margin": "0px",
                "padding": "0px",
                "display": "none",
            },
        )
        checkbox_deacoastlines = deawidgets.create_checkbox(
            self.deacoastlines, "Add DEA Coastlines overlay", layout={"width": "95%"}
        )
        checkbox_max_size = deawidgets.create_checkbox(
            self.max_size, "Enable", layout={"width": "95%"}
        )
        expand_box = widgets.VBox(
            [
                HTML("Frame interval (milliseconds):"),
                text_interval,
                HTML("</br>Resolution (metres):"),
                text_resolution,
                HTML("</br>Width of output animation in pixels:"),
                text_width,
                HTML("</br>Apply temporal resampling:"),
                dropdown_resampling,
                HTML("</br>"),
                checkbox_cloud_mask,
                checkbox_deacoastlines,
                HTML("</br>Apply power transformation to darken bright features:"),
                slider_power,
                HTML("</br>Apply unsharp masking to sharpen imagery:"),
                checkbox_unsharp_mask,
                text_unsharp_mask_radius,
                text_unsharp_mask_amount,
                HTML(
                    "</br>Override maximum size limit: (use with caution; may cause memory issues/crashes)"
                ),
                checkbox_max_size,
            ],
        )

        expand = widgets.Accordion(
            children=[expand_box],
            selected_index=None,
        )
        expand.set_title(0, "Advanced")

        # Add specific dialogs to class so they can be modified
        self.text_resolution = text_resolution
        self.text_unsharp_mask_radius = text_unsharp_mask_radius
        self.text_unsharp_mask_amount = text_unsharp_mask_amount
        self.text_rolling_median_window = text_rolling_median_window

        ####################################
        # UPDATE FUNCTIONS FOR EACH WIDGET #
        ####################################

        # Run update functions whenever various widgets are changed.
        date_picker_start.observe(self.update_start_date, "value")
        date_picker_end.observe(self.update_end_date, "value")
        dropdown_basemap.observe(self.update_basemap, "value")
        dropdown_dealayer.observe(self.update_dealayer, "value")
        dropdown_styles.observe(self.update_styles, "value")

        slider_percentile.observe(self.update_slider_percentile, "value")
        floatslider_max_cloud_cover.observe(
            self.update_floatslider_max_cloud_cover, "value"
        )
        checkbox_rolling_median.observe(self.update_checkbox_rolling_median, "value")
        text_rolling_median_window.observe(
            self.update_text_rolling_median_window, "value"
        )
        dropdown_output.observe(self.update_output, "value")
        run_button.on_click(self.run_app)
        draw_control.on_draw(update_geojson)

        # Advanced params
        text_resolution.observe(self.update_text_resolution, "value")
        slider_power.observe(self.update_slider_power, "value")
        text_width.observe(self.update_width, "value")
        text_interval.observe(self.update_interval, "value")
        dropdown_resampling.observe(self.update_dropdown_resampling, "value")
        checkbox_cloud_mask.observe(self.update_checkbox_cloud_mask, "value")
        checkbox_unsharp_mask.observe(self.update_checkbox_unsharp_mask, "value")
        text_unsharp_mask_radius.observe(self.update_text_unsharp_mask_radius, "value")
        text_unsharp_mask_amount.observe(self.update_text_unsharp_mask_amount, "value")
        checkbox_deacoastlines.observe(self.update_deacoastlines, "value")
        checkbox_max_size.observe(self.update_checkbox_max_size, "value")

        ##################################
        # COLLECTION OF ALL APP CONTROLS #
        ##################################

        parameter_selection = VBox(
            [
                HTML("<b>Start date:</b>"),
                date_picker_start,
                HTML("<b>End date:</b>"),
                date_picker_end,
                HTML("<b>Satellite imagery:</b>"),
                dropdown_dealayer,
                HTML("<b>Style:</b>"),
                dropdown_styles,
                HTML("<b>Colour percentile stretch:</b>"),
                slider_percentile,
                HTML("<b>Maximum cloud cover (%):</b>"),
                floatslider_max_cloud_cover,
                checkbox_rolling_median,
                text_rolling_median_window,
                HTML("</br><b>Output file format:</b>"),
                dropdown_output,
                HTML("</br>"),
                expand,
            ]
        )
        map_selection = VBox(
            [
                HTML("</br><b>Map overlay:</b>"),
                dropdown_basemap,
            ]
        )
        parameter_selection.layout = make_box_layout()
        map_selection.layout = make_box_layout()

        ###############################
        # SPECIFICATION OF APP LAYOUT #
        ###############################

        #       0   1    2   3   4   5   6   7    8   9
        #     ---------------------------------------------
        # 0   | Header                         | Map sel. |
        #     |-------------------------------------------|
        # 1   | Params |                                  |
        # 2   |        |                                  |
        # 3   |        |                                  |
        # 4   |        |               Map                |
        # 5   |        |                                  |
        #     |--------|                                  |
        # 6   |  Run   |                                  |
        #     |-------------------------------------------|
        # 7   |   Status info   |      Figure/output      |
        # 8   |                 |                         |
        # 9   |                 |                         |
        # 10  |                 |                         |
        # 11  ---------------------------------------------

        # Create the layout #[rowspan, colspan]
        grid = GridspecLayout(12, 10, height="1500px", width="auto")

        # Header and controls
        grid[0, :8] = self.header
        grid[0, 8:] = map_selection
        grid[1:6, 0:2] = parameter_selection
        grid[6, 0:2] = run_button

        # Status info, map and plot
        grid[1:7, 2:] = self.m  # map
        grid[7:, 0:4] = self.status_info
        grid[7:, 4:] = self.output_plot

        # Display using HBox children attribute
        self.children = [grid]

    ######################################
    # DEFINITION OF ALL UPDATE FUNCTIONS #
    ######################################

    # Update date
    def update_start_date(self, change):
        self.start_date = str(change.new)

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Update date
    def update_end_date(self, change):
        self.end_date = str(change.new)

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Update basemap
    def update_basemap(self, change):
        self.basemap = change.new
        update_map_layers(self, update_basemap=True)

    # Change layers shown on the map
    def update_dealayer(self, change):
        self.dealayer = change.new

        if change.new == "Landsat":
            self.text_resolution.value = 30

        elif change.new == "Sentinel-2":
            self.text_resolution.value = 10
        
        elif change.new == "Sentinel-2 and Landsat":
            self.text_resolution.value = 30
            
        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Set imagery style
    def update_styles(self, change):
        self.style = change.new

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Update good data slider
    def update_floatslider_max_cloud_cover(self, change):
        self.max_cloud_cover = change.new

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Set output file format
    def update_output(self, change):
        self.output_format = change.new

    # Update colour stretch
    def update_slider_percentile(self, change):
        self.vmin, self.vmax = change.new

    # Update power transform
    def update_slider_power(self, change):
        self.power = change.new

    # Enable unsharp masking and show/hide custom params
    def update_checkbox_unsharp_mask(self, change):
        self.unsharp_mask = change.new

        # Show unsharp masking params in menu if activated
        if change.new:
            self.text_unsharp_mask_radius.layout.display = "block"
            self.text_unsharp_mask_amount.layout.display = "block"
        else:
            self.text_unsharp_mask_radius.layout.display = "none"
            self.text_unsharp_mask_amount.layout.display = "none"

    # Change unsharp masking radius
    def update_text_unsharp_mask_radius(self, change):
        self.unsharp_mask_radius = change.new

    # Change unsharp masking amount
    def update_text_unsharp_mask_amount(self, change):
        self.unsharp_mask_amount = change.new

    # Enable rolling median and show/hide custom params
    def update_checkbox_rolling_median(self, change):
        self.rolling_median = change.new

        # Show rolling median params in menu if activated
        if change.new:
            self.text_rolling_median_window.layout.display = "block"
        else:
            self.text_rolling_median_window.layout.display = "none"

    # Change rolling median window
    def update_text_rolling_median_window(self, change):
        self.rolling_median_window = change.new

    # Override max size limit
    def update_checkbox_max_size(self, change):
        self.max_size = change.new

    # Add DEA Coastlines overlay
    def update_deacoastlines(self, change):
        self.deacoastlines = change.new

    # Apply cloud mask in load_ard
    def update_checkbox_cloud_mask(self, change):
        self.cloud_mask = change.new

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Override min width
    def update_width(self, change):
        self.width = change.new

    # Override interval
    def update_interval(self, change):
        self.interval = change.new

    # Update resolution
    def update_text_resolution(self, change):
        self.resolution = change.new

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    # Set output file format
    def update_dropdown_resampling(self, change):
        self.resample_freq = change.new

        # Clear data load params to trigger data re-load
        update_map_layers(self)

    def run_app(self, change):

        # Clear progress bar and output areas before running
        self.status_info.clear_output()
        self.output_plot.clear_output()

        # Verify that polygon was drawn
        if self.gdf_drawn is not None:

            with self.status_info:

                # Load data and add to attribute
                if self.timeseries_ds is None:
                    self.timeseries_ds = extract_data(self)

                else:
                    print("Using previously loaded data")

            if self.timeseries_ds is not None:

                with self.status_info:

                    # Create unique file name
                    centre_coords = self.gdf_drawn.geometry[0].centroid.coords[0][::-1]
                    site = reverse_geocode(coords=centre_coords)
                    fname = (
                        f"{self.dealayer}_{site}_{self.start_date}_"
                        f"{self.end_date}_{self.style}_{self.resolution:.0f}m."
                        f"{self.output_format}".replace(" ", "")
                        .replace(",", "")
                        .lower()
                    )

                    print(
                        f"\nExporting animation for {site}.\nThis may take several minutes..."
                    )

                ############
                # Plotting #
                ############

                with self.output_plot:
                    plot_data(self, fname)

            else:
                with self.status_info:
                    print(
                        "No satellite data found in the selected area. "
                        "Please select a new rectangle over an area with "
                        "satellite imagery."
                    )

        else:
            with self.status_info:
                print(
                    'Please draw a valid rectangle on the map, then press "Generate animation".'
                )
