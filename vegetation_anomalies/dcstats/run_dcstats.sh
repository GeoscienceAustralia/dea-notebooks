#GADI--------
#!/bin/bash\n\
#PBS -P r78
#PBS -q normal
#PBS -l walltime=1:00:00
#PBS -l mem=192GB
#PBS -l jobfs=2GB
#PBS -l ncpus=8
#PBS -l wd
#PBS -M chad.burton@ga.gov.au
#PBS -l storage=gdata/v10+gdata/r78+gdata/xu18\n\


cd /g/data1a/r78/cb3058/dea-notebooks/vegetation_anomalies/dcstats/
module use /g/data/v10/public/modules/modulefiles/
module load dea

export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_refactor/datacube-stats/:$PYTHONPATH
export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_core/datacube-core/:$PYTHONPATH

datacube-stats -E c3-samples ndvi_climatology.yaml
# datacube-stats --qsub="project=r78,nodes=1,walltime=8h,mem=large,queue=express" SON_MSAVI.yaml --workers-per-node=8