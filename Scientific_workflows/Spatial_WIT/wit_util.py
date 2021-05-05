from shapely import geometry
import awswrangler as wr
from datacube.virtual.impl import VirtualDatasetBox

def load_wit_s3(geom, db_name, table_name, session):
    """
    load wit from s3
    input:
        geom: geometry of polygon
        db_name: the `category` on aws where the table_name exits
        table_name: a table to store the metadata from parquet files
        session: boto3 session instance
    output:
        wit data in pd.DataFrame
    """
    polygon = geometry.shape(geom).convex_hull
    data = wr.athena.read_sql_query("select time, 100*bs as bs, 100*npv as npv, 100*pv as pv, 100*wet as wet, 100*water as water from %s where time > cast('1987-01-01' as timestamp) and ST_Equals('%s', geometry)" % (table_name, polygon.to_wkt()),
                         database=db_name,boto3_session=session)
    return data

def load_wofs_fc_c3(fc_product, grouped, time_slice):
    """
    Load cloud free wofs, TCW and FC data with the given time or a tuple of (start_time, end_time)
    input:
    fc_product: virtual product instance
    grouped: grouped datasets
    time_slice: a single time or tuple of (start_time, end_time)
    output:
    wofs, TCW and FC data: xr.Dataset
    """
    if not (isinstance(time_slice, list) or isinstance(time_slice, tuple)):
        time_slice = [time_slice]
    to_load = VirtualDatasetBox(grouped.box.loc[time_slice], grouped.geobox,
                                grouped.load_natively, grouped.product_definitions, grouped.geopolygon)
    fc_wofs_data = fc_product.fetch(to_load)
    return fc_wofs_data