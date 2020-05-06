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

class _batchDialog(QDialog):

	def __init__(self, **kwargs):

		super(_batchDialog, self).__init__()

		# Set up default attributes
		self.Attributes = {
					'batchFilePath': None,
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

			self.setWindowTitle('Load/run Batch file')
			self.setGeometry(10, 10, 500, 300)

		self.hbox = QtGui.QGridLayout()
		self.setLayout(self.hbox)

		# Display batch file
		self.batchFileText = QLabel('Batch file location: ' + str(self.Attributes['batchFilePath']))
		self.hbox.addWidget(self.batchFileText, 1, 0)

		# Update annotations file
		self.batchFileButton = QtGui.QPushButton("Load new batch file")
		self.batchFileButton.setFocusPolicy(QtCore.Qt.NoFocus)
		self.batchFileButton.clicked.connect(self.on_batchFileButton_clicked)
		self.hbox.addWidget(self.batchFileButton, 1, 1)

		# Match annotations file to dataset
		self.closeButton = QtGui.QPushButton("Run ISTOCSY from batch file (if dataset loaded) and close")
		self.closeButton.clicked.connect(self.on_closeButton_clicked)
		self.hbox.addWidget(self.closeButton, 2, 1)


	def getResults(self):
		""" Return results """
		
		if self.exec_() == QDialog.Accepted:

			return self.Attributes

	def on_batchFileButton_clicked(self):
		""" User defined path to batch file """		
		
		# User input to define location of annotations file
		batchFilePath, ok = QFileDialog.getOpenFileName(self, 'Select batch file', '/home')

		# Update location
		self.Attributes['batchFilePath'] = batchFilePath
		self.batchFileText.setText('Batch file location: ' + str(self.Attributes['batchFilePath']))


	def on_closeButton_clicked(self):
		""" Closes window """
		
		self.accept()