
#!/bin/bash

cd /g/data1a/r78/cb3058/dea-notebooks/dcStats/
module use /g/data/v10/public/modules/modulefiles/
module load dea

export PYTHONPATH="/g/data1a/r78/datacube_stats/":"$PYTHONPATH"

datacube-stats --qsub="project=r78,nodes=3,walltime=24h,mem=medium,queue=normal" barwon_DCstats.yaml --workers-per-node=5

#qsub -I -P r78 -q express -l walltime=2:00:00,mem=64GB,ncpus=16




