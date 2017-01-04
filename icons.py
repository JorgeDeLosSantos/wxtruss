# -*- coding: utf-8 -*-
#
# wxtruss 0.1.0
# License: MIT License
# Author: Pedro Jorge De Los Santos
# E-mail: delossantosmfq@gmail.com

import glob
from wx.tools.img2py import img2py

if __name__=='__main__':
    for img in glob.glob("img/*.png"):
        img2py(img,"iconos.py", append=True)
