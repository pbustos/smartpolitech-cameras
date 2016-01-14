import cv2, sys, requests, json, math
import numpy as np
from collections import deque
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
import pyqtgraph as pg
from subprocess import call

# Generate GUI form .ui file
call("pyuic4 vcapturegui.ui > ui_vcapturegui.py", shell=True)

from ui_vcapturegui import Ui_MainWindow

cameras = {}

class MainWindow(QMainWindow, Ui_MainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.setupUi(self)
		self.show()
		global cameras
   
		cameras = self.readJSONFile('cameras.json')["cameras"]
		
		for c,d in cameras.iteritems():
			d["grabber"] = cv2.VideoCapture(d["url"])
			d["bg"] = cv2.BackgroundSubtractorMOG()
			d["order"] = c
			print "Camera: ",c, " status = ",d["grabber"].isOpened()
		
		sumOK = sum( 1 for d in cameras.values() if d["grabber"].isOpened() )
		
		for d, cont  in zip( cameras.values(), range(sumOK)):
			row,col  = self.buildGrid(sumOK, cont)
			label = QLabel("caca")
			self.gridLayout.addWidget(label, row, col)
			d["label"] = label
			print sumOK, cont, row, col,d["label"]
	
	
		items = []
		self.treeWidget.setColumnCount(2)
		self.treeWidget.setHeaderLabels(["Live", "Camera"])
		for name, data in cameras.iteritems():
			cam = QTreeWidgetItem(self.treeWidget)
			cam.setText(1,name)
			if data["grabber"].isOpened():
				cam.setIcon(0,QIcon("greenBall.png"))
			else:
				cam.setIcon(0,QIcon("redBall.png"))
			data["widget"] = cam
			items.append(cam)
			data["live"] = False
		self.treeWidget.insertTopLevelItems(1,items)
        
		for i in range(self.treeWidget.columnCount()):
			self.treeWidget.resizeColumnToContents(i); 
		
		timer.timeout.connect( self.readCameras ) 
		timer.start(100)
		
		
	def buildGrid(self, numCams, index):		
		totalCols = int( math.ceil(math.sqrt(numCams)) )
		row = index / totalCols
		col = index % totalCols
		return row, col
		
	def readJSONFile(self, fileName, imprimir = False):
		with open(fileName, 'r') as fileJson:
			data = json.load(fileJson)
			if imprimir == True:
				pprint(data)
		return data
	
	def readCameras(self):
		for name, data in cameras.iteritems():
			if data["grabber"].isOpened():
				cool, frame = data["grabber"].read()
				if cool:
					print name, "ok"
					frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)    
					if data["live"] == False:
						data["live"] = True
						data["widget"].setIcon(0,QICon("greenBall.jpeg"))
						self.treeWidget.insertTopLevelItem(0,data["widget"])
						
					#imb = QImage(cv2.cvtColor(data["bg"].apply(frame),cv2.COLOR_GRAY2BGR).data, 640, 480, QImage.Format_RGB888)
					#imb = QImage(data["bg"].apply(frame).data, 640, 480, QImage.Format_Indexed8)                  
					#data["label"].setPixmap(QPixmap.fromImage(img).scaled(data["label"].width(), data["label"].height()))
					data["label"].setPixmap(QPixmap.fromImage(img))
				else:
					print name , "failing"
					data["widget"].setIcon(0,QICon("redBall.png"))
					self.treeWidget.insertTopLevelItem(0,data["widget"])
					data["live"] = False
                 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    timer = QTimer()
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit( ret )	
    

