#!/bin/bash
#PBS -P r78 
#PBS -N dams2
#PBS -q express
#PBS -l walltime=24:00:00
#PBS -l mem=64GB
#PBS -l jobfs=1GB
#PBS -l ncpus=32
#PBS -l wd
#PBS -M vanessa.newey@ga.gov.au
#PBS -m abe


#NNODES=16
NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
NCPUS=16
JOBDIR=$PWD

for i in $(seq 0 $(($NNODES-1))); do
    if [ $i -lt 1 ]
    then
        PARAMF="{33..48}"
    else
        PARAMF="{49..64}"
    fi
    pbsdsh -n $(( $NCPUS*$i )) -- \
    bash -l -c "\
    module use /g/data/v10/public/modules/modulefiles/;\
    module load dea;\
    module load parallel;\
    echo $i:\
    cd $JOBDIR;\
    parallel --delay 5 --retries 3 --load 100%  --colsep ' ' python /g/data/r78/vmn547/Dams/Dams_scripts/RaijinGetDamTimeHistory.py ::: $PARAMF"&
done;
wait;
