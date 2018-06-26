#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 15:02:12 2018

@author: cs401
"""

import sys
import os
import copy
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QLineEdit, QMessageBox, QFileDialog, QInputDialog
import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
import matplotlib
import numbers
import pandas
from matplotlib import pyplot as plt
from ._utilities import _loadCSV, _loadDatasetObject, _findNearest, _calcCorrelation, _findStructuralSets
from ._utilitiesUI import _displayMessage, _actionIfChange, _writeOutput
from ._plotting import plotCorrelation, plotScatter, plotHeatmap

class ISTOCSY(QtGui.QWidget):
	"""
	App to explore correlations in MS datasets

	runISTOCSY.main(**kwargs)

	NOTE: ISTOCSY can be run with no input arguments as all can be set using the menus in the app itself

	**kwargs:
		:param str correlationMethod: correlation method (default='pearson')
		:param str correlationKind: either 'relative' (neg/pos) or 'absolute' (abs) (default='relative')
		:param str correctionMethod: FDR correction method for correlation p-values (default=None)
		:param float correlationThreshold: show features which correlate to driver feature above this value (default=0.8)
		:param float structuralThreshold: features which correlate above this are defined as being in the same structural set (default=0.9)
		:param float rtThreshold: Window in RT for defining structural sets (default=None)
		:param bool showAllFeatures: flag as to whether to show all features, or only those above correlationThreshold in correlation plot (default=True)
		:param str intensityDataFile: path to directory containing intensity data csv file
		:param str featureMetadataFile: path to directory containing feature metadata csv file
		:param nPYc dataset nPYcDataset: nPYc Dataset containing at least intensityData and featureMetadata (with dimensions as described above)
		:param str saveDir: path to directory where to save any output (default=current working directory)
	"""
	

	def __init__(self, **kwargs):

		super(ISTOCSY, self).__init__()

		# Set up default attributes
		self.Attributes = {
					'correlationMethod': 'pearson',
					'correlationKind': 'relative',
					'correctionMethod': None,
					'correlationThreshold': 0.8,
					'structuralThreshold': 0.9,
					'rtThreshold': 0.02,
					'showAllFeatures': True,
					'intensityDataFile': None,
					'featureMetadataFile': None,
					'nPYcDataset': None,
					'saveDir': '.'
					}

		# Allow attributes to be overwritten by kwargs
		self.Attributes = {**self.Attributes, **kwargs}

		# Initialise layout and set up connections
		self.menus()
		self.init_ui()

		# First widget is a scatter plot of correlations to driver feature
		self.scatterpoints = pg.ScatterPlotItem()
		self.displaytext = pg.TextItem(text='', color='k', anchor=(1,1))
		self.displaytext.hide()
		self.plotwidget1.addItem(self.scatterpoints)
		self.plotwidget1.addItem(self.displaytext)
		self.plotwidget1.setLabel('left', 'm/z')

		# Second widget is a scatter plot of 'structural' associations between correlated features
		self.structuralpoints = pg.ScatterPlotItem()
		self.plotwidget2.addItem(self.structuralpoints)
		self.plotwidget2.setLabel('left', 'm/z')
		self.plotwidget2.setLabel('bottom', 'Retention Time', units='minutes')
		
		# Create dataset
		class Dataset(object):

			def __init__(self):
				self.intensityData = np.array(None)
				self.featureMetadata = pandas.DataFrame(None, columns=['Feature Name', 'Retention Time', 'm/z'])

		self.dataset = Dataset()
		
		
		# Load data if nPYcDataset input
		if self.Attributes['nPYcDataset'] is not None:
			
			_loadDatasetObject(self)

			self.resetPlot()


	def menus(self):
		""" Add all the menus """

		# Add menu bar
		self.myQMenuBar = QtGui.QMenuBar(self)
		self.myQMenuBar.setNativeMenuBar(False)
		fileMenu = self.myQMenuBar.addMenu('File')
		settingsMenu = self.myQMenuBar.addMenu('Settings')
		displayMenu = self.myQMenuBar.addMenu('Display')

		# File>Set intensity data
		setIntensityData = QtGui.QAction('Set intensity data file', self)
		setIntensityData.triggered.connect(self.on_setIntensityData_clicked)
		fileMenu.addAction(setIntensityData)

		# File>Set feature metadata
		setFeatureMetadata = QtGui.QAction('Set feature metadata file', self)
		setFeatureMetadata.triggered.connect(self.on_setFeatureMetadata_clicked)
		fileMenu.addAction(setFeatureMetadata)

		# File>Import data
		importData = QtGui.QAction('Import data', self)
		importData.triggered.connect(self.on_importData_clicked)
		fileMenu.addAction(importData)

		# File>Set output directory
		setSaveDir = QtGui.QAction('Change save directory', self)
		setSaveDir.triggered.connect(self.on_setsaveDir_clicked)
		fileMenu.addAction(setSaveDir)

		# File>Exit
		exitAction = QtGui.QAction('Exit', self)
		exitAction.triggered.connect(self.close)
		fileMenu.addAction(exitAction)

		# Settings>Current settings
		showSettings = QtGui.QAction('Current settings', self)
		showSettings.triggered.connect(self.on_showSettings_clicked)
		settingsMenu.addAction(showSettings)

		# Settings>Set driver
		setDriver = QtGui.QAction('Set driver', self)
		setDriver.triggered.connect(self.on_setDriver_clicked)
		settingsMenu.addAction(setDriver)

		# Settings>Change correlation type
		setCorrMethod = QtGui.QAction('Set correlation method', self)
		setCorrMethod.triggered.connect(self.on_setCorrMethod_clicked)
		settingsMenu.addAction(setCorrMethod)

		# Settings>Change correlation from relative to absolute
		setCorrRel = QtGui.QAction('Set correlation kind (relative or absolute)', self)
		setCorrRel.triggered.connect(self.on_setCorrRel_clicked)
		settingsMenu.addAction(setCorrRel)

		# Settings>Method for multiple testing correction
		setCorrection = QtGui.QAction('Set multiple testing correction method', self)
		setCorrection.triggered.connect(self.on_setCorrection_clicked)
		settingsMenu.addAction(setCorrection)

		# Settings>Change RT threshold (sets)
		setRtThreshold = QtGui.QAction('Set RT threshold (sets)', self)
		setRtThreshold.triggered.connect(self.on_setRtThreshold_clicked)
		settingsMenu.addAction(setRtThreshold)

		# Settings>Change correlation threshold (sets)
		setSetCorrThreshold = QtGui.QAction('Set correlation threshold (sets)', self)
		setSetCorrThreshold.triggered.connect(self.on_setSetCorrThreshold_clicked)
		settingsMenu.addAction(setSetCorrThreshold)

		# Display>Correlation to selected peak
		displayCorPlot = QtGui.QAction('Display interactive correlation to selected peak plot', self)
		displayCorPlot.triggered.connect(self.on_displayCorPlot_clicked)
		displayMenu.addAction(displayCorPlot)

		# Display>Structural sets plot
		displaySetsPlot = QtGui.QAction('Display interactive structural sets plot', self)
		displaySetsPlot.triggered.connect(self.on_displaySetsPlot_clicked)
		displayMenu.addAction(displaySetsPlot)

		# Display>Correlation vs. retention time plot
		displayCorRtPlot = QtGui.QAction('Display interactive correlation vs retention time coloured by set plot', self)
		displayCorRtPlot.triggered.connect(self.on_displayCorRtPlot_clicked)
		displayMenu.addAction(displayCorRtPlot)

		# Display>Correlation map for sets
		displayCorMap = QtGui.QAction('Display interactive correlation map for sets', self)
		displayCorMap.triggered.connect(self.on_displayCorMap_clicked)
		displayMenu.addAction(displayCorMap)


	def init_ui(self):
		""" Set up page layout """

		self.setWindowTitle('ISTOCSY')

		hbox = QtGui.QVBoxLayout()
		self.setLayout(hbox)

		class CustomViewBox(pg.ViewBox):
			def __init__(self, *args, **kwds):
				pg.ViewBox.__init__(self, *args, **kwds)
				self.setMouseMode(self.RectMode)

			def mouseClickEvent(self, ev):
				if ev.button() == QtCore.Qt.LeftButton:
					self.autoRange()

		vb = CustomViewBox()

		title1 = QLabel('Correlation to selected peak')
		title1.setAlignment(QtCore.Qt.AlignCenter)
		hbox.addWidget(title1)

		self.plotwidget1 = pg.PlotWidget(viewBox=vb)
		hbox.addWidget(self.plotwidget1)

		title2 = QLabel('Structural sets')
		title2.setAlignment(QtCore.Qt.AlignCenter)
		hbox.addWidget(title2)

		self.plotwidget2 = pg.PlotWidget()
		hbox.addWidget(self.plotwidget2)

		self.plotwidget1.getViewBox().setXLink(self.plotwidget2)
		self.plotwidget1.getViewBox().setYLink(self.plotwidget2)

		self.exportButton = QtGui.QPushButton("**EXPORT**")
		self.exportButton.clicked.connect(self.on_exportButton_clicked)
		hbox.addWidget(self.exportButton)

		self.resetButton = QtGui.QPushButton("**RESET**")
		self.resetButton.clicked.connect(self.on_resetButton_clicked)
		hbox.addWidget(self.resetButton)

		self.textbox = QLineEdit()# QtGui.QInputDialog()
		self.textbox.setText("Enter correlation threshold")
		hbox.addWidget(self.textbox)

		self.changeThresholdButton = QtGui.QPushButton("**SET CORRELATION THRESHOLD**")
		self.changeThresholdButton.clicked.connect(self.on_changeThresholdButton_clicked)
		hbox.addWidget(self.changeThresholdButton)

		self.showAllFeaturesButton = QtGui.QPushButton("**SHOW FEATURES ABOVE THRESHOLD ONLY**")
		self.showAllFeaturesButton.clicked[bool].connect(self.on_showAllFeaturesButton_clicked)
		hbox.addWidget(self.showAllFeaturesButton)

		self.setGeometry(10, 10, 1000, 600)


	def resetPlot(self):
		""" Reset plot to show all features """

		# Define all points to be plotted
		spots = [{'pos': [self.dataset.featureMetadata.loc[i,'Retention Time'], self.dataset.featureMetadata.loc[i,'m/z']], 'data': 1} for i in range(self.dataset.intensityData.shape[1])]

		# Add points to correlation plot (first widget)
		self.scatterpoints.clear()
		self.scatterpoints.addPoints(spots)

		# Set up click event - link to calculate correlation from point
		def clicked(plot, points):
			temp = points[0].pos()
			test = _findNearest(self.dataset.featureMetadata, temp[0], temp[1])
			self.latestpoint = test
			self.Attributes['recalculateCorrelation'] = True
			self.updatePlot(test)

		self.scatterpoints.sigClicked.connect(clicked)

		# Set up hover event - shows feature ID
		def hovered(pos):
			act_pos = self.scatterpoints.mapFromScene(pos)
			p1 = self.scatterpoints.pointsAt(act_pos)
			if len(p1) != 0:
				temp2 = p1[0].pos()
				test2 = _findNearest(self.dataset.featureMetadata, temp2[0], temp2[1])
				self.displaytext.setText(self.dataset.featureMetadata.loc[test2, 'Feature Name'])
				self.displaytext.setPos(temp2[0], temp2[1])
				self.displaytext.show()
			else:
				self.displaytext.hide()

		self.scatterpoints.scene().sigMouseMoved.connect(hovered)

		# Reset points in strucural association plot
		self.structuralpoints.clear()
		self.structuralpoints.addPoints(spots)
		try:
			self.structuralpoints.scene().sigMouseMoved.disconnect()
		except:
			pass

		# Reset export button
		self.exportButton.setText('**EXPORT**')

		# Delete previous driver and info
		if hasattr(self, 'latestpoint'):
			del self.latestpoint
			del self.tempTable
			self.Attributes['recalculateCorrelation'] = True


	def updatePlot(self, points):
		""" Update plot once driver set or if any parameters changed """

		# Only need to calculate correlation if driver change
		if self.Attributes['recalculateCorrelation'] == True:

			# Calculate correlation and associated p-values to driver
			self.cVect, self.pVect, self.qVect = _calcCorrelation(self.dataset.intensityData, self.dataset.intensityData[:,points], correlationMethod=self.Attributes['correlationMethod'], correctionMethod=self.Attributes['correctionMethod'])

			# Generate the colormap for the correlation plot
			norm = matplotlib.colors.Normalize(vmin=np.min(self.cVect), vmax=np.max(self.cVect))
			cb = matplotlib.cm.ScalarMappable(norm=norm, cmap=plt.cm.RdYlBu_r)

			# Return the colours for each feature
			cVectAlphas = np.zeros((self.dataset.intensityData.shape[1], 4))

			cIX = 0
			for c in self.cVect:
				cVectAlphas[cIX,:] = cb.to_rgba(self.cVect[cIX], bytes=True)
				cIX = cIX+1

			# Set the alpha (min 50, max 255)
			cVectAlphas[:,3] = (((abs(self.cVect) - np.min(abs(self.cVect))) * (255 - 50)) / (np.max(abs(self.cVect)) - np.min(abs(self.cVect)))) + 50
			if any(cVectAlphas[:,3] > 255):
				cVectAlphas[cVectAlphas[:,3]>255,3] = 255
			self.cVectAlphas = cVectAlphas

		# Extract featureMetadata and intensityData for features with correlation above threshold and absolute/relative

		# Create mask of correlating features
		if self.Attributes['correlationKind'] == 'relative':
			mask = self.cVect > self.Attributes['correlationThreshold']

		else:
			mask = np.abs(self.cVect) > self.Attributes['correlationThreshold']

		# Create table - info for all correlating features
		tempTable = self.dataset.featureMetadata[mask].copy()
		tempTable = tempTable[['Feature Name', 'Retention Time', 'm/z']]
		tempTable['Correlation'] = self.cVect[mask]
		tempTable['P-value'] = self.pVect[mask]
		if self.qVect is not None:
			tempTable['Q-value'] = self.qVect[mask]

		# Sort table so driver (correlation==1) at top
		tempTable.sort_values('Correlation', axis=0, ascending=False, inplace=True)

		# Extract corresponding intensityData
		tempData = self.dataset.intensityData[:,tempTable.index]

		nCorr = tempData.shape[1]

		# Generate our spots
		if self.Attributes['showAllFeatures'] == True:
			spots = [{'pos': [self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'Retention Time'], self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[i],'m/z']], 'brush':pg.mkColor((self.cVectAlphas[i,:]))} for i in range(self.dataset.intensityData.shape[1])]
		else:
			cVectAlphas = self.cVectAlphas[mask,:]
			spots = [{'pos': [tempTable.loc[tempTable.index[i],'Retention Time'], tempTable.loc[tempTable.index[i],'m/z']], 'brush':pg.mkColor((cVectAlphas[i,:]))} for i in range(nCorr)]

		self.scatterpoints.clear()
		self.scatterpoints.setData(spots)
		self.scatterpoints.setPen(None)

		tempTable = _findStructuralSets(tempTable, self.dataset.intensityData, self.Attributes)

		tempcVectAlphas = np.zeros((tempData.shape[1], 4))
		setcVectAlphas = np.zeros((tempData.shape[1], 4))
		tempcVect = tempTable['Set'].values
		cIX = 0

		norm = matplotlib.colors.Normalize(vmin=1, vmax=max(tempTable['Set'])+1)
		cb2 = matplotlib.cm.ScalarMappable(norm=norm, cmap=plt.cm.nipy_spectral)
		for c in tempcVect:
			tempcVectAlphas[cIX,:] = cb2.to_rgba(c, bytes=True)
			setcVectAlphas[cIX,:] = cb2.to_rgba(c)
			cIX = cIX+1
		tempcVectAlphas[:,3] = 255

		tempspots = [{'pos': [tempTable.loc[tempTable.index[i],'Retention Time'], tempTable.loc[tempTable.index[i],'m/z']], 'brush':pg.mkColor((tempcVectAlphas[i,:]))} for i in range(tempData.shape[1])]
		self.structuralpoints.clear()
		self.structuralpoints.setData(tempspots)
		self.structuralpoints.setPen(None)

		# Set up hover event - shows structural set of each feature
		def hovered(pos):
			act_pos = self.structuralpoints.mapFromScene(pos)
			p1 = self.structuralpoints.pointsAt(act_pos)
			if len(p1) != 0:
				temp2 = p1[0].pos()
				ix = _findNearest(tempTable, temp2[0], temp2[1])
				self.displaytext.setText('Set: ' + str(int(tempTable.loc[ix, 'Set'])))
				self.displaytext.setPos(temp2[0], temp2[1])
				self.displaytext.show()
			else:
				self.displaytext.hide()

		self.structuralpoints.scene().sigMouseMoved.connect(hovered)

		self.tempTable = tempTable
		self.tempcVectAlphas = tempcVectAlphas
		self.setcVectAlphas = setcVectAlphas

		# Save to self for output if required
		self.exportButton.setText('Driver: ' + self.dataset.featureMetadata.loc[self.dataset.featureMetadata.index[self.latestpoint],'Feature Name'] + '\nThreshold: ' + str(self.Attributes['correlationThreshold']) + ' (' + self.Attributes['correlationKind'] + ')\nNumber of correlating features: ' + str(nCorr-1) + '\nNumber of structural sets: ' + str(int(max(tempTable['Set']))) + '\n**EXPORT**')


	def on_resetButton_clicked(self):
		""" Reset button click - reset plot """

		self.resetPlot()


	def on_exportButton_clicked(self):
		""" Correlating features button click - save feature list to csv """

		_writeOutput(self)


	def on_changeThresholdButton_clicked(self):
		""" User input to change correlation threshold """

		original = copy.deepcopy(self.Attributes['correlationThreshold'])

		x = self.textbox.text()

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not isinstance(x, numbers.Number) & ((x < 1) & (x > 0)):
			_displayMessage("Correlation threshold must be a number in the range 0 to 1")

		else:
			self.Attributes['correlationThreshold'] = x

			_actionIfChange(self, original, self.Attributes['correlationThreshold'], False, "Correlation threshold sucessfully set to: ")

		self.textbox.setText("Enter correlation threshold")


	def on_showAllFeaturesButton_clicked(self):
		""" User input for correlation plot to toggle between showing all features or just those above corrThreshold """

		# If showing all features
		if (self.Attributes['showAllFeatures'] == True):
			self.Attributes['showAllFeatures'] = False
			self.showAllFeaturesButton.setText('**SHOW ALL FEATURES**')

		else:
			self.Attributes['showAllFeatures'] = True
			self.showAllFeaturesButton.setText('**SHOW FEATURES ABOVE THRESHOLD ONLY**')

		self.Attributes['recalculateCorrelation'] = False
		self.updatePlot(self.latestpoint)


	def on_setIntensityData_clicked(self):
		""" User set path to intensity data file """

		intensityDataDir, ok = QFileDialog.getOpenFileName(self, 'Select intensity data file', '/home')

		self.Attributes['intensityDataFile'] = intensityDataDir


	def on_setFeatureMetadata_clicked(self):
		""" User set path to feature metadata file """

		featureMetadataDir, ok = QFileDialog.getOpenFileName(self, 'Select feature metadata file', '/home')

		self.Attributes['featureMetadataFile'] = featureMetadataDir


	def on_importData_clicked(self):
		""" Import data """

		_loadCSV(self, self.Attributes['intensityDataFile'], self.Attributes['featureMetadataFile'])

		self.resetPlot()


	def on_setsaveDir_clicked(self):
		""" User input to change directory where outputs are saved """

		saveDir = QFileDialog.getExistingDirectory(self, 'Select directory', '/home')

		self.Attributes['saveDir'] = saveDir


	def on_showSettings_clicked(self):
		""" Display settings """

		QMessageBox.about(self, "ISTOCSY settings",
				  'Correlation method: %s\nCorrelation kind: %s\nCorrelation threshold: %s\nMultiple testing correction: %s\nCorrelation threshold (sets): %s\nRetention time tolerance (sets): %s' % (self.Attributes['correlationMethod'], self.Attributes['correlationKind'], str(self.Attributes['correlationThreshold']), self.Attributes['correctionMethod'], str(self.Attributes['structuralThreshold']), str(self.Attributes['rtThreshold'])) )


	def on_setDriver_clicked(self):
		""" User input to set driver feature """

		x, ok = QInputDialog.getText(self, '', 'Enter ''Feature Name'' of driver:')

		# Check that driver is in dataset
		featureix = self.dataset.featureMetadata.index[self.dataset.featureMetadata['Feature Name'] == x]

		try:
			temp = featureix.values
			self.latestpoint = temp[0]

			# Check if changed and action result of change
			_actionIfChange(self, None, x, True, "Driver succesfully set to: ")

		except:
			_displayMessage("Driver must match an entry in the ''Feature Name'' column of the feature metadata file")


	def on_setCorrMethod_clicked(self):
		""" User input to change correlation method """

		original = copy.deepcopy(self.Attributes['correlationMethod'])

		options = ("pearson", "spearman", "kendalltau")
		option, ok = QInputDialog.getItem(self, "", "Select required correlation method:", options, 0, False)

		if ok and option:
			self.Attributes['correlationMethod'] = option

			_actionIfChange(self, original, self.Attributes['correlationMethod'], True, "Correlation method sucessfully set to: ")


	def on_setCorrRel_clicked(self):
		""" User input to change correlation kind (absolute or relative) """

		original = copy.deepcopy(self.Attributes['correlationKind'])


		options = ("absolute", "relative")
		option, ok = QInputDialog.getItem(self, "", "Select required correlation kind:", options, 0, False)

		if ok and option:
			self.Attributes['correlationKind'] = option

			# Check if changed and action result of change
			_actionIfChange(self, original, self.Attributes['correlationKind'], True, "Correlation kind sucessfully set to: ")


	def on_setCorrection_clicked(self):
		""" User input to change FDR correction method for correlation p-values """

		original = copy.deepcopy(self.Attributes['correctionMethod'])

		options = ("bonferroni", "sidak", "holm-sidak", "holm", "simes-hochberg", "hommel", "fdr_bh", "fdr_by", "fdr_tsbh", "fdr_tsbky")
		option, ok = QInputDialog.getItem(self, "", "Select required correction method:", options, 0, False)

		if ok and option:
			self.Attributes['correctionMethod'] = option

			# Check if changed and action result of change
			_actionIfChange(self, original, self.Attributes['correctionMethod'], True, "Correction method sucessfully set to: ")


	def on_setSetCorrThreshold_clicked(self):
		""" User input to change correlation threshold for defining structural associations """

		original = copy.deepcopy(self.Attributes['structuralThreshold'])

		x, ok = QInputDialog.getText(self, '', 'Enter required correlation threshold (sets):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not isinstance(x, numbers.Number) & ((x < 1) & (x > 0)):
			_displayMessage("Correlation threshold (sets) must be a number in the range 0 to 1")

		else:
			self.Attributes['structuralThreshold'] = x

			# Check if changed and action result of change
			_actionIfChange(self, original, self.Attributes['structuralThreshold'], False, "Correlation threshold (sets) sucessfully set to: ")


	def on_setRtThreshold_clicked(self):
		""" User input to change retention time tolerance for defining structural associations """

		original = copy.deepcopy(self.Attributes['rtThreshold'])

		x, ok = QInputDialog.getText(self, '', 'Enter required retention time tolerance (sets):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not isinstance(x, numbers.Number) or (x < 0):
			_displayMessage("Retention time tolerance (sets) must be a number greater than zero")

		else:
			self.Attributes['rtThreshold'] = x

			# Check if changed and action result of change
			_actionIfChange(self, original, self.Attributes['rtThreshold'], False, "Retention time tolerance (sets) sucessfully set to: ")


	def on_displayCorPlot_clicked(self):
		""" Create interactive (plotly) correlation to selected peak plot """

		if hasattr(self, 'tempTable'):

			if self.Attributes['showAllFeatures'] == False:

				# Create mask of correlating features
				if self.Attributes['correlationKind'] == 'relative':
					mask = self.cVect > self.Attributes['correlationThreshold']

				else:
					mask = np.abs(self.cVect) > self.Attributes['correlationThreshold']
			else:
				mask=None

			saveName = self.tempTable.loc[self.tempTable.index[0],'Feature Name'].replace('/','')
			plotCorrelation(self.dataset.featureMetadata, self.cVect, mask, savePath=os.path.join(self.Attributes['saveDir'], saveName + '_plotCorrelation'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displaySetsPlot_clicked(self):
		""" Create interactive (plotly) structural sets plot """

		if hasattr(self, 'tempTable'):
			saveName = self.tempTable.loc[self.tempTable.index[0],'Feature Name'].replace('/','')
			plotScatter(self.tempTable, 'Retention Time', 'm/z', self.setcVectAlphas, title='m/z vs. RT coloured by Set', savePath=os.path.join(self.Attributes['saveDir'], saveName + '_plotStructuralSets'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displayCorRtPlot_clicked(self):
		""" Create interactive (plotly) correlation vs. RT sets plot """

		if hasattr(self, 'tempTable'):
			saveName = self.tempTable.loc[self.tempTable.index[0],'Feature Name'].replace('/','')
			plotScatter(self.tempTable, 'Retention Time', 'Correlation', self.setcVectAlphas, title='Correlation vs. RT coloured by Set', savePath=os.path.join(self.Attributes['saveDir'], saveName + '_plotCorrelationVsRT'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


	def on_displayCorMap_clicked(self):
		""" Create interactive (plotly) heatmap of internal correlations between all features above correationThreshold to driver """

		if hasattr(self, 'tempTable'):
			saveName = self.tempTable.loc[self.tempTable.index[0],'Feature Name'].replace('/','')
			plotHeatmap(self.tempTable, self.dataset.intensityData, correlationMethod=self.Attributes['correlationMethod'], savePath=os.path.join(self.Attributes['saveDir'], saveName + '_plotSetsHeatmap'))

		else:
			_displayMessage("Driver feature must be selected before plots can be displayed!")


def main(**kwargs):

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName('ISTOCSY')
	app.aboutToQuit.connect(app.deleteLater)
	myapp = ISTOCSY(**kwargs)
	myapp.show()
	sys.exit(app.exec())


if __name__ == '__main__':

	main()
