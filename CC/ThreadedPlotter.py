import numpy as np
import os
import threading
from scipy.optimize import curve_fit
import cv2MAXPIX
import cv2
import multiprocessing as mp
from scipy.interpolate import interp1d
import shutil

class Plot(threading.Thread):
    def __init__(self,queue_plot,filename):
        threading.Thread.__init__(self)
        self.queue_plot=queue_plot
        self.filename=filename+"/Images_calibration"        
        
    def run(self):
        #list folders
        folders=os.listdir(self.filename)
        
        #thickness
        thickness=[float(f.split("/")[-1]) for f in folders]
        thickness=np.asarray(thickness)
        
        #extract hist for each folder
        values=[]
        for i in range(len(folders)):
            pictures_names=os.listdir(self.filename+"/"+folders[i])
            pictures_path=[self.filename+"/"+folders[i]+"/"+n for n in pictures_names]
            
            histograms=[]
            for j in pictures_path:
                histograms.append(self.extract_hist(j))
            
            hist_k,hist_b,hist_g,hist_r=self.merge_hist(histograms)
            
            k,k_error=self.extract_values(hist_k)
            b,b_error=self.extract_values(hist_b)
            g,g_error=self.extract_values(hist_g)
            r,r_error=self.extract_values(hist_r)
            values.append([k,b,g,r,k_error,b_error,g_error,r_error])
        
        values=np.asarray(values)
        
        self.queue_plot.put([thickness,values])
        
    def extract_hist(self,path):
    
        image = cv2.imread(path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        b,g,r = cv2.split(image)
        gray=gray.astype("uint8")
        b=b.astype("uint8")
        g=g.astype("uint8")
        r=r.astype("uint8")

        hist_k = cv2.calcHist([gray],[0],None,[256],[0,256])[:,0]
        hist_b = cv2.calcHist([b],[0],None,[256],[0,256])[:,0]
        hist_g = cv2.calcHist([g],[0],None,[256],[0,256])[:,0]
        hist_r = cv2.calcHist([r],[0],None,[256],[0,256])[:,0]
    
        return [hist_k,hist_b,hist_g,hist_r]
        
    def merge_hist(self,histograms):

        k,b,g,r=np.zeros(len(histograms[0][0])),np.zeros(len(histograms[0][0])),np.zeros(len(histograms[0][0])),np.zeros(len(histograms[0][0]))
        for i in range(len(histograms)):
            k+=np.asarray(histograms[i][0])
            b+=np.asarray(histograms[i][1])
            g+=np.asarray(histograms[i][2])
            r+=np.asarray(histograms[i][3])
        return k,b,g,r
    
    def extract_values(self,histograms):
        
        prob=histograms
        vmax=np.argmax(prob)
        
        i=vmax
        ratio=0.1
        while prob[i]/prob[vmax]>ratio and i<255:
            i += 1
        vsup=i
    
        i= vmax
        while prob[i]/prob[vmax]>ratio and i>0:
            i -= 1
        vinf=i
    
        v=(vinf+vsup)/2
        error=(vsup-vinf)/2
    
        return v,error+3
