import numpy

import folium
import folium.plugins        

from odc.ui import mk_data_uri, zoom_from_bbox
from odc.ui._images import xr_bounds
from datacube.testutils.geom import epsg4326
from datacube_ows.styles.api import apply_ows_style_cfg, xarray_image_as_png

# ipyleaflet is listed as an optional dependency for the dea-tools package
# so instead of trying to import it here, we do that as needed

# default fallback OWS style configuration
RGB_CFG = {
    "components": {
        "red": {"red": 1.0},
        "green": {"green": 1.0},
        "blue": {"blue": 1.0},
    },

    "scale_range": (50, 3000),
}


def center_of_bbox(bbox):
    return (bbox.bottom + bbox.top) * 0.5, (bbox.right + bbox.left) * 0.5


def folium_map_default(bbox, zoom_start=None, location=None, **kwargs):
    """
    Sensible defaults for a folium map based on the bounding box of the image to be shown.
    """
    if zoom_start is None:
        zoom_start = zoom_from_bbox(bbox)
    if location is None:
        location = center_of_bbox(bbox)

    kwargs['zoom_start'] = zoom_start
    kwargs['location'] = location
    
    return folium.Map(**kwargs)


def folium_dualmap_default(bbox, zoom_start=None, location=None, **kwargs):
    """
    Sensible defaults for a folium dual map based on the bounding box of the image to be shown.
    """
    if zoom_start is None:
        zoom_start = zoom_from_bbox(bbox)
    if location is None:
        location = center_of_bbox(bbox)

    kwargs['zoom_start'] = zoom_start
    kwargs['location'] = location
    
    return folium.plugins.DualMap(**kwargs)


def ipyleaflet_map_default(bbox, zoom=None, center=None, **kwargs):
    """
    Sensible defaults for a ipyleaflet map based on the bounding box of the image to be shown.
    """
    import ipyleaflet

    if zoom is None:
        zoom = zoom_from_bbox(bbox)
    if center is None:
        center = center_of_bbox(bbox)

    kwargs['zoom'] = zoom
    kwargs['center'] = center
    
    return ipyleaflet.Map(**kwargs)


def valid_data_mask(data):
    """
    Calculate valid data mask array for xarray dataset.
    """
    def mask_array(data_array):
        # adopted from odc.algo._rgba.to_rgba_np
        nodata = data_array.attrs.get('nodata')
        if data_array.dtype.kind == "f":
            valid = ~numpy.isnan(data_array)
            if nodata is not None:
                valid = valid & (data_array != nodata)
        elif nodata is not None:
            valid = data_array != nodata
        else:
            valid = np.ones(data_array.shape, dtype=bool)
            
        return valid
    
    var_names = list(data.data_vars)
    if var_names == []:
        raise ValueError("no data given")
    
    first, *rest = var_names
    mask = mask_array(data.data_vars[first])
    for other in rest:
        mask = mask & mask_array(data.data_vars[other])
    return mask


def apply_ows_style(data, ows_style_config=None):
    """
    Convert xarray dataset to a PNG image by applying the OWS style.
    """
    # inspired by odc.ui.mk_image_overlay
    # and https://datacube-ows.readthedocs.io/en/latest/styling_howto.html

    # get rid of the time dimension
    if "time" in data.dims:
        assert data.time.shape[0] == 1, "multiple observations not supported yet"
        data = data.isel(time=0)
    
    if ows_style_config is None:
        ows_style_config = RGB_CFG

    mask = valid_data_mask(data)
    xr_image = apply_ows_style_cfg(ows_style_config, data, valid_data_mask=mask)   
    return xarray_image_as_png(xr_image)
    

def folium_image_overlay(data, ows_style_config=None, name=None):
    png_str = mk_data_uri(apply_ows_style(data, ows_style_config=ows_style_config), "image/png")
    return folium.raster_layers.ImageOverlay(png_str, bounds=xr_bounds(data), name=name)


def ipyleaflet_image_overlay(data, ows_style_config=None, layer_name="Image"):
    import ipyleaflet
    
    png_str = mk_data_uri(apply_ows_style(data, ows_style_config=ows_style_config), "image/png")
    return ipyleaflet.ImageOverlay(url=png_str, bounds=xr_bounds(data), layer_name=layer_name)


def folium_add_controls(fm, enable_fullscreen=True, enable_layers_control=False):
    if enable_fullscreen:
        folium.plugins.Fullscreen(position="topright", title="Fullscreen", title_cancel="Exit fullscreen").add_to(fm)
        
    if enable_layers_control:
        folium.LayerControl().add_to(fm)

        
def ipyleaflet_add_controls(im, enable_fullscreen=True, enable_layers_control=False):
    import ipyleaflet

    if enable_fullscreen:
        im.add_control(ipyleaflet.FullScreenControl())
    
    if enable_layers_control:
        im.add_control(ipyleaflet.LayersControl())


def bounding_box(data):
    return data.extent.to_crs(epsg4326).boundingbox
    

def folium_map(data,
               ows_style_config=None,
               enable_fullscreen=True,
               enable_layers_control=False,
               zoom_start=None,
               location=None,
               **folium_map_kwargs):
    """
    Puts an xarray Dataset with a single observation in time
    on to a `folium` map (see: https://python-visualization.github.io/folium/).

    Parameters
    ----------
    data : xarray Dataset
        A dataset with a single observation in time (or without a time dimension)
    ows_style_config : dict 
        Datacube OWS style configuration (see https://datacube-ows.readthedocs.io/en/latest/styling_howto.html)
    enable_fullscreen : bool
        Enable a Full Screen control on the map
    enable_layers_control : bool
        Enable a Layers control (that lists the layers to show/hide them)
    zoom_start : int
        The zoom level (default: a zoom layer that shows the whole dataset)
    location : (float, float)
        The location the starting view is centered on (default: center of the dataset bounds)

    Returns
    -------
    the newly created `folium` map
    """
    fm = folium_map_default(bounding_box(data), zoom_start=zoom_start, location=location, **folium_map_kwargs)

    folium_image_overlay(data, ows_style_config=ows_style_config).add_to(fm)
    
    folium_add_controls(fm, enable_fullscreen=enable_fullscreen, enable_layers_control=enable_layers_control)
    
    return fm


def folium_dual_map(left_data,
                    right_data,
                    left_ows_style=None,
                    right_ows_style=None,
                    enable_fullscreen=False,
                    enable_layers_control=False,
                    zoom_start=None,
                    location=None,
                    **folium_map_kwargs):
    """
    Puts two xarray datasets side-by-side for comparison
    on to a `folium` map (see: https://python-visualization.github.io/folium/).

    Parameters
    ----------
    data : xarray Dataset
        A dataset with a single observation in time (or without a time dimension)
    ows_style_config : dict 
        Datacube OWS style configuration (see https://datacube-ows.readthedocs.io/en/latest/styling_howto.html)
    enable_fullscreen : bool
        Enable a Full Screen control on the map
    enable_layers_control : bool
        Enable a Layers control (that lists the layers to show/hide them)
    zoom_start : int
        The zoom level (default: a zoom layer that shows the whole dataset)
    location : (float, float)
        The location the starting view is centered on (default: center of the dataset bounds)

    Returns
    -------
    the newly created `folium` map
    """
    
    fm = folium_dualmap_default(bounding_box(left_data), zoom_start=zoom_start, location=location, **folium_map_kwargs)

    left_layer = folium_image_overlay(left_data, ows_style_config=left_ows_style, name="left")
    right_layer = folium_image_overlay(right_data, ows_style_config=right_ows_style, name="right")
    
    left_layer.add_to(fm.m1)
    right_layer.add_to(fm.m2)    

    folium_add_controls(fm, enable_fullscreen=enable_fullscreen, enable_layers_control=enable_layers_control)

    return fm
    

def ipyleaflet_map(data,
                   ows_style_config=None,
                   enable_fullscreen=True,
                   enable_layers_control=False,
                   zoom=None,
                   center=None,
                   **ipyleaflet_map_kwargs):
    """
    Puts two xarray datasets side-by-side for comparison
    on to a `ipyleaflet` map.

    Parameters
    ----------
    data : xarray Dataset
        A dataset with a single observation in time (or without a time dimension)
    ows_style_config : dict 
        Datacube OWS style configuration (see https://datacube-ows.readthedocs.io/en/latest/styling_howto.html)
    enable_fullscreen : bool
        Enable a Full Screen control on the map
    enable_layers_control : bool
        Enable a Layers control (that lists the layers to show/hide them)
    zoom_start : int
        The zoom level (default: a zoom layer that shows the whole dataset)
    location : (float, float)
        The location the starting view is centered on (default: center of the dataset bounds)

    Returns
    -------
    the newly created `ipyleaflet` map
    """
    import ipyleaflet

    im = ipyleaflet_map_default(bounding_box(data), zoom=zoom, center=center, **ipyleaflet_map_kwargs)

    layer = ipyleaflet_image_overlay(data, ows_style_config=ows_style_config)
    im.add_layer(layer)

    ipyleaflet_add_controls(im, enable_fullscreen=enable_fullscreen, enable_layers_control=enable_layers_control)

    return im
