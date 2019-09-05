#!/bin/bash

# # Option 1: default option for smaller waterbodies with low memory requirements
# PBS="#!/bin/bash\n\
# #PBS -N CustomisableTemporalWaterAnalysis\n\
# #PBS -o PBS_output.out\n\
# #PBS -e PBS_output.err\n\
# #PBS -P r78\n\
# #PBS -q normal\n\
# #PBS -l walltime=24:00:00\n\
# #PBS -l mem=128GB\n\
# #PBS -l jobfs=2GB\n\
# #PBS -l ncpus=7\n\
# #PBS -l wd\n\
# module use /g/data/v10/public/modules/modulefiles\n\
# module load dea\n\
# python /g/data/r78/rt1527/dea-notebooks/05_Temporal_analysis/CustomisableTemporalWaterAnalysis.py"

# Option 2: express queue for prototyping code for smaller waterbodies with low memory requirements 
PBS="#!/bin/bash\n\
#PBS -N CustomisableTemporalWaterAnalysis\n\
#PBS -o PBS_output.out\n\
#PBS -e PBS_output.err\n\
#PBS -P r78\n\
#PBS -q express\n\
#PBS -l walltime=24:00:00\n\
#PBS -l mem=128GB\n\
#PBS -l jobfs=2GB\n\
#PBS -l ncpus=7\n\
#PBS -l wd\n\
module use /g/data/v10/public/modules/modulefiles\n\
module load dea\n\
python /g/data/r78/rt1527/dea-notebooks/05_Temporal_analysis/CustomisableTemporalWaterAnalysis.py"

# # Option 3: for very large waterbodies that require extremely high memory (e.g. 1TB)
# PBS="#!/bin/bash\n\
# #PBS -N CustomisableTemporalWaterAnalysis\n\
# #PBS -o PBS_output.out\n\
# #PBS -e PBS_output.err\n\
# #PBS -P r78\n\
# #PBS -q hugemem\n\
# #PBS -l walltime=24:00:00\n\
# #PBS -l mem=1TB\n\
# #PBS -l jobfs=2GB\n\
# #PBS -l ncpus=7\n\
# #PBS -l wd\n\
# module use /g/data/v10/public/modules/modulefiles\n\
# module load dea\n\
# python /g/data/r78/rt1527/dea-notebooks/05_Temporal_analysis/CustomisableTemporalWaterAnalysis.py"

echo -e ${PBS} | qsub
echo "Submitting job"
