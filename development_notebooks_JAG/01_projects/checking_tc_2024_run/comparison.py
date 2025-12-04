import time
import logging
import argparse
import os
import re
import s3fs
import xarray as xr
import numpy as np
from datacube.utils.aws import configure_s3_access

LOGGER = {}
S3FS = {}

##################
## Util Methods ##
##################

def parse_args():
    """
        Method for retrieving parameters required for this tool to run. the params can all be passed in on command line, or the user can just point to a file which contains them
    """
    parser = argparse.ArgumentParser(description="A tool for comparing products generated for tiles")
    parser.add_argument("--input", help="an input file to pull values from")
    parser.add_argument("--product1", help="the name of the first product")
    parser.add_argument("--product2",  help="the name of the second product, if not included the first product name will be used by both")
    parser.add_argument("--band", help="The band, etc, dev, nbart_blue, etc..., if none given all bands will be compared")
    parser.add_argument("--year", help="The year the products are encapsulating")
    parser.add_argument("--version", help="The verison")
    parser.add_argument("--product1-dir", help="The directory the first product is stored in")
    parser.add_argument("--product2-dir", help="The Directory the second products is stored in, if blank this will be set to same as the first")
    parser.add_argument("--output-dir",  help="The directory to save the report file, defaults to './report' of run dir")
    parser.add_argument("--folder-only", "-f", action="store_true", help="does a light check, comparing the subfolder combinations which describe a tile, e.g. x52/y34")
    parser.add_argument("--verbose", "-v", action="store_true", help="For fuller logging")
    
    args = parser.parse_args()

    hasFile = bool(args.input)

    hasRequiredParams = all([
        args.product1,
        args.year,
        args.version,
        args.product1_dir,
    ])

    hasAnyOtherParams = any([
        args.product1,
        args.product2,
        args.band,
        args.year,
        args.version,
        args.product1_dir,
        args.product2_dir,
        args.output_dir,
    ])

    # make sure user has given file OR required params, not both or neither
    if (not hasFile and not hasRequiredParams) or (hasFile and hasAnyOtherParams):
        parser.error("This tool requires either an '--input' value OR at least '--product1', '--year', '--version', '--product1-dir' of the other values")

    # values with defaults already populated
    values = {
        "band": "*",
        "output_dir": "./reports",
        "folder_only": args.folder_only,
        "verbose": args.verbose
    }

    if hasFile:
        # get values from file
        if not os.path.exists(args.input):
            parser.error(f"Input file not found: {args.input}")

        with open(args.input, "r") as f:
            for line in f:
                line = line.strip()

                # ignore blank lines, comments
                if not line or line.startswith("#"):
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                values[key] = value
    else:
        # get values from args
        for key, value in vars(args).items():
            if value != None:
                values[key] = value

    # make product2 & product dir2, if missing set to 1
    if not values.get("product2"):
        values["product2"] = values["product1"]
    if not values.get("product2_dir"):
        values["product2_dir"] = values["product1_dir"]

    return values

def configure_logging(verbose: bool):
    """
    Configure logging for the application.
    """
    global LOGGER
    LOGGER = logging.getLogger("Difference")
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.DEBUG if verbose else logging.INFO)

def configure_s3():
    """ configure S3 connection """
    global S3FS
    S3FS = s3fs.S3FileSystem(anon=True)
    configure_s3_access(cloud_defaults=True, aws_unsigned=False)
    LOGGER.debug("S3 configured")

def format_time(start: float, end: float) -> str:
    """
        Simple method for formatting a time period in ms into a human readable string using hours, minutes & seconds
    """
    elapsed = end - start
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = elapsed % 60

    result = f"{seconds:.2f}s"
    if minutes > 0:
        result = f"{minutes}m " + result
    if hours > 0:
        result = f"{hours}h " + result

    return result

def get_band_label(band: str) -> str:
    """ A simple method for formatiing the band for display/reporting. useful is the band is '*' which means all bands """
    return band if band != '*' else 'all'

def get_tiles(root_dir: str) -> set:
    """
        retreives a list of folders and sub folders based on the product directory, these first level of folder will be the x value of the tile 
        and the sub folders will be the y values. the result will be a list of tile identifiers, e.g. x34/y54
    """
    unique_pairs = set()
    orig_paths = S3FS.glob(f"{root_dir}/*/*")

    for p in orig_paths:
        # Extract only the last two components, e.g. x34/y48
        x, y = p.rsplit("/", 2)[-2:]
        unique_pairs.add(f"{x}/{y}")
    
    LOGGER.debug(f"Retrieved tiles from: {root_dir}")
    return unique_pairs

def log_progress(done: int, total: int, threshold: int) -> int:
    """ 
        Logs the progress of a task based on how many of the total items are completed
        messages will be logged when progess meets the given threshold and a new threhold will be set to the next mutliple of 5
    """
    completed = done * 100 / total

    if completed >= threshold:
        completed = completed - (completed % 5) # round down to mult of 5
        LOGGER.info(f"TIFF Comparison: {int(completed)}% completed.")
        return completed + 5
    else:
        return threshold

########################
## Comparison Methods ##
########################

def compare_tiles(product1_dir, product2_dir) -> set:    
    """
        gets a complete list of tiles for which folder/subfolders exist in both the original and new data product directories.
        these lists are then compared to find a list of tiles which were not processed in the new data product output
    """
    # Determine what tiles are available on S3
    orig_paths = get_tiles(product1_dir)
    new_paths = get_tiles(product2_dir)
    mising_tiles = set()

    for path in orig_paths:
        if path not in new_paths:
            LOGGER.info(f"Tile missing: {path}")
            mising_tiles.add(path)
    
    return mising_tiles

def compare_tiffs(    
    product1,
    product2,
    band,
    year,
    product1_dir,
    product2_dir,
    missing_tiles,
    output_dir) -> dict:
        """
            Finds all tiffs in both the new and original product directories and compares them, to ensure all expected products exist and match.
            the 'missing_tiles' list is used so any tiffs in belonging to a location which is known to be missing is not tried
        """
        LOGGER.info(f"Identifying original data from S3 bucket")

        cogs = S3FS.glob(f"{product1_dir}/**/**/{year}--P1Y/{product1}_*{year}--P1Y_*_{band}.tif")

        LOGGER.info(f"Starting comparison of {len(cogs)} files")

        # Track results
        differences_found = []
        identical_files = []
        missing_files = []
        error_files = []
        progress_threshold = 5
        cog_length = len(cogs)

        for i, cog_path in enumerate(cogs):
            # get tile details from path, e.g. x60/y32
            tile = re.search("(x[0-9]{1,3}\/y[0-9]{1,3})", cog_path)
            if tile.group() in missing_tiles:
                # Path points to a tile known to be missing, skip comparison
                continue
            # Construct the corresponding path in product2_dir
            # First replace the product name in just the filename part, then replace the directory
            filename = os.path.basename(cog_path)
            # in case product name has changed do a simple replace
            filename2 = filename.replace(product1, product2)

            # Replace the product_dir with product2_dir to get the new directory structure
            cog2_path = cog_path.replace(product1_dir, product2_dir)
            
            # Now replace just the filename at the end
            cog2_path = cog2_path.replace(filename, filename2)
        
            # Add s3:// prefix back if working with S3
            cog_path_full = f"s3://{cog_path}"
            cog2_path_full = f"s3://{cog2_path}"

            LOGGER.debug(f"Comparing file {i+1}/{cog_length}: {os.path.basename(cog_path)}")

            try:
                # Open both files with xarray
                with xr.open_dataset(cog_path_full, engine='rasterio') as ds1, \
                    xr.open_dataset(cog2_path_full, engine='rasterio') as ds2:
                    
                    # Check if arrays are all close (handles floating point comparison)
                    arrays_match = xr.DataArray.equals(ds1, ds2)
                    
                    if not arrays_match:
                        # Try allclose for numerical tolerance
                        try:
                            arrays_allclose = np.allclose(
                                ds1.to_array().values, 
                                ds2.to_array().values, 
                                rtol=1e-5, 
                                atol=1e-8,
                                equal_nan=True
                            )
                        except:
                            arrays_allclose = False
                        
                        if not arrays_allclose:
                            
                            # Calculate and save the difference, using squeeze to remove potential extra singleton dims
                            diff = (ds1.to_array() - ds2.to_array()).squeeze()

                            # Create output filename
                            output_filename = os.path.basename(cog_path).replace('.tif', '_diff.tif')
                            output_path = os.path.join(output_dir, output_filename)
                            
                            # Save difference to output directory
                            diff.rio.to_raster(
                                output_path,
                                compress='DEFLATE',
                                driver='COG'
                            )

                            # recording differences here so if error is thrown we don't do twice
                            differences_found.append({
                                'file1': cog_path,
                                'file2': cog2_path,
                                'basename': os.path.basename(cog_path)
                            })
                            LOGGER.warning(f"Differences found in {os.path.basename(cog_path)}")
                            LOGGER.debug(f"Saved difference to {output_path}")
                        else:
                            LOGGER.debug(f"Files are equivalent within tolerance")
                            identical_files.append(os.path.basename(cog_path))
                    else:
                        LOGGER.debug(f"Files are identical")
                        identical_files.append(os.path.basename(cog_path))
                        
            except FileNotFoundError as e:
                LOGGER.error(f"Could not find comparison file: {cog2_path_full}")
                missing_files.append({
                    'file1': cog_path,
                    'file2_expected': cog2_path,
                    'error': str(e)
                })
            except Exception as e:
                LOGGER.error(f"Error comparing {os.path.basename(cog_path)}: {str(e)}")
                error_files.append({
                    'file1': cog_path,
                    'file2': cog2_path,
                    'error': str(e)
                })

            progress_threshold = log_progress(i+1, cog_length, progress_threshold)

        LOGGER.info(f"Comparison complete!")
        LOGGER.info(f"Total files: {len(cogs)}")
        LOGGER.info(f"Identical: {len(identical_files)}")
        LOGGER.info(f"Differences: {len(differences_found)}")
        LOGGER.info(f"Missing: {len(missing_files)}")
        LOGGER.info(f"Errors: {len(error_files)}")
        
        if differences_found:
            LOGGER.warning(f"{len(differences_found)} files had differences - check {output_dir} for diff files")
        if missing_files:
            LOGGER.error(f"{len(missing_files)} files were missing from {product2}")
        if error_files:
            LOGGER.error(f"{len(error_files)} files encountered errors during comparison")

        return {
                "original_file_count": len(cogs),
                "identical_files": len(identical_files),
                "differences_found": differences_found,
                "error_files": error_files,
                "missing_files": missing_files
            }

def generate_report(
        product1: str, 
        year: str, 
        band: str, 
        version: str,
        missing_tiles: list, 
        tiff_report: dict,
        start_time: int,
        output_dir: str):
    """
        takes in the results from the above comparisons and generates a report file outlining any differences
    """
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, f"comparison_summary_{year}_{get_band_label(band)}.txt")
    
    with open(summary_path, 'w') as f:
        if tiff_report != None:
            f.write(f"Full Comparison Summary for {product1}\n")
            f.write(f"Year: {year}, Band: {band}, Version: {version}\n")
        else:
            f.write(f"Folder Comparison Summary for {product1}\n")
            f.write(f"Year: {year}, Version: {version}\n")
        f.write(f"{'='*80}\n\n")
        
        if tiff_report != None:
            f.write(f"Total files in original product: {tiff_report['original_file_count']}\n")
            f.write(f"Identical files: {tiff_report['identical_files']}\n")
            f.write(f"Files with differences: {len(tiff_report.get('differences_found'))}\n")
            f.write(f"Missing tiles: {len(missing_tiles)}\n")
            f.write(f"Errors encountered: {len(tiff_report.get('error_files'))}\n")
        f.write(f"Missing folder count: {len(missing_tiles)}\n")
        f.write(f"Time taken: {format_time(start_time, time.perf_counter())}\n\n")

        if len(missing_tiles) > 0:
            f.write(f"\n{'='*80}\n")
            f.write(f"MISSING TILES ({len(missing_tiles)}):\n")
            f.write(f"{'='*80}\n\n")
            for path in missing_tiles:
                f.write(f" - {path}\n")

        if tiff_report != None:
            if "differences_found" in tiff_report:
                f.write(f"\n{'='*80}\n")
                f.write(f"FILES WITH DIFFERENCES ({len(tiff_report['differences_found'])}):\n")
                f.write(f"{'='*80}\n")
                for diff in tiff_report["differences_found"]:
                    f.write(f"\nFile: {diff['basename']}\n")
                    f.write(f"  Path 1: {diff['file1']}\n")
                    f.write(f"  Path 2: {diff['file2']}\n")
            
            if "missing_files" in tiff_report:
                f.write(f"\n{'='*80}\n")
                f.write(f"MISSING FILES ({len(tiff_report['missing_files'])}):\n")
                f.write(f"{'='*80}\n")
                for missing in tiff_report["missing_files"]:
                    f.write(f"\nExpected file not found:\n")
                    f.write(f"  Source: {missing['file1']}\n")
                    f.write(f"  Missing: {missing['file2_expected']}\n")
                    f.write(f"  Error: {missing['error']}\n")
            
            if "error_files" in tiff_report:
                f.write(f"\n{'='*80}\n")
                f.write(f"FILES WITH ERRORS ({len(tiff_report['error_files'])}):\n")
                f.write(f"{'='*80}\n")
                for error in tiff_report["error_files"]:
                    f.write(f"\nError during comparison:\n")
                    f.write(f"  File 1: {error['file1']}\n")
                    f.write(f"  File 2: {error['file2']}\n")
                    f.write(f"  Error: {error['error']}\n")
        
    LOGGER.info(f"Summary report written to: {summary_path}")

###################
## Logic at work ##
###################

def main():
    """
        The 'main' method where all the logic is orchestrated.
    """
    start_time = time.perf_counter()

    #TOOD can these be cleaned up ??? used in more than 1 or 2 spots??
    values = parse_args()
    product1 = values["product1"]
    product2 = values["product2"]
    band = values["band"]
    year = values["year"]
    version = values["version"]
    product1_dir = values["product1_dir"]
    product2_dir = values["product2_dir"]
    output_dir = values["output_dir"]
    folder_only = values["folder_only"]

    # Config
    configure_logging(values["verbose"])
    configure_s3()

    LOGGER.debug(f"Using parameters {values}")

    # format product directories
    product1_dir = f"{product1_dir.replace('s3://', '').rstrip('/')}/{version}"
    product2_dir = f"{product2_dir.replace('s3://', '').rstrip('/')}/{version}"
    LOGGER.debug(f"Using original data product directory: {product1_dir}")
    LOGGER.debug(f"Using new data product directory: {product2_dir}")

    missing_tiles = compare_tiles(product1_dir, product2_dir)

    if not folder_only:
        # full run 
        tiff_comparison_results = compare_tiffs(    
            product1,
            product2,
            band,
            year,
            product1_dir,
            product2_dir,
            missing_tiles,
            output_dir)
    else:
        tiff_comparison_results = None

    # Summary
    generate_report(
            product1, 
            year, 
            band, 
            version,
            missing_tiles, 
            tiff_comparison_results,
            start_time,
            output_dir)

if __name__ == "__main__":
    main()
