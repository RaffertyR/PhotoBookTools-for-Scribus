#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
VERSION: 1.0 of 2021-07-31
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
This script loops over every selected object, and for all image frames that
are not empty, it scales the image proportionally, filling the entire frame
with your image. This means that some of the image will be cropped by
the frame in either the horizontal or vertical dimension. Then the scaled
image will be centered in its frame.

This is an adapted version of an old Scribus script from Jeremy Brown.
"""
##################################################

from scribus import *

if haveDoc():
    nbrSelected = selectionCount()
else:
    scribus.messageBox("Error: No document open",
        "Please, create (or open) a document before running this script ...",
        scribus.ICON_WARNING,scribus.BUTTON_OK)
    sys.exit(1)
    
scribus.progressTotal(nbrSelected)
# since there is an issue with units other than points, we switch to points then restore later.
restore_units = scribus.getUnit()
scribus.setUnit(0)

objList = []
for i in range(nbrSelected):
    objList.append(getSelectedObject(i))

for i in range(nbrSelected):
    try:
        scribus.progressSet(i)
        obj = objList[i]
        setScaleImageToFrame(True, False, obj)
        setScaleImageToFrame(False, False, obj)
        scale = getImageScale(obj)
        max_scale = max(scale)
        setImageScale(max_scale, max_scale, obj)
        # center scaled image in frame:
        frameX, frameY = getPosition(obj)
        frameWidth, frameHeight = getSize(obj)
        setImageOffset((frameWidth * (1 - max_scale / scale[0])) / 2,
            (frameHeight * (1 - max_scale / scale[1])) / 2, obj)
        docChanged(1)
        setRedraw(True)
    except:
        nothing = "nothing"

scribus.setUnit(restore_units)
scribus.progressReset()
