# -*- coding: utf-8 -*-
"""
Image export widget, which can be used to interactively select and 
export satellite imagery from multiple DEA products.
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
import dea_tools.app.widgetconstructors as deawidgets
from dea_tools.dask import create_local_dask_cluster
from dea_tools.spatial import reverse_geocode
from dea_tools.datahandling import xr_pansharpen


# WMS params and satellite style bands
sat_params = {
    "ga_ls_ard_3": {
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
    "ga_s2m_ard_3": {
        "products": ["ga_s2am_ard_3", "ga_s2bm_ard_3"],
        "styles": {
            "True colour": ("simple_rgb", ["nbart_red", "nbart_green", "nbart_blue"]),
            "False colour": (
                "infrared_green",
                ["nbart_swir_2", "nbart_nir_1", "nbart_green"],
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


def update_map_layers(self):
    """
    Updates map to add new DEA layers, styles or basemap when selected
    using menu options. Triggers data reload by resetting load params
    and output arrays.
    """

    # Clear data load params to trigger data re-load
    self.rgb_array = None
    self.sensor = None
    self.load_params = None
    self.query_params = None

    # Clear all layers and add basemap
    self.map_layers.clear_layers()
    self.map_layers.add_layer(self.basemap)

    # Get style name for specific satellite sensor
    style = sat_params[self.dealayer]["styles"][self.style][0]

    # Add DEA layers over the top of the basemap
    dea_layer = deawidgets.create_dea_wms_layer(self.dealayer, self.date, styles=style)
    self.map_layers.add_layer(dea_layer)


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
    start_date = np.datetime64(self.date) - np.timedelta64(10, "h")
    end_date = np.datetime64(self.date) + np.timedelta64(14, "h")
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

        # Get sensor (try/except to account for different S2 NRT metadata)
        try:
            sensor = dss[0].metadata_doc["properties"]["eo:platform"].capitalize()
        except:
            sensor = dss[0].metadata_doc["platform"]["code"].capitalize()
        self.sensor = sensor[0:-1].replace("_", "-") + sensor[-1].capitalize()

        # Meets pansharpening requirements
        can_pansharpen = self.style == "True colour" and self.sensor in [
            "Landsat-7",
            "Landsat-8",
            "Landsat-9",
        ]

        # Set up load params
        if self.pansharpen and can_pansharpen:
            self.load_params = {
                "measurements": sat_params[self.dealayer]["styles"][self.style][1]
                + ["nbart_panchromatic"],
                "resolution": (-self.resolution, self.resolution),
                "align": (7.5, 7.5),
                "output_crs": crs,
            }

        else:

            # Use resolution if provided, otherwise use default
            if self.resolution:
                sat_params[self.dealayer]["resolution"] = (
                    -self.resolution,
                    self.resolution,
                )

            self.load_params = {
                "measurements": sat_params[self.dealayer]["styles"][self.style][1],
                "resolution": (-self.resolution, self.resolution),
                "output_crs": crs,
                "skip_broken_datasets": True,
            }

        # Load data from datasets
        print(f"Loading {self.sensor} satellite data")
        ds = dc.load(
            datasets=dss,
            resampling="bilinear",
            group_by="solar_day",
            dask_chunks={"time": 1, "x": 2048, "y": 2048},
            **self.load_params,
            **self.query_params,
        )
        ds = masking.mask_invalid_data(ds)

        # Create plain numpy array, optionally after pansharpening
        if self.pansharpen and can_pansharpen:

            # Perform Brovey pan-sharpening and return numpy.array
            print(f"Pansharpening {self.sensor} image to 15 m resolution")
            rgb_array = (
                xr_pansharpen(ds, transform="brovey").to_array().squeeze("time").values
            )

        # If pansharpening is requested but not possible, deactivate
        # pansharpening and reset to 30 m resolution
        elif self.pansharpen and not can_pansharpen:
            print("\nUnable to pansharpen; reverting to 30 m resolution")
            self.checkbox_pansharpen.value = False
            self.text_resolution.disabled = False
            self.text_resolution.value = 30
            rgb_array = ds.isel(time=0).to_array().values

        else:
            rgb_array = ds.isel(time=0).to_array().values

        # Transpose numpy array
        rgb_array = np.transpose(rgb_array, axes=[1, 2, 0])

    # Else if no data is returned, return None
    else:
        rgb_array = None

    # Close down the dask client
    client.close()

    return rgb_array


def plot_data(self, fname):

    # Data to plot
    to_plot = self.rgb_array

    # If percentile stretch is supplied, calculate vmin and vmax
    # from percentiles
    if self.percentile_stretch:
        vmin, vmax = np.nanpercentile(to_plot, self.percentile_stretch)
    else:
        vmin, vmax = self.vmin, self.vmax

    # Raise by power to dampen bright features and enhance dark.
    # Raise vmin and vmax by same amount to ensure proper stretch
    if self.power < 1.0:
        with self.status_info:
            print(f"\nApplying power transformation ({self.power})")
        to_plot = to_plot ** self.power
        vmin, vmax = vmin ** self.power, vmax ** self.power

    # Rescale/stretch imagery between vmin and vmax
    to_plot = exposure.rescale_intensity(
        to_plot.astype(float), in_range=(vmin, vmax), out_range=(0.0, 1.0)
    )

    # Unsharp mask
    if self.unsharp_mask:
        with self.status_info:
            print(
                f"\nApplying unsharp masking with {self.unsharp_mask_radius} "
                f"radius and {self.unsharp_mask_amount} amount"
            )
        to_plot = unsharp_mask(
            to_plot, radius=self.unsharp_mask_radius, amount=self.unsharp_mask_amount
        )

    # Create figure with aspect ratio of data
    fig = plt.figure(dpi=100)
    fig.set_size_inches(10, 10 / (to_plot.shape[1] / to_plot.shape[0]))

    # Remove axes to plot just array data
    ax = plt.Axes(
        fig,
        [0.0, 0.0, 1.0, 1.0],
    )
    ax.set_axis_off()
    fig.add_axes(ax)

    # Add data to plot
    ax.imshow(to_plot)

    # If a min DPI is specified and image is less than DPI
    if (self.dpi > 0) and (to_plot.shape[1] < self.dpi * 10):

        # Export figure to file using exact DPI
        with self.status_info:
            print(f"\nExporting image at {self.dpi} DPI")
        fig.savefig(
            fname.replace("resolution", f"resolution, {self.dpi} DPI"), dpi=self.dpi
        )

    # If no minumum DPI is specified, export raw array data in native
    # resolution
    else:
        plt.imsave(
            fname=fname, arr=np.ascontiguousarray(to_plot), format=self.output_format
        )

    # Add plot preview below map and finish
    plt.show()
    with self.status_info:
        print(f"\nImage successfully exported to:\n{fname}.")


class imageexport_app(HBox):
    def __init__(self):
        super().__init__()

        ######################
        # INITIAL ATTRIBUTES #
        ######################

        # Basemap
        self.basemap_list = [
            ("Open Street Map", basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)),
            ("ESRI World Imagery", basemap_to_tiles(basemaps.Esri.WorldImagery)),
        ]
        self.basemap = self.basemap_list[0][1]

        # Satellite data using yesterday's date
        date = datetime.datetime.today()
        date = datetime.datetime(year=date.year, month=date.month, day=date.day - 1)
        self.date = date.strftime("%Y-%m-%d")
        self.dealayer_list = [
            ("Landsat", "ga_ls_ard_3"),
            ("Sentinel-2", "ga_s2m_ard_3"),
        ]
        self.dealayer = self.dealayer_list[0][1]

        # Styles
        self.styles_list = ["True colour", "False colour"]
        self.style = self.styles_list[0]

        # Analysis params
        self.resolution = 30
        self.pansharpen = False
        self.standardise_name = False
        self.vmin = 50
        self.vmax = 3000
        self.percentile_stretch = None  # (1, 99)
        self.power = 1.0
        self.output_list = [("JPG", "jpg"), ("PNG", "png")]
        self.output_format = self.output_list[0][1]
        self.unsharp_mask = False
        self.unsharp_mask_radius = 20
        self.unsharp_mask_amount = 0.3
        self.max_size = False
        self.dpi = 0

        # Drawing params
        self.target = None
        self.action = None
        self.gdf_drawn = None

        # Data load params
        self.rgb_array = None
        self.sensor = None
        self.load_params = None
        self.query_params = None

        ##################
        # HEADER FOR APP #
        ##################

        # Create the Header widget
        header_title_text = "<h3>Digital Earth Australia satellite image export</h3>"
        instruction_text = (
            "<p>Select the desired satellite data, imagery "
            "date and image style, zoom in until satellite "
            "imagery appears on the map, then draw a "
            "rectangle to select an area of imagery to "
            "export as a high-resolution image file.</p>"
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
            self.rgb_array = None
            self.sensor = None
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
            m2_per_km2 = 10 ** 6
            area = gdf_drawn_albers.area.values[0] / m2_per_km2
            polyarea_label = "Total area of satellite data to extract"
            polyarea_text = f"<b>{polyarea_label}</b>: {area:.2f} km<sup>2</sup>"

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
            elif area <= 10000:
                confirmation_text = (
                    '<span style="color: #33cc33"> '
                    "<b>(Area to extract falls within "
                    "recommended limit)</b></span>"
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
                    "please select an area less than 10000 "
                    "km<sup>2)</b></span>"
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
        self.m = deawidgets.create_map(map_center=(-28, 135), zoom_level=4)
        self.m.layout = make_box_layout()

        # Add tools to map widget
        self.m.add_control(draw_control)
        self.m.add_layer(self.map_layers)

        # Update all maps to starting defaults
        update_map_layers(self)

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
        date_picker = deawidgets.create_datepicker(value=date)
        dropdown_styles = deawidgets.create_dropdown(
            self.styles_list, self.styles_list[0]
        )
        slider_abs = widgets.IntRangeSlider(
            value=[50, 3000],
            min=0,
            max=10000,
            step=25,
            description="",
            layout={"width": "85%"},
        )
        run_button = create_expanded_button("Export imagery", "info")

        # Expandable advanced section
        text_resolution = widgets.FloatText(
            value=30,
            description="",
            layout={"width": "100%", "margin": "0px", "padding": "0px"},
        )
        checkbox_pansharpen = deawidgets.create_checkbox(
            self.pansharpen, "Pansharpen Landsat"
        )
        slider_power = widgets.FloatSlider(
            value=1.0,
            min=0.01,
            max=1.0,
            step=0.01,
            description="",
            layout={"width": "85%"},
        )
        checkbox_unsharp_mask = deawidgets.create_checkbox(
            self.unsharp_mask, "Enable", layout={"width": "100%"}
        )
        text_unsharp_mask_radius = widgets.FloatText(
            value=20,
            step=1,
            description="Radius",
            layout={
                "width": "100%",
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
                "width": "100%",
                "margin": "0px",
                "padding": "0px",
                "display": "none",
            },
        )
        checkbox_max_size = deawidgets.create_checkbox(self.max_size, "Enable")
        text_dpi = widgets.IntText(
            value=0, description="", step=50, layout={"width": "85%"}
        )
        html_dpi = HTML(
            "</br>Minimum DPI for image export</br>(100 DPI = 1000 pixels wide):"
        )
        expand_box = widgets.VBox(
            [
                HTML("Resolution (metres):"),
                text_resolution,
                checkbox_pansharpen,
                HTML("</br>Apply power transformation to darken bright features:"),
                slider_power,
                HTML("</br>Apply unsharp masking to sharpen image:"),
                checkbox_unsharp_mask,
                text_unsharp_mask_radius,
                text_unsharp_mask_amount,
                HTML(
                    "</br>Override maximum size limit: (use with caution; may cause memory issues/crashes)"
                ),
                checkbox_max_size,
                html_dpi,
                text_dpi,
            ],
            layout={"overflow": "hidden"},
        )

        expand = widgets.Accordion(children=[expand_box], selected_index=None)
        expand.set_title(0, "Advanced")

        # Add specific dialogs to class so they can be modified
        self.text_resolution = text_resolution
        self.checkbox_pansharpen = checkbox_pansharpen
        self.text_unsharp_mask_radius = text_unsharp_mask_radius
        self.text_unsharp_mask_amount = text_unsharp_mask_amount
        self.html_dpi = html_dpi

        ####################################
        # UPDATE FUNCTIONS FOR EACH WIDGET #
        ####################################

        # Run update functions whenever various widgets are changed.
        date_picker.observe(self.update_date, "value")
        dropdown_basemap.observe(self.update_basemap, "value")
        dropdown_dealayer.observe(self.update_dealayer, "value")
        dropdown_styles.observe(self.update_styles, "value")
        dropdown_output.observe(self.update_output, "value")
        run_button.on_click(self.run_app)
        draw_control.on_draw(update_geojson)
        slider_abs.observe(self.update_slider_abs, "value")

        # Advanced params
        text_resolution.observe(self.update_text_resolution, "value")
        checkbox_pansharpen.observe(self.update_checkbox_pansharpen, "value")
        slider_power.observe(self.update_slider_power, "value")
        checkbox_unsharp_mask.observe(self.update_checkbox_unsharp_mask, "value")
        text_unsharp_mask_radius.observe(self.update_text_unsharp_mask_radius, "value")
        text_unsharp_mask_amount.observe(self.update_text_unsharp_mask_amount, "value")
        checkbox_max_size.observe(self.update_checkbox_max_size, "value")
        text_dpi.observe(self.update_dpi, "value")

        ##################################
        # COLLECTION OF ALL APP CONTROLS #
        ##################################

        parameter_selection = VBox(
            [
                HTML("<b>Date:</b>"),
                date_picker,
                HTML("<b>Satellite imagery:</b>"),
                dropdown_dealayer,
                HTML("<b>Style:</b>"),
                dropdown_styles,
                HTML("<b>Colour stretch:</b>"),
                slider_abs,
                HTML("<b>Output file format:</b>"),
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
        grid = GridspecLayout(12, 10, height="1400px", width="auto")

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
    def update_date(self, change):
        self.date = str(change.new)
        update_map_layers(self)

    # Update colour stretch
    def update_slider_abs(self, change):
        self.vmin, self.vmax = change.new

    # Update power transform
    def update_slider_power(self, change):
        self.power = change.new

    # Enable pansharpening and reset/deactivate resolution
    def update_checkbox_pansharpen(self, change):
        self.pansharpen = change.new

        # Override default resolution if pansharpening is specified;
        # disable input if so
        if change.new:
            self.text_resolution.value = 15
            self.text_resolution.disabled = True
        else:
            self.text_resolution.value = 30
            self.text_resolution.disabled = False

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

    # Override max size limit
    def update_checkbox_max_size(self, change):
        self.max_size = change.new

    # Override min DPI
    def update_dpi(self, change):
        self.dpi = change.new

        # Update DPI helper text to give output resolution
        self.html_dpi.value = (
            f"</br>Minimum DPI for image export</br>"
            f"({change.new} DPI = {change.new * 10} "
            f"pixels wide):"
        )

    # Update resolution
    def update_text_resolution(self, change):
        self.resolution = change.new

        # Clear data load params to trigger data re-load
        self.rgb_array = None
        self.sensor = None
        self.load_params = None
        self.query_params = None

    # Change layers shown on the map
    def update_dealayer(self, change):
        self.dealayer = change.new

        if change.new == "ga_ls_ard_3":
            self.text_resolution.value = 30
            self.checkbox_pansharpen.disabled = False

            if self.pansharpen:
                self.text_resolution.value = 15
                self.text_resolution.disabled = True

        else:
            self.text_resolution.value = 10
            self.checkbox_pansharpen.disabled = True
            self.text_resolution.disabled = False

        update_map_layers(self)

    # Update basemap
    def update_basemap(self, change):
        self.basemap = change.new
        update_map_layers(self)

    # Set imagery style
    def update_styles(self, change):
        self.style = change.new
        update_map_layers(self)

    # Set output file format
    def update_output(self, change):
        self.output_format = change.new

    def run_app(self, change):

        # Clear progress bar and output areas before running
        self.status_info.clear_output()
        self.output_plot.clear_output()

        # Verify that polygon was drawn
        if self.gdf_drawn is not None:

            with self.status_info:

                # Load data and add to attribute
                if self.rgb_array is None:
                    self.rgb_array = extract_data(self)
                else:
                    print("Using previously loaded data")

            if self.rgb_array is not None:

                with self.status_info:

                    # Create unique file name
                    centre_coords = self.gdf_drawn.geometry[0].centroid.coords[0][::-1]
                    site = reverse_geocode(coords=centre_coords)
                    fname = (
                        f"{self.sensor} - {self.date} - {site} - {self.style}, "
                        f"{self.resolution:.0f} m resolution.{self.output_format}"
                    )

                    # Remove spaces and commas if requested
                    if self.standardise_name:
                        fname = (
                            fname.replace(" - ", "_")
                            .replace(", ", "-")
                            .replace(" ", "-")
                            .lower()
                        )

                    print(
                        f"\nExporting image for {site}.\nThis may take several minutes..."
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
                        "satellite imagery visible on the map."
                    )

        else:
            with self.status_info:
                print(
                    'Please draw a valid rectangle on the map, then press "Export imagery"'
                )
