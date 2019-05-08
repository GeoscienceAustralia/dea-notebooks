#!/bin/bash
module load gsl
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/load_landsat_data_wagga.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/create_tsmask_wagga.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/create_indices_wagga.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/create_clusters_wagga.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/map_raw_class_wagga.sh
/g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir/wagga/urban_change_wagga.sh
