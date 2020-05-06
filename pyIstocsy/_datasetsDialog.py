#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 16:53:11 2020

@author: cs401
"""

import sip
import os
from functools import partial
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QDialog, QLabel
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
from PyQt5.QtCore import QSizeF
from PyQt5.QtPrintSupport import QPrinter

class _datasetsDialog(QDialog):

    
	def __init__(self, **kwargs):

		super(_datasetsDialog, self).__init__()

		# Set up default attributes
		self.Attributes = {
					'datasetsDetails': [],
                    'istocsyDatasetDetails': [],
                    'action': None,
					'datasetToDelete': None,
                    'datasetDetails': [None] * 5,
					'datasetName': None,
                    'datasetType': None,
					'intensityDataFile': None,
					'featureMetadataFile': None,
					'sampleMetadataFile': None,
					'dataRoot': '.',
					'saveDir': '.'
					}

		# Allow attributes to be overwritten by kwargs
		self.Attributes = {**self.Attributes, **kwargs}

		self.init_ui()
        

	def init_ui(self):
		""" Set up the user interface window """

		if hasattr(self, 'hbox'):

			while self.hbox.count():
				item = self.hbox.takeAt(0)
				if item:
					item.widget().deleteLater()
			sip.delete(self.hbox)

		else:

			self.setWindowTitle('Import Data')
			self.setGeometry(10, 10, 500, 300)

		self.hbox = QtGui.QGridLayout()
		self.setLayout(self.hbox)
        
  		# Load new dataset      
		self.newDatasetText = QLabel('Load new dataset: ')
		self.hbox.addWidget(self.newDatasetText, 1, 0)
        
		self.nameButton = QtGui.QPushButton("Enter dataset name")
		self.nameButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.nameButton.clicked.connect(self.on_setDatasetName_clicked)
		self.hbox.addWidget(self.nameButton, 1, 1)

		self.typeButton = QtGui.QPushButton("Enter dataset type")
		self.typeButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.typeButton.clicked.connect(self.on_setDatasetType_clicked)
		self.hbox.addWidget(self.typeButton, 2, 1)

		self.intensityButton = QtGui.QPushButton("Enter path to intensity data file")
		self.intensityButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.intensityButton.clicked.connect(self.on_setIntensityData_clicked)
		self.hbox.addWidget(self.intensityButton, 3, 1)

		self.sampledataButton = QtGui.QPushButton("Enter path to sample metadata file")
		self.sampledataButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.sampledataButton.clicked.connect(self.on_setSampleMetadata_clicked)
		self.hbox.addWidget(self.sampledataButton, 4, 1)

		self.featuredataButton = QtGui.QPushButton("Enter path to feature metadata file")
		self.featuredataButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.featuredataButton.clicked.connect(self.on_setFeatureMetadata_clicked)
		self.hbox.addWidget(self.featuredataButton, 5, 1)

		self.closeButton = QtGui.QPushButton("Import new dataset and close")
		self.closeButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.closeButton.clicked.connect(self.on_closeButton_clicked)
		self.hbox.addWidget(self.closeButton, 6, 1)

		row = 8
        
        # VDetails of existing datasets
		if len(self.Attributes['datasetsDetails']) != 0:
            
			self.hbox.addWidget(QLabel('Details of existing datasets: '), row, 0)

			for dataset in self.Attributes['datasetsDetails']:
                
				self.hbox.addWidget(QLabel(dataset[0]), row+1, 0)
				self.hbox.addWidget(QLabel('Data type: ' + dataset[1]), row+1, 1)
				self.hbox.addWidget(QLabel('intensityData path: ' + dataset[2]), row+2, 1)
				self.hbox.addWidget(QLabel('sampleMetadata path: ' + dataset[3]), row+3, 1)
				self.hbox.addWidget(QLabel('featureMetadata path: ' + dataset[4]), row+4, 1)
				self.hbox.addWidget(QLabel('Number of samples: ' + str(dataset[5])), row+5, 1)
				self.hbox.addWidget(QLabel('Number of features: ' + str(dataset[6])), row+6, 1)
                
				# Add button to remove dataset
				self.deleteDatasetButton = QtGui.QPushButton("Delete dataset and close")
				self.deleteDatasetButton.setFocusPolicy(QtCore.Qt.NoFocus)
				self.deleteDatasetButton.clicked.connect(partial(self.on_deleteDatasetButton_clicked, dataset[0]))
				self.hbox.addWidget(self.deleteDatasetButton, row+7, 1)
                
				row = row+9
 
        # Details of complete ISTOCSY dataset
		if self.Attributes['istocsyDatasetDetails'][0] is not None:
            
			self.hbox.addWidget(QLabel('Details of ISTOCSY dataset: '), row, 0)
               
			self.hbox.addWidget(QLabel('Number of samples: ' + str(self.Attributes['istocsyDatasetDetails'][0])), row, 1)
			self.hbox.addWidget(QLabel('Number of features: ' + str(self.Attributes['istocsyDatasetDetails'][1])), row+1, 1)

			# Button to export ISTOCSY dataset
			self.exportButton = QtGui.QPushButton("Export ISTOCSY dataset and close")
			self.exportButton.setFocusPolicy(QtCore.Qt.NoFocus)
			self.exportButton.clicked.connect(self.on_exportButton_clicked)
			self.hbox.addWidget(self.exportButton, row+2, 1)        
        
       
	def getResults(self):
		""" Return results """

		if self.exec_() == QDialog.Accepted:

			return self.Attributes

	def on_setDatasetName_clicked(self):
		""" User set dataset name """

		x, ok = QInputDialog.getText(self, '', 'Enter name for dataset:')

		self.nameButton.setText(x)

		self.Attributes['datasetName'] = x
        
		self.Attributes['datasetDetails'][0] = x
        
	def on_setDatasetType_clicked(self):
		""" User set data type, choice of LC-MS, NMR or Targeted """
		
		options = ("LC-MS", "NMR", "Targeted")
		option, ok = QInputDialog.getItem(self, "", "Select required correlation method:", options, 0, False)

		self.typeButton.setText(option)

		self.Attributes['datasetType'] = option
		self.Attributes['datasetDetails'][1] = option

	def on_setIntensityData_clicked(self):
		""" User set path to intensity data file """

		intensityDataDir, ok = QFileDialog.getOpenFileName(self, 'Select intensity data file', self.Attributes['dataRoot'])

		temp = os.path.split(intensityDataDir)
		self.intensityButton.setText(temp[1])

		self.Attributes['intensityDataFile'] = intensityDataDir

		# Set root so easier to navigate to subsequent files
		self.Attributes['dataRoot'] = temp[0]
        
		self.Attributes['datasetDetails'][2] = intensityDataDir

	def on_setFeatureMetadata_clicked(self):
		""" User set path to feature metadata file """

		featureMetadataDir, ok = QFileDialog.getOpenFileName(self, 'Select feature metadata file', self.Attributes['dataRoot'])

		temp = os.path.split(featureMetadataDir)
		self.featuredataButton.setText(temp[1])

		self.Attributes['featureMetadataFile'] = featureMetadataDir

        	# Set root so easier to navigate to subsequent files
		self.Attributes['dataRoot'] = temp[0]
        
		self.Attributes['datasetDetails'][3] = featureMetadataDir

	def on_setSampleMetadata_clicked(self):
		""" User set path to sample metadata file """

		sampleMetadataDir, ok = QFileDialog.getOpenFileName(self, 'Select sample metadata file', self.Attributes['dataRoot'])

		temp = os.path.split(sampleMetadataDir)
		self.sampledataButton.setText(temp[1])

		self.Attributes['sampleMetadataFile'] = sampleMetadataDir

        	# Set root so easier to navigate to subsequent files
		self.Attributes['dataRoot'] = temp[0]

		self.Attributes['datasetDetails'][4] = sampleMetadataDir
		
	def on_deleteDatasetButton_clicked(self, datasetName):
		""" Flags dataset for deletion and closes window """
		
		self.Attributes['action'] = 'deleteDataset'
		self.Attributes['datasetToDelete'] = datasetName
		
		self.accept()

	def on_closeButton_clicked(self):
		""" Flags dataset for loading and closes window """

        # Flat to load new dataset
		self.Attributes['action'] = 'loadDataset'
        
		self.accept()

	def on_exportButton_clicked(self):
		""" Flags full ISTOCSY dataset for export and closes window """
		
        # Flat to export ISTOCSY dataset
		self.Attributes['action'] = 'exportDataset'
        
        # Export screenshot
		printer = QPrinter(QPrinter.HighResolution)
		printer.setOutputFileName(os.path.join(self.Attributes['saveDir'], 'ISTOCSY_dataset_details.pdf'))
		printer.setOutputFormat(QPrinter.PdfFormat)
		size = self.size()
		printer.setPaperSize(QSizeF(size.width(), size.height()), QPrinter.DevicePixel) # QPrinter.DevicePixel
		printer.setFullPage(True)
		self.render(printer)        
                
		self.accept()