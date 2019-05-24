#!/bin/bash
#PBS -P r78 
#PBS -q express 
#PBS -N wb_append
#PBS -l walltime=04:00:00
#PBS -l mem=16GB
#PBS -l jobfs=1GB
#PBS -l ncpus=8
#PBS -l wd
#PBS -M vanessa.newey@ga.gov.au
#PBS -m abe

module use /g/data/v10/public/modules/modulefiles/
module load dea
module load parallel

parallel --delay 2 --retries 3 --load 100%  --colsep ',' python /g/data/r78/vmn547/Dams/Dams_scripts/RaijinAppendWBTimeHistory.py ::: {1..8},8
wait;
