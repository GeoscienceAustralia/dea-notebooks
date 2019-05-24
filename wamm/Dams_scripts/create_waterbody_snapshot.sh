#!/bin/bash
#PBS -P r78 
#PBS -q express 
#PBS -N nsw_snapshot
#PBS -l walltime=24:00:00
#PBS -l mem=16GB
#PBS -l jobfs=1GB
#PBS -l ncpus=1
#PBS -l wd
#PBS -M vanessa.newey@ga.gov.au
#PBS -m abe

module use /g/data/v10/public/modules/modulefiles/
module load dea
python /g/data/r78/vmn547/Dams/Dams_scripts/create_water_snapshot.py

