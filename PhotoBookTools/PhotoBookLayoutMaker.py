#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
VERSION: 1.0 of 2021-07-31
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
(tested on Scribus 1.5.6+ with Python 3 on Windows 10 and Linux).

PhotoBookLayoutMaker is a script for creating Image Frames in Scribus in
a fast and flexible way. Many options are available in the interface.
"""
##################################################
# imports
import sys,  platform, os
from configparser import ConfigParser

try:
    from scribus import *
except ImportError:
    print("This Python script is written for the Scribus \
      scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

python_version = platform.python_version()
if python_version[0:1] != "3":
    print("This script runs only with Python 3.")
    messageBox("Script failed",
        "This script runs only with Python 3.",
        ICON_CRITICAL)	
    sys.exit(1)

try:
    from tkinter import * # python 3 syntax
    from tkinter import messagebox
    from tkinter import ttk # for ComboBox

except ImportError:
    print("This script requires Python Tkinter properly installed.")
    messageBox('Script failed',
               'This script requires Python Tkinter properly installed.',
               ICON_CRITICAL)
    sys.exit(1)

##################################################
class ScPhotoBookLayoutMaker:
    """ PhotoBookLayoutMaker itself."""

    def __init__(self, cols=0, rows=0, gap=0.0, aspectratio=0, scale=0.0,
        alignh="", alignv="", captionh=0.0, removeframe=1, alternateborder=0):
        """ Setup basic things """
        # params
        self.cols = cols
        self.rows = rows
        self.gap = gap
        self.aspectratio = aspectratio
        self.scale = scale / 100
        self.alignh = alignh
        self.alignv = alignv
        self.captionh = captionh
        self.removeframe = removeframe
        self.alternateborder = alternateborder        
        defineColorCMYK("frameFillColor", 0, 0, 0, 64) # default is Light Grey

        # create 2 frame border styles (line width is measured in points)
        defineColorCMYK("frameBorderColor1", 0, 0, 0, 200) # default is Dark Grey
        self.frameBorderLineStyle1 = "frameBorderLineStyle1"
        createCustomLineStyle(self.frameBorderLineStyle1, [
            {
                'Color': "frameBorderColor1",
                'Width': 1
            }
        ]);
        defineColorCMYK("frameBorderColor2", 0, 0, 0, 0) # default is White
        self.frameBorderLineStyle2 = "frameBorderLineStyle2"
        createCustomLineStyle(self.frameBorderLineStyle2, [
            {
                'Color': "frameBorderColor2",
                'Width': 1
            }
        ]);

        # create character and paragraph style for caption text (if needed)
        if self.captionh != 0:
            unit = [pt, mm, inch, p, cm, c]   # Scribus units
            self.cStyleCaption = "characterStyleCaptionText"
            scribus.createCharStyle(name=self.cStyleCaption,
                fontsize=abs(self.captionh / unit[getUnit()]) // 1.5)
            self.pStyleCaption = "paragraphStyleCaptionText"
            scribus.createParagraphStyle(name=self.pStyleCaption, linespacingmode=0,
                alignment=ALIGN_CENTERED, charstyle=self.cStyleCaption)

    def createLayout(self):
        """ Draw image frame(s) within a rectangular selection or within page margins."""

        # current page measures
        pageWidth, pageHeight = getPageNSize(currentPage())
        marginTop, marginLeft, marginRight, marginBottom = getPageNMargins(currentPage())

        # source frame measures
        selectionList = []
        nbrSelected = scribus.selectionCount()
        if nbrSelected == 0:    # nothing selected: select area within page margins
            frameX = marginLeft
            frameY = marginTop
            frameWidth = pageWidth - marginLeft - marginRight
            frameHeight = pageHeight - marginTop - marginBottom
        else:    # one or more items selected
            for i in range (0, nbrSelected):
                obj = getSelectedObject(i)
                selectionList.append(obj)
                if (getProperty(obj, 'itemType')) == 12:
                    messageBox('Warning', 'Grouped items are not allowed as source.\nPlease ungroup "'
                        +obj+'" and try again.', ICON_CRITICAL)
                    sys.exit(1)
                frameX, frameY = getPosition(obj)
                frameWidth, frameHeight = getSize(obj)
                if i == 0:
                    posXmin, posYmin = getPosition(obj)
                    posXmax = posXmin + frameWidth
                    posYmax = posYmin + frameHeight                 
                else:
                    if frameX < posXmin:
                        posXmin = frameX
                    if frameY < posYmin:
                        posYmin = frameY
                    if frameX + frameWidth > posXmax:
                        posXmax = frameX + frameWidth
                    if frameY + frameHeight > posYmax:
                        posYmax = frameY + frameHeight
            frameX = posXmin
            frameY = posYmin
            frameWidth = posXmax - posXmin
            frameHeight = posYmax - posYmin

        # generated frame(s) measures
        newFrameW = (self.scale * frameWidth - (self.gap * (self.cols - 1))) / self.cols
        if self.captionh > 0:
            newFrameH = (self.scale * frameHeight - self.gap * (self.rows - 1) - self.captionh * self.rows) / self.rows
        else:
            newFrameH = (self.scale * frameHeight - (self.gap * (self.rows - 1))) / self.rows
        newAspectR = newFrameW / newFrameH

        # aspect ratio
        if self.aspectratio == 0.0:
            pass
        else:
            if self.aspectratio < newAspectR:
                newFrameW = newFrameH * self.aspectratio
            else:
                newFrameH = newFrameW / self.aspectratio

        # alignment
        if self.alignh == "Center":
            offsetX =  frameX + (frameWidth - newFrameW * self.cols - self.gap * (self.cols - 1))/2
        elif self.alignh == "Right":
            offsetX =  frameX + frameWidth - newFrameW * self.cols - self.gap * (self.cols - 1)
        else:
            offsetX = frameX
        if self.alignv == "Center":
            if self.captionh > 0:
                offsetY =  frameY + (frameHeight - (newFrameH + self.captionh) * self.rows - self.gap * (self.rows - 1))/2
            else:
                offsetY =  frameY + (frameHeight - newFrameH * self.rows - self.gap * (self.rows - 1))/2
        elif self.alignv == "Bottom":
            if self.captionh > 0:
                offsetY =  frameY + frameHeight - (newFrameH + self.captionh) * self.rows - self.gap * (self.rows - 1)
            else:
                offsetY =  frameY + frameHeight - newFrameH * self.rows - self.gap * (self.rows - 1)
        else:
            offsetY = frameY

        # border style
        if self.alternateborder:
            frameBorderLineStyle = self.frameBorderLineStyle2
        else:
            frameBorderLineStyle = self.frameBorderLineStyle1

        # draw the frames
        for i in range (1,  self.cols + 1):
            resetY = offsetY
            for j in range (1, self.rows + 1):
                newFrame = createImage(offsetX, offsetY, newFrameW, newFrameH)
                setFillColor("frameFillColor", newFrame)
                setCustomLineStyle(frameBorderLineStyle, newFrame)
                # draw caption text (if needed):
                if self.captionh != 0:
                    if self.captionh > 0:
                        captionTxt = createText(offsetX, offsetY + newFrameH, newFrameW, self.captionh)
                        offsetY = offsetY + self.captionh
                    else:    #self.captionh < 0
                        captionTxt = createText(offsetX, offsetY + newFrameH + self.captionh,
                            newFrameW, - self.captionh)
                    setText(newFrame, captionTxt)
                    selectObject(captionTxt)
                    setParagraphStyle(self.pStyleCaption, captionTxt)
                    setTextVerticalAlignment(ALIGNV_CENTERED, captionTxt)
                offsetY = offsetY + self.gap + newFrameH
            offsetX = offsetX + self.gap + newFrameW
            j = 1
            offsetY = resetY

        # remove source items
        if self.removeframe:
            for i in range (0, len(selectionList)):
                deleteObject(selectionList[i])
        else:
            pass

        return None

##################################################
class TkPhotoBookLayoutMaker(Frame):
    """ GUI interface for PhotoBook Layout Maker with Tkinter"""

    def __init__(self, master=None):
        """ Setup the dialog """
        Frame.__init__(self, master)
        self.grid()
        self.master.resizable(0, 0)
        self.master.title('Scribus PhotoBook Layout Maker')

        # define variables
        self.statusVar = StringVar(self, value='Enter Values and Options and press OK.')
        self.statusLabel = Label(self, fg="red", textvariable=self.statusVar)
        self.colsVar = StringVar()
        self.colsLabel = Label(self, text='Split/merge rectangle of selected item(s)\n\
        or area within page margins in columns:')
        self.colsEntry = Entry(self, textvariable=self.colsVar, width=9)
        self.rowsVar = StringVar()
        self.rowsLabel = Label(self, text=' and rows:')
        self.rowsEntry = Entry(self, textvariable=self.rowsVar, width=9)
        self.gapVar = DoubleVar()
        self.gapLabel = Label(self, text='Gap in document units:')
        self.gapEntry = Entry(self, textvariable=self.gapVar, width=9)
        self.aspectwidthVar = StringVar()
        self.aspectLabel = Label(self, text='New frame(s) aspect ratio (0=maximum area)')
        self.aspectwidthLabel = Label(self, text='width:')
        self.aspectwidthEntry = Entry(self, textvariable=self.aspectwidthVar, width=9)
        self.aspectheightVar = StringVar()
        self.aspectheightLabel = Label(self, text='  to height:')
        self.aspectheightEntry = Entry(self, textvariable=self.aspectheightVar, width=9)
        self.scaleVar = DoubleVar()
        self.scaleLabel = Label(self, text='New frame(s) scaling in % of selected rectangle:')
        self.scaleEntry = Entry(self, textvariable=self.scaleVar, width=9)
        self.alignhLabel = Label(self, text='New frame(s) alignment - horizontal:')
        self.alignhVar = ttk.Combobox(self, values = ["Left", "Center", "Right"], width=6)
        self.alignvLabel = Label(self, text=' vertical:')
        self.alignvVar = ttk.Combobox(self, values = ["Top", "Center", "Bottom"], width=6)
        self.captionVar = IntVar()
        self.captionLabel = Label(self, text='Text caption below image frame:')
        self.captionCheck = Checkbutton(self, variable=self.captionVar)
        self.captionhVar = DoubleVar()
        self.captionhLabel = Label(self, text='Caption height\n in document units:')
        self.captionhEntry = Entry(self, textvariable=self.captionhVar, width=9)
        self.removeframeVar = IntVar()
        self.removeframeLabel = Label(self, text='Remove source items:')
        self.removeframeCheck = Checkbutton(self, variable=self.removeframeVar)
        self.alternateborderVar = IntVar()
        self.alternateborderLabel = Label(self, text='Alternative border style for new frame(s):')
        self.alternateborderCheck = Checkbutton(self, variable=self.alternateborderVar)
        self.saveparamsVar = IntVar()
        self.saveparamsLabel = Label(self, text='Save above parameters for future use:')
        self.saveparamsCheck = Checkbutton(self, variable=self.saveparamsVar)

        self.okButton = Button(self, text="OK", width=6, command=self.okButton_pressed)
        self.cancelButton = Button(self, text="Cancel", command=self.quit)

        # open 'PhotoBookLayoutMaker.cfg' - parameters file and read values
        self.config = ConfigParser()
        self.configFile = (os.path.join(os.path.dirname(__file__), 'PhotoBookLayoutMaker.cfg'))
        self.config.read(self.configFile)
        self.configItems = self.config.items('DEFAULT')
        self.colsVar.set(self.configItems[0][1])
        self.rowsVar.set(self.configItems[1][1])
        self.gapVar.set(self.configItems[2][1])
        self.aspectwidthVar.set(self.configItems[3][1])
        self.aspectheightVar.set(self.configItems[4][1])
        self.scaleVar.set(self.configItems[5][1])
        self.alignhVar.set(self.configItems[6][1])
        self.alignvVar.set(self.configItems[7][1])
        self.captionVar.set(self.configItems[8][1])
        if (self.configItems[8][1] == '1'):
            self.captionCheck.select()
        self.captionhVar.set(self.configItems[9][1])
        self.removeframeVar.set(self.configItems[10][1])
        if (self.configItems[10][1]) == '1':
            self.removeframeCheck.select()
        self.alternateborderVar.set(self.configItems[11][1])
        if (self.configItems[11][1]) == '1':
            self.alternateborderCheck.select()
        #self.saveparamsCheck.select()

        # make interface layout
        self.columnconfigure(0, pad=6)
        currRow = 0
        self.statusLabel.grid(column=0, row=currRow, columnspan=4)
        currRow += 1
        self.colsLabel.grid(column=0, row=currRow, sticky=S+E)
        self.colsEntry.grid(column=1, row=currRow, sticky=S+W)
        self.rowsLabel.grid(column=2, row=currRow, sticky=S+E)
        self.rowsEntry.grid(column=3, row=currRow, sticky=S+W, padx=5)
        currRow += 1
        self.gapLabel.grid(column=0, row=currRow, sticky=S+E)
        self.gapEntry.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.aspectLabel.grid(column=0, row=currRow, sticky=S+E)
        currRow += 1
        self.aspectwidthLabel.grid(column=0, row=currRow, sticky=S+E)
        self.aspectwidthEntry.grid(column=1, row=currRow, sticky=S+W)
        self.aspectheightLabel.grid(column=2, row=currRow, sticky=S+E)
        self.aspectheightEntry.grid(column=3, row=currRow, sticky=S+W, padx=5)
        currRow += 1
        self.scaleLabel.grid(column=0, row=currRow, sticky=S+E)
        self.scaleEntry.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.alignhLabel.grid(column=0, row=currRow, sticky=S+E)
        self.alignhVar.grid(column=1, row=currRow, sticky=S+W)
        self.alignvLabel.grid(column=2, row=currRow, sticky=S+E)
        self.alignvVar.grid(column=3, row=currRow, sticky=S+W, padx=5)
        currRow += 1
        self.captionLabel.grid(column=0, row=currRow, sticky=S+E)
        self.captionCheck.grid(column=1, row=currRow, sticky=S+W)
        self.captionhLabel.grid(column=2, row=currRow, sticky=S+E)
        self.captionhEntry.grid(column=3, row=currRow, sticky=S+W, padx=5)
        currRow += 1
        self.removeframeLabel.grid(column=0, row=currRow, sticky=S+E)
        self.removeframeCheck.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.alternateborderLabel.grid(column=0, row=currRow, sticky=S+E)
        self.alternateborderCheck.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.saveparamsLabel.grid(column=0, row=currRow, sticky=S+E)
        self.saveparamsCheck.grid(column=1, row=currRow, sticky=S+W)
        currRow += 1
        self.rowconfigure(currRow, pad=6)
        self.okButton.grid(column=1, row=currRow, sticky=E)
        self.cancelButton.grid(column=2, row=currRow, sticky=W) 

    def okButton_pressed(self):
        """ User variables testing and preparing """
        # create PhotoBook Layout

        # checks for input errors
        if (self.colsVar.get().isdigit() == False or self.colsVar.get().isdigit() == False
            or int(self.colsVar.get()) == 0 or int(self.rowsVar.get()) == 0):
            self.statusVar.set('Columns and Rows must be integers > 0.')
            return

        if (self.aspectwidthVar.get().isdigit() == False 
            or self.aspectheightVar.get().isdigit() == False):
            self.statusVar.set('Aspect ratio figures must be integers.')
            return
        if int(self.aspectheightVar.get()) == 0:
            aspectratio = 0	# fill entire frame
        else:
            aspectratio = int(self.aspectwidthVar.get()) / int(self.aspectheightVar.get())

        if int(self.removeframeVar.get()) == 0:
            removeframe = 0
        else:
            removeframe = 1

        if int(self.alternateborderVar.get()) == 0:
            alternateborder = 0
        else:
            alternateborder = 1

        if self.saveparamsVar.get() == 1:    # save parameters to 'PhotoBookLayoutMaker.cfg'
            self.config = ConfigParser()
            self.configFile = (os.path.join(os.path.dirname(__file__), 'PhotoBookLayoutMaker.cfg'))
            self.config.read(self.configFile)
            self.configItems = self.config.items('DEFAULT')
            self.config.set('DEFAULT', self.configItems[0][0], self.colsVar.get())
            self.config.set('DEFAULT', self.configItems[1][0], self.rowsVar.get())
            self.config.set('DEFAULT', self.configItems[2][0], str(self.gapVar.get()))
            self.config.set('DEFAULT', self.configItems[3][0], self.aspectwidthVar.get())
            self.config.set('DEFAULT', self.configItems[4][0], self.aspectheightVar.get())
            self.config.set('DEFAULT', self.configItems[5][0], str(self.scaleVar.get()))
            self.config.set('DEFAULT', self.configItems[6][0], self.alignhVar.get())
            self.config.set('DEFAULT', self.configItems[7][0], self.alignvVar.get())
            self.config.set('DEFAULT', self.configItems[8][0], str(self.captionVar.get()))
            self.config.set('DEFAULT', self.configItems[9][0], str(self.captionhVar.get()))
            self.config.set('DEFAULT', self.configItems[10][0], str(removeframe))
            self.config.set('DEFAULT', self.configItems[11][0], str(alternateborder))
            with open(self.configFile, 'w') as configfile:
                self.config.write(configfile)    # converts all items to lowercase !
            #self.configItems = self.config.items('DEFAULT') 
            #msg = messagebox.showinfo("INFO:", self.configItems) #################

        if not int(self.captionVar.get()) == 1:
            self.captionhVar.set("0.0")

        spblm = ScPhotoBookLayoutMaker(int(self.colsVar.get()), int(self.rowsVar.get()),
            float(self.gapVar.get()), float(aspectratio), float(self.scaleVar.get()),
            self.alignhVar.get(), self.alignvVar.get(), float(self.captionhVar.get()),
            removeframe, alternateborder)
        self.master.withdraw()
        err = spblm.createLayout()

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
        scribus.messageBox("Error: No document open",
            "Please, create (or open) a document before running this script ...",
            scribus.ICON_WARNING,scribus.BUTTON_OK)
        return
    
    try:
        scribus.statusMessage('Running script...')
        scribus.progressReset()
        unit = scribus.getUnit()
        root = Tk()
        app = TkPhotoBookLayoutMaker(root)
        root.mainloop()
    finally:
        if scribus.haveDoc():
            scribus.redrawAll()
        scribus.setUnit(unit)
        scribus.statusMessage('Done.')
        scribus.progressReset()

if __name__ == '__main__':
    main()
