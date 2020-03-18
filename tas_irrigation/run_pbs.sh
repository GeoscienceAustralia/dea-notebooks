#!/bin/bash
#PBS -P r78
#PBS -l walltime=5:00:00
#PBS -l mem=1TB
#PBS -l ncpus=7
#PBS -q hugemem
#PBS -l wd
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/tas_irrigation/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python3 range.py

