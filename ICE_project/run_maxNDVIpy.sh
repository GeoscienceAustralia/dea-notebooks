
#!/bin/bash
#PBS -P r78
#PBS -l walltime=10:00:00
#PBS -l mem=96GB
#PBS -l ncpus=8
#PBS -q express
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea/20181213

python MaxNDVI_dcStats_MDB_newsegMethod.py > results_dcStats_MDB_newsegMethod.log
