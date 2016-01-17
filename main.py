import cv2, sys, requests, json, math, logging
import numpy as np
from collections import deque
from PySide.QtCore import *
from PySide.QtGui import *
import pyqtgraph as pg
from subprocess import call
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


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
			
		for cam,data in cameras.iteritems():
			data["grabber"] = None
			data["thread"] = CameraReader(cam)
			data["thread"].signalDrawImg.connect(self.slotDrawImage)
			data["thread"].signalAddImg.connect(self.slotAddImage)
			data["live"] = False
			
		self.buildTreeWidget()
		
		[c["thread"].start() for c in cameras.values() ]
		self.show()
		
	def buildTreeWidget(self):
		items = []
		self.treeWidget.setColumnCount(2)
		self.treeWidget.setHeaderLabels(["Live", "Camera"])
		for name, data in cameras.iteritems():
			widget = QTreeWidgetItem(self.treeWidget)
			widget.setText(1,name)
			widget.setIcon(0,QIcon("redBall.png"))
			data["widget"] = widget
			#items.append(widget)
			self.treeWidget.insertTopLevelItem(1,widget)
			for cont in data.keys():
				child = QTreeWidgetItem(self.treeWidget)
				print cont
				child.setText( 1, str(cont) )
				widget.addChild( child )
		
		for i in range(self.treeWidget.columnCount()):
			self.treeWidget.resizeColumnToContents(i); 
		
	
	def readJSONFile(self, fileName, imprimir = False):
		with open(fileName, 'r') as fileJson:
			data = json.load(fileJson)
			if imprimir == True:
				pprint(data)
		return data
	
	@Slot( str, QImage )
	def slotDrawImage(self, ident, img):
		#print ident
		label = cameras[ident]["label"]
	#	label.setPixmap(QPixmap.fromImage(img).scaled(label.width(), label.height()))
		label.setPixmap(QPixmap.fromImage(img))
		self.show()
		
	@Slot( str )
	def slotAddImage(self, ident):
		#print ident, "ok"
		cameras[ident]["widget"].setIcon(0,QIcon("greenBall.png"))
		self.treeWidget.insertTopLevelItem(0,cameras[ident]["widget"])
		
		sumOK = sum([1 for data in cameras.values() if data["live"] == True ])
		totalCols = int( math.ceil(math.sqrt(sumOK)) )
		index = 0
		for data in cameras.values():
			if data["live"] == True:
				row = index / totalCols
				col = index % totalCols
				index += 1
				label = QLabel("img")
				self.gridLayout.addWidget(label, row, col)
				cameras[ident]["label"] = label
				print sumOK, row, col
		self.show()	
	
	@Slot( str )
	def slotRemoveImage(self, ident ):
		#print ident, "ok"
		cameras[ident]["widget"].setIcon(0,QIcon("redBall.png"))
		self.treeWidget.insertTopLevelItem(0,cameras[ident]["widget"])
		self.show()
	
	#QThread reader for cameras sensors
class CameraReader(QThread):
	signalDrawImg = Signal( str, QImage)
	signalAddImg = Signal( str )
	
	def __init__(self, ident):
		super(CameraReader, self).__init__()
		self.ident = ident
		
	def run(self):
		while True:
			#print "hola", self.ident
			cam  = cameras[self.ident]
			#Check for the first time
			if cam["grabber"] is None:
				#print "connecting" , cam["url"]
				cam["grabber"] = cv2.VideoCapture(cam["url"])
				if cam["grabber"].isOpened():
					cam["live"] = True
					self.signalAddImg.emit( self.ident )
			#Try to read
			if  cam["grabber"].isOpened():
					#print self.ident, "grabbing"
					cool, frame = cam["grabber"].read()
					if cool:
						if cam["live"] == False:
							cam["live"] = True
							self.signalAddImg.emit( self.ident )
						frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
						img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)    
						self.signalDrawImg.emit( self.ident, img )
					else:
						cam["live"] = False
						#self.signalRemoveImg
					self.msleep(100)
			else:  #not working
				cam["live"] = False
				cam["grabber"] = cv2.VideoCapture(cam["url"])
				self.msleep(500)
				
	
if __name__ == '__main__':
    app = QApplication(sys.argv)
    timer = QTimer()
    mainWin = MainWindow()
    
    #File changing daemon
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, "..")
    observer.start()
    
    ret = app.exec_()
    sys.exit( ret )	
    

