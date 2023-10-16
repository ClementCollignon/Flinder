import os
import threading
import time
import cv2
import numpy as np
from fpdf import FPDF
import shutil
from matplotlib import cm
import functions

config = functions.get_config()
(MAIN_FOLDER, SCREEN_SCALING, ZEROS, 
 FOV, OVERLAP, SCALE, JPG,
 LOW_RES, HIGH_RES, CCD,
 OFFSET_X, OFFSET_Y, OFFSET_Z) = config


class ThreadedAutoStitch(threading.Thread):
    """Put 0 into the queue_auto_stitch when the last picture has been taken by the scope.
    Attributes:
        queue_auto_stitch: queue to hold results
        path_to_check: path where the pictures are being stored after being snapped by Nikon software
    """
    def __init__(self, queue_auto_stitch,path_to_check):
        threading.Thread.__init__(self)
        self.queue_auto_stitch = queue_auto_stitch
        self.path_to_check=path_to_check
    
    def run(self):
        while os.path.exists(self.path_to_check[-1]) == False:
            time.sleep(10)
        self.queue_auto_stitch.put(0)

class ThreadedCombine(threading.Thread):
    """Put 0 into the queue_auto_stitch when the last picture has been taken by the scope.
    Attributes:
        queue_combine: queue to hold results
        Nwafer: path where the pictures are being stored after being snapped by Nikon software
        filename:
        material:
    """

    def __init__(self, queue_combine, filename, Nwafer, material):
        threading.Thread.__init__(self)
        
        self.queue_combine = queue_combine
        self.Nwafer=Nwafer
        self.filename=filename
         
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale=3
        self.font_thickness=6
        
        self.material=material
        self.criterium_file_path=f"{MAIN_FOLDER}/Materials/{material}/50/criterium.dat"
        self.calibration_file_path=f"{MAIN_FOLDER}/Materials/{material}/50/calibration.dat"
        calibration_details=f"{MAIN_FOLDER}/Materials/{material}/50/calibration_details.dat"
        self.cal50=0
        
        if os.path.exists(self.criterium_file_path):
            self.cal50=1
            D=np.genfromtxt(calibration_details)
            self.layer_or_thickness=int(D[0])
            self.number_of_intervals=int(D[1])
            self.use_k=int(D[2])
            self.use_b=int(D[3])
            self.use_g=int(D[4])
            self.use_r=int(D[5])
            self.hc = int(D[6])
            
        self.criterium_file_path_100=f"{MAIN_FOLDER}/Materials/{material}/100/criterium.dat"
        self.calibration_file_path_100=f"{MAIN_FOLDER}/Materials/{material}/100/calibration.dat"
        calibration_details=f"{MAIN_FOLDER}/Materials/{material}/100/calibration_details.dat"
        self.cal100=0
        if os.path.exists(self.criterium_file_path_100):
            self.cal100=1
            D=np.genfromtxt(calibration_details)
            self.layer_or_thickness=int(D[0])
            self.number_of_intervals=int(D[1])
            self.use_k_100=int(D[2])
            self.use_b_100=int(D[3])
            self.use_g_100=int(D[4])
            self.use_r_100=int(D[5])    
    
    def run(self):
        total = (6.+self.cal50+self.cal100)*self.Nwafer
        counter=0.
        self.queue_combine.put([0,int(counter/total*100)])
        for i in range(self.Nwafer):
            self.Correct("50x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
            self.Correct("100x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
            self.Combine("50x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
            self.Combine("100x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
            self.HighContrast("50x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
            self.HighContrast("100x",i)
            counter+=1
            self.queue_combine.put([0,int(counter/total*100)])
        
        if self.cal50==1:
            for i in range(self.Nwafer):
                self.identify_master(i,"50")
                counter+=1
                self.queue_combine.put([0,int(counter/total*100)])
        
        if self.cal100==1:
            for i in range(self.Nwafer):
                self.identify_master(i,"100")
                counter+=1
                self.queue_combine.put([0,int(counter/total*100)])
        
        self.queue_combine.put([1,"pdf"])
        self.create_pdf()
        self.queue_combine.put([2,"done"])
        
        
    def colormap(self,Ncurves,degrade="jet") :
        cmap=cm.get_cmap(degrade,Ncurves)
        colors=cmap(np.arange(Ncurves))
        return colors
    
    def identify_master(self,indice,magnification):
        path=self.filename+"\Wafer_"+str(indice).zfill(2)+"\Analysed_picture"
        for j in os.listdir(path):
            image_path=path+"\\"+j+"\\"+magnification+"x_BF_"+j+"_00_Cor.jpg"
            
            image_path_id=path+"\\"+j+"\\"+magnification+"x_ID_"+j+".jpg"
            
            if self.hc==1:
                image_path=path+"\\"+j+"\\"+magnification+"x_HC_"+j+".jpg"
            
            if os.path.exists(image_path):
                self.identify(image_path,image_path_id,magnification)
    
    def identify(self,image_path,image_path_id,magnification):
        
        self.image = cv2.imread(image_path)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.k = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        self.r,self.g,self.b = cv2.split(self.image)
        self.k=self.k.astype("uint8")
        self.b=self.b.astype("uint8")
        self.g=self.g.astype("uint8")
        self.r=self.r.astype("uint8")
        self.image_width=self.b.shape[1]
        self.image_height=self.b.shape[0]
        
        ##read calibration
        D=np.genfromtxt(self.calibration_file_path)
        if magnification == "100":
            D=np.genfromtxt(self.calibration_file_path_100)
        
        thickness=D[:,0]
        kcal=D[:,1]
        bcal=D[:,2]
        gcal=D[:,3]
        rcal=D[:,4]
        kerror=D[:,5]
        berror=D[:,6]
        gerror=D[:,7]
        rerror=D[:,8]
        
        mask_values=[]
        for i in range(len(thickness)):
            kmin,kmax=kcal[i]-kerror[i],kcal[i]+kerror[i]
            bmin,bmax=bcal[i]-berror[i],bcal[i]+berror[i]
            gmin,gmax=gcal[i]-gerror[i],gcal[i]+gerror[i]
            rmin,rmax=rcal[i]-rerror[i],rcal[i]+rerror[i]
            mask_values.append([kmin,kmax,bmin,bmax,gmin,gmax,rmin,rmax])
        
        color=self.colormap(len(thickness))
        for i in range(len(thickness)):
            self.identify_one_thickness(thickness[i],mask_values[i],color[i],magnification)
        
        self.image = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(image_path_id,self.image)
        
    
    def identify_one_thickness(self,thickness,mask_values,color,magnification):
        selected=self.make_selection(mask_values)
        #cv2.imwrite(str(thickness)+".jpg",selected*200)
            
        contours,contours_indices = self.number_of_contours(selected)    
        
        for i in contours_indices:
            mask = np.zeros(self.k.shape, np.uint8)
            cv2.drawContours(mask, [contours[i]], -1, 255, thickness=cv2.FILLED)
            
            k_max, k_var=self.get_max_variance_hist(self.k,mask)
            b_max, b_var=self.get_max_variance_hist(self.b,mask)
            g_max, g_var=self.get_max_variance_hist(self.g,mask)
            r_max, r_var=self.get_max_variance_hist(self.r,mask)
            
            condition_color = 0
            if magnification=="50":
                if self.use_k==1:
                    condition_color += k_max>mask_values[0] and k_max<mask_values[1]
                if self.use_b==1:
                    condition_color += b_max>mask_values[2] and b_max<mask_values[3] 
                if self.use_g==1:
                    condition_color += g_max>mask_values[4] and g_max<mask_values[5] 
                if self.use_r==1:
                    condition_color += r_max>mask_values[6] and r_max<mask_values[7] 
            
                if condition_color == (self.use_k+self.use_b+self.use_g+self.use_r):
                    position=self.position_contour(contours[i])
                    self.drawText_Contour(position,thickness,contours[i],color)
            
            if magnification=="100":
                if self.use_k_100==1:
                    condition_color += k_max>mask_values[0] and k_max<mask_values[1] 
                if self.use_b_100==1:
                    condition_color += b_max>mask_values[2] and b_max<mask_values[3] 
                if self.use_g_100==1:
                    condition_color += g_max>mask_values[4] and g_max<mask_values[5] 
                if self.use_r_100==1:
                    condition_color += r_max>mask_values[6] and r_max<mask_values[7] 
            
                if condition_color == (self.use_k+self.use_b+self.use_g+self.use_r):
                    position=self.position_contour(contours[i])
                    self.drawText_Contour(position,thickness,contours[i],color)
        
        
    def drawText_Contour(self,position,thickness,contour,color):
        tupple_color=(int(color[0]*255),int(color[1]*255),int(color[2]*255))
        
        text=str(int(thickness))
        textsize = cv2.getTextSize(text, self.font, self.font_scale, self.font_thickness+1)[0]
        
        tupple_position=(int(position[0] - textsize[0]/2),int(position[1] + textsize[1]/2))
        
        cv2.putText(self.image, text , tupple_position , self.font, self.font_scale, (0,0,0), self.font_thickness+1)
        cv2.putText(self.image, text , tupple_position , self.font, self.font_scale, tupple_color, self.font_thickness)
        cv2.drawContours(self.image, [contour], -1, tupple_color, thickness=3)
        
    
    def position_contour(self,contour):
        rect = cv2.minAreaRect(contour)
        center_x,center_y=rect[0]
        # x,y,w,h = cv2.boundingRect(contour)
        # print(x,y,w,h)
        # center_x=x+w/2
        # center_y=y+h/2
        return center_x, center_y
    
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
    
    def number_of_contours(self,selected):
        contours, hierarchy = cv2.findContours(selected, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        large_contours_indices=[]
        
        for i in range(len(contours)):
            area=cv2.contourArea(contours[i])
            per=cv2.arcLength(contours[i],True)
            if area > 5000 and per*per/4/area < 100:
            # if area > 500 :
                large_contours_indices.append(i)
        return contours,large_contours_indices
    
    def get_max_variance_hist(self,channel,mask):
        hist = cv2.calcHist([channel],[0],mask,[256],[0,256])
        maximum=np.argmax(hist[:,0])
        proba=hist[:,0]
        values=np.arange(len(proba))
        variance=np.sqrt(np.sum(proba*(values-maximum)**2)/np.sum(proba))
        return maximum, variance
        
    def mask(self,channel,lmin,lmax):
        square=7
        blurred=self.local_averaging(channel,square)
        if self.hc==1:
            blurred=cv2.medianBlur(blurred,21)
        
        #channel max limit
        treshold=lmin
        _, binary = cv2.threshold(blurred, treshold, 255, cv2.THRESH_BINARY_INV)

        #channel min limit
        treshold=lmax
        _, binary2 = cv2.threshold(blurred, treshold, 255, cv2.THRESH_BINARY_INV)

        #difference of the two
        selected=binary-binary2
        
        selected=cv2.medianBlur(selected,31)
        selected=cv2.medianBlur(selected,31)
        selected=cv2.medianBlur(selected,31)
                
        return selected
    
    def local_averaging(self,channel,square):
        channel = cv2.blur(channel,(square,square))
        channel=channel.astype("uint8")
        return channel

    def correct_channel(self,v,v_bkg):
        v_bkg=v_bkg.astype(np.float32)
        v=v.astype(np.float32)
        factor=np.median(v/v_bkg)
        v=v/(factor*v_bkg)*140
        
        v[v>255]=255
        v[v<0]=0
        
        return v.astype(np.uint8)

    def Correct(self,magnification,indice):
        path=f"{MAIN_FOLDER}/100X/bkg.jpg"
        if magnification=="50x":
            path=f"{MAIN_FOLDER}/50X/bkg.jpg"
        
        image = cv2.imread(path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        r_bkg,g_bkg,b_bkg=cv2.split(image)
                
        path=self.filename+"\Wafer_"+str(indice).zfill(2)+"\Analysed_picture"
        for j in os.listdir(path):
            image_path=path+"\\"+j+"\\"+magnification+"_BF_"+j+"_00.jpg"
            image_path_corrected=path+"\\"+j+"\\"+magnification+"_BF_"+j+"_00_Cor.jpg"
                        
            if os.path.exists(image_path):
                image = cv2.imread(image_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                r,g,b = cv2.split(image)
                
                r=self.correct_channel(r,r_bkg)
                g=self.correct_channel(g,g_bkg)
                b=self.correct_channel(b,b_bkg)
                
                image=cv2.merge((b,g,r))
                
                cv2.imwrite(image_path_corrected,image)
                
    def combined(self,v1,v2,k2,mean):
        
        c0=10/mean
        v2=v2*c0
        c1=0.6
        a0=(1-c1)*v1.astype(np.int16)+c1*v2.astype(np.int16)
    
        a0[a0<0]=0
        a0[a0>255]=255
            
        return a0.astype(np.uint8)

    def Combine(self,magnification,indice):
        path=self.filename+"\Wafer_"+str(indice).zfill(2)+"\Analysed_picture"
        for j in os.listdir(path):
            image1_path=path+"\\"+j+"\\"+magnification+"_BF_"+j+"_00.jpg"
            image2_path=path+"\\"+j+"\\"+magnification+"_DF_"+j+"_00.jpg"
            image_comb_path=path+"\\"+j+"\\"+magnification+"_combined_"+j+".jpg"
            if os.path.exists(image1_path) and os.path.exists(image2_path) and os.path.exists(image_comb_path)==False:
                image1 = cv2.imread(image1_path)
                image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
                b1,g1,r1 = cv2.split(image1)
                image2 = cv2.imread(image2_path)
                k2 = cv2.cvtColor(image2, cv2.COLOR_RGB2GRAY)
                image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
                b2,g2,r2 = cv2.split(image2)
                
                mean_val=np.median(k2)
                b=self.combined(b1,b2,k2,mean_val)
                g=self.combined(g1,g2,k2,mean_val)
                r=self.combined(r1,r2,k2,mean_val)
    
                img = cv2.merge((r,g,b))
                cv2.imwrite(image_comb_path,img)
    
    def HighContrast(self,magnification,indice):
        path=self.filename+"\Wafer_"+str(indice).zfill(2)+"\Analysed_picture"
        for j in os.listdir(path):
            image_path=path+"\\"+j+"\\"+magnification+"_BF_"+j+"_00_Cor.jpg"
            image_HC_path=path+"\\"+j+"\\"+magnification+"_HC_"+j+".jpg"
            if os.path.exists(image_path) and os.path.exists(image_HC_path)==False:
                image = cv2.imread(image_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                b,g,r = cv2.split(image)
                
                kernel=7
                b=cv2.medianBlur(b,kernel)
                g=cv2.medianBlur(g,kernel)
                r=cv2.medianBlur(r,kernel)
                
                bhc=self.filtering_extreme_values(b)
                ghc=self.filtering_extreme_values(g)
                rhc=self.filtering_extreme_values(r)
                
                img = cv2.merge((rhc,ghc,bhc))
                cv2.imwrite(image_HC_path,img)
                
    def filtering_extreme_values(self,v):  
        v=v.astype(np.float32)
        spread=20
        liminf=140.-spread
        limsup=140.+spread

        mid=140.

        a=mid/(mid-liminf)
        b=-a*liminf
    
        cond1=v<mid
        v[cond1]=a*v[cond1]+b
        
        a=(mid-255)/(mid-limsup)
        b=255-a*limsup
        
        cond2=v>mid
        v[cond2]=a*v[cond2]+b
    
        v[v>255]=255
        v[v<0]=0
    
        return v.astype(np.uint8)
    
    def create_pdf(self):
        self.pdf = FPDF('L', 'cm', (17,30))
        self.pdf.set_margins(0, 0, 0)
        
        if os.path.exists("temp"):
            shutil.rmtree("temp")
        os.mkdir("temp")
        
        for i in range(self.Nwafer):
            path=self.filename+"\Wafer_"+str(i).zfill(2)+"\Analysed_picture"
            relative_path="Wafer_"+str(i).zfill(2)+"\Analysed_picture\\"
            directories=os.listdir(path)
            for directory in directories:
                if directory != "full_image.jpg":
                    self.add_flake(i,path+"\\"+directory,relative_path+directory)
        
        self.pdf.output(self.filename+'/report.pdf', 'F')
        print("done")
        
    def add_flake(self,wafer,path,relative_path):
        self.pdf.add_page()
        self.pdf.set_font('Arial', 'B', 16)
        
        flake_number=relative_path.split("_")[-1]
        
        
        files=os.listdir(path)
        for i in range(len(files)):
            if files[i][0:3]=="log":
                log = open(path+"\\"+files[i], "r")
                log_lines=log.read().split("\n")
                X=log_lines[0].split("\t")[1]
                Y=log_lines[1].split("\t")[1]
                X=X.replace('m','')
                X=X.replace(' ','')
                Y=Y.replace('m','')
                Y=Y.replace(' ','')
        
        files.remove("AI.jpg")
        self.pdf.cell(30,2, 'Wafer '+str(wafer).zfill(2)+' - Flake '+flake_number+' - Position ('+X+','+Y+')', align = "C", ln=1)
        
        figure1,figure2,figure3="","",""        
        name1,name2,name3="","",""
        
        
        for i in range(len(files)):
            try:
                if files[i].split("_")[1]=="zoom" and files[i][-5]!="c":
                    figure2=files[i]
                    name2=files[i].split("_")[0]+" zoom"
            except:
                print("manual pic")
        for i in range(len(files)):
            try:
                if files[i].split("_")[1]=="zoom" and files[i][-5]=="c":
                    figure1=files[i]
                    name1=files[i].split("_")[0]+" zoom"
            except:
                print("manual pic")
                
        for i in range(len(files)):
            if files[i][0:6]=="50x_HC":
                figure1=files[i]
                name1="high contrast"
        for i in range(len(files)):
            if files[i][0:7]=="100x_HC":
                figure1=files[i]
                name1="high contrast"
        for i in range(len(files)):
            if files[i][0:3]=="loc":
                figure3=files[i]
                name3="localization"
        
        for i in range(len(files)):
            if files[i][0:6]=="50x_BF":
                figure2=files[i]
                name2="50X"
        for i in range(len(files)):
            if files[i][0:6]=="50x_ID":
                figure1=files[i]
                name1="Thickness"
        for i in range(len(files)):
            if files[i][0:6]=="50x_DF":
                figure3=files[i]
                name3="Dark Field"
        
        for i in range(len(files)):
            if files[i][0:7]=="100x_BF":
                figure2=files[i]
                name2 = "100X"
        for i in range(len(files)):
            if files[i][0:7]=="100x_ID":
                figure1=files[i]
                name1="Thickness"
        for i in range(len(files)):
            if files[i][0:7]=="100x_DF":
                figure3=files[i]
                name3="Dark Field"
        
        
        figure1=path+"\\"+figure1
        figure2=path+"\\"+figure2
        figure3=path+"\\"+figure3
        
        
        fig1="temp/fig_"+str(wafer)+"_"+flake_number+"1.jpg"
        fig2="temp/fig_"+str(wafer)+"_"+flake_number+"2.jpg"
        fig3="temp/fig_"+str(wafer)+"_"+flake_number+"3.jpg"
        
        try:
            im_temp=cv2.imread(figure1)
            cv2.imwrite(fig1,im_temp,[cv2.IMWRITE_JPEG_QUALITY, 50])
            self.pdf.cell(10,1.5,name1, align='C')
            self.pdf.image(fig1, x = 0.01, y = 4, w = 9.98, h = 0, type = 'JPG', link = relative_path)
        except:
            print("image missing",name1,"1")
        
        try:
            im_temp=cv2.imread(figure2)
            cv2.imwrite(fig2,im_temp,[cv2.IMWRITE_JPEG_QUALITY, 50])
            self.pdf.cell(10,1.5,name2, align='C')
            self.pdf.image(fig2, x = 10.01, y = 4, w = 9.98, h = 0, type = 'JPG', link = relative_path)
        except:
            print("image missing",name2,"2")

        try:
            im_temp=cv2.imread(figure3)
            cv2.imwrite(fig3,im_temp,[cv2.IMWRITE_JPEG_QUALITY, 50])
            self.pdf.cell(10,1.5,name3, align='C')
            self.pdf.image(fig3, x = 20.01, y = 4, w = 9.98, h = 0, type = 'JPG', link = relative_path)
        except:
            print("image missing",name3,"3")
        