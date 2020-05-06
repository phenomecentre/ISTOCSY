#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 17:10:24 2020

@author: cs401
"""

import sip
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QDialog, QFileDialog
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class _annotationsDialog(QDialog):

	def __init__(self, **kwargs):

		super(_annotationsDialog, self).__init__()

		# Set up default attributes
		self.Attributes = {
					'annotationFilePath': None,
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

			self.setWindowTitle('Load/match Annotations')
			self.setGeometry(10, 10, 500, 300)

		self.hbox = QtGui.QGridLayout()
		self.setLayout(self.hbox)

		# Display annotations file
		self.annotationFileText = QLabel('Annotations file location: ' + str(self.Attributes['annotationFilePath']))
		self.hbox.addWidget(self.annotationFileText, 1, 0)

		# Update annotations file
		self.annotationFileButton = QtGui.QPushButton("Load new annotations file")
		self.annotationFileButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.annotationFileButton.clicked.connect(self.on_annotationFileButton_clicked)
		self.hbox.addWidget(self.annotationFileButton, 1, 1)

		# Match annotations file to dataset
		self.closeButton = QtGui.QPushButton("Match to ISTOCSY dataset (if available) and close")
		self.closeButton.clicked.connect(self.on_closeButton_clicked)
		self.hbox.addWidget(self.closeButton, 2, 1)


	def getResults(self):
		""" Return results """
		
		if self.exec_() == QDialog.Accepted:

			return self.Attributes

	def on_annotationFileButton_clicked(self):
		""" User input to define file path to annotations file """
		
		# User input to define location of annotations file
		annotationFilePath, ok = QFileDialog.getOpenFileName(self, 'Select annotations data file', '/home')

		# Update location
		self.Attributes['annotationFilePath'] = annotationFilePath
		self.annotationFileText.setText('Annotations file location: ' + str(self.Attributes['annotationFilePath']))


	def on_closeButton_clicked(self):
		""" Close window """

		self.accept()
