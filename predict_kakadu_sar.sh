#!/bin/bash
#PBS -P r78 
#PBS -q hugemem
#PBS -N kakaduSAR_predict
#PBS -l walltime=5:00:00
#PBS -l mem=500GB
#PBS -l ncpus=7
#PBS -l wd
#PBS -M richard.taylor@ga.gov.au
#PBS -m abe


module use /g/data/v10/public/modules/modulefiles/
module load dea

python bigpredict_kakadu.py
