import tkinter as tk
import os
import functions
import Stitcher
import Hunter_parallele
import Auto_functions
import numpy as np
import multiprocessing as mp
import ThreadedTrainer
import sys

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import queue

from tkinter import ttk
from tkinter import filedialog

from PIL import Image, ImageTk

import shutil

config = functions.get_config()
(MAIN_FOLDER, SCREEN_SCALING, ZEROS, 
 FOV, OVERLAP, SCALE, JPG,
 LOW_RES, HIGH_RES, CCD,
 OFFSET_X, OFFSET_Y, OFFSET_Z) = config

scaling_factor = float(SCREEN_SCALING)
police_factor = scaling_factor

size_l=int(28/scaling_factor*police_factor)
size_s=int(18/scaling_factor*police_factor)
size_xs=int(12/scaling_factor*police_factor)

color_error="#EC7063"
color_set=['#e3e4e7','#ffffff','#d9d9d9']
text_color='#312820'

Window_size=[2400,1270]


class Root(tk.Tk):
    def __init__(self):
        super(Root, self).__init__()
        self.title("Flinder")
        
        self.minsize(int(Window_size[0]/scaling_factor), int(Window_size[1]/scaling_factor))
        self.wm_iconbitmap('icon.ico')
        self.configure(bg=color_set[0])
        
        self.nosepieces=["5x","10x","20x","50x","100x"]
        self.overlap = OVERLAP
        self.Fieldvalues=[FOV[0]*(1-self.overlap),FOV[1]*(1-self.overlap)]
        
        self.factors=[1,2,4,10,20]
        self.step_focus = [3,4,5,6,7]
        
        self.zaxis=[(2,0.5,10),(2,0.5,0.1),(1,0.25,0.05),(1,0.25,0.05),(0.5,0.1,0.01)]
        self.zaxis_step=[10,10,30]
        
        self.stitching_running=0
        self.hunting_running=0
        self.stitch_counter=0
        self.hunt_counter=0
        
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing_main)
        
        #Create two vertical lines to separate the window in 3 pannels
        Vertical_ligne1=tk.Frame(self,height=Window_size[1]/scaling_factor,width=2,bg=color_set[1])
        Vertical_ligne1.place(x=799/scaling_factor,y=0)

        Vertical_ligne2=tk.Frame(self,height=Window_size[1]/scaling_factor,width=2,bg=color_set[1])
        Vertical_ligne2.place(x=1599/scaling_factor,y=0)

        #Define the working folder
        X,Y=30/scaling_factor,10/scaling_factor
        Label_working_folder = tk.Label(self,  text="Working Folder", fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_working_folder.place(x=X, y=Y, anchor = 'nw')
        
        X,Y,height,width=195/scaling_factor,Y+120/scaling_factor,170/scaling_factor,590/scaling_factor
        Frame_path_working_folder=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_path_working_folder.place(x=X,y=Y,anchor='nw')
        
        X,Y=200/scaling_factor,Y+5/scaling_factor
        self.Label_path = tk.Label(self,  text="Path: ", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.Label_path.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=30/scaling_factor,Y-5/scaling_factor
        Button_browse = ttk.Button(self, text = "Browse",command = self.workingfolderDialog)
        Button_browse.place(x=X,y=Y,anchor='nw')

        #Scanning size text and entry
        posX,posY=30/scaling_factor,320/scaling_factor
        Label_scanning_size = tk.Label(self, text= 'Position and size', fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_scanning_size.place(x=posX, y=posY, anchor = 'nw')
        
        posX,posY=40/scaling_factor,480/scaling_factor
        stepY=100/scaling_factor
        
        Label_numberofwafers = tk.Label(self, text= "Number of Wafers", fg='black', font=('helvetica', size_s), bg = color_set[0])
        Label_numberofwafers.place(x=posX, y=posY, anchor='w')
        
        Offset=430/scaling_factor
        self.entry_numberofwafers = tk.Entry(self,width=3,font=('helvetica', size_s)) 
        self.entry_numberofwafers.place(x=posX+Offset, y=posY, anchor='w')
        
        X,Y=400/scaling_factor,570/scaling_factor
        Button_setup = ttk.Button(self, text = " Enter position and size ",command = self.position_size_popup)
        Button_setup.place(x=X,y=Y,anchor='center')
        
        X,Y=40/scaling_factor,650/scaling_factor
        self.var_auto_stitch = tk.IntVar()
        self.button_auto_stitch = tk.Checkbutton(self, text='Auto Stitch',variable=self.var_auto_stitch, onvalue=1, offvalue=0, bg = color_set[0],font=('helvetica', size_s))
        self.button_auto_stitch.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=X+400/scaling_factor,Y
        self.var_auto_hunt = tk.IntVar()
        self.button_auto_hunt = tk.Checkbutton(self, text='Auto Hunt',variable=self.var_auto_hunt, onvalue=1, offvalue=0, bg = color_set[0],font=('helvetica', size_s))
        self.button_auto_hunt.place(x=X, y=Y, anchor = 'nw')
        
        
        
        #Eyepiece Magnification text and button
        X,Y=30/scaling_factor,780/scaling_factor
        X0=50/scaling_factor
        Y0=160/scaling_factor
        stepX=130/scaling_factor
        
        Label_nosepiece = tk.Label(self, text= 'Nosepiece', fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_nosepiece.place(x=X, y=Y, anchor = 'nw')
        
        self.nosepiece_selected = tk.IntVar()
        text=['5x','10x','20x','50x','100x']
        for i in range(len(text)):
            self.button_nosepiece(text[i],i+1,X+X0+i*stepX,Y+Y0)

        
        #Create the scanning macro
        X,Y=30/scaling_factor,1050/scaling_factor
        Label_create_macro = tk.Label(self,  text="Create Macro", fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_create_macro.place(x=X, y=Y, anchor = 'nw')
        
        X,Y,height,width=195/scaling_factor,1165/scaling_factor,55/scaling_factor,590/scaling_factor
        Frame_path_create_macro=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_path_create_macro.place(x=X,y=Y,anchor='nw')
        
        X,Y=480/scaling_factor,1192/scaling_factor
        self.Label_macro = tk.Label(self,  text="Waiting for the Go...", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.Label_macro.place(x=X, y=Y, anchor = 'center')
        
        X,Y=30/scaling_factor,1170/scaling_factor
        Button_macro = ttk.Button(self, text = "GO",command = self.checkEverything)
        Button_macro.place(x=X,y=Y,anchor='nw')
        
        #Image stitching pannel
        X,Y=830/scaling_factor, 10/scaling_factor
        Label_stitch = tk.Label(self,  text="Stitch Image", fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_stitch.place(x=X, y=Y, anchor = 'nw')
        
        X,Y,height,width=1350/scaling_factor, 380/scaling_factor,480/scaling_factor,480/scaling_factor
        Frame_stitched_image=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_stitched_image.place(x=X,y=Y,anchor='center')
        self.Label_image = tk.Label(self,  text="No Image\nto Display", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.Label_image.place(x=X, y=Y, anchor = 'center')
        
        X=950/scaling_factor
        Button_stitch = ttk.Button(self, text = "Stitch",command = self.stitchImage_popup)
        Button_stitch.place(x=X,y=Y,anchor='center')
    
        #Flake Hunt
        X,Y=830/scaling_factor,650/scaling_factor
        Label_flake_hunt = tk.Label(self,  text="Flake Hunt", fg='black', font=('helvetica', size_l), bg = color_set[0])
        Label_flake_hunt.place(x=X, y=Y, anchor = 'nw')
        
        X,Y,Ystep=850/scaling_factor,810/scaling_factor,85/scaling_factor
        
        self.Var_hunt_material = tk.StringVar()
    
        # Hunt_choices = set(os.listdir("Materials"))
        Hunt_choices = [""]
        
        self.Optionmenu_hunt = tk.OptionMenu(self, self.Var_hunt_material, *Hunt_choices, command = self.actualize_range)
        self.Optionmenu_hunt.config(font=('helvetica', size_s),width=14,bg = color_set[0])
        self.Optionmenu_hunt.place(x=X,y=Y,anchor='w')
        
        Offset=570/scaling_factor        
        self.Entry_size = tk.Entry(self,width=6,font=('helvetica', size_s)) 
        self.Entry_size.place(x=X+Offset, y=Y, anchor='center')
        
        OffsetX,OffsetY=570/scaling_factor,120/scaling_factor
        Label_size = tk.Label(self,  text=u"Size ( \u03bc\u33A1 )", fg='black', font=('helvetica', size_s), bg = color_set[0])
        Label_size.place(x=X+OffsetX, y=Y-OffsetY, anchor = 'n')
        
        X,Y=1200/scaling_factor,1003/scaling_factor
        Label_range = tk.Label(self,  text="Range", fg='black', font=('helvetica', size_s), bg = color_set[0])
        Label_range.place(x=X, y=Y, anchor = 'nw')
        
        X+=170/scaling_factor
        self.Entry_range_min = tk.Entry(self,width=3,font=('helvetica', size_s), justify="right") 
        self.Entry_range_min.place(x=X, y=Y, anchor='nw')
        
        X+=100/scaling_factor
        self.Entry_range_max = tk.Entry(self,width=3,font=('helvetica', size_s), justify="right") 
        self.Entry_range_max.place(x=X, y=Y, anchor='nw')
        
        X,Y=1000/scaling_factor,910/scaling_factor
        self.button_train =  ttk.Button(self, text = "        Train        ",command = self.check_training)
        self.button_train.place(x=X,y=Y,anchor='nw')
        
        X,Y=1250/scaling_factor,910/scaling_factor
        self.button_import = ttk.Button(self, text = " Import Calibration ",command = self.import_calibration)
        self.button_import.place(x=X,y=Y,anchor='nw')
        
        X,Y=870/scaling_factor,1000/scaling_factor
        self.var_AI = tk.IntVar()
        self.button_AI = tk.Checkbutton(self, text='Use AI',variable=self.var_AI, onvalue=1, offvalue=0, bg = color_set[0],font=('helvetica', size_s))
        self.button_AI.place(x=X, y=Y, anchor = 'nw')
        
        X,Y=830/scaling_factor,1135/scaling_factor
        Button_hunt = ttk.Button(self, text = "Hunt",command = self.Hunt)
        Button_hunt.place(x=X,y=Y,anchor='w')
        
        X,Y,height,width=1000/scaling_factor,1105/scaling_factor,130/scaling_factor,585/scaling_factor
        Frame_hunt=tk.Frame(self,height=height,width=width,bg=color_set[1])
        Frame_hunt.place(x=X,y=Y,anchor='nw')
        
        lw_hunt = tk.Label(self,  text="Progress:", fg='black', font=('helvetica', int(size_xs/1)), bg = color_set[1],justify='left')
        lw_hunt.place(x=X, y=Y, anchor = 'nw')
        
        self.label_hunt = tk.Label(self,  text="", fg='black', font=('helvetica', int(size_xs/1)), bg = color_set[1],justify='left')
        self.label_hunt.place(x=X+150/scaling_factor, y=Y, anchor = 'nw')
        
        #Select flakes
        lw5 = tk.Label(self,  text="Select Flakes", fg='black', font=('helvetica', size_l), bg = color_set[0])
        lw5.place(x=1630/scaling_factor, y=10/scaling_factor, anchor = 'nw')
        
        frame_path=tk.Frame(self,height=55/scaling_factor,width=590/scaling_factor,bg=color_set[1])
        frame_path.place(x=(1600+195)/scaling_factor,y=150/scaling_factor,anchor='nw')
        
        self.label_select = tk.Label(self,  text="No selection done", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.label_select.place(x=(480+1600)/scaling_factor, y=175/scaling_factor, anchor = 'center')
        
        self.button_select = ttk.Button(self, text = "Select",command = self.doSelection)
        self.button_select.place(x=1630/scaling_factor,y=150/scaling_factor,anchor='nw')
        
        
        #Bright field 
        lw6 = tk.Label(self,  text="Step 1: 50x scan", fg='black', font=('helvetica', size_l), bg = color_set[0])
        lw6.place(x=1630/scaling_factor, y=260/scaling_factor, anchor = 'nw')
        
        X0,Y0=1650,410
        lw61 = tk.Label(self,  text="Exposure:             ms", fg='black', font=('helvetica', size_s), bg = color_set[0])
        lw61.place(x=(X0)/scaling_factor, y=(Y0)/scaling_factor, anchor = 'w')
        
        shift=250
        self.entry_exposure_BF_50 = tk.Entry(self,width=4,font=('helvetica', size_s)) 
        self.entry_exposure_BF_50.place(x=(X0+shift)/scaling_factor, y=Y0/scaling_factor, anchor='w')
        
        frame_BF=tk.Frame(self,height=100/scaling_factor,width=320/scaling_factor,bg=color_set[1])
        frame_BF.place(x=2070/scaling_factor,y=(Y0+50)/scaling_factor,anchor='nw')
        
        self.button_BF = ttk.Button(self, text = " Create Macro ",command = self.create50xmacro)
        self.button_BF.place(x=2150/scaling_factor,y=(Y0+0/2)/scaling_factor,anchor='w')
        
        self.Label_macro_BF=tk.Label(self,  text="Don't type any input\nfor auto-exposure", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.Label_macro_BF.place(x=2225/scaling_factor, y=(Y0+56)/scaling_factor, anchor = 'n')
        
        
        X0=1650
        Y0=510
        step=100
        self.BF100x = tk.IntVar()
        
        shift=320
        
        #Dark field
        lw7 = tk.Label(self,  text="Step 2: 100x and DF", fg='black', font=('helvetica', size_l), bg = color_set[0])
        lw7.place(x=1630/scaling_factor, y=610/scaling_factor, anchor = 'nw')
        
        X0=1610
        Y0=860
        step=100
        self.BF100x = tk.IntVar()
        self.DF50x = tk.IntVar()
        self.DF100x = tk.IntVar()
        tk.Checkbutton(self, 
              indicatoron = 0,
              text="BF100x",
              selectcolor = color_set[2],
              bg = color_set[0],
              width=6,
              font=('helvetica', size_s),
              variable=self.BF100x).place(x=(X0)/scaling_factor,y=(Y0)/scaling_factor,anchor='w')
        tk.Checkbutton(self, 
              indicatoron = 0,
              text="DF50x",
              selectcolor = color_set[2],
              bg = color_set[0],
              width=6,
              font=('helvetica', size_s),
              variable=self.DF50x).place(x=(X0+0*step)/scaling_factor,y=(Y0+step)/scaling_factor,anchor='w')
        tk.Checkbutton(self, 
              indicatoron = 0,
              text="DF100x",
              selectcolor = color_set[2],
              bg = color_set[0],
              width=6,
              font=('helvetica', size_s),
              variable=self.DF100x).place(x=(X0)/scaling_factor,y=(Y0+2*step)/scaling_factor,anchor='w')
        
        shift=260
        lw71 = tk.Label(self,  text="Exp (ms)", fg='black', font=('helvetica', size_xs), bg = color_set[0])
        lw71.place(x=(X0+shift)/scaling_factor, y=(Y0-100)/scaling_factor, anchor = 'n')
        
        self.entry_exposure_BF_100 = tk.Entry(self,width=4,font=('helvetica', size_s)) 
        self.entry_exposure_BF_100.place(x=(X0+shift)/scaling_factor, y=(Y0)/scaling_factor, anchor='center')
    
        self.entry_exposure_DF_50 = tk.Entry(self,width=4,font=('helvetica', size_s), justify="right") 
        self.entry_exposure_DF_50.insert(0,2000)
        self.entry_exposure_DF_50.place(x=(X0+shift)/scaling_factor, y=(Y0+step)/scaling_factor, anchor='center')

        self.entry_exposure_DF_100 = tk.Entry(self,width=4,font=('helvetica', size_s))
        self.entry_exposure_DF_100.insert(0,3000)
        self.entry_exposure_DF_100.place(x=(X0+shift)/scaling_factor, y=(Y0+2*step)/scaling_factor, anchor='center')
        
        shift=380
        lw71 = tk.Label(self,  text="Gain", fg='black', font=('helvetica', size_xs), bg = color_set[0])
        lw71.place(x=(X0+shift)/scaling_factor, y=(Y0-100)/scaling_factor, anchor = 'n')
        
        self.entry_gain_BF_100 = tk.Entry(self,width=2,font=('helvetica', size_s)) 
        self.entry_gain_BF_100.place(x=(X0+shift)/scaling_factor, y=(Y0)/scaling_factor, anchor='center')
    
        self.entry_gain_DF_50 = tk.Entry(self,width=2,font=('helvetica', size_s))
        self.entry_gain_DF_50.insert(0,15)
        self.entry_gain_DF_50.place(x=(X0+shift)/scaling_factor, y=(Y0+step)/scaling_factor, anchor='center')

        self.entry_gain_DF_100 = tk.Entry(self,width=2,font=('helvetica', size_s))
        self.entry_gain_DF_100.insert(0,20)
        self.entry_gain_DF_100.place(x=(X0+shift)/scaling_factor, y=(Y0+2*step)/scaling_factor, anchor='center')
        
        self.button_DF = ttk.Button(self, text = " Create Macro ",command = self.createDFmacro)
        self.button_DF.place(x=2150/scaling_factor,y=(Y0+0/2)/scaling_factor,anchor='w')
        
        frame_DF=tk.Frame(self,height=100/scaling_factor,width=320/scaling_factor,bg=color_set[1])
        frame_DF.place(x=2070/scaling_factor,y=(Y0+50)/scaling_factor,anchor='nw')
        
        self.Label_macro_DF=tk.Label(self,  text="Don't type any input\nfor auto-exposure", fg='black', font=('helvetica', size_xs), bg = color_set[1])
        self.Label_macro_DF.place(x=2225/scaling_factor, y=(Y0+56)/scaling_factor, anchor = 'n')
        
        self.button_combine = ttk.Button(self, text = "Post Processing",command = self.combine_picture)
        self.button_combine.place(x=1866/scaling_factor,y=(Y0+330)/scaling_factor,anchor='c')
        
        self.button_done = ttk.Button(self, text = "Free Space",command = self.LastStep)
        self.button_done.place(x=2132/scaling_factor,y=(Y0+330)/scaling_factor,anchor='c')
        
        self.Label_report = tk.Label(self, text="", fg='black', font=('helvetica', size_xs), bg = color_set[0])
        self.Label_report.place(x=1866/scaling_factor,y=(Y0+320+55)/scaling_factor,anchor='c')
        
        self.Login_popup()
    
    def on_closing_main(self):
        if hasattr(self, "trainer"):
            self.trainer.join()
        if hasattr(self,"hunter"):
            self.hunter.join()
        self.destroy()
        sys.exit()
        pass
    
    def Login_popup(self):
        self.window_login = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_login.wm_iconbitmap('icon.ico')
        self.window_login.geometry("%dx%d%+d%+d" % (int(600/scaling_factor), 250/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_login.grab_set()
        
        self.window_login.protocol("WM_DELETE_WINDOW", self.on_closing_login)
        
        X,Y = 50, 75
        text_user="User"
        label = tk.Label(self.window_login, text=text_user,bg=color_set[0],font=('helvetica', size_s))
        label.configure(justify="left")
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        X=X+150
        self.entry_user = tk.Entry(self.window_login,width=13,font=('helvetica', size_s)) 
        self.entry_user.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        self.entry_user.focus()
        
        Y = 200

        button_login = ttk.Button(self.window_login, text="Login", command=self.login)
        button_login.place(x=100/scaling_factor,y=Y/scaling_factor,anchor='s')
        button_login.bind('<Return>',self.login)
        
        button_newuser = ttk.Button(self.window_login, text="New User", command=self.new_user)
        button_newuser.place(x=300/scaling_factor,y=Y/scaling_factor,anchor='s')
        button_newuser.bind('<Return>',self.new_user)
        
        
        button_exit = ttk.Button(self.window_login, text="Exit", command=self.close_all)
        button_exit.place(x=500/scaling_factor,y=Y/scaling_factor,anchor='s')
        button_exit.bind('<Return>',self.close_all)
    
    def new_user(self, event = "e"):
        new_user = self.entry_user.get()
        
        if new_user.isidentifier() == False or new_user == "":
            self.enter_name()
            return 0
        
        known_users = os.listdir(f"{MAIN_FOLDER}/Materials")
        if new_user in known_users:
            self.user_exists()
            return 0
        
        self.user = new_user
        self.create_user()
    
    def user_exists(self):
        X,Y = 550, 100
        self.window_userexists = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_userexists.wm_iconbitmap('icon.ico')
        self.window_userexists.geometry("%dx%d%+d%+d" % (int(X/scaling_factor), Y/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_userexists.grab_set()
        
        X,Y = X/2, 75
        text_user="User already exists"
        label = tk.Label(self.window_userexists, text=text_user,bg=color_set[0],font=('helvetica', size_s))
        label.configure(justify="left")
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
    
    def enter_name(self):
        X,Y = 550, 100
        self.window_userexists = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_userexists.wm_iconbitmap('icon.ico')
        self.window_userexists.geometry("%dx%d%+d%+d" % (int(X/scaling_factor), Y/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_userexists.grab_set()
        
        X,Y = X/2, 75
        text_user="Enter a valid Username"
        label = tk.Label(self.window_userexists, text=text_user,bg=color_set[0],font=('helvetica', size_s))
        label.configure(justify="left")
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
    
    def create_user(self):
        os.mkdir(f"{MAIN_FOLDER}/Materials/{self.user}")
        self.imported_calibration = "hBN"
        self.copy_calibration()
        self.login()
        
    def copy_calibration(self):
        path_default = f"{MAIN_FOLDER}/Materials/Default/{self.imported_calibration}"
        path_user = f"{MAIN_FOLDER}/Materials/{self.user}/{self.imported_calibration}"
        
        os.mkdir(path_user)
        
        os.mkdir(f"{path_user}/NN_database")
        os.mkdir(f"{path_user}/NN_database/Good")
        os.mkdir(f"{path_user}/NN_database/Bad")
        
        
        files = os.listdir(path_default)
        for file in files:
            if file != "NN_database":
                src = f"{path_default}/{file}"
                dst = f"{path_user}/{file}"
                try:
                    shutil.copytree(src, dst)
                except:
                    shutil.copy(src, dst)
    
    def check_import_calibration(self):
        self.imported_calibration = self.Var_import_calibration.get()
        path_calibration = f"{MAIN_FOLDER}/Materials/{self.user}/{self.imported_calibration}"
        
        if os.path.exists(path_calibration):
            self.overwrite()
        
        else:
            self.import_calibration_routine()
    
    def import_calibration_routine(self):
        
        if hasattr(self, "window_overwrite"):
            self.window_overwrite.destroy()
        
        path_calibration = f"{MAIN_FOLDER}/Materials/{self.user}/{self.imported_calibration}"
        if os.path.exists(path_calibration):
            shutil.rmtree(path_calibration)
        
        self.copy_calibration()
        self.load_calibration()
        self.window_import.destroy()
        
        self.attributes('-topmost', True)
        self.attributes('-topmost', False)
        
    
    def overwrite(self):
        self.window_overwrite = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_overwrite.wm_iconbitmap('icon.ico')
        self.window_overwrite.geometry("%dx%d%+d%+d" % (int(750/scaling_factor), 250/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_overwrite.grab_set()
        
        X,Y = 375,100
        
        select = "This calbration already exists \ndo you want to overwrite it?"
        label = tk.Label(self.window_overwrite, text=select,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
        X,Y=375-100,200
        button_yes = ttk.Button(self.window_overwrite, text="YES", command=self.import_calibration_routine)
        button_yes.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
        X=375+100
        button_no = ttk.Button(self.window_overwrite, text="NO", command=self.window_overwrite.destroy)
        button_no.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
        
     
    def login(self,event = "e"):
        user = self.entry_user.get()
        known_users = os.listdir(f"{MAIN_FOLDER}/Materials")
        if user in known_users:
            self.user = user
            self.title(f"Flinder - {self.user}")
            self.load_calibration()
            
    
    def on_closing_login(self):
        self.destroy()

    def close_all(self, event = "e"):
        self.window_login.destroy()
        self.destroy()
    
    def load_calibration(self):
        Hunt_choices = set(os.listdir(f"{MAIN_FOLDER}/Materials/{self.user}"))
        Hunt_choices = sorted(Hunt_choices)
        
        if len(Hunt_choices) > 0:
            X,Y,Ystep=850/scaling_factor,810/scaling_factor,85/scaling_factor
        
            self.Optionmenu_hunt = tk.OptionMenu(self, self.Var_hunt_material, *Hunt_choices, command = self.actualize_range)
            self.Optionmenu_hunt.config(font=('helvetica', size_s),width=14,bg = color_set[0])
            self.Optionmenu_hunt.place(x=X,y=Y,anchor='w')
            self.Var_hunt_material.set(Hunt_choices[0])
            self.actualize_range(Hunt_choices[0])
        
        self.window_login.destroy()
        self.attributes('-topmost', True)
        self.attributes('-topmost', False)

    
    def actualize_range(self,material):
        #material = self.Var_hunt_material.get()
        calib = f"{MAIN_FOLDER}/Materials/{self.user}/{material}/calibration.dat"
        D=np.genfromtxt(calib)
        thickness = D[:,0]
        rmin,rmax = int(thickness[0]),int(thickness[-1])
        self.Entry_range_min.delete(0,tk.END)
        self.Entry_range_max.delete(0,tk.END)

        self.Entry_range_min.insert(0,rmin)
        self.Entry_range_max.insert(0,rmax)
    
    def import_calibration(self):        
        self.window_import = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_import.wm_iconbitmap('icon.ico')
        self.window_import.geometry("%dx%d%+d%+d" % (int(750/scaling_factor), 250/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_import.grab_set()
        
        X,Y = 50,50
        
        select = "Chose a calibration to import:"
        label = tk.Label(self.window_import, text=select,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        Y+=100
        
        self.Var_import_calibration = tk.StringVar()
        Hunt_choices = set(os.listdir(f"{MAIN_FOLDER}/Materials/Default"))
        self.Optionmenu_import = tk.OptionMenu(self.window_import, self.Var_import_calibration, *Hunt_choices)
        self.Optionmenu_import.config(font=('helvetica', size_s),width=14,bg = color_set[0])
        self.Optionmenu_import.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        X+=500
        button_ok = ttk.Button(self.window_import, text="OK", command=self.check_import_calibration)
        button_ok.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
    
    def check_training(self):
        material = self.Var_hunt_material.get()
        
        path_good = f"{MAIN_FOLDER}/Materials/{self.user}/{material}/NN_database/Good"
        path_bad = f"{MAIN_FOLDER}/Materials/{self.user}/{material}/NN_database/Bad"
        
        if os.path.exists(path_good) and os.path.exists(path_bad):
            N_good = len(os.listdir(path_good))
            N_bad = len(os.listdir(path_bad))
                        
            if N_good > 46 and N_bad > 46:
                self.openTrainWindow()
            
            else:
                self.not_enough_flakes()
        
    def not_enough_flakes(self):
        DX = 500
        
        self.window_not_enough_flakes = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_not_enough_flakes.wm_iconbitmap('icon.ico')
        self.window_not_enough_flakes.geometry("%dx%d%+d%+d" % (int(DX/scaling_factor), 200/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.window_not_enough_flakes.grab_set()
        
        X,Y = DX/2,100
        
        select = "Not enough flakes in data base.\nYou'll need to hunt more"
        label = tk.Label(self.window_not_enough_flakes, text=select,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
        Y+=75
        button_ok = ttk.Button(self.window_not_enough_flakes, text="OK", command=self.window_not_enough_flakes.destroy)
        button_ok.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
    
    def openTrainWindow(self):
        DX = 400
        self.training_popup = tk.Toplevel(bg=color_set[0],bd=2)
        self.training_popup.wm_iconbitmap('icon.ico')
        self.training_popup.geometry("%dx%d%+d%+d" % (int(DX/scaling_factor), 200/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.training_popup.grab_set()
        
        X,Y = DX/2,50
        
        select = "Training iterations"
        label = tk.Label(self.training_popup, text=select,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='center')
        
        Y+=75
        X = DX/2-100
        self.entry_epoch = tk.Entry(self.training_popup,width=4,font=('helvetica', size_s), justify="right")
        self.entry_epoch.insert(0,50)
        self.entry_epoch.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='center')
        
        X = DX/2+100
        button_go = ttk.Button(self.training_popup, text="Go", command=self.train_model)
        button_go.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='center')
        
    def train_model(self):
        DX, DY = 400, 200
        self.epoch = int(self.entry_epoch.get())
        self.training_popup.destroy()
        
        self.training_popup = tk.Toplevel(bg=color_set[0],bd=2)
        self.training_popup.wm_iconbitmap('icon.ico')
        self.training_popup.geometry("%dx%d%+d%+d" % (int(DX/scaling_factor), DY/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
        self.training_popup.grab_set()
        
        X,Y = DX/2,DY/2
        
        inprogress = "Training in progress 0%"
        self.label_progress = tk.Label(self.training_popup, text=inprogress,bg=color_set[0],font=('helvetica', size_xs))
        self.label_progress.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='center')
        
        self.queue_train = queue.Queue()
        
        database_path = f"{MAIN_FOLDER}/Materials/{self.user}/{self.Var_hunt_material.get()}/NN_database"
        model_path = f"{MAIN_FOLDER}/Materials/{self.user}/{self.Var_hunt_material.get()}"
        filters,kernels = 0, 0 #dummy
        
        self.trainer = ThreadedTrainer.Train(self.queue_train,
                              database_path,
                              model_path,
                              filters, kernels,
                              int(128),
                              int(100),
                              self.epoch)
        self.trainer.start()
        self.after(20, self.process_queue_training)
        
        epoch_dir=f"{MAIN_FOLDER}/temp_model"
        if os.path.exists(epoch_dir):
            shutil.rmtree(epoch_dir)
        
        try:    
            os.mkdir(epoch_dir)
        except Exception as e:
            print(e)
        
        self.check_epoch()
        
    def check_epoch(self):
        try:
            if os.path.exists(f"{MAIN_FOLDER}/temp_model"):
                n_checkpoint=(len(os.listdir(f"{MAIN_FOLDER}/temp_model"))-1)/2
                percent=int(np.round(n_checkpoint/float(self.epoch)*100,0))
                if percent<0: percent=0
                self.label_progress.configure(text=f"Training in progress {percent}%")
            self.after(100, self.check_epoch)
            
        except Exception as e:
            pass
            # if hasattr(self, "label_progress"):
            #     self.label_progress.configure(text="Training completed\n Accuracy: "+str(np.round(self.accuracy[1][-1]*100,1))+" %")

    def process_queue_training(self):
        try:
            msg = self.queue_train.get(0)
            
            self.names=msg[0]
            self.accuracy=msg[1]
            self.model=msg[2][0]
            
            self.show_plot_training()
            

        except queue.Empty:
            self.after(10, self.process_queue_training)
            
    def saveModel(self):
        try:
            self.model.save_weights(f"{MAIN_FOLDER}/Materials/{self.user}/{self.Var_hunt_material.get()}/trained_model.h5")
            model_json = self.model.to_json()
            with open(f"{MAIN_FOLDER}/Materials/{self.user}/{self.Var_hunt_material.get()}/trained_model.json", "w") as json_file:
                json_file.write(model_json)
            
            self.button_save.configure(text="saved")
            
            f = open(f"{MAIN_FOLDER}/Materials/{self.user}/{self.Var_hunt_material.get()}/model_details.dat", "w")
            model_detail ="pic size\t100\n"
            model_detail+=f"Epoch\t{self.epoch}\n"
            model_detail+="Accuracy\t"+str(np.round(self.accuracy[1][-1]*100,1))+"\n"
            
            f.write(model_detail)
            f.close()
            
        except:
            self.label_save.configure(text="No model to save")
            
    def show_plot_training(self):
        self.training_popup.destroy()
        
        self.window_plot = tk.Toplevel(bg=color_set[0],bd=2)
        self.window_plot.wm_iconbitmap('icon.ico') 
        self.window_plot.geometry("%dx%d%+d%+d" % (int(1400/scaling_factor), int(1400/scaling_factor), (2560/2)/scaling_factor, (100)/scaling_factor)) 
        self.window_plot.grab_set()
        
        
        X,Y = 50,50
        text = "Training completed"
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_l))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        X,Y = X+50,Y+150
        text = "Genral accuracy: "
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        offsetx = 500
        X = X+offsetx
        text = f"{np.round(self.accuracy[2][-1]*100,1)} %"
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='e')
        text 
        
        Xs = X+50
        text = f"(Sample size: {int(self.accuracy[6])})"
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=Xs/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        X,Y = X-offsetx,Y+75
        text = "Misidentified good flakes: "
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        X = X+offsetx
        text = f"{np.round(self.accuracy[5]*100,1)} %"
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='e')
        
        Xs = X+50
        text = f"(Sample size: {int(self.accuracy[6]/2)})"
        label = tk.Label(self.window_plot, text=text,bg=color_set[0],font=('helvetica', size_xs))
        label.place(x=Xs/scaling_factor,y=Y/scaling_factor,anchor='w')
        
        
        
        plt.rc('axes', labelsize=20/scaling_factor)
        plt.switch_backend('agg')
        
        ylabel=["accuracy","loss"]

        self.plot_routine_training(1,ylabel[0],700-350)
        self.plot_routine_training(3,ylabel[1],700+350)
        
        Y=1300
        X = 700-200
        self.button_save = ttk.Button(self.window_plot, text="save", command=self.saveModel)
        self.button_save.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
        X = 700+200
        button_discard = ttk.Button(self.window_plot, text="close", command=self.window_plot.destroy)
        button_discard.place(x=X/scaling_factor,y=Y/scaling_factor,anchor='s')
        
            
    def plot_routine_training(self,i,ylabel,X):
        sq = 7
        figure = plt.Figure(figsize=(sq/scaling_factor,sq/scaling_factor), dpi=100, tight_layout=True)
        plt.switch_backend('agg')
        ax = figure.add_subplot(111)
        line = FigureCanvasTkAgg(figure,self.window_plot)
        Y=800
        line.get_tk_widget().place(x=X/scaling_factor,y=Y/scaling_factor,anchor='center')
        
        ax.plot(self.accuracy[0],self.accuracy[i],color="b",marker='o',lw=2,ms=0)
        ax.plot(self.accuracy[0],self.accuracy[i+1],color="r",marker='o',lw=2,ms=0)
        
        if i==1:
            figure.text(0.6,0.35,"training",color = "b")
            figure.text(0.6,0.3,"validation",color = "r")
        
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
    
    def LastStep(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.Label_image.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_image.configure(text="Specify working folder")
        
        if Proceed==1:
            self.window_RUSURE = tk.Toplevel(bg=color_set[0],bd=2)
            self.window_RUSURE.wm_iconbitmap('icon.ico')
            self.window_RUSURE.geometry("%dx%d%+d%+d" % (int(1100/scaling_factor), 250/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
            self.window_RUSURE.grab_set()
                
            text_attention="Hunting will not be possible anymore!\nOnly do this when you are fully done."
                
            label = tk.Label(self.window_RUSURE, text=text_attention,bg=color_set[0],font=('helvetica', size_s))
            label.pack(fill='x', padx=50, pady=5)

            button_yes = ttk.Button(self.window_RUSURE, text="Continue", command=self.clean_folder)
            button_no = ttk.Button(self.window_RUSURE, text="Cancel", command=self.window_RUSURE.destroy)
                                
            button_no.place(x=400/scaling_factor,y=210/scaling_factor,anchor='s')
            button_yes.place(x=700/scaling_factor,y=210/scaling_factor,anchor='s')
        
    def clean_folder(self):
        try:
            self.window_RUSURE.destroy()
        except:
            print("no window to destroy")
        
        if os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        
            for i in range(self.Nwafer):
                self.clean_wafer_folder(i)
    
    def clean_wafer_folder(self,i):
        path=self.filename+"/Wafer_"+str(i).zfill(2)+"/"
        folders=["Raw_pictures","Color_Corrected_Pictures","Color_Corrected_Pictures_HC","Position_files"]
        for folder in folders:
            try:
                shutil.rmtree(path+folder)
            except:
                print("folder already removed")
        
    
    def button_nosepiece(self,text,value,posX,posY):
         tk.Radiobutton(self, 
              indicatoron = 0,
              text=text,
              selectcolor = color_set[2],
              bg = color_set[0],
              width=4,
              font=('helvetica', size_s),
              variable=self.nosepiece_selected, 
              value=value).place(x=posX,y=posY,anchor='w')
    
    def entry_hunt_size(self,text,posX,posY):
        Offset=480/scaling_factor
        variable = tk.IntVar()
        tk.Checkbutton(self, 
              indicatoron = 0,
              text=text,
              selectcolor = color_set[2],
              bg = color_set[0],
              width=9,
              font=('helvetica', size_s),
              variable=variable).place(x=posX,y=posY,anchor='w')
        
        entry_size = tk.Entry(self,width=5,font=('helvetica', size_s)) 
        entry_size.place(x=posX+Offset, y=posY, anchor='center')

        return variable, entry_size
    
    def workingfolderDialog(self):
        
        self.filename = filedialog.askdirectory(initialdir =  "", title = "Select A Folder")
        text=functions.long_path_cutter(self.filename)
        self.Label_path.configure(text = text, justify="left")
    
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
    
    def combine_picture(self):
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
            
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.Label_macro_DF.configure(text = "No log file\nUse left pannel\nto create one")
        
        if Proceed==1:
            self.material=f"{self.user}/{self.Var_hunt_material.get()}"
            self.queue_combine = queue.Queue()
            
            Auto_functions.ThreadedCombine(self.queue_combine, self.filename,self.Nwafer,self.material).start()
            self.after(100, self.process_queue_combine)
                        
    
    def checkEverything(self):
        #check the inside of the folder (is there a macro in there?) 
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.Label_macro.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])

        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_macro.configure(text="Specify working folder")
        
        posX,posY=10/scaling_factor,420/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        if Proceed==1 and hasattr(self, 'Nwafer')==False:
            Proceed=0
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_macro.configure(text="Specify wafer position and size")
        elif Proceed==1 and hasattr(self, 'Nwafer'):
            Proceed=1
            self.errorFrame(posX,posY,width,height,color_set[0])  
        
        posX,posY=10/scaling_factor,420/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        if Proceed==1 and hasattr(self, 'sample_dim')==False:
            Proceed=0
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_macro.configure(text="Specify wafer position and size")
        elif Proceed==1 and hasattr(self, 'sample_dim'):
            Proceed=1
            self.errorFrame(posX,posY,width,height,color_set[0])
        
        posX,posY=10/scaling_factor,650/scaling_factor
        height,width=90/scaling_factor,780/scaling_factor
        if Proceed==1 and self.var_auto_hunt.get()==1 and self.var_auto_stitch.get()==0:
            Proceed=0
            self.Label_macro.configure(text = "Auto Stitch if you Auto Hunt")
            self.errorFrame(posX,posY,width,height,color_error)
        elif Proceed==1 and self.var_auto_hunt.get()==1 and self.var_auto_stitch.get()==1:
            self.errorFrame(posX,posY,width,height,color_set[0])
        elif Proceed==1 and self.var_auto_hunt.get()==0 and self.var_auto_stitch.get()==0:
            self.errorFrame(posX,posY,width,height,color_set[0])
        elif Proceed==1 and self.var_auto_hunt.get()==1 and self.var_auto_stitch.get()==0:
            self.errorFrame(posX,posY,width,height,color_set[0])
        
        posX,posY=810/scaling_factor,760/scaling_factor
        height,width=100/scaling_factor,780/scaling_factor
        if Proceed==1:
            self.material=f"{self.user}/{self.Var_hunt_material.get()}"
            self.errorFrame(posX,posY,width,height,color_set[0])
            if self.var_auto_hunt.get()==1 and self.material == f"{self.user}/":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.label_hunt.configure(text="Specify flake type if you Auto Hunt")
        
        if Proceed==1 and self.var_auto_hunt.get()==1:
            try :
                  print(float(self.Entry_size.get()))
                  self.errorFrame(posX,posY,width,height,color_set[0])
                  Proceed=1
            except:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)        
                self.Label_macro.configure(text = "Specify flake size if you Auto Hunt")
        
        if Proceed==1 and self.var_auto_hunt.get()==1:
            try :
                print(float(self.Entry_size.get()))
                self.errorFrame(posX,posY,width,height,color_set[0])
            except:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)        
                self.Label_macro.configure(text = "Specify flake size if you Auto Hunt")
        
        posX,posY=50/scaling_factor,880/scaling_factor
        height,width=115/scaling_factor,710/scaling_factor
        if Proceed==1 and self.nosepiece_selected.get()==0:
            Proceed=0
            self.Label_macro.configure(text = "Specify Nosepiece")
            self.errorFrame(posX,posY,width,height,color_error)
        elif Proceed==1 and self.nosepiece_selected.get()>0:
            self.errorFrame(posX,posY,width,height,color_set[0])       
        
        if  Proceed==1:
            does_logfile_exists=0
            for i in range(self.Nwafer):
                does_logfile_exists+=os.path.exists(self.filename+"Wafer_"+str(i).zfill(2)+"/log_file.dat")
            if does_logfile_exists>0:
                self.window_eraselog = tk.Toplevel(bg=color_set[0],bd=2)
                self.window_eraselog.wm_iconbitmap('icon.ico') 
                int(Window_size[0]/scaling_factor)
                self.window_eraselog.geometry("%dx%d%+d%+d" % (int(1500/scaling_factor), 300/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor)) 
                self.window_eraselog.grab_set()
                
                text_attention="Current log files will be lost.\nThis might prevent later stitching of already acquired images.\nAre you sure you want to proceed?"
                
                label = tk.Label(self.window_eraselog, text=text_attention,bg=color_set[0],font=('helvetica', size_s))
                label.pack(fill='x', padx=50, pady=5)

                button_yes = ttk.Button(self.window_eraselog, text="OK", command=self.createMacro)
                button_no = ttk.Button(self.window_eraselog, text="Cancel", command=self.window_eraselog.destroy) 
                button_no.place(x=600/scaling_factor,y=260/scaling_factor,anchor='s')
                button_yes.place(x=900/scaling_factor,y=260/scaling_factor,anchor='s')      
            else:
                self.createMacro()
        

    def createMacro(self):
        if hasattr(self, 'window_eraselog'):
            self.window_eraselog.destroy()

        indicator=self.nosepiece_selected.get()-1
        
        self.wrange,self.hrange=[],[]
        total_shot=0
        for i in range(self.Nwafer):
            w=int(round(float(self.sample_dim[i][3])/self.Fieldvalues[0]*self.factors[indicator],0))
            h=int(round(float(self.sample_dim[i][2])/self.Fieldvalues[1]*self.factors[indicator],0))
            self.wrange.append(w)
            self.hrange.append(h)
            total_shot+=w*h
        
        wafer="wafers"
        if self.Nwafer==1:
            wafer="wafer"
        self.Label_macro.configure(text = "Macro created: " + str(self.Nwafer) +" "+wafer+" ..."+str(int(total_shot*0.1125+2.5))+" min",font=('helvetica', int(size_xs*0.8)))
           
        fieldofview_w=self.Fieldvalues[0]/self.factors[indicator]
        fieldofview_h=self.Fieldvalues[1]/self.factors[indicator]
        
        try:
            os.mkdir(self.filename+"/Macro_files")
        except Exception as e:
                print(e)   
                
        for i in range(self.Nwafer):
            try:
                os.mkdir(self.filename+"/Wafer_"+str(i).zfill(2))
            except Exception as e:
                print(e)   
                
        for i in range(self.Nwafer):
            try:
                os.mkdir(self.filename+"/Wafer_"+str(i).zfill(2)+"/Raw_pictures")
            except Exception as e:
                print(e)
            try:
                os.mkdir(self.filename+"/Wafer_"+str(i).zfill(2)+"/Position_files")
            except Exception as e:
                print(e)
        
        
        functions.scanning_macro(self.filename,self.Nwafer,self.hrange,self.wrange,self.sample_dim,self.nosepieces[indicator],fieldofview_h,fieldofview_w,self.step_focus[indicator])
        functions.log_file(self.filename,self.Nwafer,self.sample_dim,self.hrange,self.wrange,self.nosepieces[indicator])
        
        if self.var_auto_stitch.get()==1:
            path_to_check=[]
            for i in range(self.Nwafer):
                lastpic_number=int(self.wrange[i]*self.hrange[i]-1)
                path_to_check.append(self.filename+"/Wafer_"+str(i).zfill(2)+"/Raw_pictures/pic"+str(lastpic_number).zfill(ZEROS)+".jpg")
            self.queue_auto_stitch = queue.Queue()

            Auto_functions.ThreadedAutoStitch(self.queue_auto_stitch,path_to_check).start()
            self.after(100, self.process_queue_auto_stitch)
    
    def create50xmacro(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.Label_macro_BF.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_macro_BF.configure(text="Specify working folder")
            
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
            self.Nosepiece=log_lines[1].split("\t")[1]
            log.close()
        
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.Label_macro_BF.configure(text = "No log file\nUse left pannel to create one")
            
        if Proceed==1:
            Proceed,text,exp50=functions.macro_50x_Proceed(self.filename,self.entry_exposure_BF_50)
        
        if Proceed == 1:
                functions.macro50x(self.filename,exp50,self.Nwafer,self.Nosepiece)
        else:
            self.Label_macro_BF.configure(text=text)
            
    def createDFmacro(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.Label_macro_DF.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_macro_DF.configure(text="Specify working folder")
        
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.Label_macro_DF.configure(text = "No log file\nUse left pannel to create one")
        
        if Proceed==1:
            Proceed,text,exp100BF,exp50DF,exp100DF,gain100BF,gain50DF,gain100DF=functions.macro_DFBF_Proceed(self.filename,self.BF100x,self.DF50x,self.DF100x,self.entry_exposure_BF_100,self.entry_exposure_DF_50,self.entry_exposure_DF_100,self.entry_gain_BF_100,self.entry_gain_DF_50,self.entry_gain_DF_100)
      
        if Proceed == 1:
            print("Making DF Macros")
            if self.BF100x.get() == 1:
                print("100x BF")
                functions.macro50_100x(self.filename,"BF",exp100BF,gain100BF,"100x",self.Nwafer)
            if self.DF50x.get() == 1:
                print("50x DF")
                functions.macro50_100x(self.filename,"DF",exp50DF,gain50DF,"50x",self.Nwafer)
            if self.DF100x.get() == 1:
                print("100x DF")
                functions.macro50_100x(self.filename,"DF",exp100DF,gain100DF,"100x",self.Nwafer)
        else:
            self.Label_macro_DF.configure(text=text)
    
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
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.label_select.configure(text="Specify working folder")
        
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.label_select.configure(text = "No log file")
        
        if Proceed == 1:
            try:
                self.list_name=[]
                self.folders=[]
                for i in range(self.Nwafer):
                    directories=os.listdir(self.filename+"/Wafer_"+str(i).zfill(2)+'/Analysed_picture')
                    directories.remove("full_image.jpg")
                    for j in range(len(directories)):
                        directories[j]=self.filename+"/Wafer_"+str(i).zfill(2)+"/Analysed_picture/"+directories[j]
                    self.folders.extend(directories)
                    self.list_name.extend(os.listdir(self.filename+"/Wafer_"+str(i).zfill(2)+'/Analysed_picture'))
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
            self.width_window_selection=1600*2
            self.height_window_selection=1800
            self.window_selection.geometry("%dx%d%+d%+d" % (int(self.width_window_selection/scaling_factor), self.height_window_selection/scaling_factor, (2560-3200)/2/scaling_factor, (1440-self.height_window_selection)/2/scaling_factor))
        
            self.label_select.configure(text="Selection done")
            
            
            self.list_name=[]
            self.folders=[]
            ppp=[]
            
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nosepiece=log_lines[1].split("\t")[1]
            spread="1"
            if self.Nosepiece=='10x':
                spread='0p5'
            if self.Nosepiece=='20x':
                spread='0p25'
            
            for i in range(self.Nwafer):
                directories=os.listdir(self.filename+"/Wafer_"+str(i).zfill(2)+'/Analysed_picture')
                directories.remove("full_image.jpg")
                self.list_name.extend(directories)
                for j in range(len(directories)):
                    directories[j]=self.filename+"/Wafer_"+str(i).zfill(2)+"/Analysed_picture/"+directories[j]
                    ppp.append("/"+spread+"mm_zoom_Wafer"+str(i).zfill(2)+"_")
                self.folders.extend(directories)
            
            self.list_name_hc=[0 for i in self.list_name]
            for i in range(len(self.list_name)):
                self.list_name_hc[i]=self.folders[i]+ppp[i]+self.list_name[i]+"_hc.jpg"
                self.list_name[i]=self.folders[i]+ppp[i]+self.list_name[i]+".jpg"
                
            self.indice_max=len(self.list_name)
            self.indice_flake=0
            
            self.dict_keep_remove = {}
            for names in self.list_name :
                self.dict_keep_remove[names] = 0
            
            self.progress=tk.Label(self.window_selection,  text=str(self.indice_flake+1)+" / "+str(self.indice_max), fg='black', font=('helvetica', size_s), bg = color_set[0])
            self.progress.tk.place(x=50/scaling_factor, y=50/scaling_factor, anchor = 'w')
            
            self.label_name=tk.Label(self.window_selection,  text=str(self.list_name[self.indice_flake].split("/")[-1]), fg='black', font=('helvetica', size_s), bg = color_set[0])
            self.label_name.place(x=self.width_window_selection/2/scaling_factor, y=50/scaling_factor, anchor = 'center')
            
            self.showFlake()
            
            button_next     = ttk.Button(self.window_selection, text="Next", command=self.next_flake)
            button_previous = ttk.Button(self.window_selection, text="Previous", command=self.previous_flake)
            button_discard = ttk.Button(self.window_selection, text="Discard", command=self.delete_flake)
            button_keep = ttk.Button(self.window_selection, text="Keep", command=self.keep_flake)
            button_end = ttk.Button(self.window_selection, text="END", command=self.end_flake)
        
            button_next.place(x=self.width_window_selection*0.60/scaling_factor,y=self.height_window_selection*0.94/scaling_factor,anchor='s')
            button_previous.place(x=self.width_window_selection*0.40/scaling_factor,y=self.height_window_selection*0.94/scaling_factor,anchor='s')      
            button_discard.place(x=self.width_window_selection*0.47/scaling_factor,y=self.height_window_selection*0.94/scaling_factor,anchor='s')
            button_keep.place(x=self.width_window_selection*0.53/scaling_factor,y=self.height_window_selection*0.94/scaling_factor,anchor='s')
            button_end.place(x=self.width_window_selection*0.5/scaling_factor,y=self.height_window_selection*0.985/scaling_factor,anchor='s')
    
    
    def display_valdel_logo(self):
        pos=0.26
        
        name = self.list_name[self.indice_flake]
        if self.dict_keep_remove[name] == 0:
            return 0
        
        if self.dict_keep_remove[name] == 1:
            load = Image.open("validate.png")
        else:
            load = Image.open("delete.png")
        load = load.resize((int(100/scaling_factor), int(100/scaling_factor)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        
        val = tk.Label(self.window_selection, image=render, bg=color_set[0])
        val.image = render
        offset = 700/scaling_factor
        val.place(x=self.width_window_selection*(1-pos)/scaling_factor+offset,y=self.height_window_selection*0.95/2/scaling_factor-offset,anchor='center')
    
    def keep_flake(self):
        name = self.list_name[self.indice_flake]
        self.dict_keep_remove[name] = 1
        self.next_flake()
    
    def delete_flake(self):
        name = self.list_name[self.indice_flake]
        self.dict_keep_remove[name] = 2
        self.next_flake()

    
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
        pos=0.26
        
        load_wafer = Image.open(self.list_name[self.indice_flake])
        load_wafer = load_wafer.resize((int(1500/scaling_factor), int(1500/scaling_factor)), Image.ANTIALIAS)
        render_wafer = ImageTk.PhotoImage(load_wafer)
        
        self.flake = tk.Label(self.window_selection, image=render_wafer, bg = color_set[1])
        self.flake.image = render_wafer
        self.flake.place(x=self.width_window_selection*(1-pos)/scaling_factor,y=self.height_window_selection*0.95/2/scaling_factor,anchor='center')
        
        load_wafer = Image.open(self.list_name_hc[self.indice_flake])
        load_wafer = load_wafer.resize((int(1500/scaling_factor), int(1500/scaling_factor)), Image.ANTIALIAS)
        render_wafer = ImageTk.PhotoImage(load_wafer)
        
        self.flake_hc = tk.Label(self.window_selection, image=render_wafer, bg = color_set[1])
        self.flake_hc.image = render_wafer
        self.flake_hc.place(x=self.width_window_selection*pos/scaling_factor,y=self.height_window_selection*0.95/2/scaling_factor,anchor='center')
        
        self.progress.configure(text=str(self.indice_flake+1)+" / "+str(self.indice_max))
        self.label_name.configure(text=str(self.list_name[self.indice_flake].split("/")[-1]))
        
        self.display_valdel_logo()
     
    def erase_flake(self,i):
        to_be_deleted_folder=self.folders[i]
        to_be_deleted_name=self.list_name[i]
        to_be_deleted_name_hc=self.list_name_hc[i]
        shutil.rmtree(to_be_deleted_folder)
        self.indice_max-=1
        self.folders.remove(to_be_deleted_folder)
        self.list_name.remove(to_be_deleted_name)
        self.list_name_hc.remove(to_be_deleted_name_hc)
        
    def end_flake(self):
        k=0
        temp_list_name=self.list_name.copy()
        
        for name in temp_list_name:
            if self.dict_keep_remove[name] == 0:
                self.erase_flake(k)
                self.dict_keep_remove.pop(name)
            
            if name in self.dict_keep_remove:
                self.add_flake_NNdatabase(name,k)
                
                if self.dict_keep_remove[name] == 2:
                    self.erase_flake(k)
                    self.dict_keep_remove.pop(name)
                    
                else:
                    k+=1
        
        self.window_selection.destroy()
        
    def add_flake_NNdatabase(self,name,k):
        self.expand_database(name,k,self.user)
        self.expand_database(name,k,"Default")
    
    def expand_database(self,name,k,who):
        s = self.folders[k].split("/")[-1]
        N = len(s.split("_")[-1])
        calibration = s[0:-1-N]
        
        if self.dict_keep_remove[name] == 1:
            path = f"{MAIN_FOLDER}/Materials/{who}/{calibration}/NN_database/Good"
        if self.dict_keep_remove[name] == 2:
            path = f"{MAIN_FOLDER}/Materials/{who}/{calibration}/NN_database/Bad"
        
        try:
            os.mkdir(f"{MAIN_FOLDER}/Materials/{who}/{calibration}")
        except:
                pass   
        try:
            os.mkdir(f"{MAIN_FOLDER}/Materials/{who}/{calibration}/NN_database")
        except:
                pass    
        try:
            os.mkdir(path)
        except:
                pass 
        
        src = self.folders[k]+"/AI.jpg"
        N = len(os.listdir(path))
        shutil.copyfile(src, path+"/"+str(N)+".jpg")
     
    def position_size_popup(self):
        Proceed=0
        try:
            self.Nwafer=int(self.entry_numberofwafers.get())
            self.entry_numberofwafers.configure(bg="white")
            Proceed=1
        except:
            self.entry_numberofwafers.configure(bg=color_error)


        if Proceed == 1:
            height=200/scaling_factor+(self.Nwafer+1)*80/scaling_factor
            width=int(1500/scaling_factor)
        
            self.window_position_size = tk.Toplevel(bg=color_set[0],bd=2)
            self.window_position_size.wm_iconbitmap('icon.ico')
            self.window_position_size.geometry("%dx%d%+d%+d" % (width, height, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
        
            posX,posY=80/scaling_factor,60/scaling_factor
    
            text=["Wafer","X","Y","W","H"]
            posX=115/scaling_factor
            step=210/scaling_factor
            for i in range(5):
                Label_header = tk.Label(self.window_position_size, text= text[i], fg='black', font=('helvetica', size_s), bg = color_set[0])
                Label_header.place(x=posX+i*step, y=posY, anchor='c')
            
            X=10/scaling_factor
            step=210/scaling_factor
            for i in range(6):
                Vertical_ligne=tk.Frame(self.window_position_size,height=(self.Nwafer+1)*80/scaling_factor,width=2,bg=color_set[1])
                Vertical_ligne.place(x=X+i*step,y=10)
            X=10/scaling_factor
            step=80/scaling_factor
            for i in range(self.Nwafer+2):
                Horizontal_ligne=tk.Frame(self.window_position_size,height=2,width=1050/scaling_factor,bg=color_set[1])
                Horizontal_ligne.place(x=X,y=10+i*step)
        
            posX=115/scaling_factor
            posY=(60+80)/scaling_factor
            step=80/scaling_factor
            for i in range(self.Nwafer):
                Label_header = tk.Label(self.window_position_size, text= str(i), fg='black', font=('helvetica', size_s), bg = color_set[0])
                Label_header.place(x=posX, y=posY+i*step, anchor='c')


            #A picture to illustrate the scanning size
            image_size=int(270/scaling_factor)
            X,Y=1300/scaling_factor,150/scaling_factor
        
            Image_scan_size = Image.open("scan_size.png")
            Image_scan_size = Image_scan_size.resize((image_size, image_size), Image.ANTIALIAS)
            Render_image_scan_size = ImageTk.PhotoImage(Image_scan_size)
        
            Label_image_scan_size= tk.Label(self.window_position_size, image=Render_image_scan_size, bg = color_set[0])
            Label_image_scan_size.image = Render_image_scan_size
            Label_image_scan_size.place(x=X, y=Y, anchor='c')
        
        
            #entries
            stepY=80/scaling_factor
            stepX=210/scaling_factor
            posX=(115+210)/scaling_factor
            posY=(60+80)/scaling_factor
            self.entry_sample=[]
            for i in range(self.Nwafer):
                entry_X=tk.Entry(self.window_position_size,width=6,font=('helvetica', size_s))
                entry_Y=tk.Entry(self.window_position_size,width=6,font=('helvetica', size_s))
                entry_W=tk.Entry(self.window_position_size,width=6,font=('helvetica', size_s))
                entry_H=tk.Entry(self.window_position_size,width=6,font=('helvetica', size_s))
            
                entry_X.place(x=posX, y=posY+i*stepY, anchor='c')
                entry_Y.place(x=posX+stepX, y=posY+i*stepY, anchor='c')
                entry_W.place(x=posX+2*stepX, y=posY+i*stepY, anchor='c')
                entry_H.place(x=posX+3*stepX, y=posY+i*stepY, anchor='c')
        
                self.entry_sample.append([entry_X,entry_Y,entry_H,entry_W])
        
            split=150
            X,Y=(1060/2+split)/scaling_factor,100/scaling_factor+(self.Nwafer+1)*80/scaling_factor
            Button_validate = ttk.Button(self.window_position_size, text = " Validate ",command = self.validate_position)
            Button_validate.place(x=X,y=Y,anchor='center')
            X,Y=(1060/2-split)/scaling_factor,100/scaling_factor+(self.Nwafer+1)*80/scaling_factor
            Button_cancel = ttk.Button(self.window_position_size, text = " Cancel ",command = self.window_position_size.destroy)
            Button_cancel.place(x=X,y=Y,anchor='center')
        
    def validate_position(self):
        N_entries=4
        error=0
        self.sample_dim=np.zeros((len(self.entry_sample),len(self.entry_sample[0])))
        for i in range(len(self.entry_sample)):
            for j in range(N_entries):
                try:
                    self.sample_dim[i][j]=float(self.entry_sample[i][j].get())
                    self.entry_sample[i][j].configure(bg="white")
                except:
                    error=1
                    self.entry_sample[i][j].configure(bg=color_error)
        
        if error==0:
            self.window_position_size.destroy()
                
    def stitchImage_popup(self):
        Proceed=1
        posX,posY=10/scaling_factor,120/scaling_factor
        height,width=190/scaling_factor,780/scaling_factor
        try:
            if self.filename == "":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.Label_image.configure(text="Specify working folder")
            
            else:
                Proceed=1
                self.errorFrame(posX,posY,width,height,color_set[0])
        except :
            Proceed=0            
            self.errorFrame(posX,posY,width,height,color_error)         
            self.Label_image.configure(text="Specify working folder")
        
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.Label_image.configure(text = "No log file\nUse left pannel to create one")

        if Proceed==1:
            are_logfiles_there=0
            is_there_analysed_pictures=0
            for i in range(self.Nwafer):
                is_there_analysed_pictures+=os.path.exists(self.filename+"/Wafer_"+str(i).zfill(2)+"/Analysed_picture/full_image.jpg")
                are_logfiles_there+=os.path.exists(self.filename+"/Wafer_"+str(i).zfill(2)+"/log_file.dat")
        
        if Proceed==1 and are_logfiles_there<self.Nwafer-1:
            Proceed=0
            self.Label_image.configure(text = "No log file\nUse left pannel to create one")
        
        if Proceed==1 and is_there_analysed_pictures>0 and self.stitching_running==0:
            self.window_loadimage = tk.Toplevel(bg=color_set[0],bd=2)
            self.window_loadimage.wm_iconbitmap('icon.ico')
            self.window_loadimage.geometry("%dx%d%+d%+d" % (int(1500/scaling_factor), 300/scaling_factor, (2560/2)/scaling_factor, (1440/2)/scaling_factor))
            
            self.window_loadimage.grab_set()
                
            text_attention="There are already stitched images.\nDo you want to erase them and stitch again?\nOr do you want to load them?"
                
            label = tk.Label(self.window_loadimage, text=text_attention,bg=color_set[0],font=('helvetica', size_s))
            label.pack(fill='x', padx=50, pady=5)

            button_yes = ttk.Button(self.window_loadimage, text="Load", command=self.loadImage)
            button_no = ttk.Button(self.window_loadimage, text="Erase", command=self.stitchImage)
                                
            button_no.place(x=600/scaling_factor,y=260/scaling_factor,anchor='s')
            button_yes.place(x=900/scaling_factor,y=260/scaling_factor,anchor='s')      
        
        elif Proceed==1 and self.stitching_running==1:
            X0=1350
            Y0=350+150
            self.label_molo = tk.Label(self,  text="please be patient", fg='black', font=('helvetica', size_xs), bg = color_set[1])
            self.label_molo.place(x=X0/scaling_factor, y=Y0/scaling_factor, anchor = 'center')
            
        elif Proceed==1 and self.stitching_running==0:
            self.stitchImage()
    
    def stitchImage_one(self,indice):
        log = open(self.filename+"/Wafer_"+str(indice).zfill(2)+"/log_file.dat", "r")
        log_lines=log.read().split("\n")
        h=int(log_lines[4].split("\t")[1])
        w=int(log_lines[5].split("\t")[1])
        self.Nosepiece=log_lines[1].split("\t")[1]
            
        if hasattr(self, 'img_wafer'):
            self.img_wafer.destroy()
        
        self.queue_stitch = queue.Queue()
        Stitcher.ThreadedStitcher(self.queue_stitch,w,h,self.filename+"/Wafer_"+str(indice).zfill(2),self.Nosepiece,scaling_factor,indice,self.load,self.overlap).start()
        self.after(20, self.process_queue_stitch)
                
    def stitchImage(self):
        self.load=0
        if hasattr(self, 'window_loadimage'):
            self.window_loadimage.destroy()
        
        if self.stitching_running==0:
            self.stitching_running=1
            self.queue_stitch = queue.Queue()
            self.queue_stitch_multi = queue.Queue()
            self.after(100, self.process_queue_stitch_multi)
            self.stitch_counter=0
            self.stitchImage_one(self.stitch_counter)
    
    def loadImage(self):
        self.load=1
        if hasattr(self, 'window_loadimage'):
            self.window_loadimage.destroy()
        
        if self.stitching_running==0:
            self.stitching_running=1
            self.queue_stitch = queue.Queue()
            self.queue_stitch_multi = queue.Queue()
            self.after(100, self.process_queue_stitch_multi)
            self.stitch_counter=0
            self.stitchImage_one(self.stitch_counter)
    
    def Hunt_one(self,indice,factor):
        AI=[]
        if int(self.var_AI.get())==1:
            thresold=0.5 #float(self.Entry_thresold.get())/100
            model_path=f"{MAIN_FOLDER}/Materials/{self.material}/trained_model"
            model_details_path=f"{MAIN_FOLDER}/Materials/{self.material}/model_details.dat"
            file = open(model_details_path, 'r')
            Lines = file.readlines()
            image_AI_size=int(Lines[0].split("\t")[1])
        
            AI=[model_path,thresold,image_AI_size]
        
        self.queue_hunt = queue.Queue()
        t_range = [int(self.Entry_range_min.get()), int(self.Entry_range_max.get())]
        self.hunter = Hunter_parallele.ThreadedHunter(self.queue_hunt,self.filename+"/Wafer_"+str(self.hunt_counter).zfill(2),self.material,self.targeted_area,factor,indice,AI,t_range,self.step_focus_actual)
        self.hunter.start()
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
        #Proceed=1
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
        
        
        if Proceed==1 and os.path.exists(self.filename+"/log_file.dat"):
            log = open(self.filename+"/log_file.dat", "r")
            log_lines=log.read().split("\n")
            self.Nwafer=int(log_lines[2].split("\t")[1])
        elif Proceed==1 and os.path.exists(self.filename+"/log_file.dat")==False:
            Proceed=0
            self.label_hunt.configure(text = "No log file\nUse left pannel to create one")
        
        ## Picture (No stiched picture)
        if Proceed==1:
            is_there_stitched_images=0
            for i in range(self.Nwafer):
                is_there_stitched_images+=os.path.exists(self.filename+"/Wafer_"+str(i).zfill(2)+"/Analysed_picture/full_image.jpg")
            if is_there_stitched_images==self.Nwafer:
                Proceed=1
            else:
                Proceed=0
                self.label_hunt.configure(text="No stitched pictures")
                
        ## Nosepiece (No log file)
        if Proceed==1:
            is_there_logfiles=0
            for i in range(self.Nwafer):
                is_there_logfiles+=os.path.exists(self.filename+"/Wafer_"+str(i).zfill(2)+"/log_file.dat")
            
            if is_there_logfiles==self.Nwafer:
                log = open(self.filename+"/Wafer_"+str(i).zfill(2)+"/log_file.dat", "r")
                log_lines=log.read().split("\n")
                self.Nosepiece=log_lines[1].split("\t")[1]
                self.factor=self.factors[self.nosepieces.index(self.Nosepiece)]
                self.step_focus_actual = self.step_focus[self.nosepieces.index(self.Nosepiece)]

                Proceed=1
            else:
                Proceed=0
                self.label_hunt.configure(text="No log files")
                                
        
        posX,posY=810/scaling_factor,760/scaling_factor
        height,width=100/scaling_factor,780/scaling_factor
        if Proceed==1:
            self.material=f"{self.user}/{self.Var_hunt_material.get()}"
            self.errorFrame(posX,posY,width,height,color_set[0])
            if self.material == self.user+"/":
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)
                self.label_hunt.configure(text="Specify flake type")
                
            
        ## Area (Specify area of what you want to hunt)
        if Proceed==1:
            self.targeted_area = self.Entry_size.get()
            
            posX,posY=1300/scaling_factor,760/scaling_factor
            height,width=100/scaling_factor,280/scaling_factor
            try :
                self.targeted_area=float(self.targeted_area)
                if self.targeted_area<10:
                    self.targeted_area=10
                self.errorFrame(posX,posY,width,height,color_set[0])
                Proceed=1
            except:
                Proceed=0
                self.errorFrame(posX,posY,width,height,color_error)        
                self.label_hunt.configure(text="Specify area")
        
        ## Check AI
        if Proceed==1:
            if int(self.var_AI.get())==1:
                model_details_path=os.path.exists(f"{MAIN_FOLDER}/Materials/{self.material}/model_details.dat")
                model_path=os.path.exists(f"{MAIN_FOLDER}/Materials/{self.material}/trained_model.h5")
                
                if model_details_path and model_path:
                    Proceed=1
                else:
                    Proceed=0
                    self.label_hunt.configure(text="No trained model")
        
        if Proceed==1:
            self.hunting_running=1
            self.queue_hunt_multi = queue.Queue()
            self.after(100, self.process_queue_hunt_multi)
            self.hunt_counter=0
            self.Hunt_one(self.hunt_counter,self.factor)

    def process_queue_stitch(self):
        try:
            msg = self.queue_stitch.get(0)
            if msg[0] == 4:
                self.Label_image.configure(text = msg[1])
                self.stitching_running=0
                if hasattr(self,"label_molo"):
                    self.label_molo.destroy()
                    
            if msg[0] == 3:                
                X0=1350
                Y0=380                
                self.Label_image.configure(text = msg[1])                
                self.stitching_running=0

                if hasattr(self,"label_molo"):
                    self.label_molo.destroy()
                
                self.queue_stitch_multi.put(1)
                
            elif msg[0] == 2 :
                self.Label_image.configure(text = msg[1])
                self.after(20, self.process_queue_stitch)
            elif msg[0] == 1:
                self.Label_image.configure(text = msg[1])
                self.after(20, self.process_queue_stitch)
        except queue.Empty:
            self.after(20, self.process_queue_stitch)
    
    def process_queue_stitch_multi(self):
        try:
            msg = self.queue_stitch_multi.get(0)
            self.stitch_counter+=1
#            self.waiting_for_next_stitch=1
            
            if self.stitch_counter<self.Nwafer:
                self.queue_stitch = queue.Queue()
                self.after(100, self.process_queue_stitch_multi)
                self.stitchImage_one(self.stitch_counter)
            
            else:
                self.stitching_running=0
                self.stitch_counter=0
                self.queue_load = queue.Queue()
#                self.after(100, self.process_queue_load)
                self.process_queue_load()
                Stitcher.ThreadedLoader(self.queue_load,self.filename,scaling_factor,self.Nwafer).start()

                
            
        except:
            self.after(100, self.process_queue_stitch_multi)
                
    def process_queue_load(self):
        try:
            msg = self.queue_load.get(0)
            # Show result of the task if needed
            if msg[0] == 1:
                
                X0,Y0=msg[2],msg[3]
                
                
                self.img_wafer = tk.Label(self, image=msg[1], bg = color_set[1])
                self.img_wafer.image = msg[1]
                self.img_wafer.place(x=X0,y=Y0,anchor='nw')
                self.after(100, self.process_queue_load)
            
            if msg[0] == 2:
                self.Label_image.configure(text = "")
                if self.var_auto_hunt.get()==1:
                    self.Hunt()
        
            elif msg[0] == 0 :
                self.Label_image.configure(text = msg[1])
                self.after(100, self.process_queue_load)
                
        except queue.Empty:
            self.after(100, self.process_queue_load)
    
    def process_queue_hunt_multi(self):
        try:
            msg = self.queue_hunt_multi.get(0)
            self.hunt_counter+=1
            
            if self.hunt_counter<self.Nwafer:
                self.queue_hunt = queue.Queue()
                self.after(100, self.process_queue_hunt_multi)
                self.Hunt_one(self.hunt_counter,self.factor)
            
            else:
#                self.remove_double()
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

    def process_queue_combine(self):
        try:
            msg = self.queue_combine.get(0)
            
            if msg[0] == 0:
                self.Label_report.configure(text = str(msg[1])+"%")
                self.after(100, self.process_queue_combine)
                
            if msg[0] == 1:
                self.Label_report.configure(text = "saving pdf")
                self.after(100, self.process_queue_combine)
            
            if msg[0] == 2:
                self.Label_report.configure(text = "done")     
        except:
            self.after(100, self.process_queue_combine)            
    
    def process_queue_auto_stitch(self):
        try:
            msg = self.queue_auto_stitch.get(0)
            self.stitchImage_popup()

        except queue.Empty:
            self.after(100, self.process_queue_auto_stitch)
    
    


if __name__ == '__main__':
    mp.freeze_support()
    
    root = Root()
    root.mainloop()
