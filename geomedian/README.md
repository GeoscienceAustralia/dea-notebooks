Instructions:
=============


# single-thread database scrape:

module add dea/unstable
cat allcells | while read i j ; do datacube-stats --save-tasks tasks/task_$i\_$j --tile-index $i $j config.yaml ; echo $(date) $i $j ; done 


# partition tasks into a job array:

split -n l/20 -d allcells parts/part


# submit job array: 

for i in $(seq -f %02g 0 19); do qsub -v inputfile=parts/part$i job.pbs ; done


# Verify quality (most efficient on VDI)

#find output -iname \*.tif | xargs gdalbuildvrt geomedian.vrt


gdaladdo geomedian.vrt -ro --config BIGTIFF_OVERVIEW YES --config SPARSE_OK TRUE --config COMPRESS_OVERVIEW LZW --config NUM_THREADS ALL_CPUS




The .geotiff files represent an alternative approach that was also experimented with.
