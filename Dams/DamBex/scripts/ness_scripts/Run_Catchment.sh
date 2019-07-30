#!/bin/bash
#PBS -P r78
#PBS -q express
#PBS -l walltime=10:00:00
#PBS -l mem=64GB
#PBS -l jobfs=1GB
#PBS -l ncpus=16
#PBS -l wd
#PBS -N Catch
 
module use /g/data/v10/public/modules/modulefiles/
module load dea

PYTHONPATH=$PYTHONPATH:/g/data/r78/cek156/dea-notebooks

python /g/data/r78/cek156/dea-notebooks/NRMAustralia/QLD_DAF/WOFSCountCatchmentExtraction.py
