
#!/bin/bash
#PBS -P r78
#PBS -l walltime=2:00:00
#PBS -l mem=64GB
#PBS -l ncpus=16
#PBS -q express
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data1a/u46/users/cb3058/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python MaxNDVI_dcStatsMADS.py >& results_dcStatsMADS.log

