#!/bin/bash
#PBS -P r78 
#PBS -q hugemem 
#PBS -N 4wb_h_missing
#PBS -l walltime=24:00:00
#PBS -l mem=1TB
#PBS -l jobfs=50GB
#PBS -l ncpus=28
#PBS -l wd
#PBS -M claire.krause@ga.gov.au
#PBS -m abe

NCHUNKS=168
CONFIG=config.ini
PROCESSED=processed.txt
SIZE=all
JOBDIR=$PWD

module use /g/data/v10/public/modules/modulefiles/
module load dea
module load parallel

cd $JOBDIR;
parallel --delay 5 --retries 3 --load 100%  --colsep ',' python /g/data/r78/vmn547/Dams/Dams_scripts/RaijinGetWBTimeHistory.py ::: $CONFIG,{85..112},$NCHUNKS,$SIZE,missing,$PROCESSED

wait;
