#!/bin/bash
#PBS -l storage=gdata/v10+gdata/r78+gdata/xu18+gdata/u46+scratch/rs0+gdata/fk4+gdata/fr1+gdata/if87
#PBS -P r78 
#PBS -q express
#PBS -l walltime=3:00:00
#PBS -l mem=192GB
#PBS -l jobfs=2GB
#PBS -l ncpus=16
#PBS -l wd

#wd and module load
cd /g/data1a/r78/cb3058/dea-notebooks/vegetation_anomalies/dcstats/
module use /g/data/v10/public/modules/modulefiles/
module load dea

#point to our custom versions of dcstats and dc-core
export PYTHONUSERBASE=/g/data/r78/cb3058/python_lib
export PYTHONPATH=$PYTHONUSERBASE/lib/python3.6/site-packages:$PYTHONPATH
export PATH=$PYTHONUSERBASE/bin:$PATH

QUERY_THREAD=2
MEM=192
NCPUS=8
JOBDIR=/scratch/r78/$LOGNAME/tmp

./organize_cluster.sh -q $QUERY_THREAD -c $NCPUS -m $MEM -j $JOBDIR

#run the job
datacube-stats -E c3-samples -vvv --query-workers $QUERY_THREAD --queue-size $(( QUERY_THREAD*1 )) --scheduler-file $JOBDIR/scheduler.json ndvi_climatology.yaml

#kill the scheduler
pbsdsh -n 0 -- \
bash -l -c "\
pgrep 'dask-scheduler' | xargs kill -9;\
pgrep 'dask-worker' | xargs kill -9;\
rm $JOBDIR/scheduler.json"

wait
