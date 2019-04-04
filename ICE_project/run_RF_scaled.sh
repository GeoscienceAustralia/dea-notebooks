#!/bin/bash
#PBS -P r78
#PBS -l walltime=3:00:00
#PBS -l mem=256GB
#PBS -l ncpus=14
#PBS -q expressbw
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data1a/r78/cb3058/dea-notebooks/ICE_project
module use /g/data/v10/public/modules/modulefiles/
module load dea/20181213

# python randomForest_scaled.py > RFscaled_allClasses.log

python applyRFmodel_scaled.py > applyRF_2015.log
