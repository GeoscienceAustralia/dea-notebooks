
#!/bin/bash
#PBS -P r78
#PBS -l walltime=1:00:00
#PBS -l mem=64GB
#PBS -l ncpus=14
#PBS -q expressbw
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

module load parallel

parallel --delay 5 -a renmark_maxNDVItiffFiles.txt python3 workaround_IE_parallel_renmark.py
wait;

# python irrigatedExtent_NMDB_parallel.py > irrigatedExtent_NMDB_parallel.log

#parallel python irrigatedExtent_NMDB_parallel.py ::: maxNDVItiffFiles.txt
#wait;

