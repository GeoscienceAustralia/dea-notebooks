
#!/bin/bash
# cd /g/data1a/r78/cb3058/dea-notebooks/vegetation_anomalies/dcstats/
# module use /g/data/v10/public/modules/modulefiles/
# module load dea

export PYTHONPATH="/g/data/r78/datacube_stats/":"$PYTHONPATH"

datacube-stats --qsub="project=r78,nodes=1,walltime=8h,mem=large,queue=express" SON_MSAVI.yaml --workers-per-node=8