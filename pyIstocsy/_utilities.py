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
import networkx as nx

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

	Clusters are defined using networkx

	:param pandas.dataFrame featureTable feature metadata, must contain 'Retention Time', and 'Correlation' columns
	:param numpy.ndarray X: intensity data for all features in featureTable
	:param dictionary attributes: settings, must contain 'structuralThreshold', 'rtThreshold', 'correlationMethod' and 'correctionMethod'
	"""

	# Calculate the correlation and the difference in RT between all features in table
	nv = featureTable.shape[0]
	C = np.zeros([nv, nv])
	R = np.zeros([nv, nv])
	for i in np.arange(0, nv):

		# Correlation
		delcVect = _calcCorrelation(X[:,featureTable.index], X[:,featureTable.index[i]], correlationMethod=attributes['correlationMethod'], correctionMethod=attributes['correctionMethod'])
		C[i,:] = delcVect[0]

		# Difference in RT
		R[i,:] = np.abs(featureTable['Retention Time'].values - featureTable.loc[featureTable.index[i], 'Retention Time'])

	# Boolean matrices for correlation and RT passing thresholds
	Cpass = C >= attributes['structuralThreshold']
	Rpass = R <= attributes['rtThreshold']

	# Feature connections passing both threshold
	O = Cpass & Rpass

	# Cluster
	G = nx.from_numpy_matrix(O)
	temp = list(nx.connected_components(G))

	# Extract unique sets from clustering network
	setix = 1
	for i in np.arange(len(temp)):
		for j in np.arange(nv):
			if j in temp[i]:
				featureTable.loc[featureTable.index[j], 'Set'] = setix
		setix = setix+1

	# Set as int
	featureTable['Set'] = featureTable['Set'].astype(int)

	# Sort by clusters
	featureTable.sort_values('Set', axis=0, ascending=True, inplace=True)

	return featureTable