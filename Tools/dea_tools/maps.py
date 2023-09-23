import folium
import folium.plugins        

from odc.ui import image_aspect, mk_data_uri, to_png_data, mk_image_overlay, zoom_from_bbox
from odc.algo import to_rgba
from datacube.testutils.geom import epsg4326
        
# TODO favor datacube OWS style config over the ad hoc (clamp, bands) settings

def folium_map_default(bbox, zoom_start=None, location=None, **kwargs):
    """
    Sensible defaults for a map based on the bounding box of the image to be shown.
    """
    if zoom_start is None:
        zoom_start = zoom_from_bbox(bbox)
    if location is None:
        location = (bbox.bottom + bbox.top) * 0.5, (bbox.right + bbox.left) * 0.5

    kwargs['zoom_start'] = zoom_start
    kwargs['location'] = location
    
    return folium.Map(**kwargs)


def ipyleaflet_map_default(bbox, zoom=None, center=None, **kwargs):
    """
    Sensible defaults for a map based on the bounding box of the image to be shown.
    """
    # this is an optional dependency
    import ipyleaflet

    if zoom is None:
        zoom = zoom_from_bbox(bbox)
    if center is None:
        center = (bbox.bottom + bbox.top) * 0.5, (bbox.right + bbox.left) * 0.5

    kwargs['zoom'] = zoom
    kwargs['center'] = center
    
    return ipyleaflet.Map(**kwargs)


def folium_image_overlay(data, bounds, clamp=None, bands=('red', 'green', 'blue'), name=None):
    # this is a partial port of odc.ui.mk_image_overlay
    # too bad that function returns an ipyleaflet.ImageOverlay but we need the folium one
    rgba = to_rgba(data, clamp=clamp, bands=bands)
    png_str = mk_data_uri(to_png_data(rgba.values), "image/png")
    return folium.raster_layers.ImageOverlay(png_str, bounds=bounds, name=name)
    

def folium_map(data,
               clamp=None,
               bands=('red', 'green', 'blue'),
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
    TODO: ...

    Returns
    -------
    the newly created `folium` map
    """

    # get rid of the time dimension
    if "time" in data.dims:
        assert data.time.shape[0] == 1, "multiple observations not supported yet"
        data = data.isel(time=0)

    for band in bands:
        assert band in data, f"band {band} is not found in dataset"

    bbox = data.extent.to_crs(epsg4326).boundingbox
    bounds = ((bbox.top, bbox.left), (bbox.bottom, bbox.right))

    fm = folium_map_default(bbox, zoom_start=zoom_start, location=location, **folium_map_kwargs)

    folium_image_overlay(data, bounds, clamp=clamp, bands=bands).add_to(fm)
    
    if enable_fullscreen:
        folium.plugins.Fullscreen(position="topright", title="Fullscreen", title_cancel="Exit fullscreen").add_to(fm)
        
    if enable_layers_control:
        folium.LayerControl().add_to(fm)

    return fm


def folium_sidebyside_map(left_data,
                          right_data,
                          left_clamp=None,
                          left_bands=('red', 'green', 'blue'),
                          right_clamp=None,
                          right_bands=('red', 'green', 'blue'),
                          enable_fullscreen=True,
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
    TODO: ...

    Returns
    -------
    the newly created `folium` map
    """

    # get rid of the time dimension
    if "time" in left_data.dims:
        assert left_data.time.shape[0] == 1, "multiple observations not supported yet"
        left_data = left_data.isel(time=0)

    if "time" in right_data.dims:
        assert right_data.time.shape[0] == 1, "multiple observations not supported yet"
        right_data = right_data.isel(time=0)

    for band in left_bands:
        assert band in left_data, f"band {band} is not found in left dataset"
        
    for band in right_bands:
        assert band in right_data, f"band {band} is not found in right dataset"

    bbox = left_data.extent.to_crs(epsg4326).boundingbox
    bounds = ((bbox.top, bbox.left), (bbox.bottom, bbox.right))

    fm = folium_map_default(bbox, zoom_start=zoom_start, location=location, **folium_map_kwargs)

    left_layer = folium_image_overlay(left_data, bounds, clamp=left_clamp, bands=left_bands, name="left")
    right_layer = folium_image_overlay(right_data, bounds, clamp=right_clamp, bands=right_bands, name="right")
    
    left_layer.add_to(fm)
    right_layer.add_to(fm)    

    sbs = folium.plugins.SideBySideLayers(left_layer, right_layer)
    sbs.add_to(fm)
    
    if enable_fullscreen:
        folium.plugins.Fullscreen(position="topright", title="Fullscreen", title_cancel="Exit fullscreen").add_to(fm)
        
    if enable_layers_control:
        folium.LayerControl().add_to(fm)

    return fm


def ipyleaflet_map(data,
                   clamp=None,
                   bands=('red', 'green', 'blue'),
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
    TODO: ...

    Returns
    -------
    the newly created `ipyleaflet` map
    """
    # this is an optional dependency
    import ipyleaflet

    for band in bands:
        assert band in data, f"band {band} is not found in left dataset"

    bbox = data.extent.to_crs(epsg4326).boundingbox
    bounds = ((bbox.top, bbox.left), (bbox.bottom, bbox.right))

    im = ipyleaflet_map_default(bbox, zoom=zoom, center=center, **ipyleaflet_map_kwargs)

    layer = mk_image_overlay(data, clamp=clamp, bands=bands)
    
    im.add_layer(layer)

    if enable_fullscreen:
        im.add_control(ipyleaflet.FullScreenControl())
    
    if enable_layers_control:
        im.add_control(ipyleaflet.LayersControl())

    return im


def ipyleaflet_split_map(left_data,
                         right_data,
                         left_clamp=None,
                         left_bands=('red', 'green', 'blue'),
                         right_clamp=None,
                         right_bands=('red', 'green', 'blue'),
                         enable_fullscreen=True,
                         enable_layers_control=True,
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
    TODO: ...

    Returns
    -------
    the newly created `ipyleaflet` map
    """
    # this is an optional dependency
    import ipyleaflet

    for band in left_bands:
        assert band in left_data, f"band {band} is not found in left dataset"
        
    for band in right_bands:
        assert band in right_data, f"band {band} is not found in right dataset"

    bbox = left_data.extent.to_crs(epsg4326).boundingbox
    bounds = ((bbox.top, bbox.left), (bbox.bottom, bbox.right))

    im = ipyleaflet_map_default(bbox, zoom=zoom, center=center, **ipyleaflet_map_kwargs)

    left_layer = mk_image_overlay(left_data, clamp=left_clamp, bands=left_bands, layer_name="left")
    right_layer = mk_image_overlay(right_data, clamp=right_clamp, bands=right_bands, layer_name="right")
    
    im.add_layer(left_layer)
    im.add_layer(right_layer)    
    
    smc = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    im.add_control(smc)

    if enable_fullscreen:
        im.add_control(ipyleaflet.FullScreenControl())
    
    if enable_layers_control:
        im.add_control(ipyleaflet.LayersControl())

    return im
