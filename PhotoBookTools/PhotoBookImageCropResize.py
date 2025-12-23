#! /usr/bin/env python
#-*- coding: utf-8 -*-
'''
VERSION: 1.0 of 2021-07-31
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
This script loops over every selected object, and for all image
frames that are not empty, it will crop and resize a COPY of
the image file and add the suffix "_cropped" to it.

This is a reworked version of an old Scribus script 
'Image_crop_resize_and_color_conversion_GUI.py' of 
prof. MS. José Antonio Meira da Rocha of 2011-01-05a with
License GPL.

IMPORTANT REMARK: this script needs the Pillow (PIL) package
to be installed in (Scribus) Python (https://python-pillow.org).
'''
##################################################
# imports
import sys, os

try:
    from scribus import *
except ImportError:
    scribus.messageBox("Script failed",
        "This Python script can only be run from within Scribus.",
        scribus.ICON_WARNING,scribus.BUTTON_OK)
    sys.exit(1)

try:
    from tkinter import * # python 3 syntax
    #from tkinter import messagebox
    from tkinter import ttk # for ComboBox
except ImportError:
    print("This script requires Python Tkinter properly installed.")
    messageBox('Script failed',
               'This script requires Python Tkinter properly installed.',
               ICON_CRITICAL)
    sys.exit(1)
    
try:
    # if PIL-package installed but not found, uncomment one of following lines:
    #sys.path.append('C:\\Users\\Python37\\Lib\\site-packages')  # Windows
    #sys.path.append('/usr/lib/python3/dist-packages')   # Linux
    from PIL import Image
except ImportError:
    scribus.messageBox("Script failed",
        "This script needs the PIL (Pillow) package \n\
        (compatible to your Python version) to be installed.",
        scribus.ICON_CRITICAL,scribus.BUTTON_OK)
    sys.exit(1)
    
##################################################
class ScPhotoBookImageCropResize:
    """ PhotoBookImageCropResize itself."""

    def __init__(self, resolution='300', mode='RGB', fileFormat='.jpg', resample='BICUBIC'):
        """ Setup basic things """
        self.resolution = resolution
        if mode == 'B&W':
            self.mode = '1'
        elif mode == 'Grey scale':
            self.mode = 'L'
        else:
            self.mode = mode
        self.fileFormat = fileFormat
        self.resample = resample

    def handleImage(self, imageFrame):
        """ Crop, resize, convert and save Image function."""
        imgFile = scribus.getImageFile(imageFrame)
        try:
            image = Image.open(imgFile)
            # Calculate DPI
            unit = scribus.getUnit()
            scribus.setUnit(UNIT_INCHES)
            imageResolution = int(self.resolution)
            frameSizeX,frameSizeY = scribus.getSize(imageFrame)
            newWidth = int(frameSizeX * imageResolution)
            newHeight = int(frameSizeY * imageResolution)
            scribus.setUnit(UNIT_POINTS)

            # Calculate cropping
            imageXOffset = scribus.getProperty(imageFrame,'imageXOffset')
            imageYOffset = scribus.getProperty(imageFrame,'imageYOffset')
            frameSizeX,frameSizeY = scribus.getSize(imageFrame)
            imageXScale = scribus.getProperty(imageFrame,'imageXScale')
            imageYScale = scribus.getProperty(imageFrame,'imageYScale')
            imageSizeX, imageSizeY = image.size

            # calculate crop box
            left = int(imageXOffset * -1)
            top = int(imageYOffset * -1)
            right = int(left + (frameSizeX / imageXScale))
            bottom = int(top + (frameSizeY / imageYScale))
        
            # Limit crop to image area 
            # (avoid black areas due to crop bigger than image)
            if right > imageSizeX: 
                right = imageSizeX
            if bottom > imageSizeY: 
                bottom = imageSizeY
            if imageXOffset > 0: 
                left = 0
            if imageYOffset > 0: 
                top = 0
        
            # Recalculate new image dimensions
            # to fit proportionaly
            proportionX = newWidth / (right-left)
            proportionY = newHeight / (bottom-top)
            if proportionX > proportionY:
                newHeight = int(newWidth * (bottom-top) /(right-left))
            else:
                newWidth = int(newHeight * (right-left) / (bottom-top))

            # Cropping
            newImage = image.crop((left,top,right,bottom))
        
            # Resize
            if self.resample == 'BICUBIC':
                newImage = newImage.resize((newWidth,newHeight),Image.BICUBIC)
            elif self.resample == 'LANCZOS':
                newImage = newImage.resize((newWidth,newHeight),Image.LANCZOS)
            else:
                newImage = newImage.resize((newWidth,newHeight),Image.BILINEAR)
        
            # Color space conversion
            if newImage.mode != self.mode:
                newImage = newImage.convert(self.mode)

            # Save new image with suffix '_cropped'
            scribus.setUnit(unit)  # restore original document unit
            name,ext = os.path.splitext(imgFile)
            newImageFile = (name + '_cropped'+ self.fileFormat)
            if os.path.exists(newImageFile):
                overwrite = scribus.messageBox('Warning:','Overwrite '+newImageFile+'?',
                    ICON_WARNING, button2=scribus.BUTTON_NO, button1=scribus.BUTTON_YES)
                if int(overwrite) > 16384:  # BUTTON_NO was clicked
                    return
            newImage.save(newImageFile, dpi=(imageResolution,imageResolution))

            # Reload new image in image frame
            scribus.loadImage(newImageFile,imageFrame)
            
        except:
            scribus.messageBox('Warning:', imgFile + '\n will be skipped (processing error).',
                ICON_WARNING, BUTTON_OK)
        return
        
    def handleSelection(self):
        """ Handle selected frames."""
        selectionList = []
        nbrSelected = scribus.selectionCount()
        scribus.progressTotal(nbrSelected)
        if nbrSelected == 0:
            scribus.messageBox('Warning', 'Nothing selected', ICON_WARNING)
        else:    # one or more items selected
            for i in range (0, selectionCount()):
                scribus.progressSet(i)
                obj = getSelectedObject(i)
                selectionList.append(obj)
                objectType = getObjectType(obj)
                if objectType == 'Group':
                    messageBox('Warning', 'Grouped items will be skipped.\nPlease ungroup "'
                        +obj+'" and try again.', ICON_WARNING)
                elif (objectType == 'ImageFrame') and (getImageFile(obj) != ""):
                    self.handleImage(obj)
                else: # not an image frame -> skip
                    pass
        return

##################################################
class TkPhotoBookImageCropResize(Frame):
    """ GUI interface for PhotoBookImageCropResize.py with Tkinter"""

    def __init__(self, master=None):
        """ Setup the dialog """
        Frame.__init__(self, master)
        self.grid()
        self.master.resizable(0, 0)
        self.master.title('Crop and Resize')

        # define variables
        self.statusVar = StringVar(self, value='Enter Options and press OK.')
        self.statusLabel = Label(self, fg="red", textvariable=self.statusVar)
        self.resolutionLabel = Label(self, text='Resolution: ')
        self.resolutionVar = ttk.Combobox(self, values = ['72','75','96','144','150',
           '200','288','300','600','1200'], width=9)
        self.modeLabel = Label(self, text='Color mode: ')
        self.modeVar = ttk.Combobox(self, values = ['RGB','CMYK','B&W','Grey scale'], width=9)
        self.fileFormatLabel = Label(self, text='File format: ')
        self.fileFormatVar = ttk.Combobox(self, values = ['.jpg','.png','.tif'], width=9)
        self.resampleLabel = Label(self, text='Resampling: ')
        self.resampleVar = ttk.Combobox(self, values = ['BICUBIC','BILINEAR','LANCZOS'], width=9)
        self.okButton = Button(self, text="OK", width=6, command=self.okButton_pressed)
        self.cancelButton = Button(self, text="Cancel", command=self.quit)

        # set default values
        self.resolutionVar.set('300')
        self.modeVar.set('RGB')
        self.fileFormatVar.set('.jpg')
        self.resampleVar.set('BICUBIC')
        
        # make interface layout
        self.columnconfigure(0, pad=6)
        currRow = 0
        self.statusLabel.grid(column=0, row=currRow, columnspan=2)
        currRow += 1
        self.resolutionLabel.grid(column=0, row=currRow, sticky=S+E)
        self.resolutionVar.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.modeLabel.grid(column=0, row=currRow, sticky=S+E)
        self.modeVar.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.fileFormatLabel.grid(column=0, row=currRow, sticky=S+E)
        self.fileFormatVar.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.resampleLabel.grid(column=0, row=currRow, sticky=S+E)
        self.resampleVar.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.rowconfigure(currRow, pad=6)
        self.cancelButton.grid(column=0, row=currRow, sticky=E)
        self.okButton.grid(column=1, row=currRow, sticky=W) 

    def okButton_pressed(self):
        """ Do PhotoBookImageCropResize """
        
        spbicr = ScPhotoBookImageCropResize(self.resolutionVar.get(),
            self.modeVar.get(), self.fileFormatVar.get(), self.resampleVar.get())
        self.master.withdraw()
        err = spbicr.handleSelection()

        if err != None:
            self.master.deiconify()
            self.statusVar.set(err)
        else:
            self.quit()

    def quit(self):
        self.master.destroy()

##################################################
# Start program

def main():
    if scribus.haveDoc() == 0:
        scribus.messageBox("Script failed",
            "Please open a Scribus document before running this script.",
            scribus.ICON_WARNING,scribus.BUTTON_OK)
        return
    
    try:
        scribus.statusMessage('Running script...')
        scribus.progressReset()
        unit = scribus.getUnit()
        root = Tk()
        app = TkPhotoBookImageCropResize(root)
        root.mainloop()
    finally:
        if scribus.haveDoc():
            scribus.redrawAll()
        scribus.setUnit(unit)
        scribus.statusMessage('Done.')
        scribus.progressReset()

if __name__ == '__main__':
    main()
