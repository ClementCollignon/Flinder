import tkinter as tk
import os
import functions
import ThreadedPlotter
import Hunter_parallele
import ThreadedTrainer
import numpy as np
import multiprocessing as mp

import cv2

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.interpolate import interp1d
import queue
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import PIL
from PIL import Image, ImageTk
import shutil

PIL.Image.MAX_IMAGE_PIXELS = 11660313600

scaling_factor=2
police_factor=scaling_factor
plt.rcParams.update({'font.size':20/scaling_factor})

size_l=int(28/scaling_factor*police_factor)
size_s=int(18/scaling_factor*police_factor)
size_xs=int(12/scaling_factor*police_factor)
           
color_set=['#505050','#2b2b2b','#999999']
text_color="#fffff9"

color_set=['#e3e4e7','#ffffff','#d9d9d9']
text_color='#312820'

color_error="#EC7063"

Window_size=[2400,1270]

class Root(tk.Tk):
    def __init__(self):
        super(Root, self).__init__()
        self.title("Calibration Creator")

        self.minsize(int(Window_size[0]/scaling_factor), int(Window_size[1]/scaling_factor))
        self.wm_iconbitmap('icon.ico')
        self.configure(bg=color_set[0])
        
        self.nosepieces=["5x","10x","20x","50x","100x"]
        self.Fieldvalues=[2.13,1.425]
        self.factors=[1,2,4,10,20]
        
        self.zaxis=[(2,0.5,10),(2,0.5,0.1),(1,0.25,0.05),(1,0.25,0.05),(0.5,0.1,0.01)]
        self.zaxis_step=[10,10,30]
        
        self.stitching_running=0
        self.hunting_running=0
        self.stitch_counter=0
        self.hunt_counter=0
        
        #Create two vertical lines to separate the window in 3 pannels
        Vertical_ligne1=tk.Frame(self,height=Window_size[1]/scaling_factor,width=2,bg=color_set[1])
        Vertical_ligne1.place(x=799/scaling_factor,y=0)

        Vertical_ligne2=tk.Frame(self,height=Window_size[1]/scaling_factor,width=2,bg=color_set[1])
        Vertical_ligne2.place(x=1599/scaling_factor,y=0)

        #Define the working folder
        X,Y=30/scaling_factor,10/scaling_factor
        Label_working_folder = tk.Label(self,  text="Working Folder", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        Label_working_folder.place(x=X, y=Y, anchor = 'nw')
        
        X,Y,height,width=195/scaling_factor,Y+120/scaling_factor,170/scaling_factor,590/scaling_factor
        Frame_path_working_folder=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_path_working_folder.place(x=X,y=Y,anchor='nw')
        
        X,Y=200/scaling_factor,Y+5/scaling_factor
        self.Label_path = tk.Label(self,  text="Path: ", fg=text_color, font=('helvetica', size_xs), bg = color_set[1])
        self.Label_path.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=30/scaling_factor,Y-5/scaling_factor
        Button_browse = ttk.Button(self, text = "Browse",command = self.workingfolderDialog)
        Button_browse.place(x=X,y=Y,anchor='nw')
        
        #Add flakes
        X,Y=400/scaling_factor,340/scaling_factor 
        
        Button_add = ttk.Button(self, text = "Add calibration image",command = self.addflakeDialog)
        Button_add.place(x=X,y=Y,anchor='n')
        
        #Layer or Thickness
        X,Y=30/scaling_factor,400/scaling_factor 
        X0=90/scaling_factor
        Y0=160/scaling_factor
        stepX=300/scaling_factor
        
        Label_layer_thickness = tk.Label(self,  text="# of layers or nm?", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        Label_layer_thickness.place(x=X, y=Y, anchor = 'nw')
        
        self.layer_or_thickness = tk.IntVar()
        text=['layers','nm']
        for i in range(len(text)):
            self.button_layer(text[i],i+1,X+X0+i*stepX,Y+Y0)

        #Plot and create
        X,Y=30/scaling_factor,670/scaling_factor
        Label_create_macro = tk.Label(self,  text="Create Calibration", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=400/scaling_factor,790/scaling_factor
        Button_plot = ttk.Button(self, text = "Plot",command = self.plot)
        Button_plot.place(x=X,y=Y,anchor='n')
        
        X,Y=30/scaling_factor,870/scaling_factor
        Label_create_macro = tk.Label(self,  text="Use channels:", fg=text_color, font=('helvetica', size_s), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=X+350/scaling_factor,Y-2/scaling_factor
        Xstep,Ystep=200/scaling_factor,90/scaling_factor
        self.var_useBlack = tk.IntVar()
        self.button_useBlack = tk.Checkbutton(self, text='black',variable=self.var_useBlack, onvalue=1, offvalue=0, bg = color_set[0], fg =text_color ,font=('helvetica', size_s))
        self.button_useBlack.place(x=X, y=Y, anchor = 'nw')
        self.var_useBlue = tk.IntVar()
        self.button_useBlue = tk.Checkbutton(self, text='blue',variable=self.var_useBlue, onvalue=1, offvalue=0, bg = color_set[0], fg =text_color,font=('helvetica', size_s))
        self.button_useBlue.place(x=X+Xstep, y=Y, anchor = 'nw')
        self.var_useGreen = tk.IntVar()
        self.button_useGreen = tk.Checkbutton(self, text='green',variable=self.var_useGreen, onvalue=1, offvalue=0, bg = color_set[0], fg =text_color,font=('helvetica', size_s))
        self.button_useGreen.place(x=X, y=Y+Ystep, anchor = 'nw')
        self.var_useRed = tk.IntVar()
        self.button_useRed = tk.Checkbutton(self, text='red',variable=self.var_useRed, onvalue=1, offvalue=0, bg = color_set[0], fg =text_color,font=('helvetica', size_s))
        self.button_useRed.place(x=X+Xstep, y=Y+Ystep, anchor = 'nw')
        
        self.var_useBlack.set(1)
        self.var_useBlue.set(1)
        self.var_useGreen.set(1)
        self.var_useRed.set(1)
        
        X,Y=30/scaling_factor,1060/scaling_factor
        Label_create_macro = tk.Label(self,  text="Number of intervals", fg=text_color, font=('helvetica', size_s), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        
        X=X+450/scaling_factor
        self.Entry_interval = tk.Entry(self,width=4,font=('helvetica', size_s)) 
        self.Entry_interval.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=400/scaling_factor,1170/scaling_factor
        Button_plot = ttk.Button(self, text = "Create",command = self.create_calibration)
        Button_plot.place(x=X,y=Y,anchor='n')
        
        #Criteria pannel
        X,Y=830/scaling_factor, 10/scaling_factor
        Label_stitch = tk.Label(self,  text="Criteria", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        Label_stitch.place(x=X, y=Y, anchor = 'nw')        
        
        X,Y=830/scaling_factor,120/scaling_factor
        Label_create_macro = tk.Label(self,  text="Standard deviation:", fg=text_color, font=('helvetica', size_s), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        
        Y=Y+70/scaling_factor
        Xstep=200/scaling_factor
        Label_create_macro = tk.Label(self,  text="min", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+198/scaling_factor, y=Y, anchor = 'nw')
        Label_create_macro = tk.Label(self,  text="max", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+342/scaling_factor, y=Y, anchor = 'nw')
        Label_create_macro = tk.Label(self,  text="use", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+480/scaling_factor, y=Y, anchor = 'nw')
        
        Ystep=80/scaling_factor
        Y=Y+50/scaling_factor
        self.var_useBlackVariance=tk.IntVar()
        self.entry_variance_black_min,self.entry_variance_black_max,self.button_variance_black_use=self.variance(X,Y,self.var_useBlackVariance,"black")
        self.var_useBlueVariance=tk.IntVar()
        self.entry_variance_blue_min,self.entry_variance_blue_max,self.button_variance_blue_use=self.variance(X,Y+Ystep,self.var_useBlueVariance,"blue")
        self.var_useGreenVariance=tk.IntVar()
        self.entry_variance_green_min,self.entry_variance_green_max,self.button_variance_green_use=self.variance(X,Y+2*Ystep,self.var_useGreenVariance,"green")
        self.var_useRedVariance=tk.IntVar()
        self.entry_variance_red_min,self.entry_variance_red_max,self.button_variance_red_use=self.variance(X,Y+3*Ystep,self.var_useRedVariance,"red")
        
        X,Y=830/scaling_factor,550/scaling_factor
        Label_create_macro = tk.Label(self,  text="Aspect ratio:", fg=text_color, font=('helvetica', size_s), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        Y=Y+70/scaling_factor
        Label_create_macro = tk.Label(self,  text="min", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+198/scaling_factor, y=Y, anchor = 'nw')
        Label_create_macro = tk.Label(self,  text="max", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+342/scaling_factor, y=Y, anchor = 'nw')
        Label_create_macro = tk.Label(self,  text="use", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X+480/scaling_factor, y=Y, anchor = 'nw')
        
        self.var_useAspectRatio=tk.IntVar()
        self.entry_aspectratio_min,self.entry_aspectratio_max,self.button_aspectratio_use=self.variance(X,Y+50/scaling_factor,self.var_useAspectRatio,"")
        
        self.entry_aspectratio_min.delete(0, 'end')
        self.entry_aspectratio_max.delete(0, 'end')
        self.entry_aspectratio_min.insert(0,1)
        self.entry_aspectratio_max.insert(0,4)
        
        X,Y=1200/scaling_factor,740/scaling_factor
        Button_plot = ttk.Button(self, text = "Create",command = self.create_criteria)
        Button_plot.place(x=X,y=Y,anchor='n')
        
        #Flake Hunt
        X,Y=830/scaling_factor,800/scaling_factor
        Label_flake_hunt = tk.Label(self,  text="Test Hunt", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        Label_flake_hunt.place(x=X, y=Y, anchor = 'nw')
        
        Y=Y+90/scaling_factor
        self.var_high_contrast = tk.IntVar()
        self.button_high_contrast = tk.Checkbutton(self, text='High Contrast mode',variable=self.var_high_contrast, onvalue=1, offvalue=0, bg = color_set[0],font=('helvetica', size_s))
        self.button_high_contrast.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=830/scaling_factor,1020/scaling_factor
        Label_size = tk.Label(self,  text="Size ( μm² )", fg=text_color, font=('helvetica', size_s), bg = color_set[0])
        Label_size.place(x=X, y=Y, anchor = 'w')
        
        Offset=300/scaling_factor        
        self.Entry_size = tk.Entry(self,width=6,font=('helvetica', size_s)) 
        self.Entry_size.place(x=X+Offset, y=Y, anchor='w')
        
        
        X,Y=830/scaling_factor,1135/scaling_factor
        Button_hunt = ttk.Button(self, text = "Hunt",command = self.Hunt)
        Button_hunt.place(x=X,y=Y,anchor='w')
        
        X,Y,height,width=1000/scaling_factor,1105/scaling_factor,130/scaling_factor,585/scaling_factor
        Frame_hunt=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_hunt.place(x=X,y=Y,anchor='nw')
        
        lw_hunt = tk.Label(self,  text="Progress:", fg=text_color, font=('helvetica', int(size_xs/1)), bg = color_set[1],justify='left')
        lw_hunt.place(x=X, y=Y, anchor = 'nw')
        
        self.label_hunt = tk.Label(self,  text="", fg=text_color, font=('helvetica', int(size_xs/1)), bg = color_set[1],justify='left')
        self.label_hunt.place(x=X+150/scaling_factor, y=Y, anchor = 'nw')
        
        #Select flakes
        lw5 = tk.Label(self,  text="Create Database", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        lw5.place(x=1630/scaling_factor, y=10/scaling_factor, anchor = 'nw')
        
        frame_path=tk.Frame(self,height=150/scaling_factor,width=590/scaling_factor,bg=color_set[1])
        frame_path.place(x=(1600+195)/scaling_factor,y=120/scaling_factor,anchor='nw')
        
        self.label_select = tk.Label(self,  text="No selection done", fg=text_color, font=('helvetica', size_xs), bg = color_set[1])
        self.label_select.place(x=(210+1600)/scaling_factor, y=120/scaling_factor, anchor = 'nw')
        
        self.button_select = ttk.Button(self, text = "Select",command = self.doSelection)
        self.button_select.place(x=1630/scaling_factor,y=120/scaling_factor,anchor='nw')
        
    
        #Neural network
        lw5 = tk.Label(self,  text="Neural Network", fg=text_color, font=('helvetica', size_l), bg = color_set[0])
        lw5.place(x=1630/scaling_factor, y=280/scaling_factor, anchor = 'nw')
        
        X=1630/scaling_factor
        Y=380/scaling_factor

        self.button_select_model_path = ttk.Button(self, text = "Browse", command = self.modelPathDialog)
        self.button_select_model_path.place(x=X,y=Y,anchor='nw')
        
        X=1795/scaling_factor
        
        frame_model_path=tk.Frame(self,height=170/scaling_factor,width=590/scaling_factor,bg=color_set[1])
        frame_model_path.place(x=X,y=Y,anchor='nw')
        
        self.Label_model_path = tk.Label(self,  
                                         text="No pre-trained weights selected", 
                                         fg=text_color, 
                                         font=('helvetica', size_xs), 
                                         bg = color_set[1])
        self.Label_model_path.place(x=X, y=Y, anchor = 'nw')
        
        X=1630/scaling_factor
        Y=590/scaling_factor
        Xstep=160/scaling_factor
        Xstep2=260/scaling_factor
        Ystep=60/scaling_factor
        
        Label_BatchSize = tk.Label(self,  text="Batch size", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_BatchSize.place(x=X, y=Y, anchor = 'w')      
        self.entry_BatchSize=tk.Entry(self,width=4,font=('helvetica', size_xs)) 
        self.entry_BatchSize.place(x=X+Xstep, y=Y, anchor = 'w')
        self.entry_BatchSize.insert(0, '128')
        
        Label_ImageSize = tk.Label(self,  text="Image size", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_ImageSize.place(x=X+Xstep2, y=Y, anchor = 'w')      
        self.entry_ImageSize=tk.Entry(self,width=4,font=('helvetica', size_xs)) 
        self.entry_ImageSize.place(x=X+Xstep+5/scaling_factor+Xstep2, y=Y, anchor = 'w')
        self.entry_ImageSize.insert(0, '100')
     
        Label_Epoch = tk.Label(self,  text="Epoch", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_Epoch.place(x=X+2*Xstep2, y=Y, anchor = 'w')      
        self.entry_Epoch=tk.Entry(self,width=4,font=('helvetica', size_xs)) 
        self.entry_Epoch.place(x=X+Xstep/1.5+2*Xstep2, y=Y, anchor = 'w')
        self.entry_Epoch.insert(0, '100')
        
        X=1750/scaling_factor
        Xstep=220/scaling_factor
        Y=640/scaling_factor
        Ystep=70/scaling_factor
        Label_Layer = tk.Label(self,  text="Layer", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_Layer.place(x=X, y=Y, anchor = 'n')
        
        Label_Filters = tk.Label(self,  text="Filters", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_Filters.place(x=X+Xstep, y=Y, anchor = 'n')  
        
        Label_Kernel = tk.Label(self,  text="Kernel size", fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_Kernel.place(x=X+2*Xstep, y=Y, anchor = 'n')  
        
        for i in range(4):
            label_number = tk.Label(self,  text=str(i), fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
            label_number.place(x=X, y=Y+(i+1)*Ystep, anchor = 'n')  
        
        entry_Filters0=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Filters0.place(x=X+Xstep, y=Y+Ystep, anchor = 'n')
        entry_Filters0.insert(0, '64')
        entry_Filters1=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Filters1.place(x=X+Xstep, y=Y+2*Ystep, anchor = 'n')
        entry_Filters1.insert(0, '32')
        entry_Filters2=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Filters2.place(x=X+Xstep, y=Y+3*Ystep, anchor = 'n')
        entry_Filters2.insert(0, '64')
        entry_Filters3=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Filters3.place(x=X+Xstep, y=Y+4*Ystep, anchor = 'n')
        entry_Filters3.insert(0, '128')
        
        self.entry_Filters=[entry_Filters0,entry_Filters1,entry_Filters2,entry_Filters3]
        
        entry_Kernel0=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Kernel0.place(x=X+2*Xstep, y=Y+Ystep, anchor = 'n')
        entry_Kernel0.insert(0, '7')
        entry_Kernel1=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Kernel1.place(x=X+2*Xstep, y=Y+2*Ystep, anchor = 'n')
        entry_Kernel1.insert(0, '3')
        entry_Kernel2=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Kernel2.place(x=X+2*Xstep, y=Y+3*Ystep, anchor = 'n')
        entry_Kernel2.insert(0, '3')
        entry_Kernel3=tk.Entry(self,width=4,font=('helvetica', size_xs))
        entry_Kernel3.place(x=X+2*Xstep, y=Y+4*Ystep, anchor = 'n')
        entry_Kernel3.insert(0, '3')
        
        self.entry_Kernels=[entry_Kernel0,entry_Kernel1,entry_Kernel2,entry_Kernel3]
        
        X=1630/scaling_factor
        Y=1010/scaling_factor
        self.button_train = ttk.Button(self, text = "Train",command = self.doTraining)
        self.button_train.place(x=X,y=Y,anchor='nw')
        
        X=1795/scaling_factor
        frame_path=tk.Frame(self,height=105/scaling_factor,width=590/scaling_factor,bg=color_set[1])
        frame_path.place(x=X,y=Y,anchor='nw')
        
        X=1800/scaling_factor
        self.label_train = tk.Label(self,  text="", fg=text_color, font=('helvetica', size_xs), bg = color_set[1])
        self.label_train.place(x=X, y=Y, anchor = 'nw')
        
        X=1630/scaling_factor
        Y=1150/scaling_factor
        self.button_save = ttk.Button(self, text = "Save",command = self.saveModel)
        self.button_save.place(x=X,y=Y,anchor='nw')
        
        frame_path=tk.Frame(self,height=90/scaling_factor,width=590/scaling_factor,bg=color_set[1])
        frame_path.place(x=(1600+195)/scaling_factor,y=Y,anchor='nw')
        X=1800/scaling_factor
        self.label_save = tk.Label(self,  text="", fg=text_color, font=('helvetica', size_xs), bg = color_set[1])
        self.label_save.place(x=X, y=Y, anchor = 'nw')
    
    def variance(self,X,Y,var_useVariance,title):
        Label_create_macro = tk.Label(self,  text=title, fg=text_color, font=('helvetica', size_xs), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')      
        entry_variance_min=tk.Entry(self,width=4,font=('helvetica', size_xs)) 
        entry_variance_min.place(x=X+190/scaling_factor, y=Y, anchor = 'nw')
        entry_variance_min.insert(0, '0')
        entry_variance_max=tk.Entry(self,width=4,font=('helvetica', size_xs)) 
        entry_variance_max.place(x=X+340/scaling_factor, y=Y, anchor = 'nw')
        entry_variance_max.insert(0, '15')
        button_variance_use = tk.Checkbutton(self, text=' ',variable=var_useVariance, onvalue=1, offvalue=0, bg = color_set[0],font=('helvetica', size_s))
        button_variance_use.place(x=X+490/scaling_factor, y=Y-15/scaling_factor, anchor = 'nw')
        var_useVariance.set(1)
        
        return entry_variance_min,entry_variance_max,button_variance_use
    
    def button_layer(self,text,value,posX,posY):
         tk.Radiobutton(self, 
              indicatoron = 0,
              text=text,
              fg = text_color,
              selectcolor = color_set[2],
              bg = color_set[0],
              width=9,
              font=('helvetica', size_s),
              variable=self.layer_or_thickness,
              value=value).place(x=posX,y=posY,anchor='w')
    
    def workingfolderDialog(self):
        self.filename = filedialog.askdirectory(initialdir =  "", title = "Select A Folder")
        text=functions.long_path_cutter(self.filename)
        try:
            os.mkdir(self.filename+"/Images_calibration")
        except Exception as e:
                print(e)
        try:
            os.mkdir(self.filename+"/Neural_Network")
        except Exception as e:
                print(e)
        try:
            os.mkdir(self.filename+"/Neural_Network/Good")
        except Exception as e:
                print(e)
        try:
            os.mkdir(self.filename+"/Neural_Network/Bad")
        except Exception as e:
                print(e)
        try:
            os.mkdir(self.filename+"/Neural_Network/Wafers")
        except Exception as e:
                print(e)
                
        try:
            os.mkdir(self.filename+"/Calibration")
        except Exception as e:
                print(e)
        self.Label_path.configure(text = text, justify="left")
    
    def addflakeDialog(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)
        
        if Proceed==1:
            self.calibration_image_path = filedialog.askopenfile(initialdir =  "", title = "Select A Calibration Image").name
            self.what_thicknessDialog()
        
    def what_thicknessDialog(self):
        self.window_thickness = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_thickness.wm_iconbitmap('icon.ico') 
        int(Window_size[0]/scaling_factor)
        self.window_thickness.geometry("%dx%d%+d%+d" % (int(600/scaling_factor), 100/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor)) 
        self.window_thickness.grab_set()
                
        text_attention="thickness:"

        label = tk.Label(self.window_thickness, text=text_attention,bg=color_set[0],font=('helvetica', size_s))
        label.place(x=20/scaling_factor,y=50/scaling_factor,anchor='w')
        
        self.entry_thickness = tk.Entry(self.window_thickness,width=3,font=('helvetica', size_s)) 
        self.entry_thickness.place(x=270/scaling_factor,y=50/scaling_factor,anchor='w')
        button_yes = ttk.Button(self.window_thickness, text="OK", command=self.copyImage)
        button_yes.place(x=400/scaling_factor,y=50/scaling_factor,anchor='w')
        
    def copyImage(self):
        error=0
        try:
            t=float(self.entry_thickness.get())
            self.entry_thickness.configure(bg="white")
        except:
            error=1
            self.entry_thickness.configure(bg=color_error)
        
        if error!=1:
            self.window_thickness.destroy()
        
            try:
                os.mkdir(self.filename+"/Images_calibration/"+str(int(t)))
            except Exception as e:
                print(e)
        
            shutil.copyfile(self.calibration_image_path, self.filename+"/Images_calibration/"+str(int(t))+"/"+self.calibration_image_path.split("/")[-1])
    
    def plot(self):  
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)
        
        posX,posY=10/scaling_factor,500/scaling_factor
        height,width=120/scaling_factor,780/scaling_factor
        if Proceed==1:
            if self.layer_or_thickness.get()==0:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])    
        
        if Proceed==1:
            self.queue_plot = queue.Queue()
            ThreadedPlotter.Plot(self.queue_plot,self.filename).start()
            self.after(20, self.process_queue_plot)
        
    def process_queue_plot(self):
        try:
            msg = self.queue_plot.get(0)
            
            self.values=msg
            self.show_plot()

        except queue.Empty:
            self.after(20, self.process_queue_plot)
    
    def show_plot(self):
        self.window_plot = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_plot.wm_iconbitmap('icon.ico') 
        self.window_plot.geometry("%dx%d%+d%+d" % (int(1400/scaling_factor), int(1400/scaling_factor), (2560/2)/scaling_factor, (100)/scaling_factor)) 
        
        plt.rc('axes', labelsize=25/scaling_factor)
        
        thickness=self.values[0]
        
        topframe=tk.Frame(self.window_plot)
        topframe.pack( side = tk.TOP )
        bottomframe=tk.Frame(self.window_plot)
        bottomframe.pack( side = tk.TOP )
        
        where=[topframe,topframe,bottomframe,bottomframe]
        color=['k','b','g','r']
        ylabel=["black values","blue values","green values","red values"]
        xlabel={1:"number of layers",2:"thickness ( nm )"}
        
        for i in range(4):
            self.plot_routine(where[i],thickness,self.values[1][:,i],self.values[1][:,4+i],color[i],xlabel[self.layer_or_thickness.get()],ylabel[i])
            
    def plot_routine(self,where,thickness,y,yerr,color,xlabel,ylabel):
        figure = plt.Figure(figsize=(7/scaling_factor,7/scaling_factor), dpi=100, tight_layout=True)
        ax = figure.add_subplot(111)
        line = FigureCanvasTkAgg(figure, where)
        line.get_tk_widget().pack(side=tk.LEFT)
        ax.plot(thickness,y,color=color,marker='o',lw=2,ms=7)
        yerr_sup=y+yerr
        yerr_inf=y-yerr
        ax.fill_between(thickness,yerr_sup,yerr_inf, alpha=0.2, color=color)
        
        wafer_color="k"
        if color=='k':
            wafer_color="r"
        ax.plot([0,1000],[127.5,127.5],'--',color=wafer_color,lw=1)
        ax.set_xlim(0,max(thickness)+1)
        ax.set_ylim(min(yerr_inf-10),max(yerr_sup+10))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params('both', length=7, width=1, which='major',direction='in',top=True,right=True)
        ax.tick_params('both', length=3, width=1, which='minor',direction='in',top=True,right=True)
    
        for tick in ax.xaxis.get_major_ticks():        
            tick.set_pad(8)

        for tick in ax.yaxis.get_major_ticks():
            tick.set_pad(8)
    
    def create_calibration(self):
        Proceed=1       
        posX,posY=10/scaling_factor,770/scaling_factor
        height,width=80/scaling_factor,780/scaling_factor
        if hasattr(self,'values') == False:
            Proceed=0
            self.errorFrame(posX,posY,width,height,color_error)
        else:
            Proceed=1
            self.errorFrame(posX,posY,width,height,color_set[0])    
        
        posX,posY=360/scaling_factor,870/scaling_factor
        height,width=160/scaling_factor,400/scaling_factor
        if Proceed==1:
            if self.var_useBlack.get()+self.var_useBlue.get()+self.var_useGreen.get()+self.var_useRed.get() == 0:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        
        posX,posY=10/scaling_factor,1000/scaling_factor
        height,width=160/scaling_factor,500/scaling_factor
        if Proceed==1:
            try :
                float(self.Entry_interval.get())
                Proceed=1
                self.Entry_interval.configure(bg="white")
            except:
                Proceed=0
                self.Entry_interval.configure(bg=color_error)
        
        
        if Proceed==1:
            t=self.values[0]
            k=self.values[1][:,0]
            b=self.values[1][:,1]
            g=self.values[1][:,2]
            r=self.values[1][:,3]
            errk=self.values[1][:,4]
            errb=self.values[1][:,5]
            errg=self.values[1][:,6]
            errr=self.values[1][:,7]
        
            tnew=np.arange(t[0],t[-1]+1)
            k=np.round(interp1d(t,k)(tnew),0)
            b=np.round(interp1d(t,b)(tnew),0)
            g=np.round(interp1d(t,g)(tnew),0)
            r=np.round(interp1d(t,r)(tnew),0)
            errk=np.round(interp1d(t,errk)(tnew),0)
            errb=np.round(interp1d(t,errb)(tnew),0)
            errg=np.round(interp1d(t,errg)(tnew),0)
            errr=np.round(interp1d(t,errr)(tnew),0)
        
            W=np.asarray([tnew,k,b,g,r,errk,errb,errg,errr])
            W=np.transpose(W)
        
            layer={1:"layers",2:"thickness(nm)"}
        
            title=layer[self.layer_or_thickness.get()]+"\tk\tb\tg\tr\tkerror\tberror\tgerror\trerror"
        
            np.savetxt(self.filename+"/Calibration/calibration.dat", W, header=title,  fmt='%i')
            
            layer={1:1,2:0}
            title="layer_or_thickness(1 or 0)\tnumber_of_intervals\tuse_k?\tuse_b?\tuse_g?\tuse_r?\thigh_contrast"
            W=np.asarray([[layer[self.layer_or_thickness.get()]],[int(self.Entry_interval.get())],[self.var_useBlack.get()],[self.var_useBlue.get()],[self.var_useGreen.get()],[self.var_useRed.get()],[0]])
            W=np.transpose(W)
            np.savetxt(self.filename+"/Calibration/calibration_details.dat", W, header=title,  fmt='%i')
    
    def create_criteria(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)
            
        
        if Proceed==1:
            file="#criterium\tuse\tminimal_value\tmaximal_value\n"
 
            min_value,max_value=self.entry_variance_black_min.get(),self.entry_variance_black_max.get()
            if min_value=="":
                min_value="0"
            if max_value=="":
                max_value="15"
            file+="grey_variance\t"+str(self.var_useBlackVariance.get())+"\t"+min_value+"\t"+max_value+"\n"
        
            min_value,max_value=self.entry_variance_blue_min.get(),self.entry_variance_blue_max.get()
            if min_value=="":
                min_value="0"
            if max_value=="":
                max_value="15"
            file+="blue_variance\t"+str(self.var_useBlueVariance.get())+"\t"+min_value+"\t"+max_value+"\n"
        
            min_value,max_value=self.entry_variance_green_min.get(),self.entry_variance_green_max.get()
            if min_value=="":
                min_value="0"
            if max_value=="":
                max_value="15"
            file+="green_variance\t"+str(self.var_useGreenVariance.get())+"\t"+min_value+"\t"+max_value+"\n"
        
            min_value,max_value=self.entry_variance_red_min.get(),self.entry_variance_red_max.get()
            if min_value=="":
                min_value="0"
            if max_value=="":
                max_value="15"
            file+="red_variance\t"+str(self.var_useRedVariance.get())+"\t"+min_value+"\t"+max_value+"\n"
        
            file+="Area/Perimeter\t0\t0.1\t1e5\n"
        
            min_value,max_value=self.entry_aspectratio_min.get(),self.entry_aspectratio_max.get()
            if min_value=="":
                min_value="1"
            if max_value=="":
                max_value="4"
            file+="aspect_ratio\t"+str(self.var_useAspectRatio.get())+"\t"+min_value+"\t"+max_value+"\n"
        
            file+="Npoints_contour\t0\t0\t1e5"
        
            with open(self.filename+"/Calibration/criterium.dat", 'w') as f:
                f.write(file)

    def errorFrame(self,posX,posY,width,height,color):
        thickness=4/scaling_factor
        Vertical_ligne=tk.Frame(self,height=height,width=thickness,bg=color)
        Vertical_ligne.place(x=posX,y=posY)                
        Vertical_ligne=tk.Frame(self,height=height+thickness,width=thickness,bg=color)
        Vertical_ligne.place(x=posX+width,y=posY)            
        Horrizontal_ligne=tk.Frame(self,height=thickness,width=width,bg=color)
        Horrizontal_ligne.place(x=posX,y=posY)                
        Horrizontal_ligne=tk.Frame(self,height=thickness,width=width,bg=color)
        Horrizontal_ligne.place(x=posX,y=posY+height)            
    
    def doSelection(self):       
        Proceed = 1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.label_select.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
                self.index_good=len(os.listdir(self.filename+"/Neural_Network/Good"))
                self.index_bad=len(os.listdir(self.filename+"/Neural_Network/Bad"))
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.label_select.configure(text="Specify working folder")
        
        if Proceed==1:
            
            alldir=os.listdir(self.filename+"/Neural_Network/Wafers")
            self.wafers_path=[]
            for i in range(len(alldir)):
                log = open(self.filename+"/Neural_Network/Wafers/"+alldir[i]+"/log_file.dat", "r")
                log_lines=log.read().split("\n")
                Nwafer=log_lines[2].split("\t")[1]
                wafers_path_in_this_dir=[self.filename+"/Neural_Network/Wafers/"+alldir[i]+"/Wafer_"+str(j).zfill(2) for j in range(int(Nwafer))]
                self.wafers_path.extend(wafers_path_in_this_dir)
            
            self.Nwafer=len(self.wafers_path)
            
            #wafers_path=[self.filename+"/Neural_Network/Wafers/"+name for name in os.listdir(self.filename+"/Neural_Network/Wafers")]
            #self.Nwafer=len(wafers_path)
        
            if self.Nwafer<1:
                self.label_hunt.configure(text="No flakes to select")
        
        if Proceed == 1:
            try:
                self.list_name=[]
                self.folders=[]
                for i in range(self.Nwafer):
                    directories=os.listdir(self.wafers_path[i]+'/Analysed_picture')
                    directories.remove("full_image.jpg")
#                    directories.remove("log_file.dat")
                    self.list_name.extend(directories)
                    for j in range(len(directories)):
                        directories[j]=self.wafers_path[i]+'/Analysed_picture/'+directories[j]
                    self.folders.extend(directories)
                    
            except Exception as e:
                Proceed=0
                self.label_select.configure(text="full_image.jpg missing")
                
        if Proceed == 1:
            if len(self.list_name)>0:
                Proceed=1
            else:
                Proceed=0
                self.label_select.configure(text="No flakes to select")
                self.window_selection.destroy()
        
        if Proceed==1:
            self.window_selection = tk.Toplevel(bg=color_set[0],bd=2)
            self.window_selection.wm_iconbitmap('icon.ico')
            self.width_window_selection=1600
            self.height_window_selection=1800
            self.window_selection.geometry("%dx%d%+d%+d" % (int(self.width_window_selection/scaling_factor), self.height_window_selection/scaling_factor, (2560)/2/scaling_factor, (1440-self.height_window_selection)/2/scaling_factor))
            
            self.list_name=[]
            self.folders=[]
            ppp=[]
            
            for i in range(self.Nwafer):
                directories=os.listdir(self.wafers_path[i]+'/Analysed_picture')
                directories.remove("full_image.jpg")
                #directories.remove("log_file.dat")
                self.list_name.extend(directories)
                for j in range(len(directories)):
                    directories[j]=self.wafers_path[i]+'/Analysed_picture/'+directories[j]
                    ppp.append("/1mm_zoom_Wafer"+str(i).zfill(2)+"_")
                self.folders.extend(directories)
                
            for i in range(len(self.list_name)):
                self.list_name[i]=self.folders[i]+ppp[i]+self.list_name[i]+".jpg"

            self.indice_max=len(self.list_name)
            self.indice_flake=0
            self.showFlake()
        
            button_next     = ttk.Button(self.window_selection, text="Next", command=self.next_flake)
            button_previous = ttk.Button(self.window_selection, text="Previous", command=self.previous_flake)
            
            button_good     = ttk.Button(self.window_selection, text="Good", command=self.good_flake)
            button_bad = ttk.Button(self.window_selection, text="Bad", command=self.bad_flake)
            
#            button_discard = ttk.Button(self.window_selection, text="Discard", command=self.delete_flake)
#            button_discard.place(x=self.width_window_selection*0.5/scaling_factor,y=self.height_window_selection*0.97/scaling_factor,anchor='s')
            
            
            button_next.place(x=self.width_window_selection*0.58/scaling_factor,y=self.height_window_selection*0.92/scaling_factor,anchor='s')
            button_previous.place(x=self.width_window_selection*0.42/scaling_factor,y=self.height_window_selection*0.92/scaling_factor,anchor='s')      
            
            button_good.place(x=self.width_window_selection*0.58/scaling_factor,y=self.height_window_selection*0.96/scaling_factor,anchor='s')
            button_bad.place(x=self.width_window_selection*0.42/scaling_factor,y=self.height_window_selection*0.96/scaling_factor,anchor='s')      
    
    def delete_flake(self):
        to_be_deleted_folder=self.folders[self.indice_flake]
        to_be_deleted_name=self.list_name[self.indice_flake]
        
        shutil.rmtree(to_be_deleted_folder)
        self.indice_max-=1
        self.folders.remove(to_be_deleted_folder)
        self.list_name.remove(to_be_deleted_name)
        
        if len(self.folders)>0:
            if self.indice_flake>=self.indice_max:
                self.indice_flake=0
        
            self.showFlake()
        
        else:
            self.window_selection.destroy()
    
    def good_flake(self):
        to_be_deleted_folder=self.folders[self.indice_flake]
        to_be_deleted_name=self.list_name[self.indice_flake]
        
        image = cv2.imread(to_be_deleted_folder+"/NN.jpg")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        shutil.copyfile(to_be_deleted_folder+"/NN.jpg",self.filename+"/Neural_Network/Good/"+str(self.index_good)+".jpg")
        self.index_good+=1
        
        shutil.rmtree(to_be_deleted_folder)
        self.indice_max-=1
        self.folders.remove(to_be_deleted_folder)
        self.list_name.remove(to_be_deleted_name)
        
        self.label_select.configure(text="Data base created:\t"+str(self.index_good)+" good shots\n\t\t"+str(self.index_bad)+" bad shots")
        
        if len(self.folders)>0:
            if self.indice_flake>=self.indice_max:
                self.indice_flake=0
        
            self.showFlake()
        
        else:
            self.window_selection.destroy()
    
    def bad_flake(self):
        to_be_deleted_folder=self.folders[self.indice_flake]
        to_be_deleted_name=self.list_name[self.indice_flake]
        
        
        image = cv2.imread(to_be_deleted_folder+"/NN.jpg")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        shutil.copyfile(to_be_deleted_folder+"/NN.jpg",self.filename+"/Neural_Network/Bad/"+str(self.index_bad)+".jpg")
        self.index_bad+=1
        
        shutil.rmtree(to_be_deleted_folder)
        self.indice_max-=1
        self.folders.remove(to_be_deleted_folder)
        self.list_name.remove(to_be_deleted_name)
        
        self.label_select.configure(text="Data base created: \n"+str(self.index_good)+" good shots\n"+str(self.index_bad)+" bad shots")
        
        if len(self.folders)>0:
            if self.indice_flake>=self.indice_max:
                self.indice_flake=0
        
            self.showFlake()
        
        else:
            self.window_selection.destroy()
    
    def next_flake(self):
        self.indice_flake+=1
        if self.indice_flake>self.indice_max-1:
            self.indice_flake=0
        self.showFlake()
    
    def previous_flake(self):
        self.indice_flake-=1
        if self.indice_flake<0:
            self.indice_flake=self.indice_max-1
        self.showFlake()
    
    def showFlake(self):
        load_wafer = Image.open(self.list_name[self.indice_flake])
        load_wafer = load_wafer.resize((int(1500/scaling_factor), int(1500/scaling_factor)), Image.ANTIALIAS)
        render_wafer = ImageTk.PhotoImage(load_wafer)
        
        self.flake = tk.Label(self.window_selection, image=render_wafer, bg = color_set[1])
        self.flake.image = render_wafer
        self.flake.place(x=self.width_window_selection/2/scaling_factor,y=self.height_window_selection*0.9/2/scaling_factor,anchor='center')
    
    def Hunt_one(self,indice,factor):
        
        self.queue_hunt = queue.Queue()
        Hunter_parallele.ThreadedHunter(self.queue_hunt,self.filename,self.wafers_path,self.hunt_counter,self.targeted_area,factor,indice,self.var_high_contrast.get()).start()
        self.after(100, self.process_queue_hunt)
    
    def Hunt(self):
        Proceed=1
        ## Is running already
        if Proceed==1:
            if self.hunting_running==0:
                Proceed=1
            else:
                Proceed=0
                self.label_hunt.configure(text="Already Running")
                
        ## Folder (Specify folder)
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.label_hunt.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])

        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.label_hunt.configure(text="Specify working folder")
        
        alldir=os.listdir(self.filename+"/Neural_Network/Wafers")
        
        self.wafers_path=[]
        for i in range(len(alldir)):
            log = open(self.filename+"/Neural_Network/Wafers/"+alldir[i]+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            Nwafer=log_lines[2].split("\t")[1]
            wafers_path_in_this_dir=[self.filename+"/Neural_Network/Wafers/"+alldir[i]+"/Wafer_"+str(j).zfill(2) for j in range(int(Nwafer))]
            self.wafers_path.extend(wafers_path_in_this_dir)
            
        #wafers_path=[self.filename+"/Neural_Network/Wafers/"+name for name in os.listdir(self.filename+"/Neural_Network/Wafers")]
        self.Nwafer=len(self.wafers_path)
        
        if self.Nwafer<1:
            self.label_hunt.configure(text="Nothing to hunt")
        
        ## Picture (No stiched picture)
        if Proceed==1:
            is_there_stitched_images=0
            for i in range(self.Nwafer):
                is_there_stitched_images+=os.path.exists(self.wafers_path[i]+"/Analysed_picture/full_image.jpg")
            if is_there_stitched_images==self.Nwafer:
                Proceed=1
            else:
                Proceed=0
                self.label_hunt.configure(text="Missing stitched pictures")
                
        ## Nosepiece (No log file)
        if Proceed==1:
            is_there_logfiles=0
            for i in range(self.Nwafer):
                is_there_logfiles+=os.path.exists(self.wafers_path[i]+"/log_file.dat")
            
            if is_there_logfiles==self.Nwafer:
                log = open(self.wafers_path[0]+"/log_file.dat", "r")
                log_lines=log.read().split("\n")
                self.Nosepiece=log_lines[1].split("\t")[1]
                self.factor=self.factors[self.nosepieces.index(self.Nosepiece)]

                Proceed=1
            else:
                Proceed=0
                self.label_hunt.configure(text="No log files")                         
        
        posX,posY=810/scaling_factor,800/scaling_factor
        height,width=220/scaling_factor,780/scaling_factor
            
        ## Area (Specify area of what you want to hunt)
        if Proceed==1:
            self.targeted_area = self.Entry_size.get()
            
            posX,posY=810/scaling_factor,960/scaling_factor
            height,width=120/scaling_factor,780/scaling_factor
            try :
                self.targeted_area=float(self.targeted_area)
                self.errorFrame(posX,posY,width,height,color_set[0])
                Proceed=1
            except:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)        
                self.label_hunt.configure(text="Specify area")
        
        if Proceed==1:
            self.hunting_running=1
            self.queue_hunt_multi = queue.Queue()
            self.after(100, self.process_queue_hunt_multi)
            self.hunt_counter=0
            self.Hunt_one(self.hunt_counter,self.factor)
    
    def process_queue_hunt_multi(self):
        try:
            msg = self.queue_hunt_multi.get(0)
            self.hunt_counter+=1
            
            if self.hunt_counter<self.Nwafer:
                self.queue_hunt = queue.Queue()
                self.after(100, self.process_queue_hunt_multi)
                self.Hunt_one(self.hunt_counter,self.factor)
            
            else:
                self.hunt_running=0
                self.hunt_counter=0
                
        except:
            self.after(100, self.process_queue_hunt_multi)
            
    def process_queue_hunt(self):
        try:
            msg = self.queue_hunt.get(0)
            # Show result of the task if needed
            if msg[0] == 0:                
                self.label_hunt.configure(text = msg[1])
                self.hunting_running=1
                self.after(100, self.process_queue_hunt)
            
            elif msg[0] == 1:
                self.label_hunt.configure(text = msg[1])
                self.queue_hunt_multi.put(0)
        
        except queue.Empty:
            self.after(100, self.process_queue_hunt)   
    
    def modelPathDialog(self):
        self.model_path = filedialog.askdirectory(initialdir =  "", title = "Select A Folder")
        text=functions.long_path_cutter(self.model_path)
        self.Label_model_path.configure(text = text, justify="left")
    
    def doTraining(self):  
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)
        
        try:
            model_path = self.model_path
        except:
            model_path = ''
        
        filters=[]
        for i in range(len(self.entry_Filters)):
            try:
                filters.append(int(self.entry_Filters[i].get()))
                self.entry_Filters[i].configure(bg="white")
            except :
                self.entry_Filters[i].configure(bg=color_error)
                Proceed=0
        
        kernels=[]
        for i in range(len(self.entry_Kernels)):
            try:
                kernels.append(int(self.entry_Kernels[i].get()))
                self.entry_Kernels[i].configure(bg="white")
                if int(self.entry_Kernels[i].get())%2!=1:
                    self.entry_Kernels[i].configure(bg=color_error)
                    Proceed=0
            except :
                self.entry_Kernels[i].configure(bg=color_error)
                Proceed=0
        
        try:
            int(self.entry_BatchSize.get())
            self.entry_BatchSize.configure(bg="white")
        except :
            self.entry_BatchSize.configure(bg=color_error)
            Proceed=0
        
        try:
            int(self.entry_ImageSize.get())
            self.entry_ImageSize.configure(bg="white")
        except :
            self.entry_ImageSize.configure(bg=color_error)
            Proceed=0
        
        try:
            int(self.entry_Epoch.get())
            self.entry_Epoch.configure(bg="white")
        except :
            self.entry_Epoch.configure(bg=color_error)
            Proceed=0
        
        if Proceed==1:
            self.queue_train = queue.Queue()
            ThreadedTrainer.Train(self.queue_train,
                                  self.filename,
                                  model_path,
                                  filters, kernels,
                                  int(self.entry_BatchSize.get()),
                                  int(self.entry_ImageSize.get()),
                                  int(self.entry_Epoch.get())).start()
            self.after(20, self.process_queue_training)
            
            epoch_dir="temp_model"
            if os.path.exists(epoch_dir):
                shutil.rmtree(epoch_dir)
            
            try:    
                os.mkdir(epoch_dir)
            except Exception as e:
                print(e)
            
            self.check_epoch()
    
    def check_epoch(self):
        try:
            n_checkpoint=(len(os.listdir("temp_model"))-1)/2
            percent=int(np.round(n_checkpoint/float(self.entry_Epoch.get())*100,0))
            if percent<0: percent=0
            self.label_train.configure(text="Training in progress: "+str(percent)+ "%")
            self.after(100, self.check_epoch)
            
        except Exception as e:
            self.label_train.configure(text="Training completed\n Accuracy: "+str(np.round(self.accuracy[1][-1]*100,1))+" %")
            
    
    def process_queue_training(self):
        try:
            msg = self.queue_train.get(0)
            
            self.names=msg[0]
            self.accuracy=msg[1]
            self.model=msg[2][0]
            
            self.label_train.configure(text="Training completed\n Accuracy: "+str(np.round(self.accuracy[1][-1]*100,1))+" %")
            
            self.show_plot_training()

        except queue.Empty:
            self.after(10, self.process_queue_training)
            
    def saveModel(self):
        try:
            self.model.save_weights(self.filename+"/Calibration/trained_model.h5")
            model_json = self.model.to_json()
            with open(self.filename+"/Calibration/trained_model.json", "w") as json_file:
                json_file.write(model_json)
            
            self.label_save.configure(text="Model saved")
            
            f = open(self.filename+"/Calibration/model_details.dat", "w")
            model_detail ="pic size\t"+self.entry_ImageSize.get()+"\n"
            model_detail+="Epoch\t"+self.entry_Epoch.get()+"\n"
            model_detail+="Accuracy\t"+str(np.round(self.accuracy[1][-1]*100,1))+"\n"
            
            f.write(model_detail)
            f.close()
            
        except:
            self.label_save.configure(text="No model to save")
            
    def show_plot_training(self):
        self.window_plot = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_plot.wm_iconbitmap('icon.ico') 
        self.window_plot.geometry("%dx%d%+d%+d" % (int(1400/scaling_factor), int(700/scaling_factor), (2560/2)/scaling_factor, (100)/scaling_factor)) 
        
        plt.rc('axes', labelsize=25/scaling_factor)
        
        ylabel=["accuracy","loss"]

        self.plot_routine_training(1,ylabel[0])
        self.plot_routine_training(3,ylabel[1])
            
    def plot_routine_training(self,i,ylabel):
        
        figure = plt.Figure(figsize=(7/scaling_factor,7/scaling_factor), dpi=100, tight_layout=True)
        ax = figure.add_subplot(111)
        line = FigureCanvasTkAgg(figure,self.window_plot)
        line.get_tk_widget().pack(side=tk.LEFT)
        ax.plot(self.accuracy[0],self.accuracy[i],color="b",marker='o',lw=2,ms=0)
        ax.plot(self.accuracy[0],self.accuracy[i+1],color="r",marker='o',lw=2,ms=0)
        
        ax.set_xlim(0,self.accuracy[0][-1]+1)
        if i==1:
            ax.set_ylim(0,1)
        else:
            max1=max(self.accuracy[i])
            max2=max(self.accuracy[i+1])
           
            ax.set_ylim(0,max(max1,max2)+0.1)
        ax.set_xlabel("epoch")
        ax.set_ylabel(ylabel)
        ax.tick_params('both', length=7, width=1, which='major',direction='in',top=True,right=True)
        ax.tick_params('both', length=3, width=1, which='minor',direction='in',top=True,right=True)
    
        for tick in ax.xaxis.get_major_ticks():        
            tick.set_pad(8)

        for tick in ax.yaxis.get_major_ticks():
            tick.set_pad(8)
    
if __name__ == '__main__':
    mp.freeze_support()
    root = Root()
    root.mainloop()
