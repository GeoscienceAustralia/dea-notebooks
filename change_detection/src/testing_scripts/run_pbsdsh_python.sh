#!/bin/bash

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

INPUT=$1
echo $INPUT
python3 -u -vv irrigatedExtent_NMDB_parallel.py ${INPUT} > ${PBS_TASKNUM}.log


