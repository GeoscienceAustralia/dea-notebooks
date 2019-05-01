
#!/bin/bash
cd /g/data1a/r78/cb3058/dea-notebooks/dcStats/
module use /g/data/v10/public/modules/modulefiles/
module load dea

export PYTHONPATH="/g/data1a/r78/datacube_stats/":"$PYTHONPATH"

# datacube-stats --qsub="project=r78,nodes=2,walltime=5h,mem=small,queue=express" barwon_DCstats.yaml --workers-per-node=5

datacube-stats --qsub="project=r78,nodes=2,walltime=2h,mem=medium,queue=express" mdbNSW_DCstats_summer.yaml --workers-per-node=10





