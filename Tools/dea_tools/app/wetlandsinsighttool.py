"""
Digital Earth Australia Wetlands Insight Tool widget, which can be used to interactively
extract a stacked line plot using the wetlands insight tool on a wetland polygon.
"""

import datetime
import json
import warnings
from io import BytesIO

import fiona
import geopandas as gpd
import ipywidgets as widgets
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns
from ipyleaflet import (
    GeoData,
    LayerGroup,
    Marker,
    SearchControl,
    basemap_to_tiles,
    basemaps,
)
from ipywidgets import (
    HTML,
    Button,
    GridspecLayout,
    HBox,
    Layout,
    Output,
    VBox,
)

from dea_tools.app.widgetconstructors import (
    create_checkbox,
    create_datepicker,
    create_drawcontrol,
    create_dropdown,
    create_html,
    create_inputtext,
    create_map,
)
from dea_tools.dask import create_local_dask_cluster
from dea_tools.wetlands import generate_low_quality_data_periods, WIT_drill, spatial_wit


def make_box_layout():
    return Layout(
        #          border='solid 1px black',
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


class wit_app(HBox):
    def __init__(self):
        super().__init__()

        ######################
        # INITIAL ATTRIBUTES #
        ######################

        enddate = datetime.datetime.today()
        startdate = datetime.datetime(year=enddate.year - 1, month=enddate.month, day=enddate.day)
        self.startdate = startdate.strftime("%Y-%m-%d")
        self.enddate = enddate.strftime("%Y-%m-%d")
        self.wetland_name = "example WIT"
        # self.out_csv = "example_WIT.csv"
        self.out_plot = False
        self.product_list = [
            ("ESRI World Imagery", "none"),
            ("Open Street Map", "open_street_map"),
        ]
        self.product = self.product_list[0][1]
        self.target = None
        self.action = None
        self.gdf_drawn = None
        self.gdf_uploaded = None
        self.max_size = False
        self.spatial_wit = False

        ##################
        # HEADER FOR APP #
        ##################

        # Create the Header widget
        header_title_text = "<h3>Digital Earth Australia Wetlands Insight Tool </h3>"
        instruction_text = "Select parameters and draw a polygon on the map to extract a stacked line plot for a given area. Alternatively, <b>upload a shapefile or a GeoJSON</b> to extract a stacked line plot for your wetland of interest polygon."
        self.header = create_html(f"{header_title_text}<p>{instruction_text}</p>")
        self.header.layout = make_box_layout()

        #####################################
        # HANDLER FUNCTION FOR DRAW CONTROL #
        #####################################

        # Define the action to take once something is drawn on the map
        def update_geojson(target, action, geo_json):
            # Remove previously uploaded data if present
            self.gdf_uploaded = None
            fileupload_wetlands._counter = 0

            # Get data from action
            self.action = action

            # Convert data to geopandas
            json_data = json.dumps(geo_json)
            binary_data = json_data.encode()
            io = BytesIO(binary_data)
            io.seek(0)
            gdf = gpd.read_file(io)
            gdf.crs = "EPSG:4326"

            # Convert to Albers and compute area
            gdf_drawn_albers = gdf.copy().to_crs("EPSG:3577")
            m2_per_km2 = 10**6
            area = gdf_drawn_albers.area.values[0] / m2_per_km2
            polyarea_label = "Total polygon area"
            polyarea_text = f"<b>{polyarea_label}</b>: {area:.2f} km<sup>2</sup>"

            # Test area size
            if self.max_size:
                confirmation_text = '<span style="color: #33cc33"> <b>(Overriding maximum size limit; use with caution as may lead to memory issues)</b></span>'
                self.header.value = header_title_text + polyarea_text + confirmation_text
                self.gdf_drawn = gdf
            elif area <= 2000:
                confirmation_text = (
                    '<span style="color: #33cc33"> <b>(Area to extract falls within recommended limit)</b></span>'
                )
                self.header.value = header_title_text + polyarea_text + confirmation_text
                self.gdf_drawn = gdf
            else:
                warning_text = '<span style="color: #ff5050"> <b>(Area to extract is too large, please update your polygon)</b></span>'
                self.header.value = header_title_text + polyarea_text + warning_text
                self.gdf_drawn = None

        ###########################
        # WIDGETS FOR APP OUTPUTS #
        ###########################

        self.dask_client = Output(layout=make_box_layout())
        self.progress_bar = Output(layout=make_box_layout())
        self.wit_plot = Output(layout=make_box_layout())
        self.progress_header = create_html("")

        #########################################
        # MAP WIDGET, DRAWING TOOLS, WMS LAYERS #
        #########################################

        # Create drawing tools
        desired_drawtools = ["rectangle", "polygon"]
        draw_control = create_drawcontrol(desired_drawtools)

        # Begin by displaying an empty layer group, and update the group with desired WMS on interaction.
        self.map_layers = LayerGroup(layers=())
        self.map_layers.name = "Map Overlays"

        # Create map widget
        self.m = create_map(map_center=(-28, 135), zoom_level=4, basemap=basemaps.Esri.WorldImagery)
        self.m.layout = make_box_layout()

        # Add tools to map widget
        self.m.add_control(draw_control)
        self.m.add_control(
            SearchControl(
                position="topleft",
                url="https://nominatim.openstreetmap.org/search?format=json&q={s}",
                zoom=13,  # 'Village / Suburb' level zoom
                marker=Marker(draggable=False),
            )
        )
        self.m.add_layer(self.map_layers)

        # Store current basemap for future use
        self.basemap = self.m.basemap

        ############################
        # WIDGETS FOR APP CONTROLS #
        ############################

        # Create parameter widgets
        startdate_picker = create_datepicker(
            value=startdate,
        )
        enddate_picker = create_datepicker(
            value=enddate,
        )
        wetland_name = create_inputtext(self.wetland_name, self.wetland_name)
        # output_csv = create_inputtext(self.out_csv, self.out_csv)
        output_plot = create_checkbox(self.out_plot, "Figure (.png)")
        deaoverlay_dropdown = create_dropdown(self.product_list, self.product_list[0][1])
        run_button = create_expanded_button("Run", "info")
        fileupload_wetlands = widgets.FileUpload(accept="", multiple=True)

        # Expandable advanced section
        max_size = create_checkbox(self.max_size, "Enable", layout={"width": "95%"})
        output_spatial_wit = create_checkbox(self.spatial_wit, "Animation (.gif)")

        ####################################
        # UPDATE FUNCTIONS FOR EACH WIDGET #
        ####################################

        # Run update functions whenever various widgets are changed.
        startdate_picker.observe(self.update_startdate, "value")
        enddate_picker.observe(self.update_enddate, "value")
        wetland_name.observe(self.update_wetlandname, "value")
        # output_csv.observe(self.update_outputcsv, "value")
        output_plot.observe(self.update_outputplot, "value")
        deaoverlay_dropdown.observe(self.update_deaoverlay, "value")
        run_button.on_click(self.run_app)
        draw_control.on_draw(update_geojson)
        fileupload_wetlands.observe(self.update_fileupload_wetlands, "value")
        max_size.observe(self.update_maxsize, "value")
        output_spatial_wit.observe(self.update_outputspatialwit, "value")

        ##################################
        # COLLECTION OF ALL APP CONTROLS #
        ##################################
        expand_box = VBox([
            HTML("<b>Override maximum size limit:</b></br> (use with caution; may cause memory issues/crashes)"),
            max_size,
            HTML("<b>Spatial WIT animation:<b/>"),
            output_spatial_wit,
        ])

        expand = widgets.Accordion(
            children=[expand_box],
            selected_index=None,
        )
        expand.set_title(0, "Advanced")

        parameter_selection = VBox([
            HTML("<b>Start Date:</b>"),
            startdate_picker,
            HTML("<b>End Date:</b>"),
            enddate_picker,
            HTML("<b>Wetland Name:</b>"),
            wetland_name,
            # HTML("<b>Output CSV:</b>"),
            # output_csv,
            HTML("<b>Output Plot:</b>"),
            output_plot,
            HTML(
                "</br><i><b>Upload Polygon:</b></br>Upload a GeoJSON or"
                " Shapefile (<5 mb) containing a wetland polygon.</i>"
            ),
            fileupload_wetlands,
            HTML("</br>"),
            expand,
        ])
        map_selection = VBox([
            HTML("</br><b>Map overlay:</b>"),
            deaoverlay_dropdown,
        ])
        parameter_selection.layout = make_box_layout()
        map_selection.layout = make_box_layout()

        ###############################
        # SPECIFICATION OF APP LAYOUT #
        ###############################

        #       0   1    2   3   4   5   6   7    8   9
        #     ---------------------------------------------
        # 0   | Header                         | Map sel. |
        #     ---------------------------------------------
        # 1   | Params |                                  |
        # 2   |        |                                  |
        # 3   |        |                                  |
        # 4   |        |               Map                |
        # 5   |        |                                  |
        # 6   |        |                                  |
        #     ----------                                  |
        # 7   |  Run   |                                  |
        #     ---------------------------------------------
        # 8   |               Status info                 |
        #     ---------------------------------------------
        # 9   |                                           |
        # 10   |               Output/figure               |
        # 11  |                                           |
        # 12  | ------------------------------------------|

        # Create the layout #[rowspan, colspan]
        grid = GridspecLayout(13, 10, height="1350px", width="auto")

        # Header and controls
        grid[0, :8] = self.header
        grid[0, 8:] = map_selection
        grid[1:7, 0:2] = parameter_selection
        grid[7, 0:2] = run_button

        # Status info, map and plot
        grid[1:8, 2:] = self.m  # map
        grid[8:9, :] = self.progress_bar
        # grid[7:8, :] = self.dask_client

        # Plot
        grid[9:, :] = self.wit_plot

        # Display using HBox children attribute
        self.children = [grid]

    ######################################
    # DEFINITION OF ALL UPDATE FUNCTIONS #
    ######################################

    # Set the output csv
    def update_fileupload_wetlands(self, change):
        # Clear any drawn data if present
        self.gdf_drawn = None

        # Temporary compatibility fix for ipywidget > 8.0
        # TODO: Update code to use new fileupload API documented here:
        # https://ipywidgets.readthedocs.io/en/latest/user_migration_guides.html#fileupload
        uploaded_data = {f["name"]: {"content": f.content.tobytes()} for f in change.new}

        # Save to file
        for uploaded_filename in uploaded_data:
            with open(uploaded_filename, "wb") as output_file:
                content = uploaded_data[uploaded_filename]["content"]
                output_file.write(content)

        with self.progress_bar:
            try:
                print("Loading vector data...", end="\r")
                valid_files = [file for file in uploaded_data if file.lower().endswith((".shp", ".geojson"))]
                valid_file = valid_files[0]
                wetlands_gdf = (
                    gpd.read_file(valid_file).to_crs("EPSG:4326").explode(index_parts=True).reset_index(drop=True)
                )

                # Use ID column if it exists
                if "id" in wetlands_gdf:
                    wetlands_gdf = wetlands_gdf.set_index("id")
                    print(f"Uploaded '{valid_file}'; automatically labelling ")
                else:
                    print(f"Uploaded '{valid_file}'; no 'id' column detected.")

                # Create a geodata
                geodata = GeoData(geo_dataframe=wetlands_gdf, style={"color": "black", "weight": 3})

                # Add to map
                xmin, ymin, xmax, ymax = wetlands_gdf.total_bounds
                self.m.fit_bounds([[ymin, xmin], [ymax, xmax]])
                self.m.add_layer(geodata)

                # If completed, add to attribute
                self.gdf_uploaded = wetlands_gdf

            except IndexError:
                print(
                    "Cannot read uploaded files. Please ensure that data is in either GeoJSON or Shapefile format.",
                    end="\r",
                )
                self.gdf_uploaded = None

            except fiona.errors.DriverError:
                print(
                    "Shapefile is invalid. Please ensure that all shapefile "
                    "components (e.g. .shp, .shx, .dbf, .prj) are uploaded.",
                    end="\r",
                )
                self.gdf_uploaded = None

    # Set the start date to the new edited date
    def update_startdate(self, change):
        self.startdate = change.new

    # Set the end date to the new edited date
    def update_enddate(self, change):
        self.enddate = change.new

    # Set the wetland name
    def update_wetlandname(self, change):
        self.wetland_name = change.new

    # Set the output csv
    # def update_outputcsv(self, change):
    # self.out_csv = change.new

    # Set the output plot
    def update_outputplot(self, change):
        self.out_plot = change.new

    # Override max size limit
    def update_maxsize(self, change):
        self.max_size = change.new

    # Select to output spatial WIT
    def update_outputspatialwit(self, change):
        self.spatial_wit = change.new

    # Update product
    def update_deaoverlay(self, change):
        self.product = change.new

        if self.product == "none":
            self.map_layers.clear_layers()

        elif self.product == "open_street_map":
            self.map_layers.clear_layers()
            layer = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
            self.map_layers.add_layer(layer)

    def run_app(self, change):
        # Clear progress bar and output areas before running
        self.progress_bar.clear_output()
        self.wit_plot.clear_output()
        self.dask_client.clear_output()

        # Configure local dask cluster
        with self.dask_client:
            client = create_local_dask_cluster(return_client=True, display_client=True)

        # Set any defaults
        dask_chunks = {"x": 1000, "y": 1000, "time": 1}

        self.progress_header.value = "<h3>" + ("Progress") + "</h3>"

        # Run DEA WIT analysis
        with self.progress_bar:
            warnings.filterwarnings("ignore")

            # Load polygons from either map or uploaded files
            if self.gdf_uploaded is not None:
                wetlands_gdf = self.gdf_uploaded
                run_text = "uploaded file"
            elif self.gdf_drawn is not None:
                wetlands_gdf = self.gdf_drawn

                # save the drawn polygon as a geojson in the current directory
                try:
                    output_geojson_path = f"{self.wetland_name}_drawn_polygon.geojson"
                    wetlands_gdf.to_file(output_geojson_path, driver="GeoJSON")
                    print(f"Drawn polygon saved to: {output_geojson_path}")
                except Exception as e:
                    print(f"Error saving drawn polygon: {e}")
                run_text = "selected polygon"
            else:
                print(
                    "No polygon drawn or uploaded. Please select a polygon on the map, or upload a GeoJSON or Shapefile.",
                    end="\r",
                )
                wetlands_gdf = None

            # Run wetlands polygon drill
            df = None

            output_csv = self.wetland_name + ".csv" if not self.wetland_name.endswith(".csv") else self.wetland_name

            if wetlands_gdf is not None:
                try:
                    ds_wit, df = WIT_drill(
                        gdf=wetlands_gdf,
                        time=(self.startdate, self.enddate),
                        export_csv=output_csv,
                        dask_chunks=dask_chunks,
                        verbose=False,
                        verbose_progress=True,
                    )
                    print("WIT complete")
                except AttributeError:
                    print("No polygon selected")

            else:
                print("No valid polygon to process. Please select or draw a new polygon.")

        # close down the dask client
        client.shutdown()

        # save the csv
        if df is not None and self.wetland_name:
            df.to_csv(output_csv, index=False)

        else:
            print("No valid polygon to process. Please select or draw a new polygon.")
            df = None

        # ---Plotting------------------------------
        if df is not None:
            with self.wit_plot:
                fontsize = 17
                plt.rcParams.update({"font.size": fontsize})
                # set up color palette
                pal = [
                    sns.xkcd_rgb["cobalt blue"],
                    sns.xkcd_rgb["neon blue"],
                    sns.xkcd_rgb["grass"],
                    sns.xkcd_rgb["beige"],
                    sns.xkcd_rgb["brown"],
                ]

                # make a stacked area plot
                plt.close("all")

                fig, ax = plt.subplots(constrained_layout=True, figsize=(20, 6))

                ax.stackplot(
                    df["date"],
                    df["water"] * 100,
                    df["wet"] * 100,
                    df["norm_pv"] * 100,
                    df["norm_npv"] * 100,
                    df["norm_bs"] * 100,
                    colors=pal,
                    alpha=0.7,
                )

                # manually change the legend display order
                legend = ax.legend(
                    ["open water", "wet", "green veg", "dry veg", "bare soil"][::-1],
                    loc="lower left",
                )
                handles = legend.legend_handles

                for i, handle in enumerate(handles):
                    handle.set_facecolor(pal[::-1][i])
                    handle.set_alpha(0.7)

                # setup the display ranges
                ax.set_ylim(0, 100)
                ax.set_xlim(df["date"].min(), df["date"].max())

                # add a new column: 'off_value' based on low quality data setting
                df = generate_low_quality_data_periods(df)

                ax.fill_between(
                    df["date"],
                    0,
                    100,
                    where=df["off_value"] == 100,
                    color="white",
                    alpha=0.5,
                    hatch="//",
                )

                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))

                # Rotates and right-aligns the x labels so they don't crowd each other.
                for label in ax.get_xticklabels(which="major"):
                    label.set(rotation=30, horizontalalignment="right")

                x_label_text = "The Fractional Cover algorithm developed by the Joint Remote Sensing Research Program and\n the Water Observations from Space algorithm developed by Geoscience Australia are used in the production of this data"

                ax.set_xlabel(x_label_text, style="italic")

                ax.set_ylabel("Percentage of wetland (%)")

                # add a title
                plt.title(
                    f"Percentage of area dominated by WOs, Wetness, Fractional Cover for\n {self.wetland_name}",
                    fontsize=16,
                )
                plt.show()

                if self.out_plot:
                    # save the figure
                    fig.savefig(f"{self.wetland_name}")

        else:
            print("No valid polygon to process. Please select or draw a new polygon.")

        # Export spatial WIT animation if checkbox is selected
        if self.spatial_wit and ds_wit is not None:
            try:
                spatial_wit(ds=ds_wit, wetland_name=self.wetland_name)
                print("Animation complete")
            except AttributeError:
                print("No polygon selected")

        else:
            print("No valid polygon to process. Please select or draw a new polygon.")
