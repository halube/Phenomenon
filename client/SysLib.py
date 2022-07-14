#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#%matplotlib inline
#### SysLib.py description####
#### Author: Hans Bethge and Patrick Lüdeke
#### Description: Client/Master Library fuse Sensor.py/Sensor and Server.py/Motion; contains all function for automated phenotyping   
#### Required libraries:
import os
import numpy as np
import cv2
from matplotlib import pyplot as plt
from plantcv import plantcv as pcv
from plantcv.plantcv import params
from plantcv.plantcv import fatal_error
import glob
import os.path
import urllib.request 
from urllib.request import urlopen
import json
from time import sleep
from datetime import datetime, timedelta
import requests
import urllib


# In[ ]:


############### Empty list constants ###############
NewPositionsList=[]
NewPositionsListallOther=[]
finalList=[]
FinalList=[]
Unconsidered=[]
PlantList=[]
SpecList=[]
pcv.params.debug = 'none'

###############Data structure######################
def CreateMainFolder():
    for i in range(1,100):
        if not os.path.exists('output/Experiment_'+str(i)):
            os.makedirs('output/Experiment_'+str(i))
            break
        else:
            i=i+1
    return i

############### MotionController Linear system Constants ###################
XMax = 640 # max in the X direction
YMax = 275  # max in the Y direciton
ZMax = -60

############### RGB Image Constants ###############
ImageZ=-40 
PlantXMM2Pixel=0.0354  ### Z=-40 ~75 mm/ 2800
PlantYMM2Pixel=0.035   ### Z=-40 ~75 mm/ 2800
VesselXMM2Pixel=0.0265 ### Z=-40 ~75 mm/ 2800
VesselYMM2Pixel=0.0261 ### Z=-40 ~75 mm/ 2800

############### Thermal Image Constants ###############
ThermalXShift=+30
ThermalYShift=0 #####-37

############### Depth Scan Constants ###############
DepthXShift=+87
DepthYShift=+17
Scanpattern=50

############### Spectral measurement Constants ###############
SpecXShift=-32
SpecYShift=+8
XWhiteRefObj=0
YWhiteRefObj=265
XDarkRefObj=150
YDarkRefObj=265
Wavelength=[305,308,310,313,316,319,321,324,327,329,332,335,337,340,343,345,348,351,353,356,359,361,364,367,369,372,375,377,380,383,385,388,390,393,396,398,401,403,406,409,411,414,416,419,421,424,427,429,432,434,437,439,442,444,447,449,452,454,457,459,462,464,467,469,472,474,477,479,482,484,487,489,491,494,496,499,501,504,506,508,511,513,515,518,520,523,525,527,530,532,534,537,539,541,544,546,548,551,553,555,557,560,562,564,566,569,571,573,575,578,580,582,584,587,589,591,593,595,597,600,602,604,606,608,610,613,615,617,619,621,623,625,627,629,631,634,636,638,640,642,644,646,648,650,652,654,656,658,660,662,664,666,668,670,672,674,676,678,679,681,683,685,687,689,691,693,695,696,698,700,702,704,706,708,709,711,713,715,717,718,720,722,724,725,727,729,731,732,734,736,738,739,741,743,744,746,748,750,751,753,755,756,758,759,761,763,764,766,768,769,771,772,774,776,777,779,780,782,783,785,786,788,789,791,792,794,795,797,798,800,801,803,804,806,807,809,810,812,813,814,816,817,819,820,822,823,824,826,827,828,830,831,833,834,835,837,838,839,841,842,843,845,846,847,848,850,851,852,854,855,856,857,859,860,861,862,864,865,866,867,869,870,871,872,873,875,876,877]

############### Automated Vessel detection Scan Constants ###############
XMargin = 10
YMargin = 10
XStep = 20   
YStep = 20   
ScanZ= -6 
YDirection = 1
CircularityIndex=11
minRadius=975
maxRadius=1050

############### Biological Experiment Constants ###############
NumberOfExplantsperVessel=4

############### DEBUG Functions #########################
def showColorimage (Bild):
    plt.imshow(cv2.cvtColor(Bild, cv2.COLOR_BGR2RGB))
    plt.show()
    
def showGrayimage (Bild):
    plt.imshow(Bild, cmap=plt.cm.gray)
    plt.show()

############### Motion Functions ###############
def setupZAxis(Z=0):
    if ZMax<=Z<=0:
        requests.get('http://10.0.8.2:8000/api/v1/axis/z/abs/{0}'.format(Z))
    else:
        print ("Set position exceeds system limits XMax / Y Max / ZMax")
        
def goToHome(): 
    requests.get('http://10.0.8.2:8000/api/v1/home')
    
def goToPosition(x,y):
    if XMax>=x>=0 and YMax>=y>=0:
        requests.get('http://10.0.8.2:8000/api/v1/axis/xy/abs/{0}/{1}'.format(x,y))
        return True
    else:
        print ("Set position exceeds system limits XMax / Y Max / ZMax")
        return False
    
def goToSleepPos():
    requests.get('http://10.0.8.2:8000/api/v1/axis/xyz/abs/630/260/0')
    
def setX(x):
    if XMax>=x>=0:
        requests.get('http://10.0.8.2:8000/api/v1/axis/x/abs/{0}'.format(x))
        return True
    else:
        print ("Set position exceeds system limits XMax / Y Max / ZMax")
        return False
def setY(y):
    if YMax>=y>=0:
        requests.get('http://10.0.8.2:8000/api/v1/axis/y/abs/{0}'.format(y))
        return True
    else:
        print ("Set position exceeds system limits XMax / Y Max / ZMax")
        return False
    
def setZ(z):
    if ZMax<=z<=0:
        requests.get('http://10.0.8.2:8000/api/v1/axis/z/abs/{0}'.format(z))
        return True
    else:
        print ("Set position exceeds system limits XMax / Y Max / ZMax")
        return False

############### Sensor Reads Functions ######################        
def getRgb(name,ExperimentNr,debug):
    requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/on')
    #requests.get('http://10.0.8.3:8000/api/v1/light/white/on')
    #requests.get('http://10.0.8.3:8000/api/v1/light/uv/on')
    urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/rgb/jpg", "temp.png")
    #requests.get('http://10.0.8.3:8000/api/v1/light/white/off')
    #requests.get('http://10.0.8.3:8000/api/v1/light/uv/off')
    requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/off')
    img= cv2.imread('temp.png')
    if debug==True:
        if not os.path.exists('output/'+str(ExperimentNr)+'/Scan'):
            os.makedirs('output/'+str(ExperimentNr)+'/Scan')
        cv2.imwrite('output/{0}/Scan/{1}.{2}'.format(ExperimentNr,name,".png"),img)
    return img

def CheckIfNightImage():
    urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/rgb/png", "temp.png")
    img = cv2.imread('temp.png')
    print(np.average(img))
    Intensity=np.average(img)
    if np.average(img)<5:
        return True,Intensity
    else:
        return False,Intensity

def ImageRGBReadPNG(State):
    setZ(ImageZ)
    if State==False:
        requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/on')
        urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/rgb/png", "temp.png")
        requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/off')
        img = cv2.imread('temp.png')
        setZ(ScanZ)
        return img
    else:
        requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/on')
        requests.get('http://10.0.8.3:8000/api/v1/light/white/on')
        requests.get('http://10.0.8.3:8000/api/v1/light/red/on')
        urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/rgb/png", "temp.png")
        requests.get('http://10.0.8.3:8000/api/v1/light/white/off')
        requests.get('http://10.0.8.3:8000/api/v1/light/red/off')
        requests.get('http://10.0.8.2:8000/api/v1/DiffuseRingLight/off')
        img = cv2.imread('temp.png')
        setZ(ScanZ)
        return img
    

def ImageThermalRead():
    setZ(ImageZ)
    urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/thermal/Test", "thermal_temp.tif")
    img = cv2.imread('thermal_temp.tif',-1 )
    if np.average(img)<26000:
        urllib.request.urlretrieve("http://10.0.8.3:8000/api/v1/thermal/Test", "thermal_temp.tif")
        img = cv2.imread('thermal_temp.tif',-1 )
    img = cv2.rotate(img, cv2.ROTATE_180)
    setZ(ScanZ)
    return img
    

def LaserRead():
    #setZ(ImageZ+10)
    with urlopen("http://10.0.8.3:8000/api/v1/laser/read") as response:
        response_content = response.read()
        response_content.decode('utf-8')
        Temp_Depth = json.loads(response_content)
        Temp_Depth=Temp_Depth[0]
    return Temp_Depth
    #setZ(ScanZ)

def SpecRead(State):
    if State==True:
        ##### Measure Sample or WhiteRef signal #####
        setZ(ImageZ+10)
        requests.get('http://10.0.8.3:8000/api/v1/spec/integration/55')
        requests.get('http://10.0.8.3:8000/api/v1/spec/led/white/on')
        sleep(2)
        with urlopen("http://10.0.8.3:8000/api/v1/spec/spec") as response:
            response_content = response.read()
            response_content.decode('utf-8')
            Temp_Spec = json.loads(response_content)
        requests.get('http://10.0.8.3:8000/api/v1/spec/led/white/off')
        return Temp_Spec
        #setZ(ScanZ)
    else:
        ##### Measure Dark signal #####
        setZ(ImageZ+10)
        requests.get('http://10.0.8.3:8000/api/v1/spec/integration/55')
        sleep(2)
        with urlopen("http://10.0.8.3:8000/api/v1/spec/spec") as response:
            response_content = response.read()
            response_content.decode('utf-8')
            Temp_Spec = json.loads(response_content)
        return Temp_Spec
    setZ(ScanZ)

def SpecReadFluor(State):
    if State==True:
        ##### Measure Sample or WhiteRef signal #####
        setZ(ImageZ+10)
        requests.get('http://10.0.8.3:8000/api/v1/spec/integration/300')
        requests.get('http://10.0.8.3:8000/api/v1/light/uv/on')
        sleep(2)
        with urlopen("http://10.0.8.3:8000/api/v1/spec/spec") as response:
            response_content = response.read()
            response_content.decode('utf-8')
            Temp_Spec = json.loads(response_content)
        requests.get('http://10.0.8.3:8000/api/v1/light/uv/off')
        return Temp_Spec
        setZ(ScanZ)
    else:
        ##### Measure Dark signal #####
        setZ(ImageZ+10)
        requests.get('http://10.0.8.3:8000/api/v1/spec/integration/300')
        sleep(2)
        with urlopen("http://10.0.8.3:8000/api/v1/spec/spec") as response:
            response_content = response.read()
            response_content.decode('utf-8')
            Temp_Spec = json.loads(response_content)
        return Temp_Spec
    setZ(ScanZ)
    
##########Image Processing###################
def rgb2Hsv (Bild):
    h = pcv.rgb2gray_hsv(rgb_img=Bild, channel='h')
    s = pcv.rgb2gray_hsv(rgb_img=Bild, channel='s')
    v = pcv.rgb2gray_hsv(rgb_img=Bild, channel='v')
    return h,s,v

def rgb2Lab(Bild):
    l = pcv.rgb2gray_lab(rgb_img=Bild, channel='l')
    a = pcv.rgb2gray_lab(rgb_img=Bild, channel='a')
    b = pcv.rgb2gray_lab(rgb_img=Bild, channel='b')
    return l,a,b

def applyMasktoColorImage(Bild,Mask):
    masked = pcv.apply_mask(Bild, mask=Mask, mask_color='black')
    return masked
    
def ThresOtsuBinary(GRAYIMG):
    threshold = pcv.threshold.otsu(gray_img=GRAYIMG, max_value=255, object_type='dark')
    fill_image = pcv.fill(bin_img=threshold, size=1000000)
    if not np.average(fill_image)==0:
        fill_image_blur = cv2.medianBlur(fill_image,51)
        return fill_image_blur
    else:
        return 0
    
def selectPlantpixelwithOtsu(Bild):
        Hsv=rgb2Hsv(Bild)
        img_binary = pcv.threshold.otsu(gray_img=Hsv[0], max_value=255, object_type='dark')
        img_binary = pcv.fill(bin_img=img_binary, size=1000)
        Plant_mask = pcv.dilate(gray_img=img_binary, ksize=2, i=1)
        return Plant_mask    

def findCircularObjects(ORGINALCOLORIMG,GRAYIMG,debug):
    height, width, channels = ORGINALCOLORIMG.shape
    midpoint=[width*0.5,height*0.5]    
    # Apply hough transform on the image
    circles = cv2.HoughCircles(GRAYIMG, cv2.HOUGH_GRADIENT, 0.1,4000, ORGINALCOLORIMG.shape[0]/64, param1=200, param2=CircularityIndex, minRadius=minRadius, maxRadius=maxRadius)
    circle=circles[0][0]
    # Draw detected circles
    if circles.shape[0]<=1:
        deviation_pixel=[midpoint[0]-circle[0],midpoint[1]-circle[1]]
        ####MM2Pixel=75 mm/ 2300=0.035#######
        deviation_mm=deviation_pixel[0]*VesselXMM2Pixel,deviation_pixel[1]*VesselYMM2Pixel
        deviation_mm=np.round(deviation_mm, 1)
        deviation_mm_x=deviation_mm[0]
        deviation_mm_y=deviation_mm[1]
        circles = np.uint16(np.around(circles))
        if -15<deviation_mm_x<15 and -15<deviation_mm_y<15:
            if debug==True:
                for i in circles[0, :]:
                    cv2.circle(ORGINALCOLORIMG, (i[0], i[1]), i[2], (0, 255, 0), 10)
                    print(i[2])
            return True,deviation_mm_x,deviation_mm_y
        else:
            for i in circles[0, :]:
                    cv2.circle(ORGINALCOLORIMG, (i[0], i[1]), i[2], (0, 255, 0), 10)
                    print(i[2])
                    cv2.circle(ORGINALCOLORIMG, (i[0], i[1]), 2, (0, 0, 255), 50)
            return False,deviation_mm_x,deviation_mm_y
    else:
        return False,False,False


def CheckScanforVessels(img, XPos, YPos):
    Hsv=rgb2Hsv (img)
    Img_ThresOtsuBinary=ThresOtsuBinary(Hsv[2])
    if np.average(Img_ThresOtsuBinary)>50:
        results=findCircularObjects(img,Img_ThresOtsuBinary,True)
        showGrayimage(Img_ThresOtsuBinary)
        print(results)
        if results[0]==True:
                NewPositions=[XPos,results[1],XPos-results[1],YPos,results[2],YPos+results[2]]
                print(results)
                if not NewPositionsList:
                        NewPositionsList.append(NewPositions)
                else:
                    for i in range(0,len(NewPositionsList)):
                        if (NewPositionsList[i][2]+38)>NewPositions[2]>(NewPositionsList[i][2]-38) and (NewPositionsList[i][5]+38)>NewPositions[5]>(NewPositionsList[i][5]-38):
                            NewPositionsListallOther.append(NewPositions)
                            break
                        else:
                            i=i+1
                        if i == len(NewPositionsList):
                            NewPositionsList.append(NewPositions)
        if results[0]==False and results[1]!=False:
            print(results)
            NewPositions=[XPos,results[1],XPos-results[1],YPos,results[2],YPos+results[2]]
            NewPositionsListallOther.append(NewPositions)

def Scan(ExperimentNr):
    #########Homeing##########
    print("Homing...")
    goToHome()
    ExperimentNr=ExperimentNr
    print("Homing done.")
    curZ=ScanZ    
    setupZAxis(ScanZ)
    print("Scanning...")
    curX = XMargin
    curY = YMargin
    global YDirection
    ############Scan program###############    
    while curX <= XMax - XMargin:
        if YDirection == 1:  
            print("X:{0} Y:{1}".format(curX,curY))
            goToPosition(curX, curY)
            img=getRgb('Scan_X_{0}_Y_{1}_Z_{2}'.format(curX, curY,curZ),ExperimentNr,True)
            CheckScanforVessels(img, curX, curY)
            while (curY + YStep) <= YMax - YMargin:
                curY += YStep
                print("X:{0} Y:{1}".format(curX,curY))
                goToPosition(curX, curY)
                img=getRgb('Scan_X_{0}_Y_{1}_Z_{2}'.format(curX, curY,curZ),ExperimentNr,True)
                CheckScanforVessels(img, curX, curY)
        else:
            print("X:{0} Y:{1}".format(curX,curY))
            goToPosition(curX, curY)
            img=getRgb('Scan_X_{0}_Y_{1}_Z_{2}'.format(curX, curY,curZ),ExperimentNr,True)
            CheckScanforVessels(img, curX, curY)
            while (curY - YStep) >= YMargin :
                curY -= YStep
                print("X:{0} Y:{1}".format(curX,curY))
                goToPosition(curX, curY)
                img=getRgb('Scan_X_{0}_Y_{1}_Z_{2}'.format(curX, curY,curZ),ExperimentNr,True)
                CheckScanforVessels(img, curX, curY)
        YDirection *= -1
        curX += XStep
    curX=XMargin
    curY=YMargin
    print("Scan done.")
    print("Finished!")
            
def ProduceFinalList(NewPositionsList,NewPositionsListallOther,m):
    #######Local variables#####
    ExperimentNr='Experiment'+'_'+str(m)
    VesselID=0
    FinalList=[]
    #####Functions#####
    for z in range(0,len(NewPositionsListallOther)):
            NewPositionsListallOther[z].append([])
            NewPositionsListallOther[z][6]="False"
    for i in range(0,len(NewPositionsList)):
        Xnew=[NewPositionsList[i][2]]
        Ynew=[NewPositionsList[i][5]]
        for z in range(0,len(NewPositionsListallOther)):
            if (Xnew[0]+20)>NewPositionsListallOther[z][2]>(Xnew[0]-20) and (Ynew[0]+20)>NewPositionsListallOther[z][5]>(Ynew[0]-20):
                Xnew.append(NewPositionsListallOther[z][2])
                Ynew.append(NewPositionsListallOther[z][5])
                NewPositionsListallOther[z][6]="True"
        X=int(np.round(np.mean(Xnew),0))
        Y=int(np.round(np.mean(Ynew),0))
        finalList.append([X,Y])
    finalList.sort()
    for z in range(0,len(finalList)):
        VesselID=z+1
        finalList[z].append(VesselID)
    for z in range(0,len(NewPositionsListallOther)):
            if NewPositionsListallOther[z][6]=="False":
                Unconsidered.append(NewPositionsListallOther[z])
    np.savetxt('output/'+ExperimentNr+'/FinalList.txt', finalList, newline='\r\n', delimiter=',', fmt="%s")

def findObjects(Bild,Mask):
    #####Functions#####
    img_copy=Bild
    height, width, channels = img_copy.shape
    midpoint=[width*0.5,height*0.5]  
    contours, hierarchy= cv2.findContours(Mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for i in range (0,len(contours)):
        cv2.drawContours(img_copy, contours[i], -1, (0,0,255), thickness = 5)
    NumberofObjects = len(contours)
    Center=[]
    if len(contours)>NumberOfExplantsperVessel:
        N = NumberOfExplantsperVessel
        TopExplants = contours[:N]
        NumberofObjectsTopExplants = len(TopExplants)
    else:
        for c in contours:
            #calculate moments for each contour
            M = cv2.moments(c)
            # calculate x,y coordinate of center
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(img_copy, (cX, cY), 5, (255, 255, 255), 25)
            cv2.putText(img_copy, "centroid", (cX - 10, cY - 50),cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 10)
            deviation_pixel=[midpoint[0]-cX,midpoint[1]-cY]
            deviation_mm=deviation_pixel[0]*PlantXMM2Pixel,deviation_pixel[1]*PlantYMM2Pixel
            deviation_mm=np.round(deviation_mm, 1)
            deviation_mm_x=deviation_mm[0]
            deviation_mm_y=deviation_mm[1]
            Center.append([deviation_mm_x,deviation_mm_y])
        NumberofObjectsTopExplants=NumberofObjects
        TopExplantsCenter=Center
    if len(contours)>NumberOfExplantsperVessel:
        contours=TopExplants
        TopExplantsCenter=[]
        for c in contours:
            # calculate moments for each contour
            M = cv2.moments(c)
            # calculate x,y coordinate of center
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(img_copy, (cX, cY), 5, (255, 255, 255), 25)
            cv2.putText(img_copy, "centroid", (cX - 10, cY - 50),cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 10)
            deviation_pixel=[midpoint[0]-cX,midpoint[1]-cY]
            deviation_mm=deviation_pixel[0]*PlantXMM2Pixel,deviation_pixel[1]*PlantYMM2Pixel
            deviation_mm=np.round(deviation_mm, 1)
            deviation_mm_x=deviation_mm[0]
            deviation_mm_y=deviation_mm[1]
            TopExplantsCenter.append([deviation_mm_x,deviation_mm_y])
    return NumberofObjects,NumberofObjectsTopExplants,Center,TopExplantsCenter 

def maskPixelStats(Bild,Mask):
    #Calculate Pixel statistics of mask
    FoundObjects,FoundObjectsTopExplants,Center,CenterTopExplants=findObjects(Bild,Mask)
    obj_area=cv2.countNonZero(Mask)
    print ('Object Area=', obj_area)
    height, width, channels = Bild.shape
    TotalPixels=height*width
    print ('Total Pixel=', TotalPixels)
    degree_of_coverage=obj_area/TotalPixels*100
    print ('degree_of_coverage=', degree_of_coverage)
    print ('Objects found:', FoundObjects)
    for i in range(len(Center)):
        print(str(Center[i]))
    print ('ObjectsTopExplants found:', FoundObjectsTopExplants)
    for i in range(len(CenterTopExplants)):
        print(str(CenterTopExplants[i]))           
    return CenterTopExplants
            

        
def GoToNewPositionStoredinList(FinalList,m):
    ExperimentNr='Experiment'+'_'+str(m)
    for i in range(0,len(FinalList)):
        print("Check list for found vessel")
        Xnew=FinalList[i][0]
        print("X:",Xnew)
        Ynew=FinalList[i][1]
        print("Y:",Ynew)
        if XMax>=Xnew>=0 and YMax>=Ynew>=0:
            print("New vessel position and capture new image")
            goToPosition(Xnew, Ynew)
            img=ImageRGBReadPNG(False)
            img_copy=img
            #showColorimage(img)
            Plant_mask_presumed=selectPlantpixelwithOtsu(img_copy)
            CenterTopExplants=maskPixelStats(img_copy,Plant_mask_presumed)
            Xcurrent=FinalList[i][0]
            Ycurrent=FinalList[i][1]
            Zcurrent=ImageZ
            VesselIDcurrent=FinalList[i][2]
            if not os.path.exists('output/'+ExperimentNr+'/VesselID_'+str(VesselIDcurrent)):
                print('output/'+ExperimentNr+'/VesselID_'+str(VesselIDcurrent))
                os.makedirs('output/'+ExperimentNr+'/VesselID_'+str(VesselIDcurrent))
            for q in range(0,len(CenterTopExplants)):
                PlantID=str(VesselIDcurrent)+"."+str(q)
                Xnew=Xcurrent-CenterTopExplants[q][0]
                Ynew=Ycurrent+CenterTopExplants[q][1]
                PlantListArray=[Xnew,Ynew,PlantID]
                PlantList.append(PlantListArray)    
            f=str("VesselID_"+str(VesselIDcurrent)+"_X_"+str(Xcurrent)+"_Y_"+str(Ycurrent)+"_Z_"+str(Zcurrent))
            cv2.imwrite('output/'+ExperimentNr+'/VesselID_{0}/{1}.{2}'.format(VesselIDcurrent,f,"png"),img)
        else:
            print("Vessel midpoint out of range!")
    np.savetxt('output/'+ExperimentNr+'/PlantList.txt', PlantList, newline='\r\n', delimiter=',', fmt="%s")    
    
def VisulizeCirclesPlot(FinalList,m):
        ExperimentNr='Experiment'+'_'+str(m)
        fig, ax = plt.subplots(figsize=(13, 6))
        SystemArea = plt.Rectangle([-75, -145], 850, 590, fill=None, edgecolor="Black",alpha=1,linewidth=5)
        Detector = plt.Rectangle([-10, -10], 20, 20, facecolor="Black", edgecolor="Black",alpha=1,linewidth=1)
        SystemArea2 = plt.Rectangle([-75, -145], 850, 160, fill=None, edgecolor="Black",alpha=1,linewidth=5)
        ScanArea = plt.Rectangle([-70, -53], 850, 366, facecolor="gray", edgecolor="Black",alpha=0.1,linewidth=5,linestyle='--')
        TravelArea = plt.Rectangle([0, 0], 710, 260, facecolor="green", edgecolor="Black",alpha=0.1,linewidth=5)
        FOV = plt.Rectangle([-70, -53], 140, 106, fill=None, edgecolor="Black",alpha=0.5,linewidth=5,linestyle='--')
        ax.add_patch(SystemArea)
        ax.add_patch(SystemArea2)
        ax.add_patch(ScanArea)
        ax.add_patch(FOV)
        ax.add_patch(TravelArea)
        ax.add_patch(Detector)
        ax.annotate("Scan area", xy=(280, 280), fontsize=15,alpha=0.5)
        ax.annotate("FOV", xy=(-20, -35), fontsize=10,alpha=1,)
        ax.annotate("Travel area", xy=(280, 230), fontsize=15,alpha=0.5)
        plt.xticks(np.arange(-150, 900, step=50))
        plt.yticks(np.arange(-150, 460, step=50))
        plt.grid(linestyle='--')
        ax.set_aspect(1)
        for i in range(0,len(FinalList)):
            X=FinalList[i][0]
            Y=FinalList[i][1]
            Label=str(FinalList[i][2])
            circle=plt.Circle((X, Y), 37.5,fc='y')
            ax.annotate("VesselID:"+Label, xy=(X-15, Y), fontsize=10)
            circleout=plt.Circle((X, Y), 50, fc='darkgray')
            ax.add_artist(circleout)
            ax.add_artist(circle)
        plt.savefig('output/'+ExperimentNr+'/Vesselposition.png')
        plt.close()

def VisulizeCircles_PlantPlot(FinalList,PlantList,m):
        ExperimentNr='Experiment'+'_'+str(m)
        fig, ax = plt.subplots(figsize=(13, 6))
        SystemArea = plt.Rectangle([-75, -145], 850, 590, fill=None, edgecolor="Black",alpha=1,linewidth=5)
        Detector = plt.Rectangle([-10, -10], 20, 20, facecolor="Black", edgecolor="Black",alpha=1,linewidth=1)
        SystemArea2 = plt.Rectangle([-75, -145], 850, 160, fill=None, edgecolor="Black",alpha=1,linewidth=5)
        ScanArea = plt.Rectangle([-70, -53], 850, 366, facecolor="gray", edgecolor="Black",alpha=0.1,linewidth=5,linestyle='--')
        TravelArea = plt.Rectangle([0, 0], 710, 260, facecolor="green", edgecolor="Black",alpha=0.1,linewidth=5)
        FOV = plt.Rectangle([-70, -53], 140, 106, fill=None, edgecolor="Black",alpha=0.5,linewidth=5,linestyle='--')
        ax.add_patch(SystemArea)
        ax.add_patch(SystemArea2)
        ax.add_patch(ScanArea)
        ax.add_patch(FOV)
        ax.add_patch(TravelArea)
        ax.add_patch(Detector)
        ax.annotate("Scan area", xy=(280, 280), fontsize=15,alpha=0.5)
        ax.annotate("FOV", xy=(-20, -35), fontsize=10,alpha=1,)
        ax.annotate("Travel area", xy=(280, 230), fontsize=15,alpha=0.5)
        plt.xticks(np.arange(-150, 900, step=50))
        plt.yticks(np.arange(-150, 460, step=50))
        plt.grid(linestyle='--')
        ax.set_aspect(1)
        for i in range(0,len(FinalList)):
            X=FinalList[i][0]
            Y=FinalList[i][1]
            Label=str(FinalList[i][2])
            circle=plt.Circle((X, Y), 37.5,fc='y')
            ax.annotate("VesselID:"+Label, xy=(X-15, Y), fontsize=10)
            circleout=plt.Circle((X, Y), 50, fc='darkgray')
            ax.add_artist(circleout)
            ax.add_artist(circle)
        for p in range(0,len(PlantList)):
            X=PlantList[p][0]
            Y=PlantList[p][1]
            Label=str(PlantList[p][2])
            Plant=plt.Circle((X, Y), 5,fc='green')
            ax.annotate("Plant ID:"+Label, xy=(X-15, Y), fontsize=5)
            ax.add_artist(Plant)
        plt.savefig('output/'+ExperimentNr+'/Vessel_Plantposition.png')
        plt.close()
    
def append_new_line(file_name, text_to_append):
    """Append given text as a new line at the end of file"""
    # Open the file in append & read mode ('a+')
    with open(file_name, "a+") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\r\n")
        # Append text at the end of file
        file_object.write(text_to_append)
        file_object.close()
        
def GetTimeLapseData(FinalList,m,DAT,IpD,RGB,SPECTRAL,DEPTH):
    #######Local variables#####
    ExperimentNr='Experiment'+'_'+str(m)
    #####Experiment-Duration#####
    for DAT in range(0,60):
        DAT='DAT'+'_'+str(DAT)
        print(DAT)
        #####TimeLapse per Day#####
        Dummy3=1
        for IpD in range(0,6):
            print(datetime.now())
            next_hour = (datetime.now() + timedelta(hours=4)).replace(minute=5,second=0, microsecond=0)
            print(next_hour)
            IpD='IpD'+'_'+str(IpD)
            print(IpD)
            #####Functions#####
            goToHome()
            print("Homing...")
            #####Vessel in FinalList#####
            if RGB==True:
                for i in range(0,len(FinalList)):
                    print("Capture Time-lapse images VesselID",i+1)
                    DepthXLineArray=[]
                    if DAT==0 and IpD == 0:
                        np.savetxt('output/'+ExperimentNr+'+"/VesselID_"+str(VesselIDcurrent)'+'/Depth.txt', DepthXLineArray=[], newline='\r\n')
                    if i==0 and DAT==0 and IpD == 0:
                        np.savetxt('output/'+ExperimentNr+'/Spec_Fluor.txt', SpecArray=[], newline='\r\n')
                        np.savetxt('output/'+ExperimentNr+'/Spec_Reflec.txt', SpecArray=[], newline='\r\n')
                        np.savetxt('output/'+ExperimentNr+'/Lightintensities.txt', IntensitiesArray=[], newline='\r\n')
                    Xnew,Ynew,VesselIDcurrent=FinalList[i][0],FinalList[i][1],FinalList[i][2]
                    #####Positioning#####
                    goToPosition(Xnew, Ynew)
                    ###RGB-Focus-Stack#####
                    for z in range(0,1,1): ##in range(0,9,3)
                        Zcurrent=ImageZ+z    #####+z
                        setZ(Zcurrent)
                        State,Intensity=CheckIfNightImage()
                        img=ImageRGBReadPNG(State)
                        print(Zcurrent)
                        f=str("VesselID_"+str(VesselIDcurrent)+"_"+DAT+"_"+IpD+"_X_"+str(Xnew)+"_Y_"+str(Ynew)+"_Z_"+str(Zcurrent))
                        cv2.imwrite('output/'+ExperimentNr+'/VesselID_{0}/{1}.{2}'.format(VesselIDcurrent,f,"png"),img)
                ####Spectral measurement#####
            if SPECTRAL==True:
                State,Intensity=CheckIfNightImage()
                IntensitiesArray=str([str(DAT),str(IpD),str(State),str(Intensity)])
                #print(IntensitiesArray)
                append_new_line('output/'+ExperimentNr+'/Lightintensities.txt',IntensitiesArray)
                if State==True:
                    append_new_line('output/'+ExperimentNr+'/Spec_Fluor.txt',str([str(datetime.now())]))
                    append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str([str(datetime.now())]))
                    XPlant,YPlant=XDarkRefObj+SpecXShift, YDarkRefObj+SpecYShift
                    Pos=goToPosition(XPlant,YPlant)
                    SpecFluorArray=SpecReadFluor(False)
                    sleep(2)
                    SpecArray=SpecRead(False)
                    if Pos == False:
                        SpecArray=["NA"]
                        print("X/Y out of range")
                    append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str(SpecArray))
                    append_new_line('output/'+ExperimentNr+'/Spec_Fluor.txt',str(SpecFluorArray))
                    append_new_line('output/'+ExperimentNr+'/Spec_Fluor.txt',str(["Dark&White...now samples"]))
                    append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str(["Dark&White...now samples"]))
                    XPlant,YPlant=XWhiteRefObj+SpecXShift, YWhiteRefObj+SpecYShift
                    Pos=goToPosition(XPlant,YPlant)
                    SpecArray=SpecRead(True)
                    if Pos == False:
                        SpecArray=["NA"]
                        print("X/Y out of range")
                    append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str(SpecArray))
                    append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str(["Dark&White...now samples"]))
                    for p in range(0,len(PlantList)):
                        XPlant,YPlant=PlantList[p][0]+SpecXShift,PlantList[p][1]+SpecYShift
                        Pos=goToPosition(XPlant,YPlant)
                        SpecFluorArray=SpecReadFluor(True)
                        sleep(2)
                        SpecArray=SpecRead(True)
                        if Pos == False:
                            SpecArray=["NA"]
                            print("X/Y out of range")
                        append_new_line('output/'+ExperimentNr+'/Spec_Reflec.txt',str(SpecArray))
                        append_new_line('output/'+ExperimentNr+'/Spec_Fluor.txt',str(SpecFluorArray))
                else:
                    print("Day --> No spec readings!")
            if DEPTH==True:
                #### Depth Measurement ############
                Dummy=1+Dummy3
                Dummy2=Dummy-2
                Dummy3=Dummy+1
                for i in range(Dummy2,Dummy):
                    Vessel=i
                    print("Capture Depth-data VesselID:", Vessel+1)
                    if Vessel >= len(FinalList):
                        break
                    DepthXLineArray=[]
                    if DAT==0 and IpD == 0:
                        np.savetxt('output/'+ExperimentNr+'+"/VesselID_"+str(VesselIDcurrent)'+'/Depth.txt', DepthXLineArray=[], newline='\r\n')
                    print("Check list for found vessel")
                    Xnew,Ynew,VesselIDcurrent=FinalList[i][0],FinalList[i][1],FinalList[i][2]
                    if XMax>Xnew>0 and YMax>Ynew>0:
                        #####Vessel Pos######
                        goToPosition(Xnew, Ynew)
                        setZ(ImageZ+10)
                        #####Depth-Data#####
                        for YVesselEdge in np.arange(Ynew+DepthYShift+Scanpattern,Ynew+DepthYShift-Scanpattern,-1):
                            if YMax>YVesselEdge>0:
                                setY(YVesselEdge)
                                for XVesselEdge in np.arange(Xnew+DepthXShift-Scanpattern,Xnew+DepthXShift+Scanpattern,1):
                                    if XMax>XVesselEdge>0:
                                        setX(XVesselEdge)
                                        Temp_Depth=LaserRead()
                                        if Temp_Depth==27600:
                                            Temp_Depth="NA"
                                        #print(Temp_Depth)
                                        DepthXLineArray.append(Temp_Depth)
                                    else:
                                        print("X/Y out of range")
                                f=str("VesselID_"+str(VesselIDcurrent)+"_"+"Depth")
                                append_new_line('output/'+ExperimentNr+'/VesselID_{0}/{1}.{2}'.format(VesselIDcurrent,f,"txt"),str(DepthXLineArray))
                                DepthXLineArray=[]
                        setZ(ScanZ)
            goToSleepPos()
            print("Go to sleep position")
            delay = (next_hour - datetime.now()).seconds
            print(delay)
            sleep(delay)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




