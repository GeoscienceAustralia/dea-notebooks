# DEA Mosaic Tools Submodule

This submodule provides Python tools for generating Cloud Optimised GeoTIFF (COG) mosaics and applying colour schemes to DEA products. It includes two main scripts:

- `cog.py`: Builds mosaics from DEA tiled products. Can either be used for continental mosaics, or a limited number of tiles (in this case, include `--list_tiles`)
- `vrt.py`: Applies colour schemes and generates GDAL VRTs for the mosaics. Can either be used for single-band categorical data or three-colours composites.

---

# Usage examples

## Generate COG mosaics

To generate a continental mosaic of 2024 DEA Land Cover 2.0, first [install DEA Tools](https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Tools#installation) and then run the command below:

```
make_cog_mosaic \
  --product ga_ls_landcover_class_cyear_3 \
  --band level4 \
  --time 2024 \
  --freq P1Y \
  --version 2-0-0 \
  --dataset_maturity final \
  --product_dir s3://dea-public-data/derivative/ \
  --output_dir /path/to/output/parent/folder \
  --cog_blocksize 1024 \
  --overview_count 7 \
  --overview_resampling MODE \
  --compression_algo ZSTD \
  --compression_level 9 \
  --aws_unsigned \
  --skip_existing
```

Mosaic only a few tiles:

```
make_cog_mosaic \
  --product ga_ls_landcover_class_cyear_3 \
  --band level4 \
  --time 2024 \
  --freq P1Y \
  --version 2-0-0 \
  --dataset_maturity final \
  --product_dir s3://dea-public-data/derivative/ \
  --output_dir /path/to/output/parent/folder \
  --cog_blocksize 1024 \
  --overview_count 7 \
  --overview_resampling MODE \
  --compression_algo ZSTD \
  --compression_level 9 \
  --aws_unsigned \
  --skip_existing \
  --list_tiles x25y41,x26y42,x27y43
```

If DEA Tools package is not installed, it is possible to run the analysis directly via the Python module by replacing `make_cog_mosaic` in the command above with `python cog.py`.

## Generate colour VRTs

Apply colour scheme to single-band categorical data.
It is recommended to use the same path where the mosaics are as output directory for the VRTs. Because the VRTs look for the mosaic files in the folder where the VRTs are stored.

```
make_styling_vrt \
  --product ga_ls_landcover_class_cyear_3 \
  --time 2024 \
  --freq P1Y \
  --version 2-0-0 \
  --cog_dir /path/to/mosaic/parent/folder \
  --output_dir /path/to/mosaic/parent/folder \
  --col_scheme_dir /path/to/colour/schemes/folder \
  --band level4
```

For three-colours composites (in this example, RGB true-colour):

```
make_styling_vrt \
  --product ga_ls8cls9c_gm_cyear_3 \
  --time 2024 \
  --freq P1Y \
  --version 4-0-0 \
  --cog_dir /path/to/mosaic/parent/folder \
  --output_dir /path/to/mosaic/parent/folder \
  --r_channel_band nbart_red \
  --g_channel_band nbart_green \
  --b_channel_band nbart_blue
```

If DEA Tools package is not installed, it is possible to run the analysis directly via the Python module by replacing `make_styling_vrt` in the command above with `python vrt.py`.