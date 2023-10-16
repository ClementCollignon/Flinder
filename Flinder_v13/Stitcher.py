import threading
import os
import numpy as np
import cv2MAXPIX
import cv2
import PIL
from PIL import Image, ImageTk
import multiprocessing as mp
from scipy.optimize import curve_fit
import skimage.measure
import functions

PIL.Image.MAX_IMAGE_PIXELS = 11660313600
MID_SPECTRUM_VALUE = 255./2.
PNG_COMP = [cv2.IMWRITE_PNG_COMPRESSION, 2]

config = functions.get_config()
(MAIN_FOLDER, SCREEN_SCALING, ZEROS, 
 FOV, OVERLAP, SCALE, JPG,
 LOW_RES, HIGH_RES, CCD,
 OFFSET_X, OFFSET_Y, OFFSET_Z) = config

def filtering_extreme_values(v,newv): 
    v=v.astype(np.float32)
    newv=newv.astype(np.float32)        
    a0=(v/newv*MID_SPECTRUM_VALUE)
    a0[a0<0]=0
    a0[a0>255]=255
    
    bining=np.arange(50,200.5,0.5)
    hist=np.histogram(a0,bining)[0]
    most_probable=bining[np.argmax(hist)]
    
    if most_probable>50:
        a0n=a0/most_probable*MID_SPECTRUM_VALUE
        a0n[a0n>255]=255
    else:
        a0n=np.copy(a0)
    
    return a0n.astype(np.uint8)


def local_averaging(channel,square):
    channel = cv2.blur(channel,(square,square))
    channel=channel.astype("uint8")
    return channel
    
                
def color_correct(i,list_im,list_out,new_b,new_g,new_r):
    image = cv2.imread(list_im[i])
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    b,g,r = cv2.split(image)
    
    b=filtering_extreme_values(b,new_b)
    g=filtering_extreme_values(g,new_g)
    r=filtering_extreme_values(r,new_r)
        
    img = cv2.merge((r,g,b))
    cv2.imwrite(list_out[i],img)
    
    return i

def median_val(C,h,w):
    new_c=np.zeros((h,w),dtype=np.uint16)
    np.median(C,axis=2,out=new_c)
    return new_c
    
def extract_mean_value(i,j,Mat_im):                    
    image = cv2.imread(Mat_im[j][i])
    
    #perform a maxPooling on the image with 5px*5px*1channel clusters
    image = skimage.measure.block_reduce(image, (5,5,1), np.max)

    #get the derivative along x and y directions
    sobx = cv2.Sobel(image,cv2.CV_64F,1,0,ksize=3)
    soby = cv2.Sobel(image,cv2.CV_64F,0,1,ksize=3)
    image = ( np.abs(sobx) + np.abs(soby) ) / 2

    #perform again a maxPooling on the derivated image with 5pc*5pc*3channels cluster
    image = skimage.measure.block_reduce(image, (5,5,3), np.max)

    #return the mean of the pooled derivative
    sharpness_score = np.mean(image)
    return sharpness_score

class ThreadedStitcher(threading.Thread):
    def __init__(self, queue_stitch,N,M,filename,nosepiece,scaling_factor,indice,load,overlap):
        threading.Thread.__init__(self)
        self.N=N
        self.M=M
        self.filename=filename
        self.queue_stitch = queue_stitch
        self.nosepiece=nosepiece
        self.scaling_factor=scaling_factor
        self.indice=indice
        self.load=load
        alpha=1.5
        factor={'5x':1,'10x':2,'20x':4,'50x':10,'100x':20}
        self.compression=factor[nosepiece]*alpha
        self.micron_per_pixel=SCALE/factor[nosepiece]
        self.overlap=overlap
        
    def run(self):
        is_there_picture=False
        if self.load==1:
            is_there_picture=os.path.exists(self.filename+"/Analysed_picture/full_image.jpg")
        
        if is_there_picture and self.load==1:
            print("Wafer "+str(self.indice).zfill(2)+"\nTask finished")
            self.queue_stitch.put([3,"Wafer "+str(self.indice).zfill(2)+"\nTask finished"])
        
        else:
            color_correction_needed=1
            try:
                os.mkdir(self.filename+"/Color_Corrected_Pictures")
            except OSError:
                if len(os.listdir(self.filename+"/Color_Corrected_Pictures")) == self.N*self.M:
                    color_correction_needed=0
                else:
                    color_correction_needed=1
            else:
                color_correction_needed=1
            
            
            if color_correction_needed==1:
                I=0
                list_im=[]
                list_out=[]
                for j in range(self.M):
                    for i in range(self.N):
                        list_im.append(self.filename+"/Raw_pictures/pic"+str(I).zfill(ZEROS)+'.jpg')
                        list_out.append(self.filename+"/Color_Corrected_Pictures/pic"+str(I).zfill(ZEROS)+'.jpg')
                        I+=1

                w=4908
                h=3264

                pourtour1=[i*self.M for i in range(1,self.N-1)]
                pourtour2=[i*self.M-1 for i in range(2,self.N)]
                pourtour3=[i for i in range(self.M)]
                pourtour4=[i for i in range((self.N-1)*self.M,self.N*self.M)]
                
                p=[]
                p.extend(pourtour1)
                p.extend(pourtour2)
                p.extend(pourtour3)
                p.extend(pourtour4)
                
                # p = np.arange(500)
                
                number_of_pictures=min(100,self.N*self.M-len(p))
                
                p=np.asarray(p)
                color_correction_indice=np.arange(self.M*self.N)
                color_correction_indice=np.delete(color_correction_indice,p)
                
                B=np.zeros((h,w,number_of_pictures),dtype=np.uint8)
                G=np.zeros((h,w,number_of_pictures),dtype=np.uint8)
                R=np.zeros((h,w,number_of_pictures),dtype=np.uint8)
                
                
                for i in range(number_of_pictures):
                    self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nComputing color\ndistribution for\neach pixel\n"+str(int(round((i)/number_of_pictures*100,0)))+" %"])
                    try:
                        ii=color_correction_indice[i]
                        image = cv2.imread(list_im[ii])
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        b,g,r = cv2.split(image)

                        B[:,:,i]=b
                        G[:,:,i]=g
                        R[:,:,i]=r

                    except Exception as e:
                        print(e)
                        self.queue_stitch.put([4,"Wafer "+str(self.indice).zfill(2)+"\nPictures missing"])
                
                self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nComputing background\ncorrection"])
                num_workers = 3
                pool = mp.Pool(num_workers)
                
                handler = []
                handler.append(pool.apply_async(median_val, args = (B,), kwds={'h': h,'w': w}))
                handler.append(pool.apply_async(median_val, args = (G,), kwds={'h': h,'w': w}))
                handler.append(pool.apply_async(median_val, args = (R,), kwds={'h': h,'w': w}))
                
                new_b=handler[0].get()
                new_g=handler[1].get()
                new_r=handler[2].get()
                
                # cv2.imwrite("bkg.jpg",new_b)
                num_workers = min(10,mp.cpu_count()-1)
                pool = mp.Pool(num_workers)
                handler=[]
                
                pixel_width=(1-self.overlap)*w
                pixel_height=(1-self.overlap)*h
                
                for i in range(self.N*self.M):
                    handler.append(pool.apply_async(color_correct, args = (i,), kwds={'list_im': list_im,'list_out': list_out,'new_b':new_b,'new_g':new_g,'new_r':new_r}))
                
                for i in range(self.N*self.M):
                    ii=handler[i].get()
                    
                    self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nColor correcting\n"+str(int(round(ii/self.N/self.M*100,0)))+" %"])
                
                pool.close()
                pool.join()
                
 
            path=self.filename+"/Color_Corrected_Pictures/"
            Mat_im=[]
            I=0
        
            for j in range(self.M):
                list_im=[]
                for i in range(self.N):
                    list_im.append(path+'pic'+str(I).zfill(ZEROS)+'.jpg')
                    I+=1
                    
                Mat_im.append(list_im)
                    
            width, height = PIL.Image.open(list_im[0]).size 
            xtot=self.overlap*width
            ytot=self.overlap*height
            left,right, top,bottom=xtot/2,width-xtot/2,ytot/2,height-ytot/2

            reduced_size_px_x,reduced_size_px_y=PIL.Image.open(list_im[0]).crop((left, top, right, bottom)).size
            center_px_x=int(reduced_size_px_x/2)
            center_px_y=int(reduced_size_px_y/2)
        
            total_px_x=reduced_size_px_x*self.N
            x_micron,y_micron,z_focus,x_px,y_px,mean_v=[],[],[],[],[],[]
            counter=0
            
            pos_file = os.listdir(self.filename+"/Position_files")
            file = open(self.filename+"/Position_files/"+pos_file[1], 'r',encoding='utf-16-le')
            Lines = file.readlines()
    
            myline=0
            while Lines[myline]!="Recorded Data\n":
                myline+=1
            begining,xt,yt,zt,ludl,exp,end=Lines[myline+2].split("\t")
            
            
            for j in range(self.M):
                for i in range(self.N):
                    counter+=1
                    
                    if j%2==0:
                        alpha=self.N-i
                    else:
                        alpha=i+1
                    
                    x_px_t = int((-center_px_x+alpha*reduced_size_px_x)/self.compression)
                    y_px_t = int((center_px_y+j*reduced_size_px_y)/self.compression)
                    x_px.append(x_px_t)
                    y_px.append(y_px_t)

                    try:
                        file = open(self.filename+"/Position_files/pos"+str(counter-1)+".dat", 'r',encoding='utf-16-le')
                        Lines = file.readlines()
                
                        myline=0
                        while Lines[myline]!="Recorded Data\n":
                            myline+=1
                        begining,xt,yt,zt,ludl,exp,end=Lines[myline+2].split("\t")
                    except:                  
                        xt = x_px_t*self.compression*self.micron_per_pixel
                        yt = y_px_t*self.compression*self.micron_per_pixel
                        
                    x_micron.append(xt)
                    y_micron.append(yt)
                    z_focus.append(zt)
            
            num_workers = mp.cpu_count()-1
            pool = mp.Pool(num_workers)
            handler=[]
            for j in range(self.M):
                for i in range(self.N):
                    handler.append(pool.apply_async(extract_mean_value, args = (i,j,), kwds={'Mat_im': Mat_im}))
                
            for i in range(self.N*self.M):
                mean_v.append(handler[i].get())
                self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nExtracting Positions\n"+str(int(round(i/self.N/self.M*100,0)))+" %"])
            pool.close()
            pool.join()
            
            W=[x_px,y_px,x_micron,y_micron,z_focus,mean_v]
            W=np.asarray(W)
            W=np.transpose(W)
            W=W.astype(np.float32)
            np.savetxt(self.filename+"/Position_files/coordinates.dat",W,header='x(pixel)\ty(pixel)\tx(micron)\ty(micron)\tz(micron)\tmean_intensity')
        
            IM=[]
            count=0
            for j in range(self.M):
                list_im = Mat_im[j]
                if j%2==0: list_im=list_im[::-1]
                imgs=[]
                for i in range(len(list_im)):
                    count+=1
                    left,right, top,bottom=xtot/2,width-xtot/2,ytot/2,height-ytot/2
                    try:
                        img=PIL.Image.open(list_im[i]).crop((left, top, right, bottom))
                        width_croped, height_croped = img.size
                        size=(int(width_croped/self.compression),int(height_croped/self.compression))
                        imgs.append(img.resize(size))
                    except:
                        self.queue_stitch.put([4,"Wafer "+str(self.indice).zfill(2)+"\nPictures missing"])
                    percentage=str(int(count/(self.M*self.N)*100))
                    text="Wafer "+str(self.indice).zfill(2)+"\nLoading and cropping:\n"+percentage+" %"
                    self.queue_stitch.put([1,text])
                    
                imgs_comb = np.hstack([np.asarray( i ) for i in imgs])
                imgs_comb = imgs_comb.astype(np.uint8)
                IM.append(imgs_comb)

            try:
                os.mkdir(self.filename+"/Analysed_picture")
       
            except OSError:
                print ("every folder already exist")
        
            else:
                print ("folder created")

            self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nStitching images"])
            
            imgs_comb = np.vstack(IM)
            imgs_comb = imgs_comb.astype(np.uint8)
            imgs_comb = PIL.Image.fromarray(imgs_comb)
            self.queue_stitch.put([2,"Wafer "+str(self.indice).zfill(2)+"\nSaving stitched image\n(it might take time)"])
            imgs_comb.save(self.filename+"/Analysed_picture/full_image.jpg",quality=85)
        
            del imgs_comb
        
            self.queue_stitch.put([3,"Wafer "+str(self.indice).zfill(2)+"\nTask finished"])
 
class ThreadedLoader(threading.Thread):
    def __init__(self, queue_load,filename,scaling_factor,Nwafer):
        threading.Thread.__init__(self)
        self.filename=filename
        self.queue_load = queue_load
        self.scaling_factor=scaling_factor
        self.Nwafer=Nwafer
        
    def run(self):
        
        self.queue_load.put([0,"loading images (it can take time)"])
        grid=np.ceil(np.sqrt(self.Nwafer))
        dim=470/self.scaling_factor/grid
        
        X0=1113/self.scaling_factor
        Y0=143/self.scaling_factor
        counter=0
        step=int(dim)
        for i in range(self.Nwafer):
            print("loading wafer",i)
            load_wafer = Image.open(self.filename+"/Wafer_"+str(i).zfill(2)+"/Analysed_picture/full_image.jpg")
            load_wafer = load_wafer.resize((int(dim), int(dim)), Image.ANTIALIAS)
            render_wafer = ImageTk.PhotoImage(load_wafer)
            self.queue_load.put([1,render_wafer,int(X0),int(Y0)])
            X0+=step
            counter+=1
            if counter==grid:
                counter=0
                Y0+=step
                X0-=grid*step
            
        self.queue_load.put([2])
        
