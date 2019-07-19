## WITdrill.py

import datacube
import datetime
import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio.mask
import rasterio.features
from shapely import geometry
import seaborn as sns
import sys
import xarray as xr
from multiprocessing import Pool

from datacube.storage import masking
from datacube.utils import geometry
from digitalearthau.utils import wofs_fuser

sys.path.append('src')
import DEADataHandling, DEAPlotting, TasseledCapTools
dc = datacube.Datacube(app='wetlands insight tool')

def WITdrill(feat, crs, time_period, Output_dir, columnName):
    first_geom = feat['geometry']
    polyName = feat['properties'][columnName]
#     ID = int(polyName[-1])
#     progress = round((ID/1813) * 100, 4)
#     print("\r", "working on polygon: " + polyName + ", " + str(progress) + "%" + " complete. ", end = '')
    geom = geometry.Geometry(first_geom, crs=crs)
    #make quaery from polygon
    query = {'geopolygon': geom, 'time': time_period}
    #load and mask data. selecting data with more than 90% clear for the geobox around the polygon... #FIXME
    landsat_masked_prop = 0.90
    ls578_ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, product='nbart',
            masked_prop=landsat_masked_prop)

    ### mask the data with our original polygon to remove extra data 
    data = ls578_ds
    mask = rasterio.features.geometry_mask([geom.to_crs(data.geobox.crs)for geoms in [geom]],
                                               out_shape=data.geobox.shape,
                                               transform=data.geobox.affine,
                                               all_touched=False,
                                               invert=False)

    #for some reason xarray is not playing nicely with our old masking function
    mask_xr = xr.DataArray(mask, dims = ('y','x'))
    ls578_ds = data.where(mask_xr==False)

    #calculate tasselled cap wetness within masked AOI
    tci = TasseledCapTools.thresholded_tasseled_cap(ls578_ds,wetness_threshold=-350, drop=True , drop_tc_bands=True)
    #select only finite values (over threshold values)
    tcw = xr.ufuncs.isfinite(tci.wetness_thresholded)
    # #reapply the polygon mask
    tcw = tcw.where(mask_xr==False)
    
    #wofls = dc.load(product = 'wofs_albers', like=ls578_ds, fuse_func=wofs_fuser)
    wofls = dc.load(product = 'wofs_albers',fuse_func=wofs_fuser, **query)
    wofls = wofls.where(wofls.time==tcw.time)
    # #reapply the polygon mask
    wofls = wofls.where(mask_xr==False)
    
    wet_wofs = wofls.where(wofls.water==128)

    shadow_wofs = wofls.where(wofls.water== 136) #use bit values for wet (128) and terrain/low-angle (8)
    sea_wofs = wofls.where(wofls.water==132) #bit values for wet (128) and sea (4)
    sea_shadow_wofs = wofls.where(wofls.water==140)# bit values for wet (128) and sea (4) and terrain/low-angle (8)

    #load the  Frcational cover data according to our query
    #choose a mask proportion to look for a clear timestep
    fc_ds = DEADataHandling.load_clearlandsat(dc, query,product='fc',masked_prop=0.90)
    fc_ds = fc_ds.where(mask_xr==False)
    fc_ds_noTCW=fc_ds.where(tcw==False)
    #match timesteps
    fc_ds_noTCW= fc_ds_noTCW.where(fc_ds_noTCW.time==tcw.time)
    #drop data percentage and Unmixing Error
    fc_tester = fc_ds_noTCW.drop(['data_perc','UE'])

    #following robbi's advice, cast the dataset to a dataarray
    maxFC = fc_tester.to_array(dim='variable', name='maxFC')

    #turn FC array into integer only as nanargmax doesn't seem to handle floats the way we want it to
    FC_int = maxFC.astype('int8')

    #use numpy.nanargmax to get the index of the maximum value along the variable dimension
    #BSPVNPV=np.nanargmax(FC_int, axis=0)
    BSPVNPV=FC_int.argmax(dim='variable')

    FC_mask=xr.ufuncs.isfinite(maxFC).all(dim='variable')

    # #re-mask with nans to remove no-data
    BSPVNPV=BSPVNPV.where(FC_mask)
    #restack the Fractional cover dataset all together
    FC_dominant = xr.Dataset({
        'BS': (BSPVNPV==0).where(FC_mask),
        'PV': (BSPVNPV==1).where(FC_mask),
        'NPV': (BSPVNPV==2).where(FC_mask),
        })
    # count number of Fractional Cover pixels for each cover type in area of interest
    FC_count = FC_dominant.sum(dim=['x','y'])
    
    #number of pixels in area of interest
    pixels = (mask_xr==0).sum(dim=['x','y'])

    #count number of tcw pixels
    tcw_pixel_count = tcw.sum(dim=['x','y'])

    FC_dominant = xr.Dataset({
        'BS': (BSPVNPV==0).where(FC_mask),
        'PV': (BSPVNPV==1).where(FC_mask),
        'NPV': (BSPVNPV==2).where(FC_mask),
    })

    #number of pixels in area of interest
    pixels = (mask_xr==0).sum(dim=['x','y'])

    wofs_pixels = (wet_wofs.water.count(dim=['x','y'])+shadow_wofs.water.count(dim=['x','y']) +
    sea_wofs.water.count(dim=['x','y'])+sea_shadow_wofs.water.count(dim=['x','y']))

    #count percentage of area of wofs
    wofs_area_percent = (wofs_pixels/pixels)*100

    #count number of tcw pixels
    tcw_pixel_count = tcw.sum(dim=['x','y'])


    #calculate percentage area wet
    tcw_area_percent = (tcw_pixel_count/pixels)*100

    #calculate wet not wofs
    tcw_less_wofs = tcw_area_percent-wofs_area_percent



    #Fractional cover pixel count method
    #Get number of FC pixels, divide by total number of pixels per polygon
    #Work out the number of nodata pixels in the data, so that we can graph the variables by number of observed pixels.
    Bare_soil_percent=(FC_count.BS/pixels)*100
    Photosynthetic_veg_percent=(FC_count.PV/pixels)*100
    NonPhotosynthetic_veg_percent=(FC_count.NPV/pixels)*100
    NoData = 100 - wofs_area_percent- tcw_less_wofs - Photosynthetic_veg_percent - NonPhotosynthetic_veg_percent - Bare_soil_percent
    NoDataPixels = (NoData/100) * pixels

    #Fractional cover pixel count method
    #Get number of FC pixels, divide by total number of pixels per polygon
    Bare_soil_percent2=(FC_count.BS/(pixels - NoDataPixels))*100
    Photosynthetic_veg_percent2=(FC_count.PV/(pixels- NoDataPixels))*100
    NonPhotosynthetic_veg_percent2=(FC_count.NPV/(pixels- NoDataPixels))*100

    #count percentage of area of wofs
    wofs_area_percent2 = (wofs_pixels/(pixels - NoDataPixels))*100
    #wofs_area_percent
    wofs_area_percent = (wofs_pixels/pixels)*100
    #count number of tcw pixels
    tcw_pixel_count2 = tcw.sum(dim=['x','y'])

    #calculate percentage area wet
    tcw_area_percent2 = (tcw_pixel_count2/(pixels - NoDataPixels))*100

    #calculate wet not wofs
    tcw_less_wofs2 = tcw_area_percent2-wofs_area_percent2

    #last check for timestep matching before we plot
    wofs_area_percent2=wofs_area_percent2.where(wofs_area_percent2.time==Bare_soil_percent2.time)
    Bare_soil_percent2=Bare_soil_percent2.where(Bare_soil_percent2.time==wofs_area_percent2.time)
    Photosynthetic_veg_percent2=Photosynthetic_veg_percent2.where(Photosynthetic_veg_percent2.time==wofs_area_percent2.time)
    NonPhotosynthetic_veg_percent2=NonPhotosynthetic_veg_percent2.where(NonPhotosynthetic_veg_percent2.time==wofs_area_percent2.time)

    ### start setup of dataframe by adding only one dataset
    WOFS_df = pd.DataFrame(data=wofs_area_percent2.data, index=wofs_area_percent2.time.values,columns=['wofs_area_percent'])

    #add data into pandas dataframe for export
    WOFS_df['wet_percent']=tcw_less_wofs2.data
    WOFS_df['green_veg_percent']=Photosynthetic_veg_percent2.data
    WOFS_df['dry_veg_percent']=NonPhotosynthetic_veg_percent2.data
    WOFS_df['bare_soil_percent']=Bare_soil_percent2.data

    #call the composite dataframe something sensible, like PolyDrill
    PolyDrill_df = WOFS_df.round(2)

    #save the csv of the output data used to create the stacked plot for the polygon drill
    PolyDrill_df.to_csv(f'{Output_dir}{polyName}.csv', index_label = 'Datetime')