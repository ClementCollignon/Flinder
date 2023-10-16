import cv2MAXPIX
import cv2
import numpy as np
from scipy.interpolate import interp1d

def extract_kbgr_from_image(image):
    b,g,r = cv2.split(image)
    k = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return k.astype("uint8"),b.astype("uint8"),g.astype("uint8"),r.astype("uint8")

def trim(x,y,xmin,xmax):
    y=y[x>xmin]
    x=x[x>xmin]
    y=y[x<xmax]
    x=x[x<xmax]
    return x,y

def read_calibration(path_calibration):
    D=np.genfromtxt(path_calibration)
    thickness=D[:,0]
    k , k_error = D[:,1] , D[:,5]
    b , b_error = D[:,2] , D[:,6]
    g , g_error = D[:,3] , D[:,7]
    r , r_error = D[:,4] , D[:,8] 
    return thickness,k,b,g,r,k_error,b_error,g_error,r_error

def read_calibration_details(path_calibration_details):
    D=np.genfromtxt(path_calibration_details)
    layer_or_thickness=int(D[0])
    number_of_intervals=int(D[1])
    use_k=int(D[2])
    use_b=int(D[3])
    use_g=int(D[4])
    use_r=int(D[5])
    return layer_or_thickness, number_of_intervals, use_k, use_b, use_g, use_r
    
def find_minmax_calibration_segment(thickness,cal,tmin,tmax,error):
    
    t_temp = np.linspace(tmin,tmax,10000)
    cal_interp = interp1d(thickness,cal)(t_temp)
    error_interp = interp1d(thickness,error)(t_temp)
    
    t_trimed,cal_interp = trim(t_temp,cal_interp,tmin,tmax)
    t_trimed,error_interp = trim(t_temp,error_interp,tmin,tmax)        
    
    minimum_of_calibration = np.min(cal_interp)
    error_at_minimum_of_calibration = error_interp[np.argmin(cal_interp)]
    cal_min = minimum_of_calibration - error_at_minimum_of_calibration
    
    maximum_of_calibration = np.max(cal_interp)
    error_at_maximum_of_calibration = error_interp[np.argmax(cal_interp)]
    cal_max = maximum_of_calibration + error_at_maximum_of_calibration
    
    return int(np.round(cal_min,0)),int(np.round(cal_max,0))


def get_mask_values(path_calibration_folder):
    
    path_calibration_details = path_calibration_folder + "/calibration_details.dat"
    Data = read_calibration_details(path_calibration_details)
    number_of_intervals = Data[1]
    
    path_calibration = path_calibration_folder + "/calibration.dat"
    thickness, k, b, g, r, k_error, b_error, g_error, r_error = read_calibration(path_calibration)
    
    thickness_segments=np.linspace(min(thickness),max(thickness),number_of_intervals+1)
    
    #create mask values for each thickness
    mask_values=[]
    for i in range(number_of_intervals):
        tmin,tmax=thickness_segments[i],thickness_segments[i+1]
        kmin,kmax=find_minmax_calibration_segment(thickness,k,tmin,tmax,k_error)
        bmin,bmax=find_minmax_calibration_segment(thickness,b,tmin,tmax,b_error)
        gmin,gmax=find_minmax_calibration_segment(thickness,g,tmin,tmax,g_error)
        rmin,rmax=find_minmax_calibration_segment(thickness,r,tmin,tmax,r_error)
        mask_values.append([kmin,kmax,bmin,bmax,gmin,gmax,rmin,rmax])
    
    return mask_values