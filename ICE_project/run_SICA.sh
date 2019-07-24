#!/bin/bash
#PBS -P r78
#PBS -l walltime=2:00:00
#PBS -l mem=1TB
#PBS -l ncpus=7
#PBS -q hugemem
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python croppingFrequency.py

# module load parallel

# parallel --delay 5 -a nmdb_maxNDVItiffFiles.txt python3 SICA_parallel_nmdb.py
# wait;

# python change_threshold.py > change_threshold.log

