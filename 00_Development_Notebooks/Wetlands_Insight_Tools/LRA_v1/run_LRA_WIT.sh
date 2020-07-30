#!/bin/bash
#PBS -P r78 
#PBS -q megamem 
#PBS -N LRA-1
#PBS -l walltime=24:00:00
#PBS -l mem=9TB
#PBS -l jobfs=2400GB
#PBS -l ncpus=96
#PBS -l wd
#PBS -M bex.dunn@ga.gov.au
#PBS -m abe


#NNODES=2
NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
NCPUS=32 #number of cpus per node in this queue
NCHUNKS=270 #number of chunks in script
JOBDIR=$PWD

for i in $(seq 0 $(($NNODES-1))); do
    if [ $i -lt 1 ]
    then
        PARAMF="{1..89},$NCHUNKS"
    elif [$i -lt 2]
    then
        PARAMF="{89..179},$NCHUNKS"
    else 
        PARAMF="{180..270},$NCHUNKS" 
    fi
    pbsdsh -n $(( $NCPUS*$i )) -- \
    bash -l -c "\
    module use /g/data/v10/public/modules/modulefiles/;\
    module load dea;\
    module load parallel;\
    echo $i:\
    cd $JOBDIR;\
    parallel --delay 5 --retries 3 --load 100%  --colsep ',' python /g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/05_Temporal_analysis/raijinify_wetland_working/LRA_v1/LRA_WIT_raijin.py ::: $PARAMF"&
done;
wait;
