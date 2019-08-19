#!/bin/bash
#PBS -P r78 
#PBS -q hugemem
#PBS -l walltime=5:00:00
#PBS -l mem=1TB
#PBS -l jobfs=2GB
#PBS -l ncpus=14
#PBS -l wd
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data1a/r78/cb3058/dea-notebooks/ecological_forecasting
module use /g/data/v10/public/modules/modulefiles/
module load dea

python seasonalMSAVI_anom_griffithTest.py

