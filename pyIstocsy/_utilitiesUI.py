#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI related utility functions for runISTOCSY.py

Created on Wed May 30 14:56:56 2018

@author: cs401
"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSizeF
from PyQt5.QtPrintSupport import QPrinter
import os
import numpy as np

def _displayMessage(messageText):
	"""
	Creates a message box containing messageText

	:param str messageText: text for display
	"""

	message = QMessageBox()
	message.setText(messageText)
	message.exec_()


def _actionIfChange(self, original, new, recalcCorrelation, text):
	"""
	Updates/resets plot if a parameter has been changed

	:param ISTOCSY self: ISTOCSY object
	:param original: original value
	:param new: new value
	:param bool recalcCorrelation: whether correlation vector needs recalculating
	:param str text: text to display in message box
	"""

	if original != new:

		if hasattr(self, 'latestpoint'):
			self.Attributes['recalculateCorrelation'] = recalcCorrelation
			self.updatePlot(self.latestpoint)

		else:
			self.resetPlot()

		_displayMessage(text + str(new))


def _writeOutput(self):
	""" Save correlated feature list to csv with screenshot of app """

	if hasattr(self, 'tempTable'):
		saveName = self.tempTable.loc[self.latestpoint,'Feature Name'].replace('/','')

		# Sort table so driver (correlation==1) at top and export csv
#		tempTable = self.tempTable.sort_values('Correlation', axis=0, ascending=False, inplace=False)
		self.tempTable.to_csv(os.path.join(self.Attributes['saveDir'], saveName + '.csv'), encoding='utf-8')

		# Save internal correlation, RT difference and overlap (both passing threshold) matrices
		# NOTE, this is temporary
#		np.savetxt(os.path.join(self.Attributes['saveDir'], saveName + '_internalCorrelation.csv'), self.matrices['C'], delimiter=",")
#		np.savetxt(os.path.join(self.Attributes['saveDir'], saveName + '_internalRTdifferences.csv'), self.matrices['R'], delimiter=",")
#		np.savetxt(os.path.join(self.Attributes['saveDir'], saveName + '_internalOverlap.csv'), self.matrices['O'], delimiter=",")

	else:
		saveName = 'ISTOCSY GUI'

	# Save screen shot of app
	printer = QPrinter(QPrinter.HighResolution)
	printer.setOutputFileName(os.path.join(self.Attributes['saveDir'], saveName + '_screenshot.pdf'))
	printer.setOutputFormat(QPrinter.PdfFormat)
	size = self.size()
	printer.setPaperSize(QSizeF(size.width(), size.height()), QPrinter.DevicePixel) # QPrinter.DevicePixel
	printer.setFullPage(True)
	self.render(printer)
