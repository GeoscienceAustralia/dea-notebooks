'''
Functions for defining widgets for interactive Digital Earth Australia notebooks. 

These functions are directly modified from 
originals developed by Digital Earth Africa: 
https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/blob/main/Tools/deafrica_tools/app/widgetconstructors.py

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, post a question on the Open Data Cube 
Slack channel (http://slack.opendatacube.org/) or the GIS Stack Exchange 
(https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using 
the `open-data-cube` tag (you can view previously asked questions here: 
https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one 
on GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: June 2022
'''

import ipyleaflet as leaflet
from ipyleaflet import LayersControl
import ipywidgets as widgets
from traitlets import Unicode


def create_datepicker(description='', value=None, layout={'width': '85%'}):
    '''
    Create a DatePicker widget
    
    Last modified: October 2021
    
    Parameters
    ----------
    description : string
        descirption label to attach
    layout : dictionary
        any layout commands for the widget
        
    Returns
    -------
    date_picker : ipywidgets.widgets.widget_date.DatePicker
        
    '''

    date_picker = widgets.DatePicker(description=description,
                                     layout=layout,
                                     disabled=False,
                                     value=value)

    return date_picker


def create_inputtext(value,
                     placeholder,
                     description="",
                     layout={'width': '85%'}):
    '''
    Create a Text widget
    
    Last modified: October 2021
    
    Parameters
    ----------
    value : string
        initial value of the widget
    placeholder : string
        placeholder text to display to the user before intput
    description : string
        descirption label to attach
    layout : dictionary
        any layout commands for the widget
        
    Returns
    -------
    input_text : ipywidgets.widgets.widget_string.Text
        
    '''

    input_text = widgets.Text(value=value,
                              placeholder=placeholder,
                              description=description,
                              layout=layout,
                              disabled=False)

    return input_text


def create_boundedfloattext(value,
                            min_val,
                            max_val,
                            step_val,
                            description="",
                            layout={'width': '85%'}):
    '''
    Create a BoundedFloatText widget
    
    Last modified: October 2021
    
    Parameters
    ----------
    value : float
        initial value of the widget
    min_val : float
        minimum allowed value for the float
    max_val : float
        maximum allowed value for the float
    step_val : float
        allowed increment for the float
    description : string
        descirption label to attach
    layout : dictionary
        any layout commands for the widget
        
    Returns
    -------
    float_text : ipywidgets.widgets.widget_float.BoundedFloatText
        
    '''

    float_text = widgets.BoundedFloatText(
        value=value,
        min=min_val,
        max=max_val,
        step=step_val,
        description=description,
        layout=layout,
        disabled=False,
    )

    return float_text


def create_dropdown(options, value, description="", layout={'width': '85%'}):
    '''
    Create a Dropdown widget
    
    Last modified: October 2021
    
    Parameters
    ----------
    options : list
        a list of options for the user to select from
    value : string
        initial value of the widget
    description : string
        descirption label to attach
    layout : dictionary
        any layout commands for the widget
        
    Returns
    -------
    dropdown : ipywidgets.widgets.widget_selection.Dropdown
        
    '''

    dropdown = widgets.Dropdown(
        options=options,
        value=value,
        description=description,
        layout=layout,
        disabled=False,
    )

    return dropdown


def create_checkbox(value, description="", layout={'width': '85%'}):
    '''
    Create a Checkbox widget
    
    Last modified: January 2022
    
    Parameters
    ----------
    value : string
        initial value of the widget; True or False
    description : string
        description label to attach
    layout : dictionary
        any layout commands for the widget
        
    Returns
    -------
    dropdown : ipywidgets.widgets.widget_selection.Dropdown
        
    '''

    checklist = widgets.Checkbox(value=value,
                                 description=description,
                                 layout=layout,
                                 disabled=False,
                                 indent=False)

    return checklist


def create_html(value):
    '''
    Create a HTML widget
    
    Last modified: October 2021
    
    Parameters
    ----------
    value : string
        HTML text to display
        
    Returns
    -------
    html : ipywidgets.widgets.widget_string.HTML
        
    '''

    html = widgets.HTML(value=value,)

    return html


def create_map(map_center=(-28, 135),
               zoom_level=4,
               basemap=leaflet.basemaps.OpenStreetMap.Mapnik,
               basemap_name='Open Street Map',
               **kwargs):
    '''
    Create an interactive ipyleaflet map
    
    Last modified: October 2021
    
    Parameters
    ----------
    map_center : tuple
        A tuple containing the latitude and longitude to focus on.
        Defaults to center of Australia (-28, 135)
    zoom_level : integer
        Zoom level for the map
        Defaults to 4 to view all of Australia
    basemap : ipyleaflet basemap (dict)
        Basemap to use, can be any from https://ipyleaflet.readthedocs.io/en/latest/api_reference/basemaps.html
        Defaults to Open Street Map (basemaps.OpenStreetMap.Mapnik)
    basemap_name : string
        Layer name for the basemap
        
    Returns
    -------
    m : ipyleaflet.leaflet.Map
        interactive ipyleaflet map
        
    '''

    basemap_tiles = leaflet.basemap_to_tiles(basemap)
    basemap_tiles.name = basemap_name

    m = leaflet.Map(center=map_center,
                    zoom=zoom_level,
                    basemap=basemap_tiles,
                    scroll_wheel_zoom=True,
                    **kwargs)

    return m


def create_dea_wms_layer(product, date, **params):
    '''
    Create a Digital Earth Australia WMS layer to add to a map
    
    Last modified: October 2021
    
    Parameters
    ----------
    product : string
        The Digital Earth Australia product to load
        (e.g. 'ga_ls8cls9c_gm_cyear_3')
    date : string (yyyy-mm-dd format)
        The date to load the product for
        
    Returns
    -------
    time_wms : ipyleaflet WMS layer
        
    '''

    # Load DEA WMS
    class TimeWMSLayer(leaflet.WMSLayer):
        time = Unicode("").tag(sync=True, o=True)

    time_wms = TimeWMSLayer(
        url="https://ows.dea.ga.gov.au/",
        layers=product,
        time=date,
        format="image/png",
        transparent=True,
        attribution="Digital Earth Australia",
        **params
    )

    return time_wms


def create_drawcontrol(
    draw_controls=[
        'rectangle', 'polygon', 'circle', 'polyline', 'marker', 'circlemarker'
    ],
    rectangle_options={},
    polygon_options={},
    circle_options={},
    polyline_options={},
    marker_options={},
    circlemarker_options={},
):
    '''
    Create a draw control widget to add to ipyleaflet maps
    
    Last modified: October 2021
    
    Parameters
    ----------
    draw_controls : list
        List of draw controls to add to the map. Defaults to adding all
        Viable options are 'rectangle', 'polygon', 'circle', 'polyline', 
        'marker', 'circlemarker'.
    rectangle_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    polygon_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    circle_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    polyline_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    marker_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    circlemarker_options : dict
        Options to customise the appearence of the relevant shape. 
        Leave blank for default styling.
    
        
    Returns
    -------
    draw_control : ipyleaflet.leaflet.DrawControl
        
    '''

    # Set defualt DE Africa styling options for polygons
    default_shapeoptions = {
        "color": "#FFFFFF",
        "opacity": 0.8,
        "fillColor": "#336699",
        "fillOpacity": 0.4,
    }
    default_drawerror = {
        "color": "#FF6633",
        "message": "Drawing error, clear all and try again"
    }

    # Set draw control appearence to DE Africa defaults
    # Do this if user has requested a control, but has not provided a corresponding options dict

    if ('rectangle' in draw_controls) and (not rectangle_options):
        rectangle_options = {"shapeOptions": default_shapeoptions}

    if ('polygon' in draw_controls) and (not polygon_options):
        polygon_options = {
            "shapeOptions": default_shapeoptions,
            "drawError": default_drawerror,
            "allowIntersection": False,
        }

    if ('circle' in draw_controls) and (not circle_options):
        circle_options = {"shapeOptions": default_shapeoptions}

    if ('polyline' in draw_controls) and (not polyline_options):
        polyline_options = {"shapeOptions": default_shapeoptions}

    if ('marker' in draw_controls) and (not marker_options):
        marker_options = {'shapeOptions': {'opacity': 1.0}}

    if ('circlemarker' in draw_controls) and (not circlemarker_options):
        circlemarker_options = {"shapeOptions": default_shapeoptions}

    # Instantiate draw control and add options
    draw_control = leaflet.DrawControl()
    draw_control.rectangle = rectangle_options
    draw_control.polygon = polygon_options
    draw_control.marker = marker_options
    draw_control.circle = circle_options
    draw_control.circlemarker = circlemarker_options
    draw_control.polyline = polyline_options

    return draw_control
