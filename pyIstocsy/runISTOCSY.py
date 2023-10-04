#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 15:02:12 2018

@author: cs401
"""
from PyQt6 import sip
import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QInputDialog, QWidget, QApplication, QPushButton, QGridLayout
import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.colors import rgb2hex
from _utilities import _loadDataset, _deleteDataset, _findNearest, _applySampleMask, _calcCorrelation, _dropStructuralSetInfo, _findStructuralSets, _loadAnnotations, _matchAnnotations, _displayMessage, _writeOutput, _writeData, _loadBatchFile, _applyFitRANSAC
from _datasetsDialog import _datasetsDialog
from _settingsDialog import _settingsDialog
from _annotationsDialog import _annotationsDialog
from _batchDialog import _batchDialog
from _plotting import plotScatter, plotHeatmap, plotCorrelationScatter

# when RANSAC fails (UrineMap2 NMR) sort this

class ISTOCSY(QWidget):
	"""
	App to explore correlations in MS datasets

	runISTOCSY.main(**kwargs)

	NOTE: ISTOCSY can be run with no input arguments as all can be set using the menus in the app itself

	**kwargs:
		:param str correlationMethod: correlation method (default='pearson')
		:param str correlationKind: either 'relative' (neg/pos) or 'absolute' (abs) (default='relative')
		:param float correlationThreshold: show features which correlate to driver feature above this value (default=0.8)
		:param float structuralThreshold: features which correlate above this are defined as being in the same structural set (default=0.9)
		:param float rtThreshold: Window in RT for defining structural sets (default=None)
		:param bool showAllFeatures: flag as to whether to show all features, or only those above correlationThreshold in correlation plot (default=True)
		:param str intensityDataFile: path to directory containing intensity data csv file
		:param str featureMetadataFile: path to directory containing feature metadata csv file
		:param str saveDir: path to directory where to save any output (default=current working directory)
	"""


	def __init__(self, **kwargs):

		super(ISTOCSY, self).__init__()

		# Set up default attributes
		self.Attributes = {
                    'datasetsDetails': [],
                    'istocsyDatasetDetails': [None] * 2,
					'NMRdataPresent': True,
					'MSdataPresent': True,
					'TargetedDataPresent': True,
                    'annotationFilePath': None,
                    'batchFilePath': None,
					'correlationMethod': 'pearson',
					'correlationKind': 'relative',
					'correlationThreshold': 0.8,
					'structuralThreshold': 0.9,
					'rtThreshold': 0.15,
                    'mzThreshold': 10,
                    'ppmThreshold': 0.02,
                    'sampleIntensitySet': 'All samples',
                    'sampleIntensityThreshold': None,
                    'saveDir': '.',
                    'dataRoot': '.',
					'showAllFeatures': True,
					'applyRANSAC': False,
					'driver': None,
					'driverPair': None,
					'RANSACdegree': 1,
					'relativeIntensityMetric': 'max'
					}

		# Allow attributes to be overwritten by kwargs
		self.Attributes = {**self.Attributes, **kwargs}

		# Initialise layout and set up connections
		self.init_ui()


	def init_ui(self):
		""" Set up page layout """

		if hasattr(self, 'hbox'):

			while self.hbox.count():
				item = self.hbox.takeAt(0)
				if item:
					item.widget().deleteLater()
			sip.delete(self.hbox)

		else:

			self.setWindowTitle('ISTOCSY')
			self.setGeometry(10, 10, 1000, 600)


		self.hbox = QGridLayout()
		self.setLayout(self.hbox)

		# Add buttons to load/view/export data/settings etc
		self.setupText = QLabel('Load/view/update/export: ')
		self.hbox.addWidget(self.setupText, 0, 0)


		self.dataButton = QPushButton("Datasets")
		self.dataButton.clicked.connect(self.on_dataButton_clicked)
		self.hbox.addWidget(self.dataButton, 0, 1)

		self.settingsButton = QPushButton("Settings")
		self.settingsButton.clicked.connect(self.on_settingsButton_clicked)
		self.hbox.addWidget(self.settingsButton, 0, 2)

		self.annotationsButton = QPushButton("Annotations")
		self.annotationsButton.clicked.connect(self.on_annotationsButton_clicked)
		self.hbox.addWidget(self.annotationsButton, 0, 3)

		self.batchButton = QPushButton("Batch File")
		self.batchButton.clicked.connect(self.on_batchButton_clicked)
		self.hbox.addWidget(self.batchButton, 0, 4)


		row=1


		class CustomViewBox(pg.ViewBox):
			def __init__(self, *args, **kwds):
				pg.ViewBox.__init__(self, *args, **kwds)
				self.setMouseMode(self.RectMode)

			def mouseClickEvent(self, ev):
				if ev.button() == Qt.MouseButton.LeftButton:
					self.autoRange()

		vb1 = CustomViewBox()
		vb2 = CustomViewBox()
		vb3 = CustomViewBox()

		if (self.Attributes['MSdataPresent'] == True):

			title1 = QLabel('LC-MS data')
			title1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			self.hbox.addWidget(title1, row, 0, 1, 5)

			self.plotwidget1 = pg.PlotWidget(viewBox=vb1)
			self.hbox.addWidget(self.plotwidget1, row+1, 0, 1, 5)

			self.scatterpointsMS = pg.ScatterPlotItem()
			self.displaytextMS = pg.TextItem(text='', color='k', anchor=(0,1))
			self.displaytextMS.hide()
			self.plotwidget1.addItem(self.scatterpointsMS)
			self.plotwidget1.addItem(self.displaytextMS)
			self.plotwidget1.setLabel('left', 'm/z')
			self.plotwidget1.setLabel('bottom', 'Retention Time', units='minutes')

			row=row+2


		if (self.Attributes['NMRdataPresent'] == True):

			title2 = QLabel('NMR data')
			title2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			self.hbox.addWidget(title2, row, 0, 1, 5)

			self.plotwidget2 = pg.PlotWidget(viewBox=vb2)
			self.hbox.addWidget(self.plotwidget2, row+1, 0, 1, 5)

			self.scatterpointsNMR = pg.ScatterPlotItem()
			self.linepointsNMR1all = pg.PlotCurveItem()
			self.linepointsNMR1correlating = pg.PlotCurveItem()
			self.displaytextNMR = pg.TextItem(text='', color='k', anchor=(0,1))
			self.displaytextNMR.hide()
			self.plotwidget2.addItem(self.scatterpointsNMR)
			self.plotwidget2.addItem(self.linepointsNMR1all)
			self.plotwidget2.addItem(self.linepointsNMR1correlating)
			self.plotwidget2.addItem(self.displaytextNMR)
			self.plotwidget2.setLabel('left', 'Relative Intensity')
			self.plotwidget2.setLabel('bottom', 'ppm')

			row=row+2

		if (self.Attributes['TargetedDataPresent'] == True):

			title3 = QLabel('Targeted data')
			title3.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			self.hbox.addWidget(title3, row, 0, 1, 5)

			self.plotwidget3 = pg.PlotWidget(viewBox=vb3)
			self.hbox.addWidget(self.plotwidget3, row+1, 0, 1, 5)

			self.scatterpointsTargeted = pg.ScatterPlotItem()
			self.displaytextTargeted = pg.TextItem(text='', color='k', anchor=(0,1))
			self.displaytextTargeted.hide()
			self.plotwidget3.addItem(self.scatterpointsTargeted)
			self.plotwidget3.addItem(self.displaytextTargeted)
			self.plotwidget3.setLabel('left', 'Relative Intensity')
			self.plotwidget3.setLabel('bottom', 'Feature Name')

			row=row+2

		self.setDriverButton = QPushButton("Set driver")
		self.setDriverButton.clicked.connect(self.on_setDriver_clicked)
		self.hbox.addWidget(self.setDriverButton, row, 0, 1, 3)

		self.setDriverPairButton = QPushButton("Set driver-pair")
		self.setDriverPairButton.clicked.connect(self.on_setDriverPair_clicked)
		self.hbox.addWidget(self.setDriverPairButton, row, 3, 1, 2)

		self.showAllFeaturesButton = QPushButton("Show features above threshold only")
		self.showAllFeaturesButton.clicked[bool].connect(self.on_showAllFeaturesButton_clicked)
		self.hbox.addWidget(self.showAllFeaturesButton, row+1, 0, 1, 5)

		self.applyRANSACButton = QPushButton("Apply RANSAC")
		self.applyRANSACButton.clicked[bool].connect(self.on_applyRANSACButton_clicked)
		self.hbox.addWidget(self.applyRANSACButton, row+2, 0, 1, 5)
		
		self.exportButton = QPushButton("Export")
		self.exportButton.clicked.connect(self.on_exportButton_clicked)
		self.hbox.addWidget(self.exportButton, row+3, 0, 1, 5)

		self.hbox.setRowStretch(row+3, 5)

		self.displayPlotsText = QLabel('Display and export interactive plots: ')
		self.hbox.addWidget(self.displayPlotsText, row+4, 0)

		self.plotCorrelationButton = QPushButton("Coloured by correlation to driver")
		self.plotCorrelationButton.clicked.connect(self.on_displayCorPlot_clicked)
		self.hbox.addWidget(self.plotCorrelationButton, row+4, 1)

		self.plotSetButton = QPushButton("Coloured by structural set")
		self.plotSetButton.clicked.connect(self.on_displaySetsPlot_clicked)
		self.hbox.addWidget(self.plotSetButton, row+4, 2)

		self.plotHeatmapButton = QPushButton("Heatmap of correlations")
		self.plotHeatmapButton.clicked.connect(self.on_displayCorMap_clicked)
		self.hbox.addWidget(self.plotHeatmapButton, row+4, 3)

		self.plotScatterButton = QPushButton("Scatter plot of correlating features")
		self.plotScatterButton.clicked.connect(self.on_displayCorScatter_clicked)
		self.hbox.addWidget(self.plotScatterButton, row+4, 4)
				
		self.resetButton = QPushButton("Reset")
		self.resetButton.clicked.connect(self.on_resetButton_clicked)
		self.hbox.addWidget(self.resetButton, row+5, 0, 1, 5)


	def resetPlot(self):
		""" Reset plot to show all features """
		if hasattr(self, 'dataset'):
			if (sum(self.dataset.featureMetadata['Data Type'] == 'LC-MS') > 0):
				self.Attributes['MSdataPresent'] = True
			else:
				self.Attributes['MSdataPresent'] = False

			if (sum(self.dataset.featureMetadata['Data Type'] == 'NMR') > 0):
				self.Attributes['NMRdataPresent'] = True
			else:
				self.Attributes['NMRdataPresent'] = False

			if (sum(self.dataset.featureMetadata['Data Type'] == 'Targeted') > 0):
				self.Attributes['TargetedDataPresent'] = True
			else:
				self.Attributes['TargetedDataPresent'] = False

			self.init_ui()

			# Plot MS data
			if (self.Attributes['MSdataPresent'] == True):

				maskNum = [i for i, x in enumerate(self.dataset.featureMetadata['Data Type']) if x=='LC-MS']

				# Define all points to be plotted
				spots = [{'pos': [self.dataset.featureMetadata.loc[i,'Retention Time'], self.dataset.featureMetadata.loc[i,'m/z']], 'data': 1} for i in maskNum]

				# Add points to MS plot
				self.scatterpointsMS.clear()
				self.scatterpointsMS.addPoints(spots)

				# Set up click event - link to calculate correlation from point
				def clicked(plot, points):
					temp = points[0].pos()
					test = _findNearest(self.dataset.featureMetadata, 'Retention Time', 'm/z', temp[0], temp[1])
					self.Attributes['driver'] = test
					self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','')
					self.Attributes['recalculateCorrelation'] = True
					self.updatePlot()

				self.scatterpointsMS.sigClicked.connect(clicked)

				# Set up hover event - shows feature ID
				def hovered(pos):

					act_pos = self.scatterpointsMS.mapFromScene(pos)
					p1 = self.scatterpointsMS.pointsAt(act_pos)
					if len(p1) != 0:

						temp2 = p1[0].pos()
						test2 = _findNearest(self.dataset.featureMetadata, 'Retention Time', 'm/z',  temp2[0], temp2[1])
						self.displaytextMS.setText(self.dataset.featureMetadata.loc[test2, 'Feature Name'])
						self.displaytextMS.setPos(temp2[0], temp2[1])
						self.displaytextMS.show()
					else:
						self.displaytextMS.hide()

				self.scatterpointsMS.scene().sigMouseMoved.connect(hovered)

			# Plot NMR data
			if (self.Attributes['NMRdataPresent'] == True):


				maskNum = [i for i, x in enumerate(self.dataset.featureMetadata['Data Type']) if x=='NMR']

				# Plot line plot of data
				x = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Data Type'] == 'NMR', 'ppm'].values
				y = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Data Type'] == 'NMR', 'Relative Intensity'].values

				self.linepointsNMR1all.setData(x=x, y=y, pen=(200,200,200), connect='finite')
				self.linepointsNMR1all.getViewBox().invertX(True)

				# Use 'hidden' scatter plot for click and hover events

				# Define all points to be plotted
				spots = [{'pos': [self.dataset.featureMetadata.loc[i,'ppm'], self.dataset.featureMetadata.loc[i,'Relative Intensity']], 'data': 1, 'brush':'w', 'pen':'w'} for i in maskNum]

				# Add points to Targeted plot
				self.scatterpointsNMR.clear()
				self.scatterpointsNMR.addPoints(spots)

				# Set up click event - link to calculate correlation from point
				def clickedNMR(plot, points):
					temp = points[0].pos()
					test = _findNearest(self.dataset.featureMetadata, 'ppm', 'Relative Intensity', temp[0], temp[1])
					self.Attributes['driver'] = test
					self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','')
					self.Attributes['recalculateCorrelation'] = True
					self.updatePlot()

				self.scatterpointsNMR.sigClicked.connect(clickedNMR)

				# Set up hover event - shows feature ID
				def hoveredNMR(pos):
					act_pos = self.scatterpointsNMR.mapFromScene(pos)
					p1 = self.scatterpointsNMR.pointsAt(act_pos)
					if len(p1) != 0:
						temp2 = p1[0].pos()
						test2 = _findNearest(self.dataset.featureMetadata, 'ppm', 'Relative Intensity',  temp2[0], temp2[1])
						self.displaytextNMR.setText(self.dataset.featureMetadata.loc[test2, 'Feature Name'])
						self.displaytextNMR.setPos(temp2[0], temp2[1])
						self.displaytextNMR.show()
					else:
						self.displaytextNMR.hide()

				self.scatterpointsNMR.scene().sigMouseMoved.connect(hoveredNMR)
				self.scatterpointsNMR.getViewBox().invertX(True)

			# Plot Targeted data
			if (self.Attributes['TargetedDataPresent'] == True):

				maskNum = [i for i, x in enumerate(self.dataset.featureMetadata['Data Type']) if x=='Targeted']

				# Define all points to be plotted
				spots = [{'pos': [self.dataset.featureMetadata.loc[i,'Targeted Feature Number'], self.dataset.featureMetadata.loc[i,'Relative Intensity']], 'data': 1} for i in maskNum]

				# Add points to Targeted plot
				self.scatterpointsTargeted.clear()
				self.scatterpointsTargeted.addPoints(spots)

				# Set up click event - link to calculate correlation from point
				def clickedTargeted(plot, points):

					temp = points[0].pos()
					test = _findNearest(self.dataset.featureMetadata, 'Targeted Feature Number', 'Relative Intensity', temp[0], temp[1])
					self.Attributes['driver'] = test
					self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','')
					self.Attributes['recalculateCorrelation'] = True
					self.updatePlot()

				self.scatterpointsTargeted.sigClicked.connect(clickedTargeted)

				# Set up hover event - shows feature ID
				def hoveredTargeted(pos):
					act_pos = self.scatterpointsTargeted.mapFromScene(pos)
					p1 = self.scatterpointsTargeted.pointsAt(act_pos)
					if len(p1) != 0:
						temp2 = p1[0].pos()
						test2 = _findNearest(self.dataset.featureMetadata, 'Targeted Feature Number', 'Relative Intensity',  temp2[0], temp2[1])
						self.displaytextTargeted.setText(self.dataset.featureMetadata.loc[test2, 'Feature Name'])
						self.displaytextTargeted.setPos(temp2[0], temp2[1])
						self.displaytextTargeted.show()
					else:
						self.displaytextTargeted.hide()

				self.scatterpointsTargeted.scene().sigMouseMoved.connect(hoveredTargeted)


			# Reset export button
			self.exportButton.setText('Export')

			# Delete previous driver and info
			self.Attributes['driver'] = None
			self.Attributes['driverPair'] = None
			self.Attributes['recalculateCorrelation'] = True
			_dropStructuralSetInfo(self)

		

	def updatePlot(self):
		""" Update plot once driver set or if any parameters changed """


		# Generate the colormap for the correlation plot
		norm = matplotlib.colors.Normalize(vmin=-1, vmax=1)
		cb = matplotlib.cm.ScalarMappable(norm=norm, cmap=plt.cm.RdBu_r)

		# Only need to calculate correlation if driver change
		if self.Attributes['recalculateCorrelation'] == True:

			# Sample mask
			self.dataset.sampleMetadata['Sample Mask'] = _applySampleMask(self, applyMask=self.Attributes['sampleIntensitySet'], threshold=self.Attributes['sampleIntensityThreshold'])

			# Calculate correlation to driver
			self.dataset.featureMetadata['Correlation'] = _calcCorrelation(self.dataset.intensityData, driverIX=self.Attributes['driver'], correlationMethod=self.Attributes['correlationMethod'], sampleMask=self.dataset.sampleMetadata['Sample Mask'])

			# Create mask of correlating features
			if self.Attributes['correlationKind'] == 'relative':
				self.dataset.featureMetadata['Feature Mask'] = self.dataset.featureMetadata['Correlation'] >= self.Attributes['correlationThreshold']

			else:
				self.dataset.featureMetadata['Feature Mask'] = np.abs(self.dataset.featureMetadata['Correlation']) >= self.Attributes['correlationThreshold']

			# If Driver Pair specified ensure Driver Pair feature plotted
			if self.Attributes['driverPair'] is not None:

				self.dataset.featureMetadata['Feature Mask'] = False

				self.dataset.featureMetadata.loc[self.Attributes['driver'], 'Feature Mask'] = True
				self.dataset.featureMetadata.loc[self.Attributes['driverPair'], 'Feature Mask'] = True

			# Delete structural set info
			_dropStructuralSetInfo(self)


        	# Determine any sample outliers - if required only
		if self.Attributes['applyRANSAC'] == True:
			_applyFitRANSAC(self)

		# Update plots

        # Generate the opacity value (alpha) for each correlation colour
		alphas = (((abs(self.dataset.featureMetadata['Correlation']) - 0) * (1 - 0.2)) / (1 - 0)) + 0.2

		# MS data
		if (self.Attributes['MSdataPresent'] == True):

			MSmask = self.dataset.featureMetadata['Data Type'] == 'LC-MS'

			if self.Attributes['showAllFeatures'] == False:
				MSmask = MSmask & self.dataset.featureMetadata['Feature Mask']

			maskNum = [i for i, x in enumerate(MSmask) if x]

			# Generate our spots
			spots = [{'pos': [self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Retention Time'], self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'m/z']], 'brush':pg.mkColor(rgb2hex(cb.to_rgba(self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Correlation'], alpha=alphas[i])))} for i in maskNum]

			self.scatterpointsMS.clear()
			self.scatterpointsMS.setData(spots)
			self.scatterpointsMS.setPen(None)


		# NMR data
		if (self.Attributes['NMRdataPresent'] == True):

			# Plot red line for correlating above threshold

			x = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Data Type'] == 'NMR', 'ppm'].values
			y = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Data Type'] == 'NMR', 'Relative Intensity'].values

			NMRmask = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Data Type'] == 'NMR', 'Feature Mask']

			y[~NMRmask] = np.nan

			self.linepointsNMR1correlating.setData(x=x, y=y, pen=(153,0,0), connect='finite')
			self.linepointsNMR1correlating.getViewBox().invertX(True)

		# Targeted data
		if (self.Attributes['TargetedDataPresent'] == True):

			TargetedMask = self.dataset.featureMetadata['Data Type'] == 'Targeted'

			if self.Attributes['showAllFeatures'] == False:
				TargetedMask = TargetedMask & self.dataset.featureMetadata['Feature Mask']

			maskNum = [i for i, x in enumerate(TargetedMask) if x]

			# Generate our spots
			spots = [{'pos': [self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Targeted Feature Number'], self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Relative Intensity']], 'brush':pg.mkColor(rgb2hex(cb.to_rgba(self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Correlation'], alpha=alphas[i])))} for i in maskNum]

			self.scatterpointsTargeted.clear()
			self.scatterpointsTargeted.setData(spots)
			self.scatterpointsTargeted.setPen(None)


		# If Driver Pair specified output Driver Pair correlation
		if self.Attributes['driverPair'] is not None:

			self.exportButton.setText('Driver: ' + self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name']
									+ '; Kind: ' + self.Attributes['correlationKind']
									+ '; Method: ' + self.Attributes['correlationMethod']
									+ '; \nCorrelation calculated on: ' + self.Attributes['sampleIntensitySet'] + ' (n=' + str(sum(self.dataset.sampleMetadata['Sample Mask']))
									+ '; \nCorrelation to ' + self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Feature Name']
									+ ': ' + str(self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Correlation'])
									+ '\n**EXPORT**')
		else:

			self.exportButton.setText('Driver: ' + self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name']
									+ '\nNumber of correlating features: ' + str(sum(self.dataset.featureMetadata['Feature Mask']))
									+ '\nThreshold: ' + str(self.Attributes['correlationThreshold'])
									+ '; Kind: ' + self.Attributes['correlationKind']
									+ '; Method: ' + self.Attributes['correlationMethod']
									+ '; \nCorrelation calculated on: ' + self.Attributes['sampleIntensitySet'] + ' (n=' + str(sum(self.dataset.sampleMetadata['Sample Mask']))
									+ '\n**EXPORT**')


	def on_resetButton_clicked(self):
		""" Reset button click - reset plot """

		self.resetPlot()





	def on_exportButton_clicked(self):
		""" Correlating features button click - save feature list to csv """
		if hasattr(self, 'dataset'):

			if 'driver' in self.Attributes:

				# Determine putative structural sets
				if ('Set' not in  self.dataset.featureMetadata):

					_findStructuralSets(self)

				# Set mask
				if self.Attributes['showAllFeatures'] == False:

					mask = self.dataset.featureMetadata['Feature Mask']

				else:
					mask = None

				_writeOutput(self, mask)

			else:

				_displayMessage("Driver must be set before results can be exported!!")
		else:
			_displayMessage("Load a dataset before setting the driver")


	def on_showAllFeaturesButton_clicked(self):
		""" User input for correlation plot to toggle between showing all features or just those above corrThreshold """

		# If showing all features
		if (self.Attributes['showAllFeatures'] == True):
			self.Attributes['showAllFeatures'] = False
			self.showAllFeaturesButton.setText('Show all features')

		else:
			self.Attributes['showAllFeatures'] = True
			self.showAllFeaturesButton.setText('**Show features above threshold (or driver-driver pair features) only**')

		# Update plot
		if self.Attributes['driver'] is not None:
			self.Attributes['recalculateCorrelation'] = False
			self.updatePlot()

	def on_applyRANSACButton_clicked(self):
		""" User input to calculate RANSAC (for fit of correlation and outlier identification) or not """
		
		if (self.Attributes['applyRANSAC'] == True):
			self.Attributes['applyRANSAC'] = False
			self.applyRANSACButton.setText('Apply RANSAC')
			
			# Delete RANSAC if present
			if hasattr(self, 'RANSAC'):
				del(self.RANSAC)				
			
		else:
			self.Attributes['applyRANSAC'] = True
			self.applyRANSACButton.setText('Do not apply RANSAC')

			# Apply RANSAC fit if driver set
			if self.Attributes['driver'] is not None:
				_applyFitRANSAC(self)

	def on_dataButton_clicked (self):

		w = _datasetsDialog(dataRoot=self.Attributes['dataRoot'],
                      datasetsDetails=self.Attributes['datasetsDetails'],
                      istocsyDatasetDetails=self.Attributes['istocsyDatasetDetails'],
                      saveDir=self.Attributes['saveDir'])


		results = w.getResults()
		if results is not None:
			self.Attributes['datasetName'] = results['datasetName']
			self.Attributes['datasetType'] = results['datasetType']
			self.Attributes['intensityDataFile'] = results['intensityDataFile']
			self.Attributes['sampleMetadataFile'] = results['sampleMetadataFile']
			self.Attributes['featureMetadataFile'] = results['featureMetadataFile']
			self.Attributes['dataRoot'] = results['dataRoot']

			# Action!

			if results['action'] == 'loadDataset':

				self.Attributes['datasetsDetails'].append(results['datasetDetails'])

				_loadDataset(self, intensityDataFile=self.Attributes['intensityDataFile'], featureMetadataFile=self.Attributes['featureMetadataFile'], sampleMetadataFile=self.Attributes['sampleMetadataFile'], datasetName=self.Attributes['datasetName'], datasetType=self.Attributes['datasetType'])

				self.resetPlot()

			elif results['action'] == 'deleteDataset':

				_deleteDataset(self, results['datasetToDelete'])

				# If datasets remain, reset plot
				if hasattr(self, 'dataset'):

					self.resetPlot()

				# Otherwise re-initialise
				else:

					self.Attributes['MSdataPresent'] = True
					self.Attributes['NMRdataPresent'] = True
					self.Attributes['TargetedDataPresent'] = True

					self.init_ui()

			elif results['action'] == 'exportDataset':

				_writeData(self)


	def on_settingsButton_clicked (self):

		# Open window to display and update settings (reads in defaults or those previously set)
		w = _settingsDialog(	correlationMethod = self.Attributes['correlationMethod'],
						    correlationKind = self.Attributes['correlationKind'],
							correlationThreshold = self.Attributes['correlationThreshold'],
							structuralThreshold = self.Attributes['structuralThreshold'],
							rtThreshold = self.Attributes['rtThreshold'],
							mzThreshold = self.Attributes['mzThreshold'],
							ppmThreshold = self.Attributes['ppmThreshold'],
							sampleIntensitySet = self.Attributes['sampleIntensitySet'],
							sampleIntensityThreshold = self.Attributes['sampleIntensityThreshold'],
							RANSACdegree = self.Attributes['RANSACdegree'],
							relativeIntensityMetric = self.Attributes['relativeIntensityMetric'],
							saveDir = self.Attributes['saveDir'])

		results = w.getResults()
		if results is not None:
			# Overwrite results
			self.Attributes['correlationMethod'] = results['correlationMethod']
			self.Attributes['correlationKind'] = results['correlationKind']
			self.Attributes['correlationThreshold'] = results['correlationThreshold']
			self.Attributes['structuralThreshold'] = results['structuralThreshold']
			self.Attributes['rtThreshold'] = results['rtThreshold']
			self.Attributes['mzThreshold'] = results['mzThreshold']
			self.Attributes['ppmThreshold'] = results['ppmThreshold']
			self.Attributes['sampleIntensitySet'] = results['sampleIntensitySet']
			self.Attributes['sampleIntensityThreshold'] = results['sampleIntensityThreshold']
			self.Attributes['RANSACdegree'] = results['RANSACdegree']
			self.Attributes['relativeIntensityMetric'] = results['relativeIntensityMetric']
			self.Attributes['saveDir'] = results['saveDir']

			# Update plot
			if self.Attributes['driver'] is not None:
				self.Attributes['recalculateCorrelation'] = True
				self.updatePlot()


	def on_annotationsButton_clicked(self):
		""" Load annotations file"""

		# Open window to load new annotations file and or match to dataset (reads in file if previously loaded)
		w = _annotationsDialog(annotationFilePath=self.Attributes['annotationFilePath'])

		results = w.getResults()

		if results is not None:
			# Overwrite results
			self.Attributes['annotationFilePath'] = results['annotationFilePath']

			# Apply to dataset if loaded
			if hasattr(self, 'dataset'):

				_loadAnnotations(self)

				_matchAnnotations(self)

				self.resetPlot()


	def on_batchButton_clicked(self):
		""" Load batch file for automatically running ISTOCSY from named drivers or between defined drivers and driver-pairs"""

		# Open window to load new batch file
		w = _batchDialog(batchFilePath=self.Attributes['batchFilePath'])

		results = w.getResults()

		# Overwrite results
		self.Attributes['batchFilePath'] = results['batchFilePath']

		# Load the batch file
		_loadBatchFile(self)


		if hasattr(self, 'dataset'):

			# If Driver-Pair format
			if 'DriverPair' in self.batchData:

				# Copy data for final csv output
				output = self.batchData.copy()


			# Generate correlations and plots for every driver feature in file
			for ix in self.batchData.index:

				# Check that driver is in dataset
				featureix = self.dataset.featureMetadata.index[self.dataset.featureMetadata['Feature Name'] == self.batchData.loc[ix,'Driver']]

				try:
					temp = featureix.values
					self.Attributes['driver'] = temp[0]
					self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','')
					self.Attributes['recalculateCorrelation'] = True

				except:
					_displayMessage("Driver must match an entry in the ''Feature Name'' column of the feature metadata file")


				# If Driver-Pair format
				if 'DriverPair' in self.batchData:

					# Check that driver pair is in dataset
					featureix = self.dataset.featureMetadata.index[self.dataset.featureMetadata['Feature Name'] == self.batchData.loc[ix,'DriverPair']]

					try:
						temp = featureix.values
						self.Attributes['driverPair'] = temp[0]

					except:
						_displayMessage("Driver Pair must match an entry in the ''Feature Name'' column of the feature metadata file")


					self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','') + ' correlation to ' + self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Feature Name'].replace('/','')


				# Set up masks
				if self.Attributes['showAllFeatures'] == False:

					mask = self.dataset.featureMetadata['Feature Mask']

				else:
					mask = None

				# Update plot
				self.updatePlot()

				# Calculate sets
				_findStructuralSets(self)

				# If Driver-All format, write output for every driver in file
				if 'DriverPair' not in self.batchData:

					# Write output
					_writeOutput(self, mask)

					# Save scatter plot coloured by correlation
					plotScatter(self, colourBy='Correlation', mask=mask, savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotCorrelation'), autoOpen=False)

				# If Driver-Pair format, save output for every pair to write combined file at end
				else:

					output.loc[ix, 'Correlation'] = self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Correlation']
					output.loc[ix, 'RANSAC Number of Outliers'] = sum(self.RANSAC['outliers'].loc[:, self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Feature Name']])
					output.loc[ix, 'RANSAC Intercept'] = self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'RANSAC Intercept']
					output.loc[ix, 'RANSAC Slope'] = self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'RANSAC Slope']
					output.loc[ix, 'RANSAC SSE'] = self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'RANSAC SSE']

				# Save scatter plot with RANSAC fit
				plotCorrelationScatter(self, sampleIDs='Sample ID', savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotCorrelationScatter'), autoOpen=False)

				# Write output - CAZ need to save which are outliers for each pair
				#_writeOutput(self, mask)

		# If Driver-Pair format, export final csv
		if 'DriverPair' in self.batchData:

			temp = os.path.split(self.Attributes['batchFilePath'])
			temp = temp[1].replace('.csv','')

			output.to_csv(os.path.join(self.Attributes['saveDir'], temp + '_batchCorrelationResults.csv'), encoding='utf-8')


		self.resetPlot()


	def on_setDriver_clicked(self):
		""" User input to set driver feature """
		if hasattr(self, 'dataset'):
			x, ok = QInputDialog.getText(self, '', 'Enter ''Feature Name'' of driver:')

			# Check that driver is in dataset

			featureix = self.dataset.featureMetadata.index[self.dataset.featureMetadata['Feature Name'] == x]
			print("feature = %s" % x)
			print(self.dataset.featureMetadata[['Feature Name']])

			try:
				temp = featureix.values
				self.Attributes['driver'] = temp[0]
				self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','')
				self.Attributes['recalculateCorrelation'] = True

				# Check if changed and action result of change
				self.updatePlot()

			except:
				_displayMessage("Driver must match an entry in the ''Feature Name'' column of the feature metadata file")
				self.resetPlot()
		else:
			_displayMessage("Load a dataset before setting the driver!")

	def on_setDriverPair_clicked(self):
		""" User input to set driver-pair feature """

		if hasattr(self, 'dataset'):
			x, ok = QInputDialog.getText(self, '', 'Enter ''Feature Name'' of driver pair:')

			# Check that driver is in dataset
			featureix = self.dataset.featureMetadata.index[self.dataset.featureMetadata['Feature Name'] == x]

			try:
				temp = featureix.values
				self.Attributes['driverPair'] = temp[0]

			except:

				_displayMessage("Driver Pair must match an entry in the ''Feature Name'' column of the feature metadata file")
				self.resetPlot()

			try:

				self.Attributes['saveName'] = self.dataset.featureMetadata.loc[self.Attributes['driver'],'Feature Name'].replace('/','') + ' correlation to ' + self.dataset.featureMetadata.loc[self.Attributes['driverPair'],'Feature Name'].replace('/','')


			except:
				_displayMessage("Driver must be set")
				self.resetPlot()
			# Update plot
			self.updatePlot()
		else:
			_displayMessage("Load a dataset before setting the driver!")




	def on_displayCorPlot_clicked(self):
		""" Create interactive (plotly) correlation to selected peak plot """

		if (self.Attributes['driver'] is not None):

			if self.Attributes['showAllFeatures'] == False:

				mask = self.dataset.featureMetadata['Feature Mask']

			else:
				mask = None

			plotScatter(self, colourBy='Correlation', mask=mask, savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotCorrelation'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displaySetsPlot_clicked(self):
		""" Create interactive (plotly) structural sets plot """

		if (self.Attributes['driver'] is not None):

			if ('Set' not in  self.dataset.featureMetadata ):

				_findStructuralSets(self)

			plotScatter(self, colourBy='Set', mask=self.dataset.featureMetadata['Feature Mask'], savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotStructuralSets'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displayCorMap_clicked(self):
		""" Create interactive (plotly) heatmap of internal correlations between all features above correationThreshold to driver """

		if (self.Attributes['driver'] is not None):

			if ('Set' not in  self.dataset.featureMetadata ):

				_findStructuralSets(self)

			plotHeatmap(self, savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotSetsHeatmap'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displayCorScatter_clicked(self):
		""" Create interactive (plotly) scatter plot of driver to every other feature correlating above correationThreshold """

		if (self.Attributes['driver'] is not None):

			if ('Set' not in  self.dataset.featureMetadata ):

				_findStructuralSets(self)

			plotCorrelationScatter(self, sampleIDs='Sample ID', savePath=os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'] + '_plotCorrelationScatter'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


def main(**kwargs):

	app = QApplication(sys.argv)
	app.setApplicationName('ISTOCSY')
	myapp = ISTOCSY(**kwargs)
	myapp.show()
	app.exec()


if __name__ == '__main__':

	main()
