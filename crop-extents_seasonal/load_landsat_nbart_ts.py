
# coding: utf-8

# # Load sentinel time series data, save the data as ENVI images

# In[40]:


# Import modules
import datacube
import sys
import numpy as np
import time
import os
    


# In[41]:


import rasterio
def write_multi_time_dataarray(timebandnaes, filename, dataarray, **profile_override):
    profile = {
        'width': len(dataarray[dataarray.crs.dimensions[1]]),
        'height': len(dataarray[dataarray.crs.dimensions[0]]),
        'transform': dataarray.affine,
        'crs': dataarray.crs.crs_str,
        'count': len(dataarray.time),
        'dtype': str(dataarray.dtype)
    }
    profile.update(profile_override)

    with rasterio.open(str(filename), 'w', **profile) as dest:
        for time_idx in range(len(dataarray.time)):
            bandnum = time_idx + 1
            bandstr=timebandnames[time_idx]
            dest.write(dataarray.isel(time=time_idx).data, bandnum)
            





# In[42]:


# Import dea-notebooks functions using relative link to Scripts directory

sys.path.append('/g/data1/u46/pjt554/dea_notebooks/dea-notebooks-master/10_Scripts')
import DEADataHandling
    
    
#bands_of_interest=['nbart_red', 'nbart_green', 'nbart_blue', 'nbart_nir_2', 'nbart_swir_2', 'nbar_swir_3']
# Connect to a datacube containing Sentinel data
dc = datacube.Datacube(app='Clear Landsat')

argc = len(sys.argv)
print(argc)

if (argc != 8):
    print('Usage: python dea_fetch_data.py lat_top lat_bottom lon_left lon_right start_of_epoch(yyyy-mm-dd) end_of_epoch(yyyy-mm-dd) output_dir')
    sys.exit() 

# Set up spatial and temporal query; note that 'output_crs' and 'resolution' need to be set
param=sys.argv

lat_top = float(param[1])
lat_bottom = float(param[2])
lon_left = float(param[3]) 
lon_right = float(param[4]) 
start_of_epoch = param[5] 
end_of_epoch = param[6] 
dirc = param[7]

comm = 'mkdir ' + dirc
os.system(comm)


#lon_left=149.02
#lon_right=149.22
#lat_top=-35.11
#lat_bottom=-35.35
#epoh_beg='2015-01-01'
#epoh_end='2015-12-31'

newquery={'x': (lon_left, lon_right),
          'y': (lat_top, lat_bottom),
          'time': (start_of_epoch, end_of_epoch)
         }


query = {'x': (149.02, 149.22),
         'y': (-35.11, -35.35),
         'time': ('2015-01-01', '2015-12-31')
        }   


allbands=['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
output_bandnames = ['blue','green', 'red', 'nir', 'swir1', 'swir2']

#dirc = '/g/data1/u46/pjt554/urban_change_nbart_full_sites/act_canberra'
cc=0
# Load observations with less than 70% cloud from both S2A and S2B as a single combined dataset
for bandname in allbands:
    
    inbandlist=[]
    inbandlist.append(bandname)
    print(inbandlist)
    landsat_ds = DEADataHandling.load_clearlandsat(dc=dc, query=newquery, sensors=('ls5', 'ls7', 'ls8'), product='nbart',
                                       bands_of_interest=inbandlist, ls7_slc_off=True,
                                       mask_pixel_quality=False, mask_invalid_data=False, masked_prop=0.0)
    
    timelist = []
    for t in landsat_ds['time']:
        timelist.append(time.strftime("%Y-%m-%d", time.gmtime(t.astype(int)/1000000000)))
    
    timebandnames=np.asarray(timelist)

    banddata=landsat_ds[bandname]
    outbandname=output_bandnames[cc]
    filename=dirc+'/NBAR_'+outbandname+'.img'
    write_multi_time_dataarray(timebandnames, filename, banddata, driver='ENVI')
    cc=cc+1
    #landsat_ds = None

# In[43]:


def create_envi_header(fname, icol, irow, ts, lon_left, lat_top, description, bandnames):
    hdr_file = open(fname, "w")
    hdr_file.write("ENVI\n")
    outstr = 'description = { ' + description + '}\n'
    hdr_file.write(outstr)
    outstr = 'samples = '+str(icol)+'\n'
    hdr_file.write(outstr)
    outstr = 'lines = '+str(irow)+'\n'
    hdr_file.write(outstr)
    outstr = 'bands = '+str(ts)+'\n'
    hdr_file.write(outstr)
    hdr_file.write("header offset = 0\n")
    hdr_file.write("file type = ENVI Standard\n")
    hdr_file.write("data type = 1\n")
    hdr_file.write("interleave = bsq\n")
    hdr_file.write("sensor type = Unknown\n")
    hdr_file.write("byte order = 0\n")
    outstr = 'map info = { Geographic Lat/Lon, 1, 1, '+str(format(lon_left, '.2f'))+ ', ' +str(format(lat_top, '.2f'))
    outstr = outstr + ', 0.00025, 0.00025, WGS-84 }\n'
    hdr_file.write(outstr)
    hdr_file.write("wavelength units =\n")
    hdr_file.write("band names ={\n")
    cc=0
    for bandstr in bandnames:
        if (cc!=ts-1):
            outstr=bandstr+',\n'
        else:
            outstr=bandstr+'\n'
        hdr_file.write(outstr)
        cc=cc+1
    hdr_file.write('}\n')    
    hdr_file.close()



# In[ ]:






# In[44]:




fname=dirc+'/clouds.hdr'

xs= landsat_ds['x'].size
ys= landsat_ds['y'].size
ts= landsat_ds['time'].size
des='cloud = 3, non_cloud = 0'
lon_left=1.0
lat_top=1.0
create_envi_header(fname, xs, ys, ts, lon_left, lat_top, des, timebandnames)



# In[45]:


amm = [ts, ys, xs]
fname=dirc+'/ts_irow_icol.csv'
np.savetxt(fname, amm, fmt='%d', delimiter=', ', newline='\n', header='', footer='', comments='# ')

