#!/bin/bash
#PBS -P r78 
#PBS -q hugemem 
#PBS -N CKval
#PBS -l walltime=6:00:00
#PBS -l mem=1TB
#PBS -l jobfs=400GB
#PBS -l ncpus=28
#PBS -l wd
#PBS -M bex.dunn@ga.gov.au
#PBS -m abe


#NNODES=1
NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
NCPUS=28 #number of cpus per node in this queue
NCHUNKS=3 #number of chunks in script
JOBDIR=$PWD

for i in $(seq 0 $(($NNODES-1))); do
    if [ $i -lt 1 ]
    then
        PARAMF="{1..70},$NCHUNKS"
    #elif [$i -lt 2]
    #then
    #    PARAMF="{24..46},$NCHUNKS"
    #else 
    #    PARAMF="{47..70},$NCHUNKS" 
    fi
    pbsdsh -n $(( $NCPUS*$i )) -- \ 
    bash -l -c "\
    module use /g/data/v10/public/modules/modulefiles/;\
    module load dea;\
    module load parallel;\
    echo $i:\
    cd $JOBDIR;\
    parallel --delay 5 --retries 3 --load 100%  --colsep ',' python /g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/05_Temporal_analysis/raijinify_wetland_working/For_CK/CK_val_raijin.py ::: $PARAMF"&
done;
wait;
