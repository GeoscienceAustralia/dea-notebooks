export > $HOME/.env.tmp
while [[ $1 != "" ]]; do
    case $1 in
        -q | --query_thread )    QUERY_THREAD=$2
            shift;;
        -c | --cpus )   NCPUS=$2 
            shift;;
        -m | --memoery ) MEM=$2 
            shift;;
        -j | --jobfs ) JOBDIR=$2
            shift;;
        * ) echo "Option $1 is not available"
            exit 1
    esac
    shift
done

echo "build a cluster cpu=$NCPUS mem=$MEM query=$QUERY_THREAD jobdir=$JOBDIR" 
NNODES=$(cat $PBS_NODEFILE | uniq | wc -l)
DASKSCHEDULER=$JOBDIR/scheduler.json
DASKWORKERDIR=$JOBDIR/dask-workers

if [ -s $DASKSCHEDULER ]
then
    rm $DASKSCHEDULER
fi 

if [ -d $DASKWORKERDIR ]
then
    rm -fr $DASKWORKERDIR
fi
mkdir $DASKWORKERDIR

#build a dask cluster
for i in $(seq 0 $(( NNODES-1 ))); do
    mkdir $DASKWORKERDIR/$i
    if [[ $i -eq 0 ]]
    then
        pbsdsh -n $i -- \
        bash -l -c "\
        source $HOME/.env.tmp;\
        dask-scheduler --port 9999 --scheduler-file $DASKSCHEDULER --local-directory $DASKWORKERDIR --no-dashboard;"&
        pbsdsh -n $(( i+1 )) -- \
        bash -l -c "\
        source $HOME/.env.tmp;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $QUERY_THREAD --name query --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES/2 ))GB --no-dashboard;"&
        pbsdsh -n $(( i+1+QUERY_THREAD )) -- \
        bash -l -c "\
        source $HOME/.env.tmp;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $(( NCPUS-1-QUERY_THREAD )) --name general_$i --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES/2 ))GB --no-dashboard"&
    else
        pbsdsh -n $(( i*NCPUS )) -- \
        bash -l -c "\
        source $HOME/.env.tmp;\
        dask-worker --scheduler-file $DASKSCHEDULER --nprocs 1 --nthreads $NCPUS --name general_$i --local-directory $DASKWORKERDIR/$i --memory-limit $(( MEM/NNODES ))GB --no-dashboard"&
    fi
done;
