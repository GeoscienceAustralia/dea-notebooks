
# coding: utf-8

# In[98]:


import os
import sys
import sklearn as sk
import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.cluster import KMeans


# In[99]:



path=sys.argv[1]
sourcehdr=sys.argv[2]
numcls=int(sys.argv[3])

#numyears=int(sys.argv[3])
#styear=int(sys.argv[4])


# In[100]:


#path='/g/data1/u46/pjt554/urban_change_full_sites/act_canberra/2000'


bridatafile=path+'/phg_bri.img'
msavidatafile=path+'/phg_msavi.img'
mndwidatafile=path+'/phg_mndwi.img'

f1_imgfile=path+'/brightness_range.img'
f2_imgfile=path+'/msavi_range.img'
f3_imgfile=path+'/mndwi_range.img'

parafile=path+'/ts_irow_icol.csv'

filelist=[bridatafile, msavidatafile, mndwidatafile]
cltfilelist=[f1_imgfile, f2_imgfile, f3_imgfile]


# In[101]:


def chessbcors(rowdiv, coldiv, nrow, ncol, rlen, clen):
    
    
    rbnum = rowdiv-rlen+1
    cbnum = coldiv-clen+1
    
    
    blknum=rbnum*cbnum
    
    
    
    blkcors=np.zeros([blknum, 4])
    blkcors=blkcors.astype(np.int32)

    
    
    rowss=nrow/rowdiv
    colss=ncol/coldiv
    rowss=int(rowss)+1
    colss=int(colss)+1
    
    rowpoints=np.zeros(rowdiv+1)
    colpoints=np.zeros(coldiv+1)
    
    rowpoints=rowpoints.astype(np.int32)
    colpoints=colpoints.astype(np.int32)
    
    for i in range(rowdiv+1):
        rowpoints[i]=i*rowss
        if (rowpoints[i]>nrow):
            rowpoints[i]=nrow
            
    for i in range(coldiv+1):
        colpoints[i]=i*colss
        if (colpoints[i]>ncol):
            colpoints[i]=ncol 
    
    cc=0
    for i in range(rbnum):
        for j in range(cbnum):
                blkcors[cc, 0]=rowpoints[i]
                blkcors[cc, 1]=rowpoints[i+rlen]
                blkcors[cc, 2]=colpoints[j]
                blkcors[cc, 3]=colpoints[j+clen]
                cc=cc+1
    
    return blkcors, blknum


# In[102]:


tmm = pd.read_csv(parafile, header =None)

nrow=tmm.values[1:3][0][0]
ncol=tmm.values[1:3][1][0]
print (nrow, ncol)
pnum = nrow*ncol

data=np.zeros([pnum, 5])
cltdata=np.zeros([pnum, 3])

rowdiv=20
coldiv=16

rlen=8
clen=8


blkcors, numblk = chessbcors(rowdiv, coldiv, nrow, ncol, rlen, clen)

#print(blkcors)


# In[103]:


def readimgfile(filename, pnum, tgt, data, col):
    imgdata=np.fromfile(filename, dtype=np.float32)
    oneblock=imgdata[tgt*pnum:(tgt+1)*pnum]
    data[:, col]=imgdata[tgt*pnum:(tgt+1)*pnum]
    


def readfeaturesfile(filename, pnum, cltdata, col):
    imgdata=np.fromfile(filename, dtype=np.float32)
    cltdata[:, col]=imgdata


# In[104]:


tgt=4
col=0
for filename in filelist:
    readimgfile(filename, pnum, tgt, data, col)
    col=col+1

col=0
for filename in cltfilelist:
    readfeaturesfile(filename, pnum, cltdata, col)
    col=col+1

# In[105]:


def getoneblock(data, cors, ncol):
    x1=cors[0]
    x2=cors[1]
    y1=cors[2]
    y2=cors[3]
    brow=x2-x1
    bcol=y2-y1
    oneblock = np.zeros([brow*bcol, 5])
    for x in range(x1, x2):
        for y in range(y1, y2):
            mx=x-x1
            my=y-y1
            oneblock[mx*bcol+my, :]= data[x*ncol+y, :]
            
    return oneblock, brow, bcol


# In[106]:


def addspatialcols(data, pnum, nrow, ncol):
    for i in range(pnum):
        x=int(i/ncol)
        y=i%ncol
        data[i, 3]=x
        data[i, 4]=y

    return data


# In[107]:


def classifyoneblock_spectral(data, cltdata, nrow, ncol, rp, numcls):
    
    pnum=nrow*ncol
    
    #greenness = data[:, 1]
    greenness = cltdata[:, 1]
    brightness = data[:, 0]
    wetness = data[:, 2]
   
    wateridx=np.where(wetness>=0.02)[0]
    nonwateridx=np.where(wetness<0.02)[0]
    stidx = np.argsort(greenness)
    
    
    gresum=0
    bff=0

    
    
    
    for i in range(int(.85*pnum), pnum):
        gresum=gresum+greenness[stidx[i]]
        bff=bff+1
    gresum=gresum/bff

    grebot=0
    bff=0
    for i in range(int(.15*pnum)):
        grebot=grebot+greenness[stidx[i]]
        bff=bff+1
    grebot=grebot/bff
    
    sprst=cltdata
    sprst=sprst[nonwateridx]
    sprst=np.asarray(sprst)


    sprst_scale=preprocessing.scale(sprst)
    
    width=2
    

    clscount=np.zeros([pnum, numcls], dtype=np.int32)

    for i in range(rp):
        clsimg = clusterclassifier(sprst_scale, gresum, pnum, numcls, wateridx, nonwateridx, brightness, greenness, wetness)
        for k in range(pnum):
            m=clsimg[k]
            clscount[k, m]=clscount[k,m]+1




    bbclsimg=clscount.argmax(axis=1)
    bbclsimg=bbclsimg.astype(np.int8)

    #clsimg=bbclsimg
    
    #spfilter(clsimg, 1, 7, nrow, ncol)    
    #grate=greenrate(clsimg, width, nrow, ncol)

    #grthd=0.7

    #for i in range(pnum):
    #    ilab=clsimg[i]
    #    if (ilab>=2):
    #        clsimg[i]=ilab+1
    #    else:
    #        if (ilab==1):
    #            if (grate[i]<grthd):
    #                clsimg[i]=2


    return bbclsimg




# In[108]:


def spatialfilter(clsimg, x, y, width, thd, nrow, ncol):
    
    x1=x-width
    x2=x+width+1
    if (x1<0):
        x1=0
        x2=x1+width*2+1
    if (x2>nrow):
        x2=nrow
        x1=nrow-width*2-1
    
    
    y1=y-width
    y2=y+width+1
    if (y1<0):
        y1=0
        y2=y1+width*2+1
    if (y2>ncol):
        y2=ncol
        y1=ncol-width*2-1
        
    cc=0
    pp=0
    ccp=np.zeros(4, dtype=np.int32)
    
    for row in range(x1, x2):
        for col in range(y1, y2):
            idx=row*ncol+col
            ilab=clsimg[idx]
            ccp[ilab]=ccp[ilab]+1
            if ((row==x) & (col==y)):
                ccp[ilab]=ccp[ilab]-1
                oldlab=ilab
                
            
    mid=ccp.argmax()        
    mcc=ccp[mid]
    
    if (mcc>=thd):
        return mid
    else:
        return oldlab
    
    
        


# In[109]:


def clusterclassifier(scaled_data, gresum, pnum, numcls, wateridx, nonwateridx, brightness, greenness, wetness):
    
    clsimg = np.zeros(pnum, dtype=np.int8)
    clsimg[wateridx]=-1
    clustering=KMeans(init='k-means++', precompute_distances=True, algorithm="full", n_clusters=numcls-1)
    clustering.n_jobs=6
    labels=clustering.fit(scaled_data)
    clsimg[nonwateridx]=labels.labels_
    clsimg[:]=clsimg[:]+1
   
    cc =np.zeros(numcls)
    greencc=np.zeros(numcls)
    brightcc=np.zeros(numcls)
    wetcc=np.zeros(numcls)
    #print(clsimg.shape[0], greenness.shape[0])
    for i in range(pnum):
        clab=clsimg[i]
        greencc[clab]=greencc[clab]+greenness[i]
        brightcc[clab]=brightcc[clab]+brightness[i]
        wetcc[clab]=wetcc[clab]+wetness[i]
        cc[clab]=cc[clab]+1
        
    for i in range(numcls):
        if (cc[i]>0):
            greencc[i]=greencc[i]/cc[i]
            brightcc[i]=brightcc[i]/cc[i]
            wetcc[i]=wetcc[i]/cc[i]
    
    
    greencc[0]=1000
    stidx = np.argsort(greencc)


    maps=np.zeros(numcls, dtype=np.int32)
    for i in range(numcls):
        k=numcls-1-i
        maps[stidx[k]]=i
    
    for i in range(pnum):
        clsimg[i]=maps[clsimg[i]]
    
    return clsimg



# In[110]:


def greenrate(clsimg, width, nrow, ncol):
    
    grate=np.zeros(pnum, dtype=np.float32)
    
    for x in range(nrow):
        for y in range(ncol):
            idx=x*ncol+y
            if (clsimg[idx]==1):
                grate[idx]=nbrate(clsimg, x, y, width, nrow, ncol)  

    return grate


# In[111]:


def spfilter(clsimg, width, thd, nrow, ncol):
    
    for x in range(nrow):
        for y in range(ncol):
            idx=x*ncol+y
            if (clsimg[idx]!=1):
                clsimg[idx]=spatialfilter(clsimg, x, y, width, thd, nrow, ncol)  
 
   


# In[112]:


def nbrate(clsimg, x, y, width, nrow, ncol):
    
    x1=x-width
    x2=x+width+1
    if (x1<0):
        x1=0
        x2=x1+width*2+1
    if (x2>nrow):
        x2=nrow
        x1=nrow-width*2-1
    
    
    y1=y-width
    y2=y+width+1
    if (y1<0):
        y1=0
        y2=y1+width*2+1
    if (y2>ncol):
        y2=ncol
        y1=ncol-width*2-1
        
    cc=0
    pp=0
    for row in range(x1, x2):
        for col in range(y1, y2):
            idx=row*ncol+col
            if (clsimg[idx]==1):
                pp=pp+1
            
            cc=cc+1
    
    rr=float(pp)/float(cc)
    #print(pp, cc, rr)
    return rr
    


# In[113]:


def copyoneblockdata(oneblockclsimg, clsimg, cors, ncol):
    x1=cors[0]
    x2=cors[1]
    y1=cors[2]
    y2=cors[3]
    brow=x2-x1
    bcol=y2-y1
    for x in range(x1, x2):
        mx=x-x1
        for y in range(y1, y2):
            my=y-y1
            clsimg[x*ncol+y] = oneblockclsimg[mx*bcol+my]
            
    


# In[114]:


def getrndcors(nrow, ncol, rowss, colss):
    cors=np.zeros(4)
    cors=cors.astype(np.int32)
    for i in range(100):
        x1=np.random.randint(nrow-rowss)
        y1=np.random.randint(ncol-colss)
        x2=x1+rowss
        y2=y1+colss
        
        if ((x2<=nrow) & (y2<=ncol)):
            break
        
    cors=[x1, x2, y1, y2]
    return cors    


# In[115]:


def oneblockvotes(oneblockclsimg, votes, mpcors, ncol):
    x1=mpcors[0]
    x2=mpcors[1]
    y1=mpcors[2]
    y2=mpcors[3]
    brow=x2-x1
    bcol=y2-y1
    for x in range(x1, x2):
        mx=x-x1
        for y in range(y1, y2):
            my=y-y1
            ilab = oneblockclsimg[mx*bcol+my]
            votes[x*ncol+y, ilab] = votes[x*ncol+y, ilab] + 1
            #print(votes[x*ncol+y, :])
    
    return votes


# In[116]:


def reassignlabels(clsimg, pnum, cutp):
    for i in range(pnum):
        clab=clsimg[i]
        if (clab>0):
            if (clab<cutp):
                clab=1
            else:
                clab=3
        clsimg[i]=clab
        
    #spfilter(clsimg, 1, 7, nrow, ncol)    
    
    width=2
    grate=greenrate(clsimg, width, nrow, ncol)

    grthd=0.7

    for i in range(pnum):
        ilab=clsimg[i]
        if (ilab==1):
            if (grate[i]<grthd):
                clsimg[i]=2        
    
    return clsimg        


# In[117]:


rp=5
#numcls=7

clsimg=classifyoneblock_spectral(data, cltdata, nrow, ncol, rp, numcls)
clsimg=clsimg.astype(np.int8)


# In[118]:



sprst=preprocessing.scale(data[:, 0:3])
cores=np.zeros([numcls,3])
dist=np.zeros([numcls,2])

  
for i in range(numcls):
    classidx=np.where(clsimg==i)[0]
    apm=sprst[classidx]
    cores[i, :]=apm.mean(axis=0)
 
  
for i in range(1, numcls):
    dist[i, 0]=np.sqrt(((cores[i, :]-cores[1,:])**2).sum(0))
    dist[i, 1]=np.sqrt(((cores[i, :]-cores[numcls-1,:])**2).sum(0))
  
  
mapcls=np.zeros(numcls)
mapcls=mapcls.astype(np.int8)

midpp=int(numcls/2)+1

for i in range(1, numcls):
    if (i<midpp):
        mapcls[i]=1
    else:
        mapcls[i]=3
      
          
imgfile = path+'/urban_spec_5c_raw.img'
clsimg.tofile(imgfile)

hdrfile = path+'/urban_spec_5c_raw.hdr'

commstr='cp '+sourcehdr+' '+hdrfile
os.system(commstr)



bbclsimg=mapcls[clsimg]
imgfile = path+'/urban_spec_5c.img'
bbclsimg.tofile(imgfile)



hdrfile = path+'/urban_spec_5c.hdr'

commstr='cp '+sourcehdr+' '+hdrfile

os.system(commstr)


