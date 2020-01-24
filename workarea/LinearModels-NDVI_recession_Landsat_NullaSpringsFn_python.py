#!/usr/bin/env python
# coding: utf-8

# # Running linear models on DEA indices using Sentinel
# 
# **Background:** This document presents an example of applying a linear model to analyse Landsat data extracted from Digital Earth Australia (DEA) to make inferences about physical processes. Here we are testing the rate of decline in vegetation condition during the dry season in NW Australia. Rainfall in this part of Australia is highly seasonal. During the dry season (April to October) there is very little rain and we assume that soil moisture declines throughout.
# 
# A common approach for assessing the likelihood of vegetation being dependent on groundwater is applying the 'green island' principle. This involves inferring gorudnwater use from vegetation that maintains higher condition during dry periods. In our area of interest, we expect that vegetation condition will decline much more rapidly in vegetation communities that are wholly reliant on surface water compared to communities that access groundwater (i.e. groundwater dependent ecosystems). We use NDVI as a proxy for vegetation condition.
# 
# 
# **What does this document do?**
# 
# - Retrieve Landsat data for temporal and spatial extents
# - Calculate NDVI and groupby months
# - Demonstrate how to build a linear model to analyse the rate of decay in NDVI throughout the dry season
# - Plot linear model parameters and use spatial patterns to infer distribuition of potential GDEs
# 
# **Requirements**
# 
# You need to run the following commands from the command line prior to launching jupyter notebooks from the same terminal so that the required libraries and paths are set:
# 
# `module use /g/data/v10/public/modules/modulefiles` 
# 
# `module load dea`
# 
# If you find an error or bug in this notebook, please either create an 'Issue' in the Github repository, or fix it yourself and create a 'Pull' request to contribute the updated notebook back into the repository (See the repository [README](https://github.com/GeoscienceAustralia/dea-notebooks/blob/master/README.rst) for instructions on creating a Pull request).
# 
# **Date**: June 2019
# 
# **Authors**: Neil Symington, Robbi Bishop-Taylor, Bex Dunn

# ## Retrieving Landsat data
# Here we import data Landsat data from the DEA. In our experience using the larger number of observations decreases our signal-to-noise ration and thus enables us to resolve landscape features at a higher resolution. Hence, for the actual data product we used the entire landsat archive and ran the processing through the raijin supercomputer.  However for this example we will only consider data from 2009-2019 from landsat 8.

# ### Import modules

# In[1]:


#get_ipython().run_line_magic('matplotlib', 'inline')
import sys
import warnings
import datacube
import matplotlib.pyplot as plt
from datacube.storage import masking
from datacube.helpers import write_geotiff
import calendar
import numpy as np
import xarray as xr

sys.path.append('/g/data/zk34/pxk547/dea-notebooks/10_Scripts/')
import DEADataHandling, DEAPlotting

# Dictoinary for mapping month number to months names 
mnths =dict((k,v) for k,v in enumerate(calendar.month_name) if k!= 0)


# In[2]:


# Connect to a datacube
dc = datacube.Datacube(app='LinearModels')


# In[3]:



def linregress_3D(x, y):
    """
    
    Input: Two xr.Datarrays of any dimensions with the first dim being time. 
    Thus the input data could be a 1D time series, or for example, have three 
    dimensions (time,lat,lon). 
    Datasets can be provided in any order, but note that the regression slope 
    and intercept will be calculated for y with respect to x.
    Output: Covariance, correlation, regression slope and intercept, p-value, 
    and standard error on regression between the two datasets along their 
    aligned time dimension.  
    """ 
    # Ensure that the data are properly aligned to each other. 
    x,y = xr.align(x,y)

    
    #Compute data length, mean and standard deviation along time axis: 
    n = y.notnull().sum(dim='month')
    xmean = x.mean(axis=0)
    ymean = y.mean(axis=0)
    xstd  = x.std(axis=0)
    ystd  = y.std(axis=0)

    #4. Compute covariance along time axis
    cov   =  np.sum((x - xmean)*(y - ymean), axis=0)/(n)

    #5. Compute correlation along time axis
    cor   = cov/(xstd*ystd)

    #6. Compute regression slope and intercept:
    LRslope    = cov/(xstd**2)
    LRintercept = ymean - xmean*LRslope  

    #7. Compute P-value and standard error
    #Compute t-statistics
    tstats = cor*np.sqrt(n-2)/np.sqrt(1-cor**2)
    stderr = LRslope/tstats

    from scipy.stats import t
    pval   = t.sf(tstats, n-2)*2
    pval   = xr.DataArray(pval, dims=cor.dims, coords=cor.coords)

    return cov,cor,LRslope,LRintercept,pval,stderr

def regression_pixel_drill_ndvi(x, y, ax, slope, intercept, scatter_kwargs = None,
                          plot_kwargs = None):
    """
    Function  for plotting regression points and line on an axis
    @param x: x coordinate
    @param y: y coordinate
    @param ax: matplotlib axis
    @param scatter_kwargs: matplotlib keyword arguments for a scatter plot
    @param plot_kwargs: matplotlib keyword arguments for a plot
    """
    ndvi_pt = ndvi_dry.sel(x = x, y = y,
                           method = 'nearest').values
    months = ndvi_dry.month.values
    
    ax.scatter(months, ndvi_pt, **scatter_kwargs)
    
    # Get the slope and intercepth
    
    slope_ = slope.sel(x = x, y = y,
                       method = 'nearest').values
    
    intercept_ = intercept.sel(x = x, y = y,
                       method = 'nearest').values
    # Add a line to the graph
    
    xs = np.array([months[0], months[-1]])

    ys = np.array([slope_*v + intercept_ for v in xs])
    
    # Plot the line on the axis
    
    ax.plot(xs, ys, **plot_kwargs)
    
def regression_pixel_drill_ndmi(x, y, ax, slope, intercept, scatter_kwargs = None,
                          plot_kwargs = None):
    """
    Function  for plotting regression points and line on an axis
    @param x: x coordinate
    @param y: y coordinate
    @param ax: matplotlib axis
    @param scatter_kwargs: matplotlib keyword arguments for a scatter plot
    @param plot_kwargs: matplotlib keyword arguments for a plot
    """
    ndmi_pt = ndmi_dry.sel(x = x, y = y,
                           method = 'nearest').values
    months = ndmi_dry.month.values
    
    ax.scatter(months, ndmi_pt, **scatter_kwargs)
        
    slope_ = slope.sel(x = x, y = y,
                       method = 'nearest').values
    
    intercept_ = intercept.sel(x = x, y = y,
                       method = 'nearest').values
    # Add a line to the graph
    
    xs = np.array([months[0], months[-1]])

    ys = np.array([slope_*v + intercept_ for v in xs])
    
    # Plot the line on the axis
    
    ax.plot(xs, ys, **plot_kwargs)
    
def regression_pixel_drill_ndwi(x, y, ax, slope, intercept, scatter_kwargs = None,
                          plot_kwargs = None):
    """
    Function  for plotting regression points and line on an axis
    @param x: x coordinate
    @param y: y coordinate
    @param ax: matplotlib axis
    @param scatter_kwargs: matplotlib keyword arguments for a scatter plot
    @param plot_kwargs: matplotlib keyword arguments for a plot
    """
    ndwi_pt = ndwi_dry.sel(x = x, y = y,
                           method = 'nearest').values
    months = ndwi_dry.month.values
    
    ax.scatter(months, ndwi_pt, **scatter_kwargs)
    
    # Get the slope and intercepth
    
    slope_ = slope.sel(x = x, y = y,
                       method = 'nearest').values
    
    intercept_ = intercept.sel(x = x, y = y,
                       method = 'nearest').values
    # Add a line to the graph
    
    xs = np.array([months[0], months[-1]])

    ys = np.array([slope_*v + intercept_ for v in xs])
    
    # Plot the line on the axis
    
    ax.plot(xs, ys, **plot_kwargs)   


# In[4]:


# Create spatial and temporal query

#query to do with Nulla area
#query = {'lat': (-20.06, -19.6),
#         'lon': (144.95, 146.0),
#         'time':('1990-01-10', '2019-01-10')}

#spring in Nulla area
query = {'lat': (-20.2, -19.48),
         'lon': (144.5, 146.1),
         'time':('1987-01-10', '2019-01-10')}

#spring in Nulla area
#query = {'lat': (-19.786, -19.6765),
#         'lon': (145.32, 145.42),
#         'time':('2015-10-22', '2019-01-10')}
#'time':('1980-01-01', '2019-01-10')}

# Define query coordinate reference system

query['crs'] = 'EPSG:4326'
query['output_crs'] = 'EPSG:28355'
query['resolution'] = (25.,25.)


# In[5]:


# Load data for the specified query extent using `dc.load`:
ds = dc.load(product='ls8_nbar_albers', group_by='solar_day', **query
            )
#ds


# ## Adding code in to extract cloud free data only (from stacked plot script)

# In[6]:


#set cloudmasking threshold and load landsat nbart data
landsat_masked_prop = 0.90
ls578_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, product='nbart', masked_prop=landsat_masked_prop)


# In[7]:


#ls578_ds


# In[8]:


#ls578_ds.isel(time=9)


# In[9]:


# View the rgb image

#ls578_ds[['blue','green', 'red']].isel(time=10).to_array().plot.imshow(robust=True, figsize=(8,8))


# Our study area is the margin of a sandy, unconfined aquifer system to the south and mud flats to the north. In the middle of the area are a number of 'islands' of thick vegetation (dark green). We want to assess the likelihood of these communities having some degree of groudnwater water dependence.

# In[10]:


# Calculate NDVI and NDMI

ndvi = ((ls578_ds.nir - ls578_ds.red)/(ls578_ds.nir + ls578_ds.red))
ndmi = ((ls578_ds.nir - ls578_ds.swir2)/(ls578_ds.nir + ls578_ds.swir2))
ndwi = ((ls578_ds.green - ls578_ds.nir)/(ls578_ds.green + ls578_ds.nir))


# ## Plotting NDVI
# 
# # Make a plot for each month
# 
# To investigate the difference in vegetation condition we plot the median and standard devation ndvi for each month
# 

# ## Run trend analysis
# 
# From the median plots it appears that the vegetation condition declines from about April until January. This is somewhat counter intuitive given that we expect rains in December January. The very high standard deviation in the wet months suggest we may be getting some influence of spurious measurements, perhaps from cloud shadow and/ or surface water.
# 
# From this we decide the best way to test vegetation is to use April to November. UB looking at figures, more July - November (so 7 - 11)

# In[11]:


# We group the data by dry season for NDVI

#dry_months = [4,5,6,7,8,9,10,1]
dry_months = [5,6,7,8,9,10]

#REtrieve the dry months
ndvi_dryT = ndvi[ndvi['time.month'].isin(dry_months)]
ndvi_dry = ndvi_dryT.groupby('time.month').median(dim = 'time')
#ndvi_dry


# In[12]:


#to extract out median NDVI image, need to have individual values, not time based
ndvi_dry2 = ndvi_dryT.median(dim = 'time')
#ndvi_dry2


# In[13]:


# We group the data by dry season for NDMI

#dry_months = [4,5,6,7,8,9,10,11]
dry_months = [5,6,7,8,9,10]

#REtrieve the dry months
ndmi_dryT = ndmi[ndmi['time.month'].isin(dry_months)]
ndmi_dry = ndmi_dryT.groupby('time.month').median(dim = 'time')


# In[14]:


#to extract out median NDVI image, need to have individual values, not time based
ndmi_dry2 = ndmi_dryT.median(dim = 'time')
#ndmi_dry2


# In[15]:


# We group the data by dry season for NDWI

#dry_months = [4,5,6,7,8,9,10,11]
dry_months = [5,6,7,8,9,10]

#REtrieve the dry months
ndwi_dry = ndwi[ndwi['time.month'].isin(dry_months)]
ndwi_dry = ndwi_dry.groupby('time.month').median(dim = 'time')


# In[26]:


# Run the linear regression on the monthly ndvi
NDVIcov,NDVIcor,NDVIslope,NDVIintercept,NDVIpval,NDVIstderr = linregress_3D(ndvi_dry.month, ndvi_dry)
NDVIr_squ = NDVIcor**2


# In[27]:


# Run the linear regression on the monthly ndmi
NDMIcov,NDMIcor,NDMIslope,NDMIintercept,NDMIpval,NDMIstderr = linregress_3D(ndmi_dry.month, ndmi_dry)
NDMIr_squ = NDMIcor**2


# In[28]:


# Run the linear regression on the monthly ndwi
NDWIcov,NDWIcor,NDWIslope,NDWIintercept,NDWIpval,NDWIstderr = linregress_3D(ndwi_dry.month, ndwi_dry)


# From these plots it appears that most of the veg communities have a negative slope (i.e. declining NDVI/ vegetation condition). High r-squared values suggest a strong linear relationship in these areas. However there is a spring/vegetation at the bottom ~(327875,7813000) with a positive or small negative slope and a low-rsquared. We conclude that these communities retain their condition during the dry season and thus have a greater probability of groundwater dependence.

# From these plots it appears that most of this area has a negative slope (i.e. declining NDMI/ moisture). High r-squared values suggest a strong linear relationship in these areas. However there is an area at the bottom ~(327875,7813000) with a positive or small negative slope and a low-rsquared. We conclude that this area retains moisture during the dry season and thus have a greater probability of influence from groundwater.

# ### Exporting out NDVI image with 3 bands (slope, r squared, NDVI median value for dry period

# In[29]:


startDate = str(ls578_ds.isel(time=0).time.values)[0:10]
endDate = str(ls578_ds.isel(time=-1).time.values)[0:10]
#endDate[0:4] + " " + endDate
#print ("NDVI of dry period (months " + str(dry_months[0])+ "-"+str(dry_months[-1]) + " from "+startDate+" to " +endDate)
#print ('NDVI_landsat_dry_'+startDate+'_'+endDate[0:4]+'.tif')


# In[30]:


#Export out NDVI values, slope and r-squared for dry period specified

#set variable for path to save files
savefilepath = '/g/data/zk34/pxk547/'

#Exporting NDVI slope into new dataset
NDVIslopeDS = NDVIslope.to_dataset(name='NDVI_slope')

# We can now add other attributes (Rsquared) into our dataset as new data variables (can't add NDVI as has monthly values):

NDVIslopeDS["NDVI_rsqu"] = NDVIr_squ
NDVIslopeDS["NDVI_dry_median"] = ndvi_dry2
#NDVIslopeDS

#converting type from float64 to float32 to reduce file size
NDVIslopeDS = NDVIslopeDS.astype(np.float32)
#Adding CRS back into dataset
NDVIslopeDS.attrs = ds.attrs
#NDVIslopeDS

#this writes the geotiff with 3 bands: NDVI_slope, NDVI-rsqu, NDVI_dry_median
write_geotiff(savefilepath+'NDVI_landsat_dry_'+startDate[0:4]+'_'+endDate[0:4]+'.tif', NDVIslopeDS)

#creating metadata file for NDVI_landsat_dry.tif
print ('your metadata file is being created')
f = open(savefilepath+'NDVI_landsat_dry_'+startDate[0:4]+'_'+endDate[0:4]+'.txt','w')  #w - writes, r - reads; a- appends

f.write("NDVI of dry period (months " + str(dry_months[0])+ "-"+str(dry_months[-1]) + " from "+startDate+" to " +endDate+ "\n" +
        "NDVI_slope, NDVI_rsqu and NDVI_dry_median are the 3 bands. " + "\n" +
        "Where slope is 0 is where NDVI values don't change much during the dry period. " + "\n" + 
        "Where rsqu is 1 is where correlation is high between months, therefore no variation "+ "\n" + 
        "Ndvi_dry_median is the median value of NDVI over the dry months"+ "\n" +
        "Can use the ndvi value to select where areas are green and intersect those "+ "\n" +
         "where slope is near 0 to find potential GDV sites.")
f.write(str(ds)) #if don't have text to hand, could use this
f.close()
print ('NDVI_landsat_dry_'+startDate[0:4]+'_'+endDate[0:4]+'.txt has been saved to '+savefilepath)


# ### Exporting out NDI image with 3 bands (slope, r squared, NDVI median value for dry period

# In[31]:


#Exporting NDMI slope
NDMIslopeDS = NDMIslope.to_dataset(name='slope')

# We can now add other attributes (Rsquared) into our dataset as new data variables (can't add NDVI as has monthly values):

NDMIslopeDS["NDVI_rsqu"] = NDMIr_squ
NDMIslopeDS["NDVI_dry_median"] = ndmi_dry2

#converting type from float64 to float32 to reduce file size
NDMIslopeDS = NDMIslopeDS.astype(np.float32)
#Adding CRS back into dataset
NDMIslopeDS.attrs = ds.attrs
#NDMIslopeDS

#this writes the geotiff with 3 bands: NDMI_slope, NDMI-rsqu, NDMI_dry_median
write_geotiff(savefilepath+'NDMI_landsat_dry_'+startDate[0:4]+'_'+endDate[0:4]+'.tif', NDMIslopeDS)

#creating metadata file for Barest Earth using same name as tif
print ('your metadata file is being created')
f = open(savefilepath+"NDMI_landsat_dry.txt",'w')  #w - writes, r - reads; a- appends

f.write("NDMI of dry period over time with NDMI_slope, NDMI_rsqu and NDMI_dry_median as the 3 bands. " + "\n" +
        "Where slope is 0 is where NDMI values don't change much during the dry period. " + "\n" + 
        "Where rsqu is 1 is where correlation is high between months, therefore no variation "+ "\n" + 
        "NDMI_dry_median is the median value of NDMI over the dry months"+ "\n" +
        "Can use the ndmi value to select where areas are wet and intersect those "+ "\n" +
         "where slope is near 0 to find potential permanently wet sites.")
f.write(str(ds)) #if don't have text to hand, could use this
f.close()

print ('NDMI_landsat_dry_'+startDate[0:4]+'_'+endDate[0:4]+'.txt has been saved to '+savefilepath)


# ## Conclusion
# 
# Our conclusion from this investigation is that there are vegetation communities in the area of interest that appear to that show statistically negligible change in condition despite prolonged dry conditions. In contrast, adjacent vegetation communities decline linearly throughout the dry season as soil moisture becomes scarce. We hypothesise that the lack of recession is due to the availability of groundwater within the root zones throughout the dry season. Follow up work including field observations and chemistry are required to validate this.

