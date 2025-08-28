from ipyleaflet import Map, DrawControl
import geopandas as gpd
import ipywidgets as widgets
from IPython.display import display, clear_output
import json
import builtins

def draw_polygon_tool():
    # Create a map centered on Australia
    m = Map(center=(-25.2744, 133.7751), zoom=4)

    # Create a DrawControl to allow polygon drawing
    draw_control = DrawControl()
    draw_control.polygon = {
        "shapeOptions": {
            "color": "#6bc2e5",
            "fillOpacity": 0.4
        }
    }
    m.add_control(draw_control)

    # Display the map
    display(m)

    # Output widget to show messages
    output = widgets.Output()
    display(output)

    # Store drawn geometry
    drawn_features = []

    def handle_draw(target, action, geo_json):
        if action == 'created' and geo_json['geometry']['type'] == 'Polygon':
            drawn_features.clear()
            drawn_features.append(geo_json)

    draw_control.on_draw(handle_draw)

    # Button to finalize and process the polygon
    finished_button = widgets.Button(description="Finished")

    
    def on_finished_clicked(b):
        with output:
            clear_output()
            if not drawn_features:
                print("No polygon has been drawn.")
                return
            try:
                feature_collection = {
                    "type": "FeatureCollection",
                    "features": drawn_features
                }
                gdf = gpd.GeoDataFrame.from_features(feature_collection["features"])
                gdf.set_crs(epsg=4326, inplace=True)
                gdf = gdf.to_crs(epsg=3577)
                gdf.to_file("wetland_boundary.geojson", driver="GeoJSON")
                area_sqkm = gdf.geometry.area.sum() / 1e6
                builtins.wetland_boundary = gdf  # This makes it available globally
                print("Polygon saved as 'wetland_boundary.geojson' and loaded as variable 'wetland_boundary'.")
                print(f"Area of polygon: {area_sqkm:.2f} square kilometers.")
                if area_sqkm > 2000:
                    print("⚠️ Analysis may be slow due to large area. Recommended area is 2,000 square kilometers or less.")
                gdf.plot()
            except Exception as e:
                print(f"Error processing polygon: {e}")


    finished_button.on_click(on_finished_clicked)
    display(finished_button)