import logging
import sys
from shapely.geometry import mapping, shape
from fiona import collection

def bufferFix(shp):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    with collection(shp, "r") as input:
        schema = input.schema.copy()
        with collection(
                "with-shapely.shp", "w", "ESRI Shapefile", schema
                ) as output:
            for f in input:
                try:
                    # Make a shapely object from the dict.
                    geom = shape(f['geometry'])
                    if not geom.is_valid:
                        # Use the 0-buffer polygon cleaning trick
                        clean = geom.buffer(0.0)
                        assert clean.geom_type == 'MultiPolygon'
                        assert clean.is_valid
                        geom = clean
                        return geom
                    
                except Exception:
                    # Writing uncleanable features to a different shapefile
                    # is another option.
                    logging.exception("Error cleaning feature %s:", f['id'])