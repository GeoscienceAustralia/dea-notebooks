#!/bin/bash
module load gsl
export OMP_NUM_THREADS=8
/g/data/r78/cb3058/dea-notebooks/crop-extents/suburbchange /g/data/r78/cb3058/dea-notebooks/crop-extents/data_dir griffith 2000 2018 
