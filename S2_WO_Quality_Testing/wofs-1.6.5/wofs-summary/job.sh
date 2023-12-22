#!/bin/env bash
#PBS -l ncpus=16,mem=32GB,walltime=15:00:00,wd
#PBS -P v10
#PBS -N wofs
#PBS -q normal

module load agdc-py3-prod/1.5.2


/usr/bin/time xargs -n1 -P32 -I{} --verbose sh -c "if [ ! -e done.{} ] && [ ! -e failed.{} ] ; then /usr/bin/time python simple.py /g/data/v10/testing_ground/wofs_summary/wofs_{}_ /g/data/v10/testing_ground/wofs_brl/output/*/{} && touch done.{} || (echo $? > failed.{}) ; fi" < subset.$PBS_ARRAY_INDEX


# Usage:
#
# sort -R cells.list | split -l 264 -d -a1 - subset.
# 
# for i in {0..4} ; do qsub -v PBS_ARRAY_INDEX=$i -N wofs.$i job.sh ; done
#
#

