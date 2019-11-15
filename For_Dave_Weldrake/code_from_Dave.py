##This script automates the hydrograph check spreadsheet, whereby it marries up image dates with
##the flow on that date from the gauge, then checks if the image flow is on a rising limb and if
##any flow is greater than it within the past 21 days.
##This version has fixed parameters, will update to loop over various parameters to see how many
##images we can squeeze out - eventually.

import arcpy, os, sys, tempfile, time, string, re, csv
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")
from arcpy import env
from arcpy.sa import *
from socket import gethostname;
arcpy.env.overwriteOutput = True

outputfile = open(r"Z:\\Working\\NB_Landsat\\scripts\\automation\\imageflowsBOURKE.txt", "w")

antecedent = 21
flowmin = 500
multiplier = 1.3

#Read in WOFS image dates list as supplied by GA, needs to be in text format
wofslist = open('Z:\\Working\\NB_Landsat\\scripts\\automation\\145-031Dates.txt', 'r')
imnum = 0
counter = 0
for line1 in wofslist:
    colA1,colB1,colC1,colD1,colE1,colF1,colG1 = line1.strip().split("\t")
    imname = str(colB1)
    imnum = imnum + 1
    stardate1 = str(colG1)

    #Read in gauge timeseries, also in text format
    flownum = 0
    gauge = open('Z:\\Working\\NB_Landsat\\scripts\\automation\\Bourke.txt', 'r')
    for line2 in gauge:
        colA2,colB2,colC2,colD2,colE2,colF2 = line2.strip().split("\t")
        stardate2 = str(colD2)
        flownum = flownum + 1
        flow = float(colE2)
        datenum = int(colF2)

        #Combine and write out the gauge flow for date on which image was taken
        #step 2 uses this output file
        if stardate2 == stardate1 and flow > flowmin:
            counter = counter + 1
            print "Combining Dates with Flow for Image", imname
            outputfile.write(imname + "\t" + str(flow) + "\t" + str(flownum) + "\n")
            
    gauge.close()
outputfile.close()
wofslist.close()

#Read in the timeseries file and the output from above to check antecedent conditions
#and rising limb criteria
finalcount = 0
matchlist = open('Z:\\Working\\NB_Landsat\\scripts\\automation\\imageflowsBOURKE.txt', 'r')
finalimagelist = open(r"Z:\\Working\\NB_Landsat\\scripts\\automation\\SuccessListBOURKE.txt", "w")
for line3 in matchlist:
        colA3,colB3,colC3 = line3.strip().split("\t")
        imname2 = str(colA3)
        flow2 = float(colB3)
        imnum = int(colC3)

        passcrit = 0
        passcritsum = 0
        gauge2 = open('Z:\\Working\\NB_Landsat\\scripts\\automation\\Bourke.txt', 'r')
        for line4 in gauge2:
            colA4,colB4,colC4,colD4,colE4,colF4 = line4.strip().split("\t")
            stardate3 = str(colD4)
            flow3 = float(colE4)
            datenum2 = int(colF4)

            #Check if flow on the image date * multiplier is greater than at any time in the last 21 days.
            #Rejected if so, flag if ok or failed, then write to final output file.
            if imnum - datenum2 > 0 and imnum - datenum2 <= antecedent:
                if (flow3  - (flow2 * multiplier)) <= 0:
                        passcrit = 0
                elif (flow3 - (flow2 * multiplier)) > 0:
                        passcrit = 1        

                passcritsum = passcrit + passcritsum
                #print imname2,flow2,flow2*multiplier,flow3,imnum-datenum2,passcrit,passcritsum
                
        if passcritsum == 0:
                print imname2,"OK"
                finalcount = 1 + finalcount
                finalimagelist.write(imname2 + "\n")
        elif passcritsum > 0:
                print imname2,"FAIL"
                       
        gauge2.close()
print "Number of Suitable Images = ", finalcount
finalimagelist.close()
matchlist.close()

#Finally convert outputfile to CSV, python has trouble reading rasters from a textfile for some reason.
#Got this code from google, seems to work
txt_file = r"Z:\\Working\\NB_Landsat\\scripts\\automation\\SuccessListBOURKE.txt"
csv_file = r"Z:\\Working\\NB_Landsat\\scripts\\automation\\SuccessListBOURKE.csv"
in_txt = open(txt_file, "r")
out_csv = csv.writer(open(csv_file, 'wb'))
in_txt = csv.reader(open(txt_file, "rb"), delimiter = '\t')
out_csv = csv.writer(open(csv_file, 'wb'))
out_csv.writerows(in_txt)

