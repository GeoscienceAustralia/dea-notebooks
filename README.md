# Sub-pixel waterline extraction: characterising accuracy and sensitivity to indices and spectra  <img align="right" src="/images/dea_logo.jpg">

### Bishop-Taylor et al. (2019), _Remote Sensing_ 
### https://doi.org/10.3390/rs11242984

Accurately mapping the boundary between land and water (the ‘waterline’) is critical for tracking change in vulnerable coastal zones, and managing increasingly threatened water resources. 
The recent development of high performance earth observation ‘data cubes’ has revolutionised the spatial and temporal scale of remote sensing analyses, supporting the operational mapping and monitoring of surface water using freely available medium resolution satellite data such as Landsat. 
Previous studies have however largely relied on mapping waterlines at the pixel scale, or employed computationally intensive sub-pixel waterline extraction methods that are impractical to implement at scale. 
Accordingly, there is a pressing need for operational methods for extracting information from freely available medium resolution satellite imagery at spatial scales relevant to coastal and environmental management. 

In this study, we evaluate the accuracy and sensitivity of a [high performance sub-pixel waterline extraction method based on contour extraction](#subpixel_contours-function). 
We combine a synthetic landscape approach with high resolution satellite imagery to assess performance across multiple unique environments with contrasting spectral characteristics, and under a range of water indices and thresholding approaches. 
The sub-pixel extraction method shows a strong ability to reproduce both absolute waterline positions and relative shape at a resolution that far exceeds that of traditional whole-pixel methods, particularly in environments without extreme contrast between water and land (e.g. **accuracies of up to 1.50-3.28 m at 30 m Landsat resolution** using optimal water index thresholds). 

The sub-pixel waterline extraction method (`subpixel_contours`) has a low computational overhead and is **made available as an open-source tool**, making it suitable for operational continental-scale or full time-depth analyses aimed at accurately mapping and monitoring dynamic waterlines through time and space.

**If you use this code in your work, please cite the following paper and code:**

> Bishop-Taylor, R., Sagar, S., Lymburner, L., Alam, I. and Sixsmith, J., 2019. Sub-Pixel Waterline Extraction: Characterising Accuracy and Sensitivity to Indices and Spectra. Remote Sensing, 11(24), p.2984. Available: https://doi.org/10.3390/rs11242984

> Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger, M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A., Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth Australia notebooks and tools repository. Geoscience Australia, Canberra. https://doi.org/10.26186/145234

---

## `subpixel_contours` function

The [`subpixel_contours` function from the `dea-tools.spatial.py` module](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Tools/dea_tools/spatial.py#L321-L552) uses `skimage.measure.find_contours` to extract multiple z-value contour lines from a two-dimensional array (e.g. multiple elevations from a single digital elevation model), or one z-value for each array along a specified dimension of a multi-dimensional array (e.g. to map waterlines across time by extracting a 0 Normalised Difference Water Index contour from each individual timestep in an `xarray` timeseries).    
    
Contours are returned as a `geopandas.GeoDataFrame` with one row per z-value or one row per array along a specified dimension. The `attribute_df` parameter can be used to pass custom attributes to the output contour features.

### Installing `dea-tools` using pip

```
pip install dea-tools
from dea_tools.spatial import subpixel_contours
```


## Code examples

[Extracting contour lines](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Frequently_used_code/Contour_extraction.ipynb)

This introductory notebook demonstrates how to use the `subpixel_contours` function to:

* Extract one or multiple contour lines from a single two-dimensional digital elevation model and export these as a shapefile
* Optionally include custom attributes in the extracted contour features
* Load in a multi-dimensional satellite dataset from Digital Earth Australia, and extract a single contour value consistently through time along a specified dimension
* Filter the resulting contours to remove small noisy features

![Contour extraction image](/images/contour_extract.jpg)

## Real-world examples

[Monitoring coastal erosion along Australia's coastline](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Real_world_examples/Coastal_erosion.ipynb)

* Imagery from satellites such as the NASA/USGS Landsat program is available for free for the entire planet, making satellite imagery a powerful and cost-effective tool for monitoring coastlines and rivers at regional or national scale. 
* By identifying and extracting the precise boundary between water and land based on satellite data using the `subpixel_contours` function, it is possible to extract accurate shorelines that can be compared across time to reveal hotspots of erosion and coastal change.

![Coastal erosion](/images/coastal_erosion.jpg)

[Modelling intertidal elevation using tidal data](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Real_world_examples/Intertidal_elevation.ipynb)

* Geoscience Australia recently combined 30 years of Landsat data from the Digital Earth Australia archive with tidal modelling to produce the first 3D model of Australia's entire coastline: the National Intertidal Digital Elevation Model or NIDEM (for more information, see [Bishop-Taylor et al. 2019](https://doi.org/10.1016/j.ecss.2019.03.006) or [access the dataset here](http://dx.doi.org/10.26186/5c4fc06a79f76)).
* In this example, we demonstrate a simplified version of the NIDEM method that combines data from the Landsat 5, 7 and 8 satellites with tidal modelling, image compositing and spatial interpolation techniques. 
* Subpixel resolution waterline mapping using the `subpixel_contours` function is used to map the boundary between land and water from low to high tide, with this information then used to generate smooth, continuous 3D elevation maps of the intertidal zone.

![Intertidal elevation](/images/intertidal_elevation.jpg)

***

## Additional information

**License:** All Digital Earth Australia code referenced on this page is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). 
Digital Earth Australia data is licensed under the [Creative Commons by Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) license.

**Contact:** If you need assistance, please post a question on the [Open Data Cube Slack channel](http://slack.opendatacube.org/) or on the [GIS Stack Exchange](https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions [here](https://gis.stackexchange.com/questions/tagged/open-data-cube)).
If you would like to report an issue with this notebook, you can file one on [Github](https://github.com/GeoscienceAustralia/dea-notebooks).

**Last modified:** September 2021
