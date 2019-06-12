#!/bin/bash
#PBS -P r78
#PBS -l walltime=00:30:00
#PBS -l mem=3070GB
#PBS -l ncpus=32
#PBS -q megamem
#PBS -l wd

SCRIPT=./run_python.sh
INPUTS=./maxNDVItiffFiles.txt

tiffiles=()
while read -r line; do
  tiffiles+=("$line")
done < ${INPUTS}


for node in $(seq 1 $PBS_NCPUS);do
  pbsdsh -n $((node)) -- bash -l -c "${PBS_O_WORKDIR}/run_pbsdsh_python.sh ${tiffiles[(node-1)]}" &
done

wait
