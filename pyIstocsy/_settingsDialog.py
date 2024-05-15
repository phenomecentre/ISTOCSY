#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 17:52:22 2020

@author: cs401
"""

from PyQt6 import sip
import os
from PyQt6.QtCore import Qt, QSizeF
from PyQt6.QtGui import QPageSize
from PyQt6.QtWidgets import QInputDialog, QWidget, QApplication, QPushButton, QGridLayout

from PyQt6.QtWidgets import QLabel, QInputDialog, QDialog, QFileDialog
import pyqtgraph as pg
from _utilities import _displayMessage, _getPrinter
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
from PyQt6.QtPrintSupport import QPrinter

class _settingsDialog(QDialog):

	def __init__(self, **kwargs):

		super(_settingsDialog, self).__init__()

		# Set up default attributes
		self.Attributes = {
					'correlationMethod': 'pearson',
					'correlationKind': 'relative',
					'correlationThreshold': 0.8,
					'structuralThreshold': 0.9,
					'rtThreshold': 0.05,
                    'mzThreshold': 10,
                    'ppmThreshold': 0.02,
                    'sampleIntensitySet': "All samples",
                    'sampleIntensityThreshold': None,
					'RANSACdegree': 1,
					'relativeIntensityMetric': 'max',
					'saveDir': None,
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

			self.setWindowTitle('View/Change Settings')
			self.setGeometry(10, 10, 500, 300)

		self.hbox = QGridLayout()
		self.setLayout(self.hbox)

		# Correlation method 'correlationMethod'
		self.correlationMethodText = QLabel('Correlation method: ' + self.Attributes['correlationMethod'])
		self.correlationMethodButton = QPushButton("Change correlation method")
		self.correlationMethodButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.correlationMethodButton.clicked.connect(self.on_setCorrMethod_clicked)

		self.hbox.addWidget(self.correlationMethodText, 1, 0)
		self.hbox.addWidget(self.correlationMethodButton, 1, 1)

		# Correlation kind 'correlationKind'
		self.correlationKindText = QLabel('Correlation kind: ' + self.Attributes['correlationKind'])
		self.correlationKindButton = QPushButton("Change correlation kind")
		self.correlationKindButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.correlationKindButton.clicked.connect(self.on_setCorrRel_clicked)

		self.hbox.addWidget(self.correlationKindText, 2, 0)
		self.hbox.addWidget(self.correlationKindButton, 2, 1)

		# Correlation threshold 'correlationThreshold'
		self.correlationThresholdText = QLabel('Correlation threshold: ' + str(self.Attributes['correlationThreshold']))
		self.correlationThresholdButton = QPushButton("Change correlation threshold")
		self.correlationThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.correlationThresholdButton.clicked.connect(self.on_setCorrelationThreshold_clicked)

		self.hbox.addWidget(self.correlationThresholdText, 3, 0)
		self.hbox.addWidget(self.correlationThresholdButton, 3, 1)

		# Structural threshold 'structuralThreshold'
		self.structuralThresholdText = QLabel('Correlation threshold (structural sets): ' + str(self.Attributes['structuralThreshold']))
		self.structuralThresholdButton = QPushButton("Change structural threshold (structural sets)")
		self.structuralThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.structuralThresholdButton.clicked.connect(self.on_setStructuralThreshold_clicked)

		self.hbox.addWidget(self.structuralThresholdText, 4, 0)
		self.hbox.addWidget(self.structuralThresholdButton, 4, 1)

		# RT threshold 'rtThreshold'
		self.rtThresholdText = QLabel('LC-MS RT threshold (structural sets and annotation match): ' + str(self.Attributes['rtThreshold']))
		self.rtThresholdButton = QPushButton("Change LC-MS RT threshold (structural sets and annotation match)")
		self.rtThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.rtThresholdButton.clicked.connect(self.on_setRtThreshold_clicked)

		self.hbox.addWidget(self.rtThresholdText, 5, 0)
		self.hbox.addWidget(self.rtThresholdButton, 5, 1)

		# mz threshold 'mzThreshold'
		self.mzThresholdText = QLabel('LC-MS m/z ppm threshold (annotation match): ' + str(self.Attributes['mzThreshold']))
		self.mzThresholdButton = QPushButton("Change LC-MS m/z ppm threshold (annotation match)")
		self.mzThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.mzThresholdButton.clicked.connect(self.on_setMzThreshold_clicked)

		self.hbox.addWidget(self.mzThresholdText, 6, 0)
		self.hbox.addWidget(self.mzThresholdButton, 6, 1)

		# ppm threshold 'ppmThreshold'
		self.ppmThresholdText = QLabel('NMR ppm threshold (annotation match): ' + str(self.Attributes['ppmThreshold']))
		self.ppmThresholdButton = QPushButton("Change NMR ppm threshold (annotation match)")
		self.ppmThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.ppmThresholdButton.clicked.connect(self.on_setPpmThreshold_clicked)

		self.hbox.addWidget(self.ppmThresholdText, 7, 0)
		self.hbox.addWidget(self.ppmThresholdButton, 7, 1)

		# 'applySampleIntensityFilter'
		self.sampleIntensitySetText = QLabel('Calculate correlation on all samples or (relative) intensity filtered sample set: ' + self.Attributes['sampleIntensitySet'])
		self.sampleIntensitySetButton = QPushButton("Change sample set for correlation calculation")
		self.sampleIntensitySetButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.sampleIntensitySetButton.clicked.connect(self.on_sampleIntensitySetButton_clicked)

		self.hbox.addWidget(self.sampleIntensitySetText, 8, 0)
		self.hbox.addWidget(self.sampleIntensitySetButton, 8, 1)

		# 'sampleIntensityThreshold'
		self.sampleIntensityThresholdText = QLabel('Driver (relative) intensity threshold for defining sample set for correlation calculation: ' + str(self.Attributes['sampleIntensityThreshold']))
		self.sampleIntensityThresholdButton = QPushButton("Change driver (relative) intensity threshold")
		self.sampleIntensityThresholdButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.sampleIntensityThresholdButton.clicked.connect(self.on_setDriverThreshold_clicked)

		self.hbox.addWidget(self.sampleIntensityThresholdText, 9, 0)
		self.hbox.addWidget(self.sampleIntensityThresholdButton, 9, 1)
			
		# 'relativeIntensityMetric' for plotting NMR and targeted datasets
		self.relativeIntensityMetricText = QLabel('Metric for plotting NMR and targeted data feature intensities: ' + self.Attributes['relativeIntensityMetric'])
		self.relativeIntensityMetricButton = QPushButton("Change metric for plotting NMR and targeted data feature intensities")
		self.relativeIntensityMetricButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.relativeIntensityMetricButton.clicked.connect(self.on_relativeIntensityMetricButton_clicked)

		self.hbox.addWidget(self.relativeIntensityMetricText, 10, 0)
		self.hbox.addWidget(self.relativeIntensityMetricButton, 10, 1)
			
		# 'RANSACdegree'
		self.setRANSACdegreeText = QLabel('RANSAC degree: ' + str(self.Attributes['RANSACdegree']))
		self.setRANSACdegreeButton = QPushButton("Change RANSAC degree")
		self.setRANSACdegreeButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.setRANSACdegreeButton.clicked.connect(self.on_setRANSACdegree_clicked)

		self.hbox.addWidget(self.setRANSACdegreeText, 11, 0)
		self.hbox.addWidget(self.setRANSACdegreeButton, 11, 1)

		# 'saveDir'
		self.saveDirText = QLabel('Directory to save exports: ' + str(self.Attributes['saveDir']))
		self.saveDirButton = QPushButton("Change directory to save exports")
		self.saveDirButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.saveDirButton.clicked.connect(self.on_setsaveDir_clicked)

		self.hbox.addWidget(self.saveDirText, 12, 0)
		self.hbox.addWidget(self.saveDirButton, 12, 1)
		
		# Update settings and close
		self.closeButton = QPushButton("Update settings and close")
		self.closeButton.clicked.connect(self.on_closeButton_clicked)
		self.hbox.addWidget(self.closeButton, 13, 1, 1, 2)

		# Button to export settings and close
		self.exportButton = QPushButton("Export settings and close")
		self.exportButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self.exportButton.clicked.connect(self.on_exportButton_clicked)
		self.hbox.addWidget(self.exportButton, 14, 1, 1, 2)


	def getResults(self):
		""" Return results """
		
		if self.exec() == QDialog.DialogCode.Accepted:

			return self.Attributes


	def on_setCorrMethod_clicked(self):
		""" User input to change correlation method """

		options = ("pearson", "spearman", "kendall")
		option, ok = QInputDialog.getItem(self, "", "Select required correlation method:", options, 0, False)

		if ok and option:
			self.Attributes['correlationMethod'] = option
			self.correlationMethodText.setText('Correlation method: ' + self.Attributes['correlationMethod'])


	def on_setCorrRel_clicked(self):
		""" User input to change correlation kind (absolute or relative) """

		options = ("absolute", "relative")
		option, ok = QInputDialog.getItem(self, "", "Select required correlation kind:", options, 0, False)

		if ok and option:
			self.Attributes['correlationKind'] = option
			self.correlationKindText.setText('Correlation type ' + self.Attributes['correlationKind'])


	def on_setCorrelationThreshold_clicked(self):
		""" User input to change correlation threshold """

		x, ok = QInputDialog.getText(self, '', 'Enter required correlation threshold:')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not ((x < 1) & (x > 0)):
			_displayMessage("Correlation threshold must be a number in the range 0 to 1")

		else:
			self.Attributes['correlationThreshold'] = x
			self.correlationThresholdText.setText('Correlation threshold ' + str(self.Attributes['correlationThreshold']))


	def on_setStructuralThreshold_clicked(self):
		""" User input to change correlation threshold for defining structural associations """

		x, ok = QInputDialog.getText(self, '', 'Enter required correlation threshold (structural sets):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not ((x < 1) & (x > 0)):
			_displayMessage("Correlation threshold (structural sets) must be a number in the range 0 to 1")

		else:
			self.Attributes['structuralThreshold'] = x
			self.structuralThresholdText.setText('Correlation threshold (structural sets) ' + str(self.Attributes['structuralThreshold']))


	def on_setRtThreshold_clicked(self):
		""" User input to change LC-MS retention time tolerance for defining structural associations and match to annotations file """

		x, ok = QInputDialog.getText(self, '', 'Enter required retention time tolerance (structural sets):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = -1.0 # Bit of a hack so it fails

		if (x < 0):
			_displayMessage("LC-MS retention time tolerance (structural sets and annotation match) must be a number greater than zero")

		else:
			self.Attributes['rtThreshold'] = x
			self.rtThresholdText.setText('LC-MS RT threshold (structural sets and annotation match): ' + str(self.Attributes['rtThreshold']))


	def on_setMzThreshold_clicked(self):
		""" User input to change LC-MS m/z ppm tolerance for defining match to annotations file """

		x, ok = QInputDialog.getText(self, '', 'Enter required m/z ppm tolerance (annotation match):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = -1.0 # Bit of a hack so it fails

		if (x < 0):
			_displayMessage("LC-MS m/z ppm tolerance (annotation match) must be a number greater than zero")

		else:
			self.Attributes['mzThreshold'] = x
			self.mzThresholdText.setText('LC-MS m/z ppm threshold (annotation match): ' + str(self.Attributes['mzThreshold']))


	def on_setPpmThreshold_clicked(self):
		""" User input to change NMR ppm tolerance for defining match to annotations file """

		x, ok = QInputDialog.getText(self, '', 'Enter required retention time tolerance (annotation match):')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = -1.0 # Bit of a hack so it fails

		if (x < 0):
			_displayMessage("NMR ppm tolerance (annotation match) must be a number greater than zero")

		else:
			self.Attributes['ppmThreshold'] = x
			self.ppmThresholdText.setText('NMR ppm threshold (annotation match): ' + str(self.Attributes['ppmThreshold']))


	def on_sampleIntensitySetButton_clicked(self):
		""" User input for correlation calculation to toggle between using all samples and only those with intensity above threshold """

		options = ("All samples", "Intensity filtered samples")
		option, ok = QInputDialog.getItem(self, "", "Calculate correlation on all samples or (relative) intensity filtered sample set: ", options, 0, False)

		if ok and option:

			self.Attributes['sampleIntensitySet'] = option
			self.correlationMethodText.setText('Calculate correlation on all samples or (relative) intensity filtered sample set:  ' + self.Attributes['sampleIntensitySet'])

			if self.Attributes['sampleIntensitySet'] == 'All samples':
				self.Attributes['sampleIntensityThreshold'] = None
				self.sampleIntensityThresholdText.setText('Driver (relative) intensity threshold for defining sample set for correlation calculation: ' + str(self.Attributes['sampleIntensityThreshold']))


	def on_setDriverThreshold_clicked(self):
		""" User input to change intensity threshold for masking samples from correlation calculation """

		x, ok = QInputDialog.getText(self, '', 'Enter driver (relative) intensity threshold for defining sample set for correlation calculation:')

		# Check that correlation threshold meets requirements
		try:
			x = float(x)

		except:
			x = 100 # Bit of a hack so it fails

		if not ((x < 1) & (x > 0)):
			_displayMessage("Sample intensity threshold (relative intensity) must be a number between 0 and 1")

		else:
			self.Attributes['sampleIntensityThreshold'] = x
			self.sampleIntensityThresholdText.setText('Driver (relative) intensity threshold for defining sample set for correlation calculation: ' + str(self.Attributes['sampleIntensityThreshold']))


	def on_relativeIntensityMetricButton_clicked(self):
		""" User input to select metric for plotting NMR and targeted data feature intensities (one of mean, median, max) """
		
		options = ("mean", "median", "max")
		option, ok = QInputDialog.getItem(self, "", "Select required intensity metric:", options, 0, False)

		if ok and option:
			self.Attributes['relativeIntensityMetric'] = option
			self.relativeIntensityMetricText.setText('Metric for plotting NMR and targeted data feature intensities: ' + self.Attributes['relativeIntensityMetric'])
		
	
	def on_setRANSACdegree_clicked(self):
		"""  User input to set degree for RANSAC fit """
		
		x, ok = QInputDialog.getText(self, '', 'Enter required RANSAC degree (integer > 1):')
		
		# Check that correlation threshold meets requirements
		try:
			x = int(x)

		except:
			x = -1 # Bit of a hack so it fails

		if not ((x > 1)):
			_displayMessage("RANSAC degree must be an integer greater than zero")

		else:
			self.Attributes['RANSACdegree'] = x
			self.setRANSACdegreeText.setText('RANSAC degree: ' + str(self.Attributes['RANSACdegree']))


	def on_setsaveDir_clicked(self):
		""" User input to change directory where outputs are saved """

		saveDir = QFileDialog.getExistingDirectory(self, 'Select directory', '/home')

		self.Attributes['saveDir'] = saveDir
		self.saveDirText.setText('Directory to save exports: ' + str(self.Attributes['saveDir']))


	def on_exportButton_clicked(self):
		""" Export all settings as screenshot """
		
        # Export screenshot
		savePath = os.path.join(self.Attributes['saveDir'], 'ISTOCSY_settings.pdf')
		printer = _getPrinter(size=self.size(), savePath=savePath)

		#printer = QPrinter(QPrinter.PrinterMode.HighResolution)
		#printer.setOutputFileName(os.path.join(self.Attributes['saveDir'], 'ISTOCSY_settings.pdf'))
		#printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
		#size = self.size()
		#printer.setPageSize(QPageSize(QSizeF(size.width(), size.height()), QPrinter.Unit.DevicePixel)) # QPrinter.DevicePixel
		#printer.setFullPage(True)

		self.render(printer)

		self.accept()


	def on_closeButton_clicked(self):
		""" Close window """

		self.accept()