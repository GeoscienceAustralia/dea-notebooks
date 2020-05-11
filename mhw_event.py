# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 15:36:13 2019

@author: u56061
"""
import sys
import os
import numpy as np
from scipy.ndimage import label
import pandas as pd
import marineHeatWaves as mhw
from datetime import datetime
# read the csv file as a DataFrame


# the interpolation function
# interpolate gaps <= 2 days
def interpolatedSST(SSTData):
    
    i = 0
    dateList = []
    while i < SSTData.index.size:
        temp = SSTData.index[i]
        date = temp[1:9]
        dateList.append(date)
        i = i+1
    
    SSTData['date'] = dateList
    # the SST data missing the date of 20180213. the date needs to be inserted and interpolated if satsifying the condition 
    tempDF = pd.DataFrame({'date':['20180213']})
    SSTData = SSTData.append(tempDF)
    
    SSTData.set_index('date', inplace=True)
    SSTData.sort_index(inplace=True)
    
    SSTData_interpolated = pd.DataFrame()
    
    for col in SSTData.columns:
        arr1 = SSTData[col].values
        if np.isnan(arr1).all():
            print(col)
        else:
        
            # using the marineHeatWaves module's pad() function; Author: Eric Oliver
            arr1_interpolated = mhw.pad(arr1, maxPadLength=2)
            SSTData_interpolated[col] = arr1_interpolated
        
    SSTData_interpolated['date'] = SSTData.index.values
    SSTData_interpolated.set_index('date', inplace=True)
    return SSTData_interpolated
    
# the function calculates the SST diffences between the interpolated SST data and the 90% percentile data from the SSTAARS database
def calculate_sstDiff(SSTData,NinetyPData):
    
   
    sstDiff = pd.DataFrame()
    sstDiff['date'] = SSTData.index
    for id in SSTData.columns:
        diffL = []   
        i = 0
                    
        while i < SSTData.index.size:
            
            date = SSTData.index[i]
            month1 = str(date)[4:6]
            if month1 == '01':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Jan'][id]
            if month1 == '02':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Feb'][id]
            if month1 == '03':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Mar'][id]
            if month1 == '04':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Apr'][id]
            if month1 == '05':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['May'][id]
            if month1 == '06':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Jun'][id]
            if month1 == '07':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Jul'][id]
            if month1 == '08':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Aug'][id]
            if month1 == '09':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Sep'][id]
            if month1 == '10':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Oct'][id]
            if month1 == '11':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Nov'][id]
            if month1 == '12':
                sst_diff = SSTData.iloc[i][id] - NinetyPData.loc['Dec'][id]
                
            diffL.append(sst_diff)
            i = i + 1
        sstDiff[id] = diffL
    return sstDiff
        
## main function

def do_analysis(SSTFile, SST_90th_File, outDir):
    
    print(datetime.now())
    # 1. read the original SST data; 2. transpose the data; 3. drop the OBJECTID column; 4. conduct interpolation of the original SST data
    chunksize = 1000
 
    
    # create a dataframe to store the MHW characteristics for each point
    mhwDF1 = pd.DataFrame()
    #mhwEList = []
    idList = [] # PointID
    noEvents = [] # total number of MHWs events, within the study period
    noDays = [] # total number of MHWs days, within the study period
    totalIntensity = [] # tota accumulated MHWs intensity (oC)
    overallIntensity = [] # overall mean MHWs intensity (oC)
    
    # the event with the highest intensity
    highestIntensity = [] # the maximum intensity of the event (oC)
    date_start_HI = [] # # the start date of the event (as the day number since 20150101)
    duration_HI = [] # the duration of the event
    
    # the event with the longest duration
    largestDuration = [] # the duration of the event 
    date_start_LD = [] # the start date of the event (as the day number since 20150101)
    intensityLD = [] # the mean intensity of the event
    
    # the event with the largest mean intensity
    largestMeanIntensity = [] # the mean intensity of event
    date_start_LMI = [] # the start day of the event (as the day number since 20150101)
    duration_LMI = [] # the duration of the event
    
    # the event with the largest cumulative intensity
    largestCumIntensity = [] # the cumulative intensity of the event
    date_start_LCI = [] # the start day of the event (as the day number since 20150101)
    duration_LCI = [] # the duration of the event
    
    for chunk, chunk1 in zip(pd.read_csv(SSTFile, sep=',', header=0, index_col=1, chunksize=chunksize), pd.read_csv(SST_90th_File, sep=',', header=0, index_col=1, chunksize=chunksize)):
            
        test1T = chunk.T
        test1T = test1T.drop('OBJECTID')
        test1T_interpolated = interpolatedSST(test1T)
        
    
    # 1. read the SSTAARS 90th percentile data; 2. transpose the data; 3. drop the OBJECTID column;
    
        test90thT = chunk1.T
        test90thT = test90thT.drop('OBJECTID')
        
        
    
        i = 0
        monthList = []
        while i < test90thT.index.size:
            temp = test90thT.index[i]
            month = temp[17:]
            monthList.append(month)
            i = i+1
        
        test90thT['month'] = monthList
        test90thT.set_index('month', inplace=True)
        # calculate SST differences
        sstDiff_data = calculate_sstDiff(test1T_interpolated,test90thT)
        
        sstDiff_data.set_index('date', inplace=True)
        
    
        
        
        # loop through each Point
        for id in sstDiff_data.columns:
            print(str(id))
            idList.append(id)
            # create a dataframe to store characteristics of the MHWs events identified for this point
            mhwE = pd.DataFrame()
            date_start = []
            date_end = []
            duration = []
            
            # get the point values as a numpy array, the empty value is NaN
            point1 = sstDiff_data[id]
            point1V = point1.values
            dates = sstDiff_data.index.values
            
            # replace the NaN values with '-9999'
            point1V_1 = np.where(np.isnan(point1V),-9999,point1V)
            # convert negative values into 0 and positive values into 1
            point1V_1[point1V_1<=0] = False
            point1V_1[point1V_1>0] = True
            # label events: positive value(s)
            events, n_events = label(point1V_1)
            #print(events)
            #print(n_events)
            for ev in range(1,n_events+1):
                # calculate duration of an event
                event_duration = (events == ev).sum()
                # initially identify all events with duration of 4+ days
                # isolated 4-day event(s) will be eventually removed
                if event_duration > 3:
        
                    date_start.append(dates[np.where(events == ev)[0][0]])
                    date_end.append(dates[np.where(events == ev)[0][-1]])
                    duration.append(event_duration)
            # the initial list of mhwE
            mhwE['date_start'] = date_start
            mhwE['date_end'] = date_end
            mhwE['duration'] = duration
        
            # combine ajacent event(s) if they satisfy the criteria, this creates an updated list
            i = 0
            while i < mhwE.index.size - 1:
            
                date1 = datetime.strptime(str(mhwE.iloc[i+1]['date_start']),'%Y%m%d')
                date2 = datetime.strptime(str(mhwE.iloc[i]['date_end']),'%Y%m%d')
                gap = (date1 - date2).days
                if gap < 3:
                    # condition 1: [>=5 hot, 1 cool, 4 hot]; condition 2: [4 hot, 1 cool, >=5 hot]; condition 3: [>=5 hot, 1 cool, >=5 hot]
                    if (mhwE.iloc[i]['duration'] >= 5 and mhwE.iloc[i+1]['duration'] == 4) or  (mhwE.iloc[i]['duration'] == 4 and mhwE.iloc[i+1]['duration'] >=5) or  (mhwE.iloc[i]['duration'] >= 5 and mhwE.iloc[i+1]['duration'] >= 5):
                        mhwE['date_end'][i] = mhwE['date_end'][i+1]
                        mhwE = mhwE.drop(i+1)
                        mhwE = mhwE.reset_index(drop=True)
                        i = i
                    else:
                        i = i + 1
                elif gap < 4:
                    # condition 4: [>=5 hot, 2 cool, >=5 hot]
                    if (mhwE.iloc[i]['duration'] >= 5 and mhwE.iloc[i+1]['duration'] >= 5):              
                        mhwE['date_end'][i] = mhwE['date_end'][i+1]
                        mhwE = mhwE.drop(i+1)
                        mhwE = mhwE.reset_index(drop=True)
                        i = i
                    else:
                        i = i + 1
                else:
                    i = i + 1
            
            # drop the isolated event(s) with a duration of 4 days from the list
            i = 0
            while i < mhwE.index.size:
                date1 = datetime.strptime(str(mhwE.iloc[i]['date_start']),'%Y%m%d')
                date2 = datetime.strptime(str(mhwE.iloc[i]['date_end']),'%Y%m%d')
                duration = (date2 - date1).days + 1
                if duration == 4:
                    mhwE = mhwE.drop(i)
                    mhwE = mhwE.reset_index(drop=True)
                    i = i
                else:
                    i = i + 1
                
            # update the durations of the final list
            i = 0
            while i < mhwE.index.size:
                date1 = datetime.strptime(str(mhwE.iloc[i]['date_start']),'%Y%m%d')
                date2 = datetime.strptime(str(mhwE.iloc[i]['date_end']),'%Y%m%d')
                duration = (date2 - date1).days + 1
                mhwE['duration'][i] = duration
                i = i + 1
            
            # calculate mhw properties: intensity max, intensity mean, intensity std, 
            # cumulative intensity, onset rate and decline rate
            intensity_max = []
            intensity_mean = []
            intensity_std = []
            intensity_cumulative = []
        
            onset_rate = []
            decline_rate = []
            i = 0
            while i < mhwE.index.size:
                intensity_values = []
                date_values = []
                startDate = mhwE.iloc[i]['date_start']
                endDate = mhwE.iloc[i]['date_end']
                duration = mhwE.iloc[i]['duration']
                
                j = 0
                while j < sstDiff_data.index.size:
                    
                    date1 = dates[j]
                    if startDate == date1:
                        k = j + int(duration)
                        
                        while j < k:
                            
                            sst_diff = point1V[j]
                            intensity_values.append(sst_diff)
                            dateV = dates[j]
                            date_values.append(dateV)
                            j = j + 1
                    else:
                        j = j + 1
            #    print('event', i, ':', intensity_values)
                np_intensity = np.array(intensity_values)
                np_date = np.array(date_values)
                
                startDiff = np_intensity[0]
                endDiff = np_intensity[-1]
                maxDiff = np_intensity.max()
                meanDiff = np_intensity.mean()
                stdDiff = np_intensity.std()
                cumDiff = np_intensity.sum()
                
                peakDate = np_date[np_intensity == maxDiff][0]
                
                dateDiff1 = (datetime.strptime(str(peakDate),'%Y%m%d') - 
                            datetime.strptime(str(startDate),'%Y%m%d')).days
                if dateDiff1 > 0:        
                    rateOnset = (maxDiff - startDiff) / dateDiff1
                else: # the start date is the peak date
                    rateOnset = maxDiff / 0.5
                
                dateDiff2 = (datetime.strptime(str(endDate),'%Y%m%d') - 
                            datetime.strptime(str(peakDate),'%Y%m%d')).days
                if dateDiff2 > 0:        
                    rateDecline = (maxDiff - endDiff) / dateDiff2
                else: # the end date is the peak date
                    rateDecline = maxDiff / 0.5
                
                
                intensity_max.append(maxDiff)
                intensity_mean.append(meanDiff)
                intensity_std.append(stdDiff)
                intensity_cumulative.append(cumDiff)
        
                onset_rate.append(rateOnset)
                decline_rate.append(rateDecline)
                i = i + 1
            
            mhwE['maxIntensity'] = intensity_max
            mhwE['meanIntensity'] = intensity_mean
            mhwE['stdIntensity'] = intensity_std
            mhwE['cumIntensity'] = intensity_cumulative
        
            mhwE['onsetRate'] = onset_rate
            mhwE['declineRate'] = decline_rate
            
            # save the MHWs events identified for the point into a CSV file
            filename = os.path.join(outDir, 'mhw_' + str(id) + '.csv')
            mhwE.to_csv(filename, sep=',', index=False)
        
        #   geneate the summary characteristics of the MHWs    
        #    mhwEList.append(mhwE)
            if mhwE.index.size > 0:
                
                noEvents.append(mhwE.index.size)
                noDays.append(mhwE['duration'].sum())
                totalIntensity.append(mhwE['cumIntensity'].sum())
                overallIntensity.append(mhwE['cumIntensity'].sum()/mhwE['duration'].sum())
                
                tempDate = mhwE[mhwE['maxIntensity'] == mhwE['maxIntensity'].max()].iloc[0]['date_start']
                HIDate = pd.to_datetime(tempDate, format='%Y%m%d').toordinal() - 735599 # date number since 20150101
                HIDuration = mhwE[mhwE['maxIntensity'] == mhwE['maxIntensity'].max()].iloc[0]['duration']
                highestIntensity.append(mhwE['maxIntensity'].max())
                date_start_HI.append(HIDate)
                duration_HI.append(HIDuration)
                
                tempDate = mhwE[mhwE['duration'] == mhwE['duration'].max()].iloc[0]['date_start']
                LDDate = pd.to_datetime(tempDate, format='%Y%m%d').toordinal() - 735599
                intensityLDV = mhwE[mhwE['duration'] == mhwE['duration'].max()].iloc[0]['meanIntensity']
                largestDuration.append(mhwE['duration'].max())
                date_start_LD.append(LDDate)
                intensityLD.append(intensityLDV)
                
                
                tempDate = mhwE[mhwE['meanIntensity'] == mhwE['meanIntensity'].max()].iloc[0]['date_start']
                LMIDate = pd.to_datetime(tempDate, format='%Y%m%d').toordinal() - 735599
                LMIDuration = mhwE[mhwE['meanIntensity'] == mhwE['meanIntensity'].max()].iloc[0]['duration']
                largestMeanIntensity.append(mhwE['meanIntensity'].max())
                date_start_LMI.append(LMIDate)
                duration_LMI.append(LMIDuration)    
            
            
                tempDate = mhwE[mhwE['cumIntensity'] == mhwE['cumIntensity'].max()].iloc[0]['date_start']
                LCIDate = pd.to_datetime(tempDate, format='%Y%m%d').toordinal() - 735599
                LCIDuration = mhwE[mhwE['cumIntensity'] == mhwE['cumIntensity'].max()].iloc[0]['duration']
                largestCumIntensity.append(mhwE['cumIntensity'].max())
                date_start_LCI.append(LCIDate)
                duration_LCI.append(LCIDuration)
            else:
                noEvents.append(0)
                noDays.append(0)
                totalIntensity.append(0)
                overallIntensity.append(0)
                
                highestIntensity.append(0)
                date_start_HI.append(0)
                duration_HI.append(0)
                
      
                largestDuration.append(0)
                date_start_LD.append(0)
                intensityLD.append(0)
                
                
    
                largestMeanIntensity.append(0)
                date_start_LMI.append(0)
                duration_LMI.append(0)    
            
            
    
                largestCumIntensity.append(0)
                date_start_LCI.append(0)
                duration_LCI.append(0)            
        
        
    # populate the dataframe 
    mhwDF1['pointID'] = idList
    #mhwDF1['MHWs'] = mhwEList
    mhwDF1['noEvents'] = noEvents
    mhwDF1['noDays'] = noDays
    mhwDF1['totalIntensity'] = totalIntensity
    mhwDF1['overallIntensity'] = overallIntensity
    
    mhwDF1['highestIntensity'] = highestIntensity
    mhwDF1['date_start_HI'] = date_start_HI
    mhwDF1['duration_HI'] = duration_HI
    
    mhwDF1['largestDuration'] = largestDuration
    mhwDF1['date_start_LD'] = date_start_LD
    mhwDF1['intensityLD'] = intensityLD
    
    mhwDF1['largestMeanIntensity'] = largestMeanIntensity
    mhwDF1['date_start_LMI'] = date_start_LMI
    mhwDF1['duration_LMI'] = duration_LMI
    
    mhwDF1['largestCumIntensity'] = largestCumIntensity
    mhwDF1['date_start_LCI'] = date_start_LCI
    mhwDF1['duration_LCI'] = duration_LCI
    
          
    # save the summary characteristics to a CSV file
    mhwDF1.to_csv(os.path.join(outDir, 'results' + SSTFile[17:20] + '.csv'), sep=',', index=False) 
    print(datetime.now())
    

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.001'
SST_90th_File = 'O:/temp/mhw5/ninty.001'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.002'
SST_90th_File = 'O:/temp/mhw5/ninty.002'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.004'
SST_90th_File = 'O:/temp/mhw5/ninty.004'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.013'
SST_90th_File = 'O:/temp/mhw5/ninty.013'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.014'
SST_90th_File = 'O:/temp/mhw5/ninty.014'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.015'
SST_90th_File = 'O:/temp/mhw5/ninty.015'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.037'
SST_90th_File = 'O:/temp/mhw5/ninty.037'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.038'
SST_90th_File = 'O:/temp/mhw5/ninty.038'
do_analysis(SSTFile, SST_90th_File, outDir)

outDir = 'O:/temp/mhw5' 
SSTFile = 'O:/temp/mhw5/sst.039'
SST_90th_File = 'O:/temp/mhw5/ninty.039'
do_analysis(SSTFile, SST_90th_File, outDir)

