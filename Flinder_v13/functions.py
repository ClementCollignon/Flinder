import os
import re
import datetime
import numpy as np
import cv2MAXPIX
import cv2

def get_config():

    with open('config.txt') as config:
        lines = config.readlines()

    MAIN_FOLDER = lines[0].split("\t")[1][:-1]
    SCREEN_SCALING = lines[1].split("\t")[1][:-1]
    ZEROS = int(lines[2].split("\t")[1][:-1])
    
    FoV_w = float(lines[3].split("\t")[1])
    FoV_h = float(lines[3].split("\t")[2][:-1])
    FOV = [FoV_w, FoV_h]
    
    OVERLAP = float(lines[4].split("\t")[1][:-1])
    JPG = int(lines[5].split("\t")[1][:-1])
    LOW_RES = lines[6].split("\t")[1][:-1]
    HIGH_RES = lines[7].split("\t")[1][:-1]
    
    CCD_w = int(lines[8].split("\t")[1])
    CCD_h = int(lines[8].split("\t")[2][:-1])
    CCD = [CCD_w, CCD_h]

    OFFSET_X_5   = float(lines[9].split("\t")[1])
    OFFSET_X_10  = float(lines[9].split("\t")[2])
    OFFSET_X_20  = float(lines[9].split("\t")[3])
    OFFSET_X_50  = float(lines[9].split("\t")[4])
    OFFSET_X_100 = float(lines[9].split("\t")[5][:-1])
    OFFSET_X = [OFFSET_X_5, OFFSET_X_10, OFFSET_X_20, OFFSET_X_50, OFFSET_X_100]
    
    OFFSET_Y_5   = float(lines[10].split("\t")[1])
    OFFSET_Y_10  = float(lines[10].split("\t")[2])
    OFFSET_Y_20  = float(lines[10].split("\t")[3])
    OFFSET_Y_50  = float(lines[10].split("\t")[4])
    OFFSET_Y_100 = float(lines[10].split("\t")[5][:-1])
    OFFSET_Y = [OFFSET_Y_5, OFFSET_Y_10, OFFSET_Y_20, OFFSET_Y_50, OFFSET_Y_100]

    OFFSET_Z_5   = float(lines[11].split("\t")[1])
    OFFSET_Z_10  = float(lines[11].split("\t")[2])
    OFFSET_Z_20  = float(lines[11].split("\t")[3])
    OFFSET_Z_50  = float(lines[11].split("\t")[4])
    OFFSET_Z_100 = float(lines[11].split("\t")[5][:-1])
    OFFSET_Z = [OFFSET_Z_5, OFFSET_Z_10, OFFSET_Z_20, OFFSET_Z_50, OFFSET_Z_100]
    
    SCALE = float(lines[12].split("\t")[1][:-1])
    
    res = (MAIN_FOLDER, SCREEN_SCALING, ZEROS, 
           FOV, OVERLAP, SCALE, JPG, 
           LOW_RES, HIGH_RES, CCD,
           OFFSET_X, OFFSET_Y, OFFSET_Z)
    
    return res 

config = get_config()
(MAIN_FOLDER, SCREEN_SCALING, ZEROS, 
 FOV, OVERLAP, SCALE, JPG,
 LOW_RES, HIGH_RES, CCD,
 OFFSET_X, OFFSET_Y, OFFSET_Z) = config

def long_path_cutter(path,max_span=35,max_span0=31):
    
    length=[0]
    splited=re.split('/|_|-',path)    
    j=0
    for i in range(len(splited)):
        if length[j]>max_span0:
            length[j]-=(len(splited[i-1])+1)
            max_span0=max_span
            length.append(0)
            j+=1
            length[j]+=len(splited[i-1])+1
        length[j]+=len(splited[i])+1
        if i == len(splited)-1 and length[j]>max_span0:
            length[j]-=(len(splited[i])+1)
            length.append(0)
            j+=1
            length[j]+=len(splited[i])+1
            
    for i in range(1,len(length)):
        length[i]+=length[i-1]
    
    text="Path: "
    for i in range(len(length)):
        if i==0: text+=path[0:length[i]]+"\n"
        elif i>0 and i<len(length)-1: text+=path[length[i-1]:length[i]]+"\n"
        else: text+=path[length[i-1]:length[i]]
    return text

def scanning_macro_one(filename,poseX,poseY,hrange,wrange,nosepiece,fieldofview_h,fieldofview_w,step_focus):
    nosepiece_values={'5x':0,'10x':1,'20x':2,'50x':3,'100x':4}
    zrange=[30,15,10,3,3]
    zstep=[5,1,1,0.2,0.2]
    zrange0=[50,50,50,10,10]
    zstep0=[5,5,5,1,1]
    xymove=[2000,1000,500,250,125]
    indice_nosepiece=nosepiece_values[nosepiece]
    
    zrange=zrange[indice_nosepiece]
    zstep=zstep[indice_nosepiece]
    zrange0=zrange0[indice_nosepiece]
    zstep0=zstep0[indice_nosepiece]
    xymove=xymove[indice_nosepiece]
    
    macro_master="""SaveNext_Images(\""""+filename+"/Raw_pictures"+"""\", """+JPG+""", "pic", 0);
SaveNext_ImageInfo(NULL, NULL, NULL, NULL, 0, 0);
StgMoveXY("""+str(poseX*1000)+""", """+str(poseY*1000)+""", 0);
StgSetupFocus(2,"""+str(zstep0)+""",0);
StgSetupFocusEx("""+str(zrange0)+""",10);
StgFocus();
StgMoveXY("""+str(xymove)+""", """+str(-xymove)+""", 1);
Wait(1.00000);
CameraCmd_AutoWhite();
CameraCmd_AutoExposure();
CameraCmd_AutoWhite();
Wait(1.00000);
StgSetupFocus(2,"""+str(zstep)+""",0);
StgSetupFocusEx("""+str(zrange)+""",10);
StgSetupFocusOffset(0.00000);
StgFocus();
ZoomFitToScreen();
Wait(1.00000);
CameraCmd_AutoWhite();
CameraCmd_AutoExposure();
CameraCmd_AutoWhite();
Wait(1.00000);
StgMoveXY("""+str(-xymove)+""", """+str(xymove)+""", 1);
Wait(1.00000);
StgFocus();"""
        
    counter=-1
    counter2=0
    for i in range(hrange):
        for j in range(wrange):
            counter+=1
            counter2+=1
            if i%2==0: direction=+1
            else: direction=-1
            if counter==step_focus:
                macro_master+="\nStgFocus();"
                counter=0
            macro_master+="\nAutoCapture();"
            macro_master+="\nImageExportAllAvailableInfo(1,\""+filename+"/Position_files/pos"+str(counter2-1)+".dat\");"
            if j==wrange-1:
                macro_master+="\nStgMoveXY(0,"+str(-np.round(fieldofview_h*1000,8))+", 1);"
            else:
                macro_master+="\nStgMoveXY("+str(np.round(direction*fieldofview_w*1000,8))+", 0, 1);"
    
    return macro_master+"\n"

def scanning_macro(filename,Nwafer,hrange,wrange,sample_dim,nosepiece,fieldofview_h,fieldofview_w,step_focus):
    macro_master="""CameraFormatSet(1, \""""+LOW_RES+"""\");
StgZ_SetSpeedRamp(100);
StgZ_SetMotorSpeed(50);
CameraSet_ToggleAE(1,0);
"""
    for i in range(Nwafer):
        macro_master+=scanning_macro_one(filename+"/Wafer_"+str(i).zfill(2),sample_dim[i][0],sample_dim[i][1],hrange[i],wrange[i],nosepiece,fieldofview_h,fieldofview_w,step_focus)

    f = open(filename+"/Macro_files/macro_scan_"+nosepiece+".mac", "w")
    f.write(macro_master)
    f.close()

def log_file_one(filename,H,W,hrange,wrange,nosepiece):
    logfile="""Date:\t"""+str(datetime.date.today())+"""
Nosepiece:\t"""+nosepiece+"""
Size H ( mm ):\t"""+str(H)+"""
Size W ( mm ):\t"""+str(W)+"""
N images per column:\t"""+str(hrange)+"""
M images per row:\t"""+str(wrange)

    f = open(filename+"/log_file.dat", "w")
    f.write(logfile)
    f.close()
    
def log_file(filename,Nwafer,sample_dim,hrange,wrange,nosepiece):
    for i in range(Nwafer):
        log_file_one(filename+"/Wafer_"+str(i).zfill(2),sample_dim[i][2],sample_dim[i][3],hrange[i],wrange[i],nosepiece)
        
    logfile="""Date:\t"""+str(datetime.date.today())+"""
Nosepiece:\t"""+nosepiece+"""
Number of wafers:\t"""+str(Nwafer)

    f = open(filename+"/log_file.dat", "w")
    f.write(logfile)
    f.close()

def macro50_100x_one(filename,BFDF,exposure,gain,zoom):
        list_of_flakes=[]
        position_files=[]
        name=[]
        
        for files in os.listdir(filename+"\Analysed_picture"):
            if files!="full_image.jpg":
                name.append(files)
                list_of_flakes.append(filename+"\Analysed_picture\\"+files+"\log_"+files+".dat")
                position_files.append(filename+"\Analysed_picture\\"+files+"\\"+files+"_position.dat")
        
        macro=""
        for i in range(len(list_of_flakes)):
            file = open(position_files[i], 'r',encoding='utf-16-le')
            Lines = file.readlines()
                
            myline=0
            while Lines[myline]!="Recorded Data\n":
                myline+=1
            begining,xt,yt,zt,ludl,exp,end=Lines[myline+2].split("\t")
            Z=float(zt)
            X=float(xt)
            Y=float(yt)
            
            if zoom == "100x":
                X+=-5
                Y+=14
                Z+=4
            
            path_to_pic=filename+"\Analysed_picture\\"+name[i]
            
            macro+="CameraCmd_AutoWhite();\n"
            if exposure==0:
                macro+="CameraCmd_AutoExposure();\n"
            
            if exposure!=0:
                macro+="CameraSet_ExpTime(1,200);\n"
                macro+="CameraSet_Gain(1,60);\n"
            
            if BFDF=="BF":
                macro+="""SaveNext_Images(\""""+path_to_pic+"""\", """+JPG+""", \""""+zoom+"""_"""+BFDF+"""_"""+name[i]+"""_\", 0);
SaveNext_ImageInfo(NULL, NULL, NULL, NULL, 0, 0);
LUTsLoadSettings("C:\\Program Files\\FlakeHunter\\ASS\\LUT.lut");
EnableLUTs(1);
StgMoveXY("""+str(X)+""", """+str(Y)+""", 0);
StgMoveMainZ("""+str(np.round(Z,3))+""", 0);
StgSetupFocus(2,0.5000,0);
StgSetupFocusEx(10.00000,10);
StgFocus();
StgSetupFocus(2,0.2000,0);
StgSetupFocusEx(4.00000,10);
StgFocus();
EnableLUTs(0);
"""
            else:
                macro+="""SaveNext_Images(\""""+path_to_pic+"""\", """+JPG+""", \""""+zoom+"""_"""+BFDF+"""_"""+name[i]+"""_\", 0);
SaveNext_ImageInfo(NULL, NULL, NULL, NULL, 0, 0);
StgMoveXY("""+str(X)+""", """+str(Y)+""", 0);
StgMoveMainZ("""+str(np.round(Z,3))+""", 0);
StgSetupFocus(2,0.5000,0);
StgSetupFocusEx(10.00000,10);
StgFocus();
StgSetupFocus(2,0.2000,0);
StgSetupFocusEx(4.00000,10);
StgFocus();
"""

            macro+="CameraCmd_AutoWhite();\n"
            if exposure==0:
                macro+="CameraCmd_AutoExposure();\n"
            else:
                macro+="CameraSet_ExpTime(1,"+str(np.round(exposure,3))+");\n"
                macro+="CameraSet_Gain(1,"+str(np.round(gain,3))+");\n"
                macro+=f"Wait({np.round(exposure/1000,3)});\n"
            macro+="AutoCapture();\n"
    
            #macro+="StgMoveMainZ("+str(np.round(Z-50,3))+", 0);\n"
        
        return macro

def macro50_100x(filename,BFDF,exposure,gain,zoom,Nwafer):
    macro="""CameraFormatSet(1, \""""+LOW_RES+"""\");
StgZ_SetSpeedRamp(100);
StgZ_SetMotorSpeed(50);
"""

    for i in range(Nwafer):
        filename_temp=filename+"\Wafer_"+str(i).zfill(2)
        macro+=macro50_100x_one(filename_temp,BFDF,exposure,gain,zoom)

    f = open(filename+"/Macro_files/macro_"+BFDF+zoom+".mac", "w")
    f.write(macro)
    f.close()
    

def macro50x_one(filename,exposure,offset):
    list_of_flakes=[]
    name=[]
    
    Xoffset,Yoffset,Zoffset=offset
    
    for files in os.listdir(filename+"\Analysed_picture"):
        if files!="full_image.jpg":
            name.append(files)
            list_of_flakes.append(filename+"\Analysed_picture\\"+files+"\log_"+files+".dat")
        
    macro=""

    for i in range(len(list_of_flakes)):
        file = open(list_of_flakes[i], 'r')
        Lines = file.readlines()
        X=float(Lines[4].split('\t')[1])+Xoffset
        Y=float(Lines[5].split('\t')[1])+Yoffset
        Z=float(Lines[6].split('\t')[1])+Zoffset
            
        path_to_pic=filename+"\Analysed_picture\\"+name[i]
        macro+="""SaveNext_Images(\""""+path_to_pic+"""\", """+JPG+""", \"50x_BF_"""+name[i]+"""_\", 0);
SaveNext_ImageInfo(NULL, NULL, NULL, NULL, 0, 0);
LUTsLoadSettings("C:\\Program Files\\FlakeHunter\\ASS\\LUT.lut");
StgMoveXY("""+str(X)+""", """+str(Y)+""", 0);
StgMoveMainZ("""+str(np.round(Z,3))+""", 0);
"""

        if exposure==0:
            macro+="CameraCmd_AutoExposure();\n"
        else:
            macro+="CameraSet_ExpTime(1,"+str(np.round(exposure,3))+");\n"
            
        macro+="""CameraCmd_AutoWhite();
EnableLUTs(1);

StgSetupFocus(2,1.0000,0);
StgSetupFocusEx(50.00000,10);
StgFocus();
StgSetupFocus(2,0.20000,0);
StgSetupFocusEx(4.00000,10);
StgFocus();
EnableLUTs(0);
"""            
        macro+="CameraCmd_AutoWhite();\n"
        macro+="CameraSet_Average(1, 8);\n"
        macro+="ImageExportAllAvailableInfo(1,\""+path_to_pic+"\\"+name[i]+"_position.dat\");\n"
        macro+="AutoCapture();\n"
        macro+="CameraSet_Average(1, 1);\n"
        file.close()
    return macro
    

def macro50x(filename,exposure,Nwafer,Nosepiece):
    
    offsets_Z={"5x":OFFSET_Z[0],"10x":OFFSET_Z[1],"20x":OFFSET_Z[2],"50x":OFFSET_Z[3],"100x":OFFSET_Z[4]}
    offsets_X={"5x":OFFSET_X[0],"10x":OFFSET_X[1],"20x":OFFSET_X[2],"50x":OFFSET_X[3],"100x":OFFSET_X[4]} 
    offsets_Y={"5x":OFFSET_Y[0],"10x":OFFSET_Y[1],"20x":OFFSET_Y[2],"50x":OFFSET_Y[3],"100x":OFFSET_Y[4]}
    offset=[offsets_X[Nosepiece],offsets_Y[Nosepiece],offsets_Z[Nosepiece]]
    
    macro="""CameraFormatSet(1, \""""+LOW_RES+"""\");
StgZ_SetSpeedRamp(100);
StgZ_SetMotorSpeed(50);
"""

    for i in range(Nwafer):
        filename_temp=filename+"\Wafer_"+str(i).zfill(2)
        macro+=macro50x_one(filename_temp,exposure,offset)

    f = open(filename+"/Macro_files/macro_BF50x.mac", "w")
    f.write(macro)
    f.close()


def macro_50x_Proceed(filename,entry_exposure_BF_50):
    Proceed,text, exp50 = 1,"",0
       
    if Proceed == 1 and entry_exposure_BF_50.get()!="":
        try:
            float(entry_exposure_BF_50.get())        
        except:
            Proceed=0
            text="Exposure entry is\nnot a number"
            return Proceed, text, exp50
    
    if Proceed == 1:
        exp50=entry_exposure_BF_50.get()
        if exp50=="":
            exp50=0
        else:
            exp50=float(exp50)
    return Proceed, text, exp50

def macro_DFBF_Proceed(filename,BF100x,DF50x,DF100x,entry_exposure_BF_100,entry_exposure_DF_50,entry_exposure_DF_100,entry_gain_BF_100,entry_gain_DF_50,entry_gain_DF_100):
    Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100DF= 1,"",0,0,0,0,0,0
    

    if Proceed == 1:
        if DF50x.get() == 0 and DF100x.get() == 0 and BF100x.get() == 0:
           text="Specify at least\none magnification"
           Proceed=0
           return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
       
    if Proceed == 1 and entry_exposure_DF_50.get()!="":
        try:
            float(entry_exposure_DF_50.get())
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
    
    if Proceed == 1 and entry_gain_DF_50.get()!="":
        try:
            float(entry_gain_DF_50.get())
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
    
    if Proceed == 1 and entry_exposure_BF_100.get()!="":
        try:
            float(entry_exposure_BF_100.get())     
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
        
    if Proceed == 1 and entry_gain_BF_100.get()!="":
        try:
            float(entry_gain_BF_100.get())   
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
    
    if Proceed == 1 and entry_exposure_DF_100.get()!="":
        try:
            float(entry_exposure_DF_100.get())  
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
    
    if Proceed == 1 and entry_gain_DF_100.get()!="":
        try:
            float(entry_gain_DF_100.get())   
        except:
            Proceed=0
            text="Entry is\nnot a number"
            return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100BF
    
    if Proceed == 1:
        if DF50x.get() == 1:
            exp50DF=entry_exposure_DF_50.get()
            gain50DF=entry_gain_DF_50.get()
            if exp50DF=="":
                exp50DF=0
            else:
                exp50DF=float(exp50DF)
            if gain50DF=="":
                gain50DF=15
            else:
                gain50DF=float(gain50DF)
                
        if BF100x.get() == 1:
            exp100BF=entry_exposure_BF_100.get()
            gain100BF=entry_gain_BF_100.get()
            if exp100BF=="":
                exp100BF=0
            else:
                exp100BF=float(exp100BF)
            if gain100BF=="":
                gain100BF=1
            else:
                gain100BF=float(gain100BF)
        
        if DF100x.get() == 1:
            exp100DF=entry_exposure_DF_100.get()
            gain100DF=entry_gain_DF_100.get()
            if exp100DF=="":
                exp100DF=0
            else:
                exp100DF=float(exp100DF)
            if gain100DF=="":
                gain100DF=20
            else:
                gain100DF=float(gain100DF)
                
    return Proceed, text, exp100BF, exp50DF, exp100DF, gain100BF, gain50DF, gain100DF

def combined(v1,v2,k2):
    
    limit=10
    v1[k2>=limit]=0
    v2[k2<limit]=0

    a0=v1.astype(np.int16)+v2.astype(np.int16)
    
    a0[a0<0]=0
    a0[a0>255]=255
    
    return a0.astype(np.uint8)


