#!/bin/bash
#PBS -P r78
#PBS -l walltime=00:30:00
#PBS -l mem=400GB
#PBS -l ncpus=7
#PBS -l jobfs=100GB
#PBS -q hugemem
#PBS -l wd

SCRIPT=./run_python.sh
INPUTS=./maxNDVItiffFiles.txt

module load parallel/20150322

parallel -j ${PBS_NCPUS} pbsdsh -n {%} -- bash -l -c "'${SCRIPT} {}'" :::: ${INPUTS} 
