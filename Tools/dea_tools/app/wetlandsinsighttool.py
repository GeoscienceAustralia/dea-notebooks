# notebookapp_wetlandsinsighttool.py

"""
Wetlands insight tool widget, which can be used to run an interactive
version of the wetlands insight tool.
This is the dea_africa version, to be rewritten 
"""

# Import required packages
import datacube
import warnings
import seaborn as sns
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
from dask.diagnostics import ProgressBar

import dea_tools
from dea_tools.dask import create_local_dask_cluster
#from dea_tools.wetlands import WIT_drill
import sys #while wit is not in develop
sys.path.insert(1, '../Tools/dea_tools/') #while wit is not in develop
from wetlands import WIT_drill                
import dea_tools.app.widgetconstructors as deawidgets


def make_box_layout():
     return Layout(
         #border='solid 1px black',
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


class wit_app(HBox):
    def __init__(self):
        super().__init__()
        
        ##########################################################
        # INITIAL ATTRIBUTES #

        self.startdate = "2020-01-01"
        self.enddate = "2020-03-01"
        self.mingooddata = 0.0
        self.resamplingfreq = "1M"
        self.out_csv = "example_WIT.csv"
        self.out_plot = "example_WIT.png"
        self.product_list = [
            (_("None"), "none"),
            (_("ESRI World Imagery"), "esri_world_imagery"),
            (_("Sentinel-2 Geomedian"), "gm_s2_annual"),
            (_("Water Observations from Space"), "wofs_ls_summary_annual"),
            
        ]
        self.product = self.product_list[0][1]
        self.product_year = "2020-01-01"
        self.target = None
        self.action = None
        self.gdf_drawn = None
        
        ##########################################################
        # HEADER FOR APP #
        
        # Create the Header widget
        header_title_text = _("Wetlands Insight Tool")
        instruction_text = _("Select parameters and AOI")
        self.header = deawidgets.create_html(f"<h3>{header_title_text}</h3><p>{instruction_text}</p>")
        self.header.layout = make_box_layout()
        
        ##########################################################
        # HANDLER FUNCTION FOR DRAW CONTROL #
        
        # Define the action to take once something is drawn on the map
        def update_geojson(target, action, geo_json):

            self.action = action

            json_data = json.dumps(geo_json)
            binary_data = json_data.encode()
            io = BytesIO(binary_data)
            io.seek(0)

            gdf = gpd.read_file(io)
            gdf.crs = "EPSG:4326"
            self.gdf_drawn = gdf

            gdf_drawn_epsg6933 = gdf.copy().to_crs("EPSG:6933")
            m2_per_km2 = 10 ** 6
            area = gdf_drawn_epsg6933.area.values[0] / m2_per_km2
            polyarea_label = _('Total polygon area')
            polyarea_text = f"<p><b>{polyarea_label}</b>: {area:.2f} km<sup>2</sup></p>"

            if area <= 3000:
                confirmation_text = '<p style="color:#33cc33;">' + _('Area falls within recommended limit') + '</p>'
                self.header.value = header_title_text + polyarea_text + confirmation_text
            else:
                warning_text = '<p style="color:#ff5050;">' + _('Area is too large, please update your polygon') + '</p>'
                self.header.value = header_title_text + polyarea_text + warning_text

        ##########################################################
        # WIDGETS FOR APP OUTPUTS #

        self.dask_client = Output(layout=make_box_layout())
        self.progress_bar = Output(layout=make_box_layout())
        self.wit_plot = Output(layout=make_box_layout())
        self.progress_header = deawidgets.create_html("")

        ##########################################################
        # MAP WIDGET, DRAWING TOOLS, WMS LAYERS #

        # Create drawing tools
        desired_drawtools = ['rectangle', 'polygon']
        draw_control = deawidgets.create_drawcontrol(desired_drawtools)
        
        # Begin by displaying an empty layer group, and update the group with desired WMS on interaction.
        self.dea_layers = LayerGroup(layers=()) # 
        self.dea_layers.name = _('Map Overlays') #

        # Create map widget
        self.m = deawidgets.create_map()
        
        self.m.layout = make_box_layout()
        
        # Add tools to map widget
        self.m.add_control(draw_control)
        self.m.add_layer(self.dea_layers)
        
        # Store current basemap for future use
        self.basemap = self.m.basemap

        ##########################################################
        # WIDGETS FOR APP CONTROLS #

        # Create parameter widgets
        startdate_picker = deawidgets.create_datepicker()
        enddate_picker = deawidgets.create_datepicker()
        min_good_data = deawidgets.create_boundedfloattext(self.mingooddata, 0.0, 1.0, 0.05)
        resampling_freq = deawidgets.create_inputtext(self.resamplingfreq, self.resamplingfreq)
        output_csv = deawidgets.create_inputtext(self.out_csv, self.out_csv)
        output_plot = deawidgets.create_inputtext(self.out_plot, self.out_plot)
        deaoverlay_dropdown = deawidgets.create_dropdown(self.product_list, self.product_list[0][1])
        run_button = create_expanded_button(_("Run"), "info")

        ##########################################################
        # COLLECTION OF ALL APP CONTROLS #
        
        parameter_selection = VBox(
            [
                HTML("<b>" + _("Map Overlay:") + "</b>"),
                deaoverlay_dropdown,
                HTML("<b>" + _("Start Date:") + "</b>"),
                startdate_picker,
                HTML("<b>" + _("End Date:") + "</b>"),
                enddate_picker,
                HTML("<b>" + _("Minimum Good Data:") + "</b>"),
                min_good_data,
                HTML("<b>" + _("Resampling Frequency:") + "</b>"),
                resampling_freq,
                HTML("<b>" + _("Output CSV:") + "</b>"),
                output_csv,
                HTML("<b>" + _("Output Plot:") + "</b>"),
                output_plot,
            ]
        )
        parameter_selection.layout = make_box_layout()

        ##########################################################
        # SPECIFICATION OF APP LAYOUT #

        # Create the layout #[rowspan, colspan]
        grid = GridspecLayout(11, 10, height="1100px", width="auto")

        # Controls and Status
        grid[0, :] = self.header
        grid[1:6, 0:2] = parameter_selection
        grid[6, 0:2] = run_button
        
        # Dask and Progress info
        grid[1, 7:] = self.dask_client
        grid[2:7, 7:] = self.progress_bar

        # Map
        grid[1:7, 2:7] = self.m

        # Plot
        grid[7:, :] = self.wit_plot

        # Display using HBox children attribute
        self.children = [grid]

        ##########################################################
        # SPECIFICATION UPDATE FUNCTIONS FOR EACH WIDGET #

        # Run update functions whenever various widgets are changed.
        startdate_picker.observe(self.update_startdate, "value")
        enddate_picker.observe(self.update_enddate, "value")
        min_good_data.observe(self.update_mingooddata, "value")
        resampling_freq.observe(self.update_resamplingfreq, "value")
        output_csv.observe(self.update_outputcsv, "value")
        output_plot.observe(self.update_outputplot, "value")
        deaoverlay_dropdown.observe(self.update_deaoverlay, "value")
        run_button.on_click(self.run_app)
        draw_control.on_draw(update_geojson)

    ##############################################################
    # DEFINITION OF ALL UPDATE FUNCTIONS #

    # set the start date to the new edited date
    def update_startdate(self, change):
        self.startdate = change.new

    # set the end date to the new edited date
    def update_enddate(self, change):
        self.enddate = change.new

    # set the min good data
    def update_mingooddata(self, change):
        self.mingooddata = change.new

    # set the resampling frequency
    def update_resamplingfreq(self, change):
        self.resamplingfreq = change.new

    # set the output csv
    def update_outputcsv(self, change):
        self.out_csv = change.new

    # set the output plot
    def update_outputplot(self, change):
        self.out_plot = change.new

    # Update product
    def update_deaoverlay(self, change):

        self.product = change.new

        if self.product == "none":
            self.dea_layers.clear_layers()
        elif self.product == "esri_world_imagery":
            self.dea_layers.clear_layers()
            layer = basemap_to_tiles(basemaps.Esri.WorldImagery)
            self.dea_layers.add_layer(layer)
        else:
            self.dea_layers.clear_layers()
            layer = deawidgets.create_dea_wms_layer(self.product, self.product_year)
            self.dea_layers.add_layer(layer)

    def run_app(self, change):
        
        # Clear progress bar and output areas before running
        self.dask_client.clear_output()
        self.progress_bar.clear_output()
        self.wit_plot.clear_output()

        # Connect to datacube database
        dc = datacube.Datacube(app="wetland_app")

        # Configure local dask cluster
        with self.dask_client:
            client = create_local_dask_cluster(
                return_client=True, display_client=True
            )

        # Set any defaults
        TCW_threshold = -0.035
        dask_chunks = dict(x=1000, y=1000, time=1)
        
        #check resampling freq
        if self.resamplingfreq  == 'None':
            rsf = None
        else:
            rsf = self.resamplingfreq
        
        self.progress_header.value = f"<h3>"+_("Progress")+"</h3>"
            
        # run wetlands polygon drill
        with self.progress_bar:
#             with ProgressBar():
            warnings.filterwarnings("ignore")                
            try:
                df = WIT_drill(
                    gdf=self.gdf_drawn,
                    time=(self.startdate, self.enddate),
                    min_gooddata=self.mingooddata,
                    resample_frequency=rsf,
                    TCW_threshold=TCW_threshold,
                    export_csv=self.out_csv,
                    dask_chunks=dask_chunks,
                    verbose=False,
                    verbose_progress=True,
                )
                print(_("WIT complete"))
            except AttributeError:
                print(_("No polygon selected"))
        
        # close down the dask client
        client.shutdown()

        # save the csv
        if self.out_csv:
            df.to_csv(self.out_csv, index_label="Datetime")

        # ---Plotting------------------------------
        
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
                df.index,
                df.wofs_area_percent,
                df.wet_percent,
                df.green_veg_percent,
                df.dry_veg_percent,
                df.bare_soil_percent,
                labels=[
                    _("open water"),
                    _("wet"),
                    _("green veg"),
                    _("dry veg"),
                    _("bare soil"),
                ],
                colors=pal,
                alpha=0.6,
            )

            # set axis limits to the min and max
            ax.set_ylim(0, 100)
            ax.set_xlim(df.index[0], df.index[-1])
            ax.tick_params(axis="x", labelsize=fontsize)

            # add a legend and a tight plot box
            ax.legend(loc="lower left", framealpha=0.6)
            ax.set_title(_("Percentage Fractional Cover, Wetness, and Water"))
            # plt.tight_layout()
            plt.show()

            if self.out_plot:
                # save the figure
                fig.savefig(f"{self.out_plot}")
