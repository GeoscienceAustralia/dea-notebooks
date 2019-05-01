
#!/bin/bash
#PBS -P r78
#PBS -l walltime=36:00:00
#PBS -l mem=1TB
#PBS -l ncpus=14
#PBS -q hugemem
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python irrigatedExtent_NMDB_parallel.py > irrigatedExtent_NMDB_parallel.log
