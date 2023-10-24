import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import os
import sys
from constants_and_variables import GuiConstants, ScopeConstants, VariablesStore

import functions
import Stitcher
import Hunter_parallele
import Auto_functions
import ThreadedTrainer

import numpy as np
import multiprocessing as mp

class GuiSetup(object):
    """The main GUI.
    """ 
    def __init__(self, gui_const, main_window):
        self.main_window = main_window
        self.gui_const = gui_const

        self.main_window.title("Flinder")
        
        self.main_window.minsize(self.gui_const.window_size[0],self.gui_const.window_size[1])

        self.main_window.wm_iconbitmap('icon.ico')
        self.main_window.configure(bg = self.gui_const.color_set[0])

        #split window in 3 panels
        self.split_main_window()
    
    def split_main_window(self):
        #Create two vertical lines to separate the window in 3 pannels
        height = self.gui_const.window_size[1]
        width = 2
        bg = self.gui_const.color_set[1]
        x1 =  799 / self.gui_const.screen_scaling
        x2 = 1599 / self.gui_const.screen_scaling
        y  =    0 / self.gui_const.screen_scaling

        vertical_ligne1 = tk.Frame(self.main_window, height = height, width = width, bg = bg)
        vertical_ligne1.place(x = x1, y = y)

        vertical_ligne2 = tk.Frame(self.main_window, height = height, width = width, bg = bg)
        vertical_ligne2.place(x = x2, y = y)
    
    def setup_working_folder_panel(self):
        x          = 30 / self.gui_const.screen_scaling
        y          = 10 / self.gui_const.screen_scaling
        text       = "Working Folder"
        font_color = "black"
        font       = self.gui_const.fonts["l"]
        bg         = self.gui_const.color_set[0]
        anchor     = 'nw'
        label_working_folder = tk.Label(self.main_window,  text = text, fg = font_color, font = font, 
                                        bg = bg )
        label_working_folder.place(x = x, y = y, anchor = anchor)
        
        x      = 195 / self.gui_const.screen_scaling
        y      = 130 / self.gui_const.screen_scaling
        height = 170 / self.gui_const.screen_scaling
        width  = 590 / self.gui_const.screen_scaling
        bg     = self.gui_const.color_set[1]
        frame_path_working_folder=tk.Frame(self.main_window, height = height, width = width, bg = bg)
        frame_path_working_folder.place(x = x, y = y, anchor = anchor)

        x          = 200 / self.gui_const.screen_scaling
        y          = 135 / self.gui_const.screen_scaling
        font_color = "black"
        text       = "Path: "
        font       = self.gui_const.fonts["xs"]
        bg         = self.gui_const.color_set[1]
        anchor     = 'nw'
        label_path = tk.Label(self.main_window,  text = text, fg = font_color, font = font, bg = bg)
        label_path.place(x = x, y = y, anchor = anchor)

        x    =  30 / self.gui_const.screen_scaling
        y    = 130 / self.gui_const.screen_scaling
        text = "Browse"
        button_browse = ttk.Button(self.main_window, text = text)
        button_browse.place(x = x, y = y, anchor = anchor )

        return label_path, button_browse

    def setup_position_size(self):
        x          =  30 / self.gui_const.screen_scaling
        y          = 320 / self.gui_const.screen_scaling
        text       = "Position and size"
        font_color = "black"
        font       = self.gui_const.fonts["l"]
        bg         = self.gui_const.color_set[0]
        anchor     = 'nw'
        label_scanning_size = tk.Label(self.main_window, text = text, fg = 'black', font = font, bg = bg)
        label_scanning_size.place(x = x, y = y, anchor = anchor)
        
        x      =  40 / self.gui_const.screen_scaling
        y      = 480 / self.gui_const.screen_scaling
        text   = "Number of Wafers"
        font   = self.gui_const.fonts["s"]
        anchor = 'w'
        label_numberofwafers = tk.Label(self.main_window, text = text, fg = font_color, font = font, bg = bg)
        label_numberofwafers.place(x = x, y = y, anchor = anchor)

        x     = 470 / self.gui_const.screen_scaling
        width = 3
        entry_numberofwafers = tk.Entry(self.main_window, width = width, font = font) 
        entry_numberofwafers.place(x = x, y = y, anchor = anchor)
        
        x      = 400 / self.gui_const.screen_scaling
        y      = 570 / self.gui_const.screen_scaling
        text   = " Enter position and size "
        anchor = 'center'
        button_pos_size = ttk.Button(self.main_window, text = text)
        button_pos_size.place(x = x, y = y, anchor = anchor)

        return entry_numberofwafers, button_pos_size

    def setup_auto_stitch_hunt(self):
        x      =  40 / self.gui_const.screen_scaling
        y      = 650 / self.gui_const.screen_scaling
        text   = 'Auto Stitch'
        bg     = self.gui_const.color_set[0]
        font   = self.gui_const.fonts["s"]
        anchor = 'nw'
        button_auto_stitch = tk.Checkbutton(self.main_window, text = text, bg = bg, font = font)
        button_auto_stitch.place(x = x, y = y, anchor = anchor)
        
        x      = 440 / self.gui_const.screen_scaling
        text   = 'Auto Hunt'
        button_auto_hunt = tk.Checkbutton(self.main_window, text = text, bg = bg, font = font)
        button_auto_hunt.place(x = x, y = y, anchor = anchor)

        var_auto_stitch = tk.IntVar()
        var_auto_hunt   = tk.IntVar()
        button_auto_stitch.config(variable = var_auto_stitch, onvalue = 1, offvalue = 0)  
        button_auto_hunt.config(variable = var_auto_hunt, onvalue = 1, offvalue = 0)

        return var_auto_stitch, var_auto_hunt

    def setup_nosepiece_panel(self):
        x          =  30 / self.gui_const.screen_scaling
        y          = 780 / self.gui_const.screen_scaling
        text       = "Nosepiece"
        font_color = "black"
        font       = self.gui_const.fonts["l"]
        bg         = self.gui_const.color_set[0]
        anchor     = "nw"
        label_nosepiece = tk.Label(self.main_window, text = text, fg = font_color, font = font, bg = bg)
        label_nosepiece.place(x = x, y = y, anchor = anchor)
        
        x    =  80 / self.gui_const.screen_scaling
        y    = 940 / self.gui_const.screen_scaling
        step = 130 / self.gui_const.screen_scaling

        nosepiece_selected = tk.IntVar()
        texts = ['5x','10x','20x','50x','100x']
        for i, text in enumerate(texts):
            xx = x + i * step
            self.button_nosepiece(nosepiece_selected, i+1, text, xx, y)
        
        return nosepiece_selected

    def button_nosepiece(self, nosepiece_selected, value, text, x, y):
         rbutton = tk.Radiobutton(self.main_window, 
                                  indicatoron = 0,
                                  text        = text,
                                  selectcolor = self.gui_const.color_set[2],
                                  bg          = self.gui_const.color_set[0],
                                  width       = 4,
                                  font        = self.gui_const.fonts["s"],
                                  variable    = nosepiece_selected, 
                                  value       = value)
         rbutton.place(x = x, y = y, anchor = 'w')

    def setup_macro_panel(self):
        x          =   30 / self.gui_const.screen_scaling
        y          = 1050 / self.gui_const.screen_scaling
        text       = "Create Macro"
        font_color = "black"
        font       = self.gui_const.fonts["l"]
        bg         = self.gui_const.color_set[0]
        anchor     = "nw"
        label_create_macro = tk.Label(self.main_window, text = text, fg = font_color,
                                      font = font, bg = bg)
        label_create_macro.place(x = x, y = y, anchor = anchor)
        
        x      =  195 / self.gui_const.screen_scaling
        y      = 1165 / self.gui_const.screen_scaling
        height =   55 / self.gui_const.screen_scaling
        width  =  590 / self.gui_const.screen_scaling
        bg     = self.gui_const.color_set[1]
        
        frame_path_create_macro=tk.Frame(self.main_window,
                                         height = height, width = width, bg = bg)
        frame_path_create_macro.place(x = x, y = y, anchor = anchor)
        
        x      =  480 / self.gui_const.screen_scaling
        y      = 1192 / self.gui_const.screen_scaling
        text   = "Waiting for the Go..."
        font   = self.gui_const.fonts["xs"]
        anchor = 'center'
        label_macro = tk.Label(self.main_window,  
                               text = text, fg = font_color, font = font, bg = bg)
        label_macro.place(x = x, y = y, anchor = anchor)
        
        x =   30 / self.gui_const.screen_scaling
        y = 1170 / self.gui_const.screen_scaling
        text = "GO"
        anchor = "nw"

        button_macro = ttk.Button(self.main_window, text = text)
        button_macro.place(x = x, y = y, anchor = anchor)

        return label_macro, button_macro
