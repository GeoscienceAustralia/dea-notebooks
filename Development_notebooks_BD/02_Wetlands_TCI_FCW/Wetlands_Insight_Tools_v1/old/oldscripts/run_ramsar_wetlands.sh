#!/bin/bash
#PBS -P r78 
#PBS -q express 
#PBS -N ramsar
#PBS -l walltime=24:00:00
#PBS -l mem=64GB
#PBS -l jobfs=1GB
#PBS -l ncpus=32
#PBS -l wd
#PBS -M bex.dunn@ga.gov.au
#PBS -m abe


#NNODES=16
NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
NCPUS=16
JOBDIR=$PWD

for i in $(seq 0 $(($NNODES-1))); do
    if [ $i -lt 1 ]
    then
        PARAMF="{1..16}"
    else
        PARAMF="{17..32}"
    fi
    pbsdsh -n $(( $NCPUS*$i )) -- \
    bash -l -c "\
    module use /g/data/v10/public/modules/modulefiles/;\
    module load dea;\
    module load parallel;\
    echo $i:\
    cd $JOBDIR;\
    parallel --delay 5 --retries 3 --load 100%  --colsep ' ' python /g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/05_Temporal_analysis/raijinify_wetland_working/Wetlands_asset_raijin.py ::: $PARAMF"&
done;
wait;
