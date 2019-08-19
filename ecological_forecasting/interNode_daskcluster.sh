#!/bin/bash
#PBS -P u46 
#PBS -q hugemem
#PBS -l walltime=8:00:00
#PBS -l mem=1024GB
#PBS -l jobfs=1GB
#PBS -l ncpus=28
#PBS -l wd

NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
NCPUS=28
MEM=1024
JOBDIR=$PWD
QUERY_THREAD=10
DASKWORKERDIR=$JOBDIR/dask-workers
DASKSCHEDULER=$JOBDIR/scheduler.json
if [ -s $DASKSCHEDULER ]
then
    rm $DASKSCHEDULER
fi 

if [ -d $DASKWORKERDIR ]
then
    rm -fr $DASKWORKERDIR
fi
mkdir $DASKWORKERDIR

#build a dask cluster (#.bashrc is where the module load dea enviro is done, each node must have same python enviro. )
for i in $(seq 0 $(( NNODES-1 ))); do
    mkdir $DASKWORKERDIR/$i
    if [[ $i -eq 0 ]]
    then
        pbsdsh -n $i -- \
        bash -l -c "\
        source $HOME/.bashrc; cd $JOBDIR;\
        dask-scheduler --port 9999 --scheduler-file $DASKSCHEDULER --local-directory $DASKWORKERDIR --no-dashboard;"& 
        pbsdsh -n $(( i+1 )) -- \
        bash -l -c "\
        source $HOME/.bashrc; cd $JOBDIR;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $QUERY_THREAD --name query --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES/2 ))GB --no-dashboard;"&
        pbsdsh -n $(( i+1+QUERY_THREAD )) -- \
        bash -l -c "\
        source $HOME/.bashrc; cd $JOBDIR;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $(( NCPUS-1-QUERY_THREAD )) --name general_$i --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES/2 ))GB --no-dashboard"& 
    else
        pbsdsh -n $(( i*NCPUS )) -- \
        bash -l -c "\
        source $HOME/.bashrc; cd $JOBDIR;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $NCPUS --name general_$i --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES ))GB --no-dashboard"&
    fi
done;


#run the job
datacube-stats-raijin -E c3-samples -vvv --tile-index-file landsat_tiles.txt --year 2015 --query-workers $QUERY_THREAD --queue-size $(( QUERY_THREAD*2 ))  gm_virtual.yaml

#kill the scheduler
pbsdsh -n 0 -- \
bash -l -c "\
pgrep 'dask-scheduler' | xargs kill -9;\
pgrep 'dask-worker' | xargs kill -9;\
rm $JOBDIR/scheduler.json"

wait
