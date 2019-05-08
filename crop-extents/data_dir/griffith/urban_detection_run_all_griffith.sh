#!/bin/bash
module load gsl
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/load_landsat_data_griffith.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/create_tsmask_griffith.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/create_indices_griffith.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/create_clusters_griffith.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/map_raw_class_griffith.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/griffith/urban_change_griffith.sh
