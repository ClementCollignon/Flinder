import numpy as np
import os
import sys
import threading
from scipy.optimize import curve_fit
import cv2MAXPIX
import cv2
import multiprocessing as mp
from scipy.interpolate import interp1d
import shutil

import image_manipulation as im

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1.5
FONT_THICKNESS = 4
BLACK_COLOR = (0,0,0)
WHITE_COLOR = (255,255,255)
RED_COLOR = (0,0,255)

COMPRESSION_LOCALISATION_IMAGE = 20

IMAGE_WIDTH = 4908
IMAGE_HEIGHT = 3264

class SubHunter():
    def __init__(self,filename,path_calibration_folder,subpic_number,scale_ratio,image_binned,targeted_size,top_right_corner_positionning,hc):
        
        self.scale_ratio=scale_ratio #um/px
        self.factor=int(0.579/scale_ratio)
        self.targeted_size = targeted_size
        
        self.image_binned=image_binned
        
        self.hc=hc
        
        self.coordinates_corner=top_right_corner_positionning[0]
        self.angle=top_right_corner_positionning[1]
        
        Data=np.genfromtxt(filename+"/Position_files/coordinates.dat")
        x_px,y_px=Data[:,0],Data[:,1]
        
        self.coordinates_subpic=[x_px[subpic_number]-IMAGE_WIDTH/2,y_px[subpic_number]-IMAGE_HEIGHT/2]
        
        self.path_calibration_folder = path_calibration_folder
        self.criterium_file_path=path_calibration_folder+"/criterium.dat"
        
        calibration_details=path_calibration_folder+"/calibration_details.dat"
        D=np.genfromtxt(calibration_details)
        self.layer_or_thickness=int(D[0])
        self.number_of_intervals=int(D[1])
        self.use_k=int(D[2])
        self.use_b=int(D[3])
        self.use_g=int(D[4])
        self.use_r=int(D[5])
        
        self.filename=filename
        self.subpic_number=subpic_number
        
    def hunt(self):
        
        path=self.filename+"/Color_Corrected_Pictures/pic"+str(self.subpic_number).zfill(2)+".jpg"
        if self.hc==1:
            path=self.filename+"/Color_Corrected_Pictures_HC/pic"+str(self.subpic_number).zfill(2)+".jpg"
        
        image = cv2.imread(path)
        #image=cv2.medianBlur(image, 7)
        
        self.k,self.b,self.g,self.r = im.extract_kbgr_from_image(image)        
        
        #mask values for each thickness interval
        mask_values = im.get_mask_values(self.path_calibration_folder)
        
        thickness,kcal,bcal,gcal,rcal,k_error,b_error,g_error,r_error = im.read_calibration(self.path_calibration_folder+"/calibration.dat")
        
        ##find contours for each thickness
        large_contours = []
        segment_numbers = []
        for i in range(len(mask_values)):
            selected=self.make_selection(mask_values[i])
            large_contours_segment = self.find_large_contours(selected)
            large_contours.extend(large_contours_segment)
            segment_numbers.extend([i for j in large_contours_segment])
        
        path_folder,path_1mm,path_loc,path_log=[],[],[],[]
        path_NN=[]
        percent=0
        for contour,segment_number in zip(large_contours,segment_numbers):
            mask = np.zeros(self.k.shape, np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
            
            k_max, k_var=self.get_max_variance_hist(self.k,mask)
            b_max, b_var=self.get_max_variance_hist(self.b,mask)
            g_max, g_var=self.get_max_variance_hist(self.g,mask)
            r_max, r_var=self.get_max_variance_hist(self.r,mask)
            most_frequent_values = [k_max,b_max,g_max,r_max]
            
            croped_image, xmin, ymin, xmax, ymax, center_x, center_y=self.crop_image(contour)
            
            dimension1,dimension2,position1,position2,ofsetx,ofsety=self.flake_dimension_calc(contour,croped_image,xmin,ymin)
            
            Area,Perimeter=self.getArea_micron(contour)
            
            if Area == 0: Area = 1
            if Perimeter == 0: Perimeter = 1
            if dimension1 == 0: dimension1 = 1
            if dimension2 == 0: dimension2 = 1
            
            criteria=[k_var,b_var,g_var,r_var,16*Area/Perimeter/Perimeter,max(dimension1,dimension2)/min(dimension1,dimension2),len(contour)/Perimeter]
            
            flake_match_criteria = self.is_criteria_ok(criteria)
            flake_inside = self.is_flake_inside(center_x,center_y)
            color_in_range = self.is_color_in_range(mask_values[segment_number],most_frequent_values)
                
            if flake_match_criteria and flake_inside and color_in_range:
                dist=(b_max-bcal)**2+(r_max-rcal)**2+(g_max-gcal)**2+(k_max-kcal)**2
                thickness_flake=thickness[np.argmin(dist)]
                
                layers=str(int(round(thickness_flake,0)))

                self.flake_dimension_draw(dimension1,dimension2,position1,position2,ofsetx,ofsety,croped_image)
                
                new_folder=self.filename+"/Analysed_picture/"+str(self.subpic_number)+"_"+str(percent)
                try:
                    os.mkdir(new_folder)
                except OSError:
                    print ("every folder already exist")
                        
                x_wafer_ref, y_wafer_ref=self.getPosition_micron(center_x,center_y,self.angle)
            
                Y0,step=70,50
                self.drawText(croped_image,Y0,step,x_wafer_ref,y_wafer_ref,Area,layers)
                
                spread="1"
                if self.factor==2:
                    spread="0p5"
                if self.factor==4:
                    spread="0p25"
                
                path_1mm_loop=new_folder+"/"+spread+"mm_zoom_"+str(self.subpic_number)+"_"+str(percent)+".jpg"
                cv2.imwrite(path_1mm_loop,croped_image)
                
                localisation_img=self.localisation_image(int(xmin),int(ymin),int(xmax),int(ymax))
                path_loc_loop=new_folder+"/localization_"+str(self.subpic_number)+"_"+str(percent)+".jpg"
                cv2.imwrite(path_loc_loop,localisation_img)
             
                logfile=self.log_file_flake(center_x,center_y,x_wafer_ref,y_wafer_ref,layers,Area,criteria)
                path_log_loop=new_folder+"/log_"+str(self.subpic_number)+"_"+str(percent)+".dat"
                f = open(path_log_loop, "w")
                f.write(logfile)
                f.close()
                
                picture_for_CNN=self.crop_image_NN(contour)
                path_NN_loop=new_folder+"/NN_"+str(self.subpic_number)+"_"+str(percent)+".jpg"
                cv2.imwrite(path_NN_loop,picture_for_CNN)
                
                percent+=1
                path_folder.append(new_folder)
                path_1mm.append(path_1mm_loop)
                path_loc.append(path_loc_loop)
                path_log.append(path_log_loop)
                path_NN.append(path_NN_loop)
                
        return path_folder,path_1mm,path_loc,path_log,path_NN
    
    def is_criteria_ok(self,criteria):
        D=np.genfromtxt(self.criterium_file_path)
        to_use=D[:,1]
        minimal_value=D[:,2]
        maximal_value=D[:,3]
            
        condition=0
        total_criterium=0
        for i in range(len(criteria)):
            if to_use[i]==1:
                condition += criteria[i] > minimal_value[i] and criteria[i] < maximal_value[i]
                total_criterium+=1
        
        return condition == total_criterium
        
    def is_flake_inside(self,center_x,center_y):
        margin_x=int(0.125*IMAGE_WIDTH)
        margin_y=int(0.125*IMAGE_HEIGHT)
        xmin_flake_in = margin_x
        xmax_flake_in = IMAGE_WIDTH-margin_x
        ymin_flake_in = margin_y
        ymax_flake_in = IMAGE_HEIGHT-margin_y
        
        condition_position_x = center_x > xmin_flake_in and center_x < xmax_flake_in
        condition_position_y = center_y > ymin_flake_in and center_y < ymax_flake_in
        condition_position = condition_position_x and condition_position_y
        return condition_position
        
    def is_color_in_range(self,mask_values,most_frequent_values):
        
        kmin,kmax,bmin,bmax,gmin,gmax,rmin,rmax = mask_values
        k_max,b_max,g_max,r_max = most_frequent_values
        
        condition_color = 0
        if self.use_k==1:
            condition_color += k_max<kmax and k_max>kmin
        if self.use_b==1:
            condition_color += b_max<bmax and b_max>bmin
        if self.use_g==1:
            condition_color += g_max<gmax and g_max>gmin
        if self.use_r==1:
            condition_color += r_max<rmax and r_max>rmin
        
        return condition_color == (self.use_k+self.use_b+self.use_g+self.use_r)
        
    
    def make_selection(self,mask_values):
        
        gray_mask = self.mask(self.k,0,255)
        if self.use_k==1:
            gray_mask = self.mask(self.k,mask_values[0],mask_values[1])
        if self.use_b==1:
            blue_mask = self.mask(self.b,mask_values[2],mask_values[3])
        if self.use_g==1:
            green_mask = self.mask(self.g,mask_values[4],mask_values[5])
        if self.use_r==1:
            red_mask = self.mask(self.r,mask_values[6],mask_values[7])
        
        if self.use_b==1:
            gray_mask[blue_mask<0.5]=0
        if self.use_g==1: 
            gray_mask[green_mask<0.5]=0
        if self.use_r==1:
            gray_mask[red_mask<0.5]=0

        return gray_mask
    
    def find_large_contours(self,selected):
        contours, hierarchy = cv2.findContours(selected, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        large_contours=[]
        for contour in contours:
            if cv2.contourArea(contour)>self.targeted_size:
                large_contours.append(contour)
        return large_contours
    
    def position_contour(self,contour):
        x,y,w,h = cv2.boundingRect(contour)
        center_x=x+w/2
        center_y=y+h/2
        return center_x, center_y
    
    def get_max_variance_hist(self,channel,mask):
        hist = cv2.calcHist([channel],[0],mask,[256],[0,256])
        maximum=np.argmax(hist[:,0])
        proba=hist[:,0]
        values=np.arange(len(proba))
        variance=np.sqrt(np.sum(proba*(values-maximum)**2)/np.sum(proba))
        return maximum, variance
    
    def crop_image(self,contour):
        square_1000um=1000/self.scale_ratio/self.factor
        x,y,w,h = cv2.boundingRect(contour)
        center_x=x+w/2
        center_y=y+h/2
        ymin=int(center_y-square_1000um/2)
        ymax=int(center_y+square_1000um/2)
        xmin=int(center_x-square_1000um/2)
        xmax=int(center_x+square_1000um/2)
        
        if ymin<0:
            ymax-=ymin
            ymin=0
        if ymax>IMAGE_HEIGHT:
            ymin-=ymax-IMAGE_HEIGHT
            ymax=IMAGE_HEIGHT
            
        if xmin<0:
            xmax-=xmin
            xmin=0
        if xmax>IMAGE_WIDTH:
            xmin-=xmax-IMAGE_WIDTH
            xmax=IMAGE_WIDTH
        
        
        b_cropped=self.b[ymin:ymax, xmin:xmax]
        g_cropped=self.g[ymin:ymax, xmin:xmax]
        r_cropped=self.r[ymin:ymax, xmin:xmax]
        
        croped_image = cv2.merge((b_cropped,g_cropped,r_cropped))
        
        return croped_image, xmin, ymin, xmax, ymax, center_x, center_y
    
    def crop_image_NN(self,contour):
        x,y,w,h = cv2.boundingRect(contour)
        
        side = max(h,w)
        extra_px=25
        
        ymin=y-extra_px
        ymax=y+side+extra_px
        xmin=x-extra_px
        xmax=x+side+extra_px
        
        h,w = self.b.shape
        
        if ymin<0:ymin=0
        if ymax>h:ymax=h
        if xmin<0:xmin=0
        if xmax>w:xmax=w
        
        b_cropped=self.b[ymin:ymax, xmin:xmax]
        g_cropped=self.g[ymin:ymax, xmin:xmax]
        r_cropped=self.r[ymin:ymax, xmin:xmax]
        
        croped_image = cv2.merge((b_cropped,g_cropped,r_cropped))
        
        croped_image = cv2.resize(croped_image,(256,256))
        
        return croped_image
    
    def flake_dimension_calc(self,contour,croped_image, xmin, ymin):
        
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        dimension1=(box[0][0]-box[1][0])**2+(box[0][1]-box[1][1])**2
        dimension2=(box[1][0]-box[2][0])**2+(box[1][1]-box[2][1])**2
            
        dimension1=int(np.round(np.sqrt(dimension1)*self.scale_ratio,0))
        dimension2=int(np.round(np.sqrt(dimension2)*self.scale_ratio,0))
        
        for j in range(len(box)):
            box[j][0]-=xmin
            box[j][1]-=ymin
            
        alpha=np.arctan( np.abs((box[0][0]-box[1][0])/(box[1][1]-box[0][1])) )
        if np.isnan(alpha):
            alpha = 90
        ofsetx=int(20*np.cos(alpha))
        ofsety=int(20*np.sin(alpha))
            
        box1=[box[0],box[1]]
        for j in range(len(box1)):
            box1[j][0]+=-ofsetx
            box1[j][1]+=ofsety
        box1 = np.int0(box1)
        
        croped_image = cv2.drawContours(croped_image,[box1],0,RED_COLOR,2)
        position1=[int((box1[0][0]+box1[1][0])/2),int((box1[0][1]+box1[1][1])/2)]
            
        box2=[box[1],box[2]]
        box2[0][0]+=ofsetx
        box2[0][1]+=-ofsety
        for j in range(len(box2)):
            box2[j][0]+=-ofsety
            box2[j][1]+=-ofsetx
        box2 = np.int0(box2)
        
        croped_image = cv2.drawContours(croped_image,[box2],0,RED_COLOR,2)
        position2=[int((box2[0][0]+box2[1][0])/2),int((box2[0][1]+box2[1][1])/2)]
        
        return dimension1,dimension2,position1,position2,ofsetx,ofsety
    
    def flake_dimension_draw(self,dimension1,dimension2,position1,position2,ofsetx,ofsety,croped_image):
        label_width,label_height=cv2.getTextSize(str(dimension1),FONT,FONT_SCALE,FONT_THICKNESS)[0]
        position1[0]-=int(0.5*label_width)
        position1[1]+=int(0.5*label_height)
        position1=(position1[0]-int(2.5*ofsetx),position1[1]+int(2.5*ofsety))
        cv2.putText(croped_image, str(dimension1), position1, FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, str(dimension1), position1, FONT, FONT_SCALE, RED_COLOR, FONT_THICKNESS)
 
        label_width,label_height=cv2.getTextSize(str(dimension2),FONT,FONT_SCALE,FONT_THICKNESS)[0]
        position2[0]-=int(0.5*label_width)
        position2[1]+=int(0.5*label_height)
        position2=(position2[0]-int(2.5*ofsety),position2[1]-int(2.5*ofsetx))
        cv2.putText(croped_image, str(dimension2), position2, FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, str(dimension2), position2, FONT, FONT_SCALE, RED_COLOR, FONT_THICKNESS)
        
    def getArea_micron(self,contour):
        return cv2.contourArea(contour)*self.scale_ratio*self.scale_ratio , cv2.arcLength(contour,True)*self.scale_ratio
    
    def getPosition_micron(self,center_x,center_y,angle):
        
        x_position_from_corner=(self.coordinates_corner[0]-center_x-self.coordinates_subpic[0])*self.scale_ratio
        y_position_from_corner=(center_y-self.coordinates_corner[1]+self.coordinates_subpic[1])*self.scale_ratio
            
        x_wafer_ref=x_position_from_corner*np.cos(angle)+y_position_from_corner*np.sin(angle)
        y_wafer_ref=-x_position_from_corner*np.sin(angle)+y_position_from_corner*np.cos(angle)
            
        x_wafer_ref=str(np.round(x_wafer_ref/1000,1))
        y_wafer_ref=str(np.round(y_wafer_ref/1000,1))
        
        return x_wafer_ref, y_wafer_ref
        
    def drawText(self,croped_image,Y0,step,x_wafer_ref,y_wafer_ref,Area,layers):
        cv2.putText(croped_image, "Position from top right corner", (20,Y0), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, "Position from top right corner", (20,Y0), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
        cv2.putText(croped_image, "X = "+x_wafer_ref+" mm", (20,Y0+step), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, "X = "+x_wafer_ref+" mm", (20,Y0+step), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
        cv2.putText(croped_image, "Y = "+y_wafer_ref+" mm", (20,Y0+2*step), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, "Y = "+y_wafer_ref+" mm", (20,Y0+2*step), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
        cv2.putText(croped_image, "Area = "+str(int(np.round(Area,0))), (20,int(Y0+3.5*step)), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
        cv2.putText(croped_image, "Area = "+str(int(np.round(Area,0))), (20,int(Y0+3.5*step)), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
        if self.layer_or_thickness==1:
            cv2.putText(croped_image, "# Layers = "+layers, (20,int(Y0+5*step)), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
            cv2.putText(croped_image, "# Layers = "+layers, (20,int(Y0+5*step)), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
        if self.layer_or_thickness==0:
            cv2.putText(croped_image, "Thickness = "+layers+" nm", (20,int(Y0+5*step)), FONT, FONT_SCALE, BLACK_COLOR, FONT_THICKNESS+1)
            cv2.putText(croped_image, "Thickness = "+layers+" nm", (20,int(Y0+5*step)), FONT, FONT_SCALE, WHITE_COLOR, FONT_THICKNESS)
    
    def localisation_image(self,xmin,ymin,xmax,ymax):
        
        xmin=(xmin+self.coordinates_subpic[0])/COMPRESSION_LOCALISATION_IMAGE
        xmax=(xmax+self.coordinates_subpic[0])/COMPRESSION_LOCALISATION_IMAGE
        ymin=(ymin+self.coordinates_subpic[1])/COMPRESSION_LOCALISATION_IMAGE
        ymax=(ymax+self.coordinates_subpic[1])/COMPRESSION_LOCALISATION_IMAGE

        localisation_img = self.image_binned.copy()
            
        local_box=[[xmin,ymin],[xmax,ymin],[xmax,ymax],[xmin,ymax]]
        local_box = np.int0(local_box)
        localisation_img = cv2.drawContours(localisation_img,[local_box],0,RED_COLOR,3)
        
        return localisation_img
    
    def log_file_flake(self,center_x,center_y,x_wafer_ref,y_wafer_ref,layers,Area,criteria):
            
        Data=np.genfromtxt(self.filename+"/Position_files/coordinates.dat")
        x_micron,y_micron,zfocus,intensity=Data[:,2],Data[:,3],Data[:,4],Data[:,5]
     
        center_picture_x=IMAGE_WIDTH/2
        center_picture_y=IMAGE_HEIGHT/2
        
        x_from_center=(center_x-center_picture_x)*self.scale_ratio
        y_from_center=(center_y-center_picture_y)*self.scale_ratio
        
        Xflake=x_micron[self.subpic_number]+x_from_center
        Yflake=y_micron[self.subpic_number]+y_from_center
        
        xx=x_micron[::3]
        yy=y_micron[::3]
        zz=zfocus[::3]
        ii=intensity[::3]
        
        min_intensity=100
        xx=xx[ii>min_intensity]
        yy=yy[ii>min_intensity]
        zz=zz[ii>min_intensity]
        
        def zplane(X,a,b,c):
            x,y=X
            return a*x+b*y+c
        
        popt,pcov=curve_fit(zplane, [xx,yy], zz)
        Zflake=zplane([Xflake,Yflake],*popt)
            
        logfile="""X(from top right corner):\t"""+x_wafer_ref+""" mm
Y(from top right corner):\t"""+y_wafer_ref+""" mm
Number of layers:\t"""+layers+"""
Area:\t"""+str(int(np.round(Area,0)))+"""
X(for scope):\t"""+str(np.round(Xflake,2))+"""
Y(for scope):\t"""+str(np.round(Yflake,2))+"""
Z(for scope):\t"""+str(np.round(Zflake,2))+"""
criteria:\t"""+str(criteria)
    
        return logfile
    
    def local_averaging(self,channel,square):
        channel = cv2.blur(channel,(square,square))
        channel=channel.astype("uint8")
        return channel
    
    def mask(self,channel,lmin,lmax):
        square=5
        blurred=self.local_averaging(channel,square)
        #channel max limit
        treshold=lmin
        _, binary = cv2.threshold(blurred, treshold, 255, cv2.THRESH_BINARY_INV)

        #channel min limit
        treshold=lmax
        _, binary2 = cv2.threshold(blurred, treshold, 255, cv2.THRESH_BINARY_INV)

        #difference of the two
        selected=binary-binary2

        return selected

class ThreadedHunter(threading.Thread):
    def __init__(self, queue_hunt,filename,wafer_path,hunt_counter,targeted_size,factor,wafer_number,hc):
        threading.Thread.__init__(self)
        self.filename=wafer_path[hunt_counter]
        self.filename_cal=filename+"/Calibration"
        self.queue_hunt = queue_hunt
        self.scale_ratio=0.579/factor #um/px
        self.factor=factor
        self.targeted_size = targeted_size/self.scale_ratio/self.scale_ratio
        self.wafer_number=wafer_number
        self.hc=hc
    
    def run(self):
        ##Load image
        self.queue_hunt.put([0,"Wafer "+str(self.wafer_number).zfill(2)+"\nloading image\n(it can take time)"])
        image=self.load_image()
        
        ##Cut the picture in squares of 6000x6000 and include a margin (keep x,y,path,N_sub_pictures) and loss_less save it
        self.queue_hunt.put([0,"Wafer "+str(self.wafer_number).zfill(2)+"\nparallelizing\n(it can take time)"])
        
        path_hc=[self.filename+"/Color_Corrected_Pictures/"+i for i in os.listdir(self.filename+"/Color_Corrected_Pictures")]

        ##Bin the colored image and keep it for later (to feed to SubHunter)
        image_binned=self.compress_image(image)
        del image

        ##Look for top right corner        
        self.queue_hunt.put([0,"Wafer "+str(self.wafer_number).zfill(2)+"\nLooking for top right corner\nand angle"])
        top_right_corner_x,top_right_corner_y,angle=self.find_corner(image_binned)
        
        top_right_corner_positionning=[[top_right_corner_x,top_right_corner_y],angle]
        
        self.queue_hunt.put([0,"Wafer "+str(self.wafer_number).zfill(2)+"\nHunting: 0 %"])
        
        ##Create a subhunter for each picture
        sub_hunters=[]
        for subpic_number in range(len(path_hc)):
            sub_hunters.append(SubHunter(self.filename,self.filename_cal,subpic_number,self.scale_ratio,image_binned,self.targeted_size,top_right_corner_positionning,self.hc))
        
        ##Parallelize the hunting and update the percentage
        num_workers = min(10,mp.cpu_count()-2)
        pool = mp.Pool(num_workers)
        handler=[]
        
        for sub_hunter in sub_hunters:
            handler.append(pool.apply_async(sub_hunter.hunt))
        
        N=len(handler)
        
        path_folder,path_1mm,path_loc,path_log=[],[],[],[]
        path_NN = []
        for i in range(N):
            res=handler[i].get()
            
            self.queue_hunt.put([0,"Wafer "+str(self.wafer_number).zfill(2)+"\nHunting: "+str(int(np.round(i/N*100,0)))+" %"])
            path_folder.extend(res[0])
            path_1mm.extend(res[1])
            path_loc.extend(res[2])
            path_log.extend(res[3])
            path_NN.extend(res[4])
        pool.close()
        pool.join()
        
        ##Rename flakes
        self.rename(path_folder,path_1mm,path_loc,path_log,path_NN)
        
        self.queue_hunt.put([1,"Wafer "+str(self.wafer_number).zfill(2)+"\nHunt done: "+str(len(path_folder))+" flakes"])
    
    def load_image(self):
        image = cv2.imread(self.filename+"/Analysed_picture/full_image.jpg")
        return image
        
    def compress_image(self,image):
        size_x=int(image.shape[1]/COMPRESSION_LOCALISATION_IMAGE)
        size_y=int(image.shape[0]/COMPRESSION_LOCALISATION_IMAGE)
        image_binned=cv2.resize(image, (size_x,size_y),interpolation=cv2.INTER_NEAREST)
        return image_binned
    
    def mask(self,channel,lmin,lmax):
        #channel max limit
        treshold=lmin
        _, binary = cv2.threshold(channel, treshold, 255, cv2.THRESH_BINARY_INV)

        #channel min limit
        treshold=lmax
        _, binary2 = cv2.threshold(channel, treshold, 255, cv2.THRESH_BINARY_INV)

        #difference of the two
        selected=binary-binary2

        return selected
    
    def find_corner(self,image_binned):
        gray_binned=cv2.cvtColor(image_binned, cv2.COLOR_BGR2GRAY)
        
        lmin,lmax=10,255
        grey_mask = self.mask(gray_binned,lmin,lmax)
        
        contours, hierarchy = cv2.findContours(grey_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        maxArea=0
        for contour in contours:
            A=cv2.contourArea(contour)
            if A>maxArea:
                maxArea=A
                largest_contour = contour
                
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        midx,midy=gray_binned.shape[0]/2,gray_binned.shape[1]/2
        
        top_right_corner_x=0
        top_right_corner_y=0
        box_number_top_right_corner=0
        box_number_bottom_right_corner=0
        
        for i in range(4):
            xx=box[i][0]
            yy=box[i][1]
            if xx>midx and yy<midy:                
                top_right_corner_x=xx
                top_right_corner_y=yy
                box_number_top_right_corner=i
            if xx>midx and yy>midy:
                box_number_bottom_right_corner=i

        x2,y2=box[box_number_top_right_corner]
        x3,y3=box[box_number_bottom_right_corner]
        sign=1

        adjacent=y3-y2
        hypothenus=np.sqrt((y3-y2)**2+(x3-x2)**2)
        theta=np.arccos(adjacent/hypothenus) 

        angle=sign*theta
        
        return top_right_corner_x*COMPRESSION_LOCALISATION_IMAGE,top_right_corner_y*COMPRESSION_LOCALISATION_IMAGE,angle
    
    def rename(self,path_folder,path_1mm,path_loc,path_log,path_NN):
        N=len(path_folder)
        zeros=len(str(N))
        
        spread="1"
        if self.factor==2:
            spread="0p5"
        
        for i in range(N):
            new_folder=self.filename+"/Analysed_picture/"+str(i).zfill(zeros)
            self.rename_one(path_1mm[i],path_folder[i]+"/"+spread+"mm_zoom_Wafer"+str(self.wafer_number).zfill(2)+"_"+str(i).zfill(zeros)+".jpg")
            self.rename_one(path_loc[i],path_folder[i]+"/localization_Wafer"+str(self.wafer_number).zfill(2)+"_"+str(i).zfill(zeros)+".jpg")
            self.rename_one(path_log[i],path_folder[i]+"/log_Wafer"+str(self.wafer_number).zfill(2)+"_"+str(i).zfill(zeros)+".dat")
            self.rename_one(path_NN[i],path_folder[i]+"/NN.jpg")
            
            if os.path.exists(new_folder):
                shutil.rmtree(new_folder)
            os.rename(path_folder[i],self.filename+"/Analysed_picture/"+str(i).zfill(zeros))
    
    def rename_one(self,path1,path2):
        if os.path.exists(path2):
            os.remove(path2)
        os.rename(path1,path2)
        
        
        
        