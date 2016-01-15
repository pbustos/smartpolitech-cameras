import cv2, sys, requests, json, math
import numpy as np
from collections import deque
from PySide.QtCore import *
from PySide.QtGui import *
import pyqtgraph as pg
from subprocess import call

# Generate GUI form .ui file
call("pyside-uic vcapturegui.ui > ui_vcapturegui.py", shell=True)

from ui_vcapturegui import Ui_MainWindow

cameras = {}

class MainWindow(QMainWindow, Ui_MainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.setupUi(self)
		self.show()
		global cameras
   
		cameras = self.readJSONFile('cameras.json')["cameras"]
		
		#for c,d in cameras.iteritems():
			#d["grabber"] = cv2.VideoCapture(d["url"])
			#d["bg"] = cv2.BackgroundSubtractorMOG()
			
			#print "Camera: ",c, " status = ",d["grabber"].isOpened()
		
		#sumOK = sum( 1 for d in cameras.values() if d["grabber"].isOpened() )
		sumOK = len(cameras)
		
		for cam,data in cameras.iteritems():
			data["grabber"] = None
			data["thread"] = CameraReader(cam)
			data["thread"].signalVal.connect(self.slotDrawImage)
		
		for cam, cont  in zip( cameras.values(), range(sumOK)):
			row,col  = self.buildGrid(sumOK, cont)
			label = QLabel("caca")
			self.gridLayout.addWidget(label, row, col)
			cam["label"] = label
			print sumOK, cont, row, col,cam["label"]
	
		#Tree widget
		items = []
		self.treeWidget.setColumnCount(2)
		self.treeWidget.setHeaderLabels(["Live", "Camera"])
		for name, data in cameras.iteritems():
			widget = QTreeWidgetItem(self.treeWidget)
			widget.setText(1,name)
			widget.setIcon(0,QIcon("redBall.png"))
			data["widget"] = widget
			items.append(widget)
			data["live"] = False
		self.treeWidget.insertTopLevelItems(1,items)
        
		for i in range(self.treeWidget.columnCount()):
			self.treeWidget.resizeColumnToContents(i); 
		
		#timer.timeout.connect( self.readCameras ) 
		[c["thread"].start() for c in cameras.values() ]
		#timer.start(100)
		self.show()
		
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
	
	@Slot( str, QImage )
	def slotDrawImage(self, ident, img):
		#print ident, "ok"
		if cameras[ident]["live"] == True:
			cameras[ident]["widget"].setIcon(0,QIcon("greenBall.png"))
			self.treeWidget.insertTopLevelItem(0,cameras[ident]["widget"])
			cameras[ident]["label"].setPixmap(QPixmap.fromImage(img))
		else:
			#print name , "failing"
			cameras[ident]["widget"].setIcon(0,QIcon("redBall.png"))
			self.treeWidget.insertTopLevelItem(0,cameras[ident]["widget"])
		self.show()
		
	
	#QThread reader for cameras sensors
class CameraReader(QThread):
	signalVal = Signal( str, QImage)
	def __init__(self, ident):
		super(CameraReader, self).__init__()
		self.ident = ident
		
	def run(self):
		while True:
			#print "hola", self.ident
			cam  = cameras[self.ident] 
			if cam["grabber"] is None:
				#print "connecting" , self.ident
				cam["grabber"] = cv2.VideoCapture(cam["url"])
			if  cam["grabber"].isOpened():
					#print self.ident, "grabbing"
					cool, frame = cam["grabber"].read()
					if cool:
						frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
						img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)    
						cam["live"] = True
						self.signalVal.emit( self.ident, img )
						cam["live"] = True
					else:
						cam["live"] = False
			self.msleep(100)
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
    

