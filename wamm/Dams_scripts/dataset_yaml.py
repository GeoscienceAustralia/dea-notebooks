"""
Ingest training data from the command-line.
"""

import uuid
import os
import rasterio
import glob
import click
import yaml
import logging

def get_projection(path):
   with rasterio.open(str(path)) as img:
       left, bottom, right, top = img.bounds
       return {
           'spatial_reference': str(getattr(img, 'crs_wkt', None) or img.crs.wkt),
           'geo_ref_points': {
               'ul': {'x': left, 'y': top},
               'ur': {'x': right, 'y': top},
               'll': {'x': left, 'y': bottom},
               'lr': {'x': right, 'y': bottom},
           }
       }


def prep_dataset(path):
   #left, right, top, bottom
   with rasterio.open(str(path)) as img:
       left, bottom, right, top = img.bounds

   creation_dt='2016-04-26T00:00:00'

   doc = {
       'id': str(uuid.uuid4()),
       'product_type': 'dsm',
       'creation_dt': creation_dt,
       'extent': {
           'coord':{
               'ul':{'lon': left,  'lat': top},
               'ur':{'lon': right, 'lat': top},
               'll':{'lon': left,  'lat': bottom},
               'lr':{'lon': right, 'lat': bottom},
           },
           'from_dt': creation_dt,
           'to_dt': creation_dt,
           'center_dt': creation_dt
       },
       'format': {'name': 'GeoTiff'},
       'grid_spatial': {
           'projection': {
               'spatial_reference': str(getattr(img, 'crs_wkt', None) or img.crs.wkt),
               'geo_ref_points': {
                   'ul': {'x': left, 'y': top},
                   'ur': {'x': right, 'y': top},
                   'll': {'x': left, 'y': bottom},
                   'lr': {'x': right, 'y': bottom},
               }
        }
       },
       'image': {
           'bands': {
        'band1': {
            'path': path,
            'layer': 1
        },
        'band2': {
            'path': path,
            'layer': 2
        },
        'band3': {
            'path': path,
            'layer': 3
        }
         }
       },
       'lineage': {
           'source_datasets': {}
       }
   }
   return doc



@click.command(help="Prepare DSM data for wofs.")
@click.argument('dataloc',
               type=click.Path(exists=True, readable=True),
               nargs=-1)

@click.option('--output', required=True, help="Write datasets into this file",
             type=click.Path(exists=False, writable=True, dir_okay=False))


def main(dataloc, output):
   with open(output, 'w') as stream:
       yaml.dump_all((prep_dataset(path) for path in glob.glob(str(dataloc[0])+'*.tif')), stream)


if __name__ == "__main__":
   main()