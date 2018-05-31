#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for runISTOCSY.py

Created on Fri Apr  6 11:32:54 2018

@author: cs401
"""
import numpy as np
import pandas
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import pearsonr, spearmanr, kendalltau
from statsmodels.stats.multitest import multipletests


def _loadCSV(self, intensityDataFile, featureMetadataFile):
	""" Load data from csv """
	
	if ((intensityDataFile is None) or (featureMetadataFile is None)):
		raise TypeError('intensityDataFile and featureMetadataFile must be set')
	
	# Create dataset
	class Dataset(object):

		def __init__(self):
			self.intensityData = np.array(None)
			self.featureMetadata = pandas.DataFrame(None, columns=['Feature Name', 'Retention Time', 'm/z'])

	self.dataset = Dataset()

	self.dataset.intensityData = np.genfromtxt(intensityDataFile, delimiter=',')
	self.dataset.featureMetadata = pandas.read_csv(featureMetadataFile)

	# Check attributes
	ds, dv = self.dataset.intensityData.shape
	fv = self.dataset.featureMetadata.shape[0]
	if dv != fv:
		raise ValueError('intensityData and featureMetadata have different dimensions')
		
		
#def _loadData(self):
#	""" Load data from csv or nPYc dataset object """
#	
## 	TODO: add this functionality
#	
#	# Create dataset
#	class Dataset(object):
#
#		def __init__(self):
#			self.intensityData = np.array(None)
#			self.featureMetadata = pandas.DataFrame(None, columns=['Feature Name', 'Retention Time', 'm/z'])
#
#	self.dataset = Dataset()
#	
#	# nPYc dataset object
#	if (self.Attributes['nPYcDataset'] is not None):
#			
#		self.dataset = self.Attributes['nPYcDataset']
#		del self.Attributes['nPYcDataset']
#	
#	# Load from csv files
#	else:
#		
#		self.dataset.intensityData = np.genfromtxt(self.Attributes['intensityDataFile'], delimiter=',')
#		self.dataset.featureMetadata = pandas.read_csv(self.Attributes['featureMetadataFile'])
#
#	# Check attributes
#	ds, dv = self.dataset.intensityData.shape
#	fv = self.dataset.featureMetadata.shape[0]
#	if dv != fv:
#		raise ValueError('intensityData and featureMetadata have different dimensions')


def _findNearest(featureMetadata, Xvalue, Yvalue):
	""" Find the nearest point under the click

	:param pandas.dataFrame featureMetadata: feature metadata, must contain 'Retention Time' and 'm/z' columns
	:param float Xvalue: x axis value of point
	:param float Yvalue: y axis value of point
	"""

	xtol = np.sort(featureMetadata['Retention Time'])
	xtol = np.median(np.sort(xtol))
	ytol = np.sort(featureMetadata['m/z'])
	ytol = np.median(np.sort(ytol))
	x = 0
	y = 0

	temp = (featureMetadata['Retention Time'] >= Xvalue - x) & (featureMetadata['Retention Time'] <= Xvalue + x) & (featureMetadata['m/z'] >= Yvalue - y) & (featureMetadata['m/z'] <= Yvalue + y)

	while sum(temp==True) == 0:

		x = x + xtol
		y = y + ytol

		temp = (featureMetadata['Retention Time'] >= Xvalue - x) & (featureMetadata['Retention Time'] <= Xvalue + x) & (featureMetadata['m/z'] >= Yvalue - y) & (featureMetadata['m/z'] <= Yvalue + y)

	test = featureMetadata.index[temp].values

	return test[0]


def _shiftedColorMap(cmap, start=0.0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
	'''
	From Paul H at Stack Overflow
	http://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib
	Function to offset the "center" of a colormap. Useful for
	data with a negative min and positive max and you want the
	middle of the colormap's dynamic range to be at zero

	Input
	-----
	  cmap : The matplotlib colormap to be altered
	  start : Offset from lowest point in the colormap's range.
		  Defaults to 0.0 (no lower ofset). Should be between
		  0.0 and `midpoint`.
	  midpoint : The new center of the colormap. Defaults to
		  0.5 (no shift). Should be between 0.0 and 1.0. In
		  general, this should be  1 - vmax/(vmax + abs(vmin))
		  For example if your data range from -15.0 to +5.0 and
		  you want the center of the colormap at 0.0, `midpoint`
		  should be set to  1 - 5/(5 + 15)) or 0.75
	  stop : Offset from highets point in the colormap's range.
		  Defaults to 1.0 (no upper ofset). Should be between
		  `midpoint` and 1.0.
	'''

	cdict = {
		'red': [],
		'green': [],
		'blue': [],
		'alpha': []
	}

	# regular index to compute the colors
	reg_index = np.linspace(start, stop, 257)

	# shifted index to match the data
	shift_index = np.hstack([
		np.linspace(0.0, midpoint, 128, endpoint=False),
		np.linspace(midpoint, 1.0, 129, endpoint=True)
	])

	for ri, si in zip(reg_index, shift_index):
		r, g, b, a = cmap(ri)

		cdict['red'].append((si, r, r))
		cdict['green'].append((si, g, g))
		cdict['blue'].append((si, b, b))
		cdict['alpha'].append((si, a, a))

	newcmap = LinearSegmentedColormap(name, cdict)
	plt.register_cmap(cmap=newcmap)

	return newcmap


def _calcCorrelation(X, Y, correlationMethod='pearson', correctionMethod=None):
	"""
	Calculates the specified correlation and correction for multiple tests (if required)

	Code from:
		scipy.stats import pearsonr, spearmanr, kendalltau
		statsmodels.stats.multitest import multipletests

	See relevant documentation for details of allowed methods (listed in drop down menu in ISTOCSY app)

	:param numpy.ndarray X: intensity data for all features to calculate correlation to
	:param numpy.ndarray Y: intensity data for driver feature
	:param str correlationMethod: correlation method, one of 'pearson', 'spearman', 'kendalltau'
	:param str correctionMethod: FDR correction method, see documentation for options
	"""

	# Calculate correlation
	cVect = np.zeros(X.shape[1])
	pVect = np.zeros(X.shape[1])

	for col in range(X.shape[1]):

		if correlationMethod == 'pearson':
			cVect[col], pVect[col] = pearsonr(X[:,col], Y)

		elif correlationMethod == 'spearman':
			cVect[col], pVect[col] = spearmanr(X[:,col], Y)

		else:
			cVect[col], pVect[col] = kendalltau(X[:,col], Y)

	# Calculate corrected p-values
	if correctionMethod is None:
		qVect = None

	else:

		qVect = multipletests(pVect, method=correctionMethod)
		qVect = qVect[1]

	return cVect, pVect, qVect


def _findStructuralSets(featureTable, X, attributes):
	"""
	Finds sets of features in featureTable which are resulting from the same compound (in theory!) 
	
	Features in the same structural set are defined as those which:
		- correlate with >= attributes['structuralThreshold']
		- are within a defined retention time window (attributes['rtThreshold'])
	
	:param pandas.dataFrame featureTable feature metadata, must contain 'Retention Time', and 'Correlation' columns
	:param numpy.ndarray X: intensity data for all features in featureTable
	:param dictionary attributes: settings, must contain 'structuralThreshold', 'rtThreshold', 'correlationMethod' and 'correctionMethod'	
	"""
	
	# TODO: correlation within tempTable - sets can depend on which feature is selected as a driver...
	
	# If rtThreshold is None, set to max*2 so all features included
	if attributes['rtThreshold'] is None:
		rtThreshold = np.max(featureTable['Retention Time'])*2
	else:
		rtThreshold = attributes['rtThreshold']
		
	nv = featureTable.shape[0]
	
	# Define set 1
	findSet = (featureTable['Correlation'] >= attributes['structuralThreshold']) & (featureTable['Retention Time'] < featureTable.loc[featureTable.index[0],'Retention Time']+rtThreshold) & (featureTable['Retention Time'] > featureTable.loc[featureTable.index[0],'Retention Time']-rtThreshold)
	featureTable['Set'] = 1
	nv = nv - sum(findSet)
	delTable = featureTable.copy()
	setix = 2

	while nv != 0:
		delTable = delTable[findSet==False].copy()
		delcVect = _calcCorrelation(X[:,delTable.index], X[:,delTable.index[0]], correlationMethod=attributes['correlationMethod'], correctionMethod=attributes['correctionMethod'])
		findSet = (delcVect[0] >= attributes['structuralThreshold']) & (delTable['Retention Time'] < delTable.loc[delTable.index[0],'Retention Time']+rtThreshold) & (delTable['Retention Time'] > delTable.loc[delTable.index[0],'Retention Time']-rtThreshold)
		for i in np.arange(sum(findSet==True)):
			featureTable.loc[delTable.index[findSet][i], 'Set'] = setix

		setix = setix+1
		nv = nv - sum(findSet)
	
	return featureTable	
