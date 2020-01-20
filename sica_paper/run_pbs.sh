#GADI--------
#!/bin/bash\n\
#PBS -P r78
#PBS -q express
#PBS -l walltime=6:00:00
#PBS -l mem=32GB
#PBS -l jobfs=2GB
#PBS -l ncpus=1
#PBS -l wd
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/sica_paper/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python python3 9_summary_tiffs.py