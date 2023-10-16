# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 17:39:31 2021

@author: Nikon-fablab
"""

import numpy as np
from matplotlib import pyplot as plt

D=np.genfromtxt("calibration.dat")
# layers	k	b	g	r	kerror	berror	gerror	rerror
l,k,b,g,r,kerr,berr,gerr,rerr = D[:,0],D[:,1],D[:,2],D[:,3],D[:,4],D[:,5],D[:,6],D[:,7],D[:,8]

aaa = 127.5/140

k=np.round(k*aaa,0)
b=np.round(b*aaa,0)
g=np.round(g*aaa,0)
r=np.round(r*aaa,0)

print(k)

# k=np.int(np.round(k*aaa,0))
# b=np.int(np.round(b*aaa,0))
# g=np.int(np.round(g*aaa,0))
# r=np.int(np.round(r*aaa,0))

W=np.asarray([l,k,b,g,r,kerr,berr,gerr,rerr])
W=np.transpose(W)

np.savetxt("ttt.dat",W,fmt='%i')