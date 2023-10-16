import os
import re
import datetime
import numpy as np
import cv2MAXPIX
import cv2


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



