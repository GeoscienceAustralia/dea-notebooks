#!/bin/bash
#PBS -P r78
#PBS -l walltime=2:00:00
#PBS -l mem=3TB
#PBS -l ncpus=32
#PBS -q megamem
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/sica_paper/
module use /g/data/v10/public/modules/modulefiles/
module load dea

python3 9_summary_tiffs.py