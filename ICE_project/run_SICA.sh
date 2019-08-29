#!/bin/bash
#PBS -P r78
#PBS -l walltime=1:00:00
#PBS -l mem=256GB
#PBS -l ncpus=14
#PBS -q expressbw
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea
module load parallel

parallel --delay 5 -a SA_MDB_tiffFiles.txt python3 SICA_parallel.py
wait;

# python change_threshold.py > change_threshold.log

# python croppingFrequency.py