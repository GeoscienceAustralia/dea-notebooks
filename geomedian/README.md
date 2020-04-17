Instructions:
=============

## Step 2: run for the whole continent

single-thread database scrape:

    module add dea/unstable
    cat allcells | while read i j ; do datacube-stats --save-tasks tasks/task_$i\_$j --tile-index $i $j config.yaml ; echo $(date) $i $j ; done 


partition tasks into a job array:

    split -n l/20 -d allcells parts/part


submit job array: 

    for i in $(seq -f %02g 0 19); do qsub -v inputfile=parts/part$i job.pbs ; done

## Step 0: preparation

 - log into Gadi, do not run these commands from VDI (to ensure the tasks are saved/loaded by exactly identical `datacube-stats` versions/environments). A Gadi login node works fine.
 - if you have previously used DEA from VDI and not Gadi, you will need to copy the relevant line in your `~/.pgpass` across (and set permissions appropriately), or else incur database errors upon module load.
 - put `module use /g/data/v10/modules/modulefiles/` at the end of your `~/.bash_profile` on Gadi. (And then log in anew. But beware that if this file breaks then you can't log in at all, so maybe check that you can log in from a different terminal window, before logging out from the one that modified it.)
 
Note, the `config.yaml` has been optimised for Gadi, particularly in terms of the compute chunk size. 
The `job.pbs` has then similarly been optimised (to better maximise the number of parallel concurrent tiles done on a single node, without exceeding the available memory). If changing the statistic, it might be a good idea to run one tile (from an *inland* location with high observation frequency) on Gadi interactive worker node, to re-ascertain the memory usage (per tile), and adjust the level of parallelism accordingly.

## Step 1: check it is working

After loading the module, try processing just one tile.

    datacube-stats --save-tasks tasks/task_16_-40 --tile-index 16 -40 config.yaml

then, either

    datacube-stats --load-tasks tasks/task_16_-40 config.yaml
    
or

    cat > dummylist << EOF
    16 -40
    EOF
    qsub -v inputfile dummylist job.pbs
    
The former option will probably get killed on a Gadi login node. 
The latter option will produce some `geomedian.e/o####` files when it finishes, containing any errors/warnings.

## Step 3: Verify quality 

This step may be more efficiently conducted on VDI.

Check that the output folder contains many `.nc` files.

Look at some in QGIS. When specifying the raster path to QGIS, may need to prepend `NetCDF:` and append `:red` (or another band) to get QGIS to tolerate the NetCDF format.

Then use GDAL tools to mosaic into a virtual raster, and generate a pyramid, so that the entire continental image can be glanced at in QGIS. The commands resemble are similar but different to:

    find output -iname \*.tif | xargs gdalbuildvrt geomedian.vrt
    gdaladdo geomedian.vrt -ro --config BIGTIFF_OVERVIEW YES --config SPARSE_OK TRUE --config COMPRESS_OVERVIEW LZW --config NUM_THREADS ALL_CPUS

