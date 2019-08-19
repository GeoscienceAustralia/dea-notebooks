#for a minor qsub
#PBS -P r78
#PBS -l walltime=6:00:00
#PBS -l mem=96GB
#PBS -l ncpus=8
#PBS -q express
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/dcStats/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python3 vrt_and_mosaic_tiff.py


#starting an interactive node
#qsub -I -P r78 -q express -l walltime=1:00:00,mem=96GB,ncpus=8
    
# BELLE'S STUFF FOR RUNNING TASK FIRST ON THE VDI AND THEN RUNNING THE QUERY ON RAIJIN
# set which stats config to use & a tasks file to save to
# CONFIG=/g/data/u46/users/bt2744/work/code/datacube-stats/configurations/wofs/seasonal_stats.yaml
# TASK=task.pickle

# # run the save tasks
# datacube-stats -vvv --save-tasks $TASK --tile-index-file my_tiles $CONFIG

# # setup qsub command
# QSUB="project=u46,mem=medium,nodes=1,walltime=10h,queue=normal,name=wofs-seasonal"

# # run the load tasks 
# datacube-stats -vvv --qsub=$QSUB --load-tasks=$TASK --tile-index-file my_tiles $CONFIG
