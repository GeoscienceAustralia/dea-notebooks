"""
Digital Earth Australia Coastline widget, which can be used to 
interactively extract shoreline data using transects.
"""

# Import required packages
import fiona
import os
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
import geopandas as gpd
from io import BytesIO
import ipywidgets as widgets

import dea_tools.app.widgetconstructors as deawidgets
from dea_tools.coastal import get_coastlines, transect_distances


def make_box_layout():
    return Layout(
        #          border='solid 1px black',
        margin='0px 10px 10px 0px',
        padding='5px 5px 5px 5px',
        width='100%',
        height='100%',
    )


def create_expanded_button(description, button_style):
    return Button(
        description=description,
        button_style=button_style,
        layout=Layout(width="auto", height="auto"),
    )


class transect_app(HBox):

    def __init__(self):
        super().__init__()

        ######################
        # INITIAL ATTRIBUTES #
        ######################

        self.output_name = "example_output"
        self.export_csv = False
        self.export_plot = False
        self.product_list = [
            ("ESRI World Imagery", "none"),
            ("Open Street Map", "open_street_map"),
        ]
        self.product = self.product_list[0][1]
        self.mode_list = [('Distance', 'distance'), ('Width', 'width')]
        self.mode = self.mode_list[0][1]
        self.target = None
        self.action = None
        self.gdf_drawn = None
        self.gdf_uploaded = None

        ##################
        # HEADER FOR APP #
        ##################

        # Create the Header widget
        header_title_text = "<h3>Digital Earth Australia Coastlines shoreline transect extraction</h3>"
        instruction_text = "Select parameters and draw a transect on the map to extract shoreline data. <b>In distance mode</b>, draw a transect line starting from land that crosses multiple shorelines. <br><b>In width mode</b>, draw a transect line that intersects shorelines at least twice. Alternatively, <b>upload an vector file</b> to extract shoreline data for multiple existing transects."
        self.header = deawidgets.create_html(
            f"{header_title_text}<p>{instruction_text}</p>")
        self.header.layout = make_box_layout()

        #####################################
        # HANDLER FUNCTION FOR DRAW CONTROL #
        #####################################

        # Define the action to take once something is drawn on the map
        def update_geojson(target, action, geo_json):

            # Remove previously uploaded data if present
            self.gdf_uploaded = None
            fileupload_transects._counter = 0

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
            area = gdf_drawn_albers.envelope.area.values[0] / m2_per_km2
            polyarea_label = 'Total area of DEA Coastlines data to extract'
            polyarea_text = f"<b>{polyarea_label}</b>: {area:.2f} km<sup>2</sup>"

            # Test area size
            if area <= 50000:
                confirmation_text = '<span style="color: #33cc33"> <b>(Area to extract falls within recommended limit; click "Extract shoreline data" to continue)</b></span>'
                self.header.value = header_title_text + polyarea_text + confirmation_text
                self.gdf_drawn = gdf
            else:
                warning_text = '<span style="color: #ff5050"> <b>(Area to extract is too large, please select a smaller transect)</b></span>'
                self.header.value = header_title_text + polyarea_text + warning_text
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
        desired_drawtools = ['polyline']
        draw_control = deawidgets.create_drawcontrol(desired_drawtools)

        # Load DEACoastLines WMS
        deacl_url = 'https://geoserver.dea.ga.gov.au/geoserver/wms'
        deacl_layer = 'dea:DEACoastlines'
        deacoastlines = WMSLayer(
            url=deacl_url,
            layers=deacl_layer,
            format='image/png',
            transparent=True,
            attribution='DEA Coastlines © 2020 Geoscience Australia')

        # Begin by displaying an empty layer group, and update the group with desired WMS on interaction.
        self.map_layers = LayerGroup(layers=(deacoastlines,))
        self.map_layers.name = 'Map Overlays'

        # Create map widget
        self.m = deawidgets.create_map(map_center=(-28, 135),
                                       zoom_level=4,
                                       basemap=basemaps.Esri.WorldImagery)
        self.m.layout = make_box_layout()

        # Add tools to map widget
        self.m.add_control(draw_control)
        self.m.add_layer(self.map_layers)

        # Store current basemap for future use
        self.basemap = self.m.basemap

        ############################
        # WIDGETS FOR APP CONTROLS #
        ############################

        # Create parameter widgets
        text_output_name = deawidgets.create_inputtext(self.output_name,
                                                       self.output_name)
        checkbox_csv = deawidgets.create_checkbox(self.export_csv,
                                                  'Distance table (.csv)')
        checkbox_plot = deawidgets.create_checkbox(self.export_plot,
                                                   'Figure (.png)')
        deaoverlay_dropdown = deawidgets.create_dropdown(
            self.product_list, self.product_list[0][1])
        mode_dropdown = deawidgets.create_dropdown(self.mode_list,
                                                   self.mode_list[0][1])
        run_button = create_expanded_button("Extract shoreline data", "info")
        fileupload_transects = widgets.FileUpload(accept='', multiple=True)

        ####################################
        # UPDATE FUNCTIONS FOR EACH WIDGET #
        ####################################

        # Run update functions whenever various widgets are changed.
        text_output_name.observe(self.update_text_output_name, "value")
        checkbox_csv.observe(self.update_checkbox_csv, "value")
        checkbox_plot.observe(self.update_checkbox_plot, "value")
        deaoverlay_dropdown.observe(self.update_deaoverlay, "value")
        mode_dropdown.observe(self.update_mode, "value")
        run_button.on_click(self.run_app)
        draw_control.on_draw(update_geojson)
        fileupload_transects.observe(self.update_fileupload_transects, "value")

        ##################################
        # COLLECTION OF ALL APP CONTROLS #
        ##################################

        parameter_selection = VBox([
            HTML("<b>Output name:</b>"), text_output_name,
            HTML(
                '<b>Transect extraction mode:</b><br><img src="https://i.imgur.com/9fdTH9C.png">'
            ), 
            mode_dropdown,
            HTML("<b></br>Output files:</b>"), 
            checkbox_plot, 
            checkbox_csv,
            HTML(
                "</br><i><b>Advanced</b></br>Upload a GeoJSON or ESRI "
                "Shapefile (<5 mb) containing one or more transect lines.</i>"),
            fileupload_transects
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
        #     ----------                                  |
        # 6   |  Run   |                                  |
        #     ---------------------------------------------
        # 7   |               Status info                 |
        #     ---------------------------------------------
        # 8   |                                           |
        # 9   |               Output/figure               |
        # 10  |                                           |
        # 11  | ------------------------------------------|

        # Create the layout #[rowspan, colspan]
        grid = GridspecLayout(12, 10, height="1350px", width="auto")

        # Header and controls
        grid[0, :8] = self.header
        grid[0, 8:] = map_selection
        grid[1:6, 0:2] = parameter_selection
        grid[6, 0:2] = run_button

        # Status info, map and plot
        grid[1:7, 2:] = self.m  # map
        grid[7:8, :] = self.status_info
        grid[8:, :] = self.output_plot

        # Display using HBox children attribute
        self.children = [grid]

    ######################################
    # DEFINITION OF ALL UPDATE FUNCTIONS #
    ######################################

    # Set the output csv
    def update_fileupload_transects(self, change):

        # Clear any drawn data if present
        self.gdf_drawn = None

        # Save to file
        for uploaded_filename in change.new.keys():
            with open(uploaded_filename, "wb") as output_file:
                content = change.new[uploaded_filename]['content']
                output_file.write(content)

        with self.status_info:

            try:            

                print('Loading vector data...', end='\r')
                valid_files = [
                    file for file in change.new.keys()
                    if file.lower().endswith(('.shp', '.geojson'))
                ]
                valid_file = valid_files[0]
                transect_gdf = (gpd.read_file(valid_file).to_crs(
                    "EPSG:4326").explode().reset_index(drop=True))

                # Use ID column if it exists
                if 'id' in transect_gdf:
                    transect_gdf = transect_gdf.set_index('id')
                    print(f"Uploaded '{valid_file}'; automatically labelling "
                          "transects using column 'id'.")
                else:
                    print(
                        f"Uploaded '{valid_file}'; no 'id' column detected, "
                        f"labelling transects from 0 to {len(transect_gdf.index) - 1}."
                    )

                # Create a geodata
                geodata = GeoData(geo_dataframe=transect_gdf,
                                  style={
                                      'color': 'black',
                                      'weight': 3
                                  })

                # Add to map
                xmin, ymin, xmax, ymax = transect_gdf.total_bounds
                self.m.fit_bounds([[ymin, xmin], [ymax, xmax]])
                self.m.add_layer(geodata)

                # If completed, add to attribute
                self.gdf_uploaded = transect_gdf

            except IndexError:
                print(
                    "Cannot read uploaded files. Please ensure that data is "
                    "in either GeoJSON or ESRI Shapefile format.",
                    end='\r')
                self.gdf_uploaded = None

            except fiona.errors.DriverError:
                print(
                    "Shapefile is invalid. Please ensure that all shapefile "
                    "components (e.g. .shp, .shx, .dbf, .prj) are uploaded.",
                    end='\r')
                self.gdf_uploaded = None

    # Set output name
    def update_text_output_name(self, change):
        self.output_name = change.new

    # Output CSV
    def update_checkbox_csv(self, change):
        self.export_csv = change.new

    # Output plot
    def update_checkbox_plot(self, change):
        self.export_plot = change.new

    # Set mode
    def update_mode(self, change):
        self.mode = change.new

    # Update product
    def update_deaoverlay(self, change):

        self.product = change.new

        # Load DEACoastLines WMS
        deacl_url = "https://geoserver.dea.ga.gov.au/geoserver/wms"
        deacl_layer = "dea:DEACoastlines"
        deacoastlines = WMSLayer(
            url=deacl_url,
            layers=deacl_layer,
            format="image/png",
            transparent=True,
            attribution="DEA Coastlines © 2020 Geoscience Australia")

        if self.product == "none":
            self.map_layers.clear_layers()
            self.map_layers.add_layer(deacoastlines)

        elif self.product == "open_street_map":
            self.map_layers.clear_layers()
            layer = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
            self.map_layers.add_layer(layer)
            self.map_layers.add_layer(deacoastlines)

    def run_app(self, change):

        # Clear progress bar and output areas before running
        self.status_info.clear_output()
        self.output_plot.clear_output()

        # Run DEA Coastlines analysis
        with self.status_info:
            warnings.filterwarnings("ignore")

            # Load transects from either map or uploaded files
            if self.gdf_uploaded is not None:
                transect_gdf = self.gdf_uploaded
                run_text = 'uploaded file'
            elif self.gdf_drawn is not None:
                transect_gdf = self.gdf_drawn
                transect_gdf.index = [self.output_name]
                run_text = 'selected transect'
            else:
                print(f'No transect drawn or uploaded. Please select a transect on the map, or upload a GeoJSON or ESRI Shapefile.',
                      end='\r')
                transect_gdf = None

            # If valid data was returned, load DEA Coastlines data
            if transect_gdf is not None:
                
                # Load Coastlines data from WFS
                deacl_gdf = get_coastlines(bbox=transect_gdf)
                
                # Test that data was correctly returned
                if len(deacl_gdf.index) > 0:

                    # Dissolve by year to remove duplicates, then sort by date
                    deacl_gdf = deacl_gdf.dissolve(by='year', as_index=False)
                    deacl_gdf['year'] = deacl_gdf.year.astype(int)
                    deacl_gdf = deacl_gdf.sort_values('year')
                    deacl_gdf = deacl_gdf.set_index('year')

                else:
                    print(
                        "No annual shoreline data was found near the "
                        "supplied transect. Please draw or select a new "
                        "transect.",
                        end='\r')
                    deacl_gdf = None              

                # If valid DEA Coastlines data returned, calculate distances
                if deacl_gdf is not None:
                    print(f'Analysing transect distances using "{self.mode}" mode...',
                          end='\r')
                    dist_df = transect_distances(
                        transect_gdf.to_crs('EPSG:3577'),
                        deacl_gdf,
                        mode=self.mode)

                    # If valid data was produced:
                    if dist_df.any(axis=None):

                        # Successful output
                        print(f'DEA Coastlines data successfully extracted for {run_text}.')

                        # Export distance data
                        if self.export_csv:
                            
                            # Create folder if required and set path
                            out_dir = 'deacoastlines_outputs'
                            os.makedirs(out_dir, exist_ok=True)                                
                            csv_filename = f"{out_dir}/{self.output_name}.csv"
                            
                            # Export to file
                            dist_df.to_csv(csv_filename, index_label="Transect")
                            print(f'Distance data exported to "{csv_filename}".')

                        # Generate plot
                        with self.output_plot:

                            fig, ax = plt.subplots(constrained_layout=True,
                                                   figsize=(15, 5.5))
                            dist_df.T.plot(ax=ax, linewidth=3)

                            ax.legend(frameon=False, ncol=3, title='Transect')
                            ax.set_title(f"Digital Earth Australia Coastlines transect extraction - {self.output_name}")
                            ax.set_ylabel(f"Along-transect {self.mode} (m)")
                            ax.set_xlim(dist_df.T.index[0], dist_df.T.index[-1])

                            # Hide the right and top spines
                            ax.spines['right'].set_visible(False)
                            ax.spines['top'].set_visible(False)

                            # Only show ticks on the left and bottom spines
                            ax.yaxis.set_ticks_position('left')
                            ax.xaxis.set_ticks_position('bottom')
                            plt.show()

                        # Export plot
                        with self.status_info:
                            if self.export_plot:
                                
                                # Create folder if required and set path
                                out_dir = 'deacoastlines_outputs'
                                os.makedirs(out_dir, exist_ok=True)                                
                                figure_filename = f"{out_dir}/{self.output_name}.png"
                                
                                # Export to file
                                fig.savefig(figure_filename)
                                print(f'Figure exported to "{figure_filename}".')

                    else:
                        print(
                            "No valid shoreline data intersects with the "
                            "supplied transect. This can occur if:\n\n"
                            " - the transect does not intersect with any shorelines\n"
                            " - the transect intersects with shorelines more than once in 'distance' mode\n"
                            " - the transect intersects with shorelines only once in 'width' mode\n\n"
                            "Please draw or upload a new transect.",
                            end='\r')