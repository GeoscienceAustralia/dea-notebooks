#Code to generate wetland insight stack for a given query.
#this doesn't do anything fancy with polygon masking, so the
#returned array is for a rectangular area.
#probably extend capability in a future version.

#Richard Taylor 2019
#'Wetland Insight' calculations follow Bex Dunn's Wetlands Insight Tool
#Some bits borrowed from code by Chad Burton

import datacube
import DEADataHandling, TasseledCapTools
from digitalearthau.utils import wofs_fuser

import xarray as xr
import numpy as np

#setup datacube for this
dc = datacube.Datacube(app='wetlands insight tool')

def WIT_array(query):
    """Predict the timeseries of land cover fraction classifications based on the
    Wetlands Insight Tool.
    
    Arguments:
    
    query -- query compatible with DEADataHandling.load_clearlandsat
    
    Returns:
    
    xarray.Dataset containing pixel ratios for each WIT class at each time available in the query.
    
    """
    landsat_masked_prop = 0.90
    ls578_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, product='nbart',
        masked_prop=landsat_masked_prop)
    
    #calc tcw
    tci = TasseledCapTools.thresholded_tasseled_cap(ls578_ds,wetness_threshold=-350, drop=True)
    
    #select only finite values (over threshold values)
    tcw = xr.ufuncs.isfinite(tci.wetness_thresholded)
    
    #select cotemporal WOFLs scenes
    wofls = dc.load(product = 'wofs_albers',fuse_func=wofs_fuser, **query)
    wofls = wofls.where(wofls.time==tcw.time)
    
    wet_wofs = wofls.where(wofls.water==128)

    shadow_wofs = wofls.where(wofls.water== 136) #use bit values for wet (128) and terrain/low-angle (8)
    sea_wofs = wofls.where(wofls.water==132) #bit values for wet (128) and sea (4)
    sea_shadow_wofs = wofls.where(wofls.water==140)# bit values for wet (128) and sea (4) and terrain/low-angle (8)
    
    #load fractional cover product and restrict to areas where TCW didn't pick up 'Wet' at the same time
    fc_ds = DEADataHandling.load_clearlandsat(dc, query,product='fc',masked_prop=landsat_masked_prop)
    fc_ds_noTCW=fc_ds.where(tcw==False)
    fc_ds_noTCW= fc_ds_noTCW.where(fc_ds_noTCW.time==tcw.time)
    
    #drop data percentage and Unmixing Error
    fc_tester = fc_ds_noTCW.drop(['data_perc','UE'])
    
    #cast DS->DA and dtype to int (apparently this is because np.nanargmax doesn't handle float data appropriately, according to bex)
    maxFC = fc_tester.to_array(dim='variable', name='maxFC')
    FC_int = maxFC.astype('int8')
    
    #take argmax for dominant px type
    BSPVNPV=FC_int.argmax(dim='variable')
    #mask for nans
    FC_mask=xr.ufuncs.isfinite(maxFC).all(dim='variable')
    BSPVNPV=BSPVNPV.where(FC_mask)
    
    #restack into a dominant px type dataset
    FC_dominant = xr.Dataset({
        'BS': (BSPVNPV==0).where(FC_mask),
        'PV': (BSPVNPV==1).where(FC_mask),
        'NPV': (BSPVNPV==2).where(FC_mask),
    })
    
    #count FC
    FC_count = FC_dominant.sum(dim=['x','y'])
    
    #number of pixels in area of interest
    pixels = ls578_ds.dims['x']*ls578_ds.dims['y']
    #count TCW 'wet'
    tcw_pixel_count = tcw.sum(dim=['x','y'])
    
    #count WOfS water pixels including shadowed and sea pixels
    wofs_pixels = (wet_wofs.water.count(dim=['x','y'])+shadow_wofs.water.count(dim=['x','y']) +
        sea_wofs.water.count(dim=['x','y'])+sea_shadow_wofs.water.count(dim=['x','y']))
    
    # % of each cover class
    
    wofs_area_percent = (wofs_pixels/pixels)*100
    tcw_pixel_count = tcw.sum(dim=['x','y'])
    tcw_area_percent = (tcw_pixel_count/pixels)*100
    tcw_less_wofs = tcw_area_percent-wofs_area_percent
    
    Bare_soil_percent=(FC_count.BS/pixels)*100
    Photosynthetic_veg_percent=(FC_count.PV/pixels)*100
    NonPhotosynthetic_veg_percent=(FC_count.NPV/pixels)*100
    
    #calc number of pixels w/o data so we can go back and recalculate everything on only pixels with data
    NoData = 100 - wofs_area_percent- tcw_less_wofs - Photosynthetic_veg_percent - NonPhotosynthetic_veg_percent - Bare_soil_percent
    NoDataPixels = (NoData/100) * pixels
    
    validfrac = (pixels-NoDataPixels)/pixels
    
    #put everything in a new dataset to return the result
    cover_array = xr.Dataset()
    cover_array['water'] = wofs_area_percent
    cover_array['wet'] = tcw_less_wofs
    cover_array['green'] = Photosynthetic_veg_percent
    cover_array['dry'] = NonPhotosynthetic_veg_percent
    cover_array['bare'] = Bare_soil_percent
    
    #rescale to exclude invalid px
    cover_array = cover_array/validfrac
    
    return cover_array

def WIT_da(query):
    """calculate the WIT classes for each pixel in a query
    Arguments:
    
    query -- a query compatible with DEADataHandling.load_clearlandsat()
    
    Returns:
    
    An xarray.DataArray of Wetlands Insight Tool predictions for each pixel in an optical satellite dataset,
    given a query.
    """
    landsat_masked_prop = 0.50
    ls578_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, product='nbart',
        masked_prop=landsat_masked_prop)
    
    #calc tcw
    tci = TasseledCapTools.thresholded_tasseled_cap(ls578_ds,wetness_threshold=-350, drop=True)
    
    #select only finite values (over threshold values)
    tcw = xr.ufuncs.isfinite(tci.wetness_thresholded)
    
    #select cotemporal WOFLs scenes
    wofls = dc.load(product = 'wofs_albers',fuse_func=wofs_fuser, **query)
    wofls = wofls.where(wofls.time==tcw.time)
    
    wet_wofs = xr.ufuncs.isfinite(wofls.where(wofls.water==128).water)

    shadow_wofs = xr.ufuncs.isfinite(wofls.where(wofls.water==136).water) #use bit values for wet (128) and terrain/low-angle (8)
    sea_wofs = xr.ufuncs.isfinite(wofls.where(wofls.water==132).water) #bit values for wet (128) and sea (4)
    sea_shadow_wofs = xr.ufuncs.isfinite(wofls.where(wofls.water==140).water)# bit values for wet (128) and sea (4) and terrain/low-angle (8)
    
    #load fractional cover product and restrict to areas where TCW didn't pick up 'Wet' at the same time
    fc_ds = DEADataHandling.load_clearlandsat(dc, query,product='fc',masked_prop=landsat_masked_prop)
    fc_ds_noTCW=fc_ds.where(tcw==False)
    fc_ds_noTCW= fc_ds_noTCW.where(fc_ds_noTCW.time==tcw.time)
    
    #drop data percentage and Unmixing Error
    fc_tester = fc_ds_noTCW.drop(['data_perc','UE'])
    
    #cast DS->DA and dtype to int (apparently this is because np.nanargmax doesn't handle float data appropriately, according to bex)
    maxFC = fc_tester.to_array(dim='variable', name='maxFC')
    FC_int = maxFC.astype('int8')
    
    #take argmax for dominant px type
    BSPVNPV=FC_int.argmax(dim='variable')
    #mask for nans
    FC_mask=xr.ufuncs.isfinite(maxFC).all(dim='variable')
    BSPVNPV=BSPVNPV.where(FC_mask)
    #transform the FC classes -> 2,3,4 (open water and wet will be classes 0 and 1)
    coverclasses = BSPVNPV + 2
    
    #paint the thresholded TCW onto the array
    np.place(coverclasses.data,tcw.data,1)
    
    #paint the WOfLs waterbodies
    wofs_da = xr.ufuncs.logical_or(xr.ufuncs.logical_or(xr.ufuncs.logical_or(wet_wofs,sea_wofs),shadow_wofs),sea_shadow_wofs)
    np.place(coverclasses.data,wofs_da.data,0)
    
    return coverclasses