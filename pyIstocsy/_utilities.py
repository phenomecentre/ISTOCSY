#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for runISTOCSY.py

Created on Fri Apr  6 11:32:54 2018

@author: cs401
"""

import os
import numpy as np
import pandas
from scipy.stats import pearsonr, spearmanr, kendalltau
import networkx as nx
import warnings
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QSizeF
from PyQt6.QtPrintSupport import QPrinter
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import (LinearRegression, RANSACRegressor)


def _loadDataset(self, intensityDataFile=None, featureMetadataFile=None, sampleMetadataFile=None, datasetName='Data', datasetType='Targeted'):
	""" Load data from intensityData, featureMetadata and sampleMetadata csv files """

	# Check input
	if ((intensityDataFile is None) or (featureMetadataFile is None) or (sampleMetadataFile is None)):
		raise TypeError('Either intensityDataFile, featureMetadataFile and sampleMetadataFile files must be set')

	# Import data and do some basic checks
	(intensityData, featureMetadata, sampleMetadata) = _importAndCheckData(intensityDataFile, featureMetadataFile, sampleMetadataFile, datasetName, datasetType)

	# Update details for number of samples and features in loaded dataset
	self.Attributes['datasetsDetails'][-1].append(intensityData.shape[0])
	self.Attributes['datasetsDetails'][-1].append(intensityData.shape[1])

	# If this is the first dataset loaded
	if not hasattr(self, 'dataset'):

		# Create dataset
		class Dataset(object):

			def __init__(self):
				self.intensityData = np.array(None)
				self.featureMetadata = pandas.DataFrame(None, columns=['Dataset Name', 'Data Type', 'Feature Name', 'Feature Name Original', 'Retention Time', 'm/z', 'ppm', 'Targeted Feature Number', 'Median Intensity Scaled'])
				self.sampleMetadata = pandas.DataFrame(None, columns=['Sample ID', 'Sample File Name'])

		self.dataset = Dataset()

		# Load into dataset object
		self.dataset.intensityData = intensityData
		self.dataset.featureMetadata = self.dataset.featureMetadata.append(featureMetadata, ignore_index=True, sort=False)
		self.dataset.sampleMetadata = self.dataset.sampleMetadata.append(sampleMetadata, ignore_index=True, sort=False)

	# Else, match new data into existing (on Sample ID)
	else:

		# Match datasets
		self = _matchDatasets(self, intensityData, featureMetadata, sampleMetadata)

	# Enforce types
	try:
		self.dataset.featureMetadata['ppm'] = self.dataset.featureMetadata['ppm'].astype(np.float64)
		self.dataset.featureMetadata['Retention Time'] = self.dataset.featureMetadata['Retention Time'].astype(np.float64)
		self.dataset.featureMetadata['m/z'] = self.dataset.featureMetadata['m/z'].astype(np.float64)
		self.dataset.featureMetadata['Targeted Feature Number'] = self.dataset.featureMetadata['Targeted Feature Number'].astype(np.float64)
	except:
		_displayMessage('ALERT: please check for non-numerical values in appropriate featureMetadata.csv file columns')


	# Update details for number of samples and features in full ISTOCSY dataset
	self.Attributes['istocsyDatasetDetails'][0], self.Attributes['istocsyDatasetDetails'][1] = self.dataset.intensityData.shape



def _importAndCheckData(intensityDataFile, featureMetadataFile, sampleMetadataFile, datasetName, datasetType, relativeIntensityMetric='max'):
	""" Helper function to import new dataset """
		
	# Import data
	intensityData = np.genfromtxt(intensityDataFile, delimiter=',')
	featureMetadata = pandas.read_csv(featureMetadataFile, index_col=False)#index_col=0)
	sampleMetadata = pandas.read_csv(sampleMetadataFile, index_col=False)#index_col=0)

	# Check attributes (new data)
	ds, dv = intensityData.shape
	fv = featureMetadata.shape[0]
	ss = sampleMetadata.shape[0]

	if dv != fv:
		raise ValueError('intensityData and featureMetadata have different dimensions')
	if ds != ss:
		raise ValueError('intensityData and sampleMetadata have different dimensions')

	# Check 'Sample ID' and 'Feature Name' present
	try:
		featureMetadata['Feature Name'] = featureMetadata['Feature Name'].astype(str)
		sampleMetadata['Sample ID'] = sampleMetadata['Sample ID'].astype(str)
	except:
		raise ValueError('"Feature Name" and "Sample ID" columns must be present')

	featureMetadata['Dataset Name'] = datasetName
	featureMetadata['Data Type'] = datasetType
	if datasetType == 'Targeted':
		featureMetadata['Targeted Feature Number'] = np.arange(dv)

	# Check for and exclude samples with duplicate 'Sample ID's
	u_ids, u_counts = np.unique(sampleMetadata['Sample ID'], return_counts=True)
	if any(u_counts > 1):

		# Warn
		warnings.warn('Check and remove duplicates in sampleMetadata file, by default these will be excluded')

		# By default delete duplicates
		sampleList = u_ids[u_counts > 1]

		sampleMask = np.squeeze(np.ones([sampleMetadata.shape[0], 1], dtype=bool), axis=1)

		for sample in sampleList:
			sampleMask[sampleMetadata[sampleMetadata['Sample ID'] == sample].index] = False

		sampleMetadata = sampleMetadata.loc[sampleMask]
		sampleMetadata.reset_index(drop=True, inplace=True)
		intensityData = intensityData[sampleMask, :]

	# NOTE: nan values must not be present (for correlation calculation) - replace with zeros
	if (np.isnan(intensityData).any()):

		# Warn
		warnings.warn('Missing (nan) values found in intensity data file, by default these will be replaced with zeros')

		# By default replace with zeros
		intensityData[np.isnan(intensityData)] = 0

	# Calculate 'Relative Intensity' for NMR and Targeted feature plotting
	if relativeIntensityMetric == 'max':
		featureMetadata['Relative Intensity'] = np.nanmax(intensityData, axis=0)

	elif relativeIntensityMetric == 'median':
		featureMetadata['Relative Intensity'] = np.nanmedian(intensityData, axis=0)
		
	else:
		featureMetadata['Relative Intensity'] = np.nanmean(intensityData, axis=0)

	# Scale so max value is 1 (if multiple datasets present on different scales)
	featureMetadata['Relative Intensity'] = np.divide(featureMetadata['Relative Intensity'], np.nanmax(featureMetadata['Relative Intensity']))

    # Append dataset name to 'Feature Name' for plotting
	featureMetadata['Feature Name Original'] = featureMetadata['Feature Name']
	featureMetadata['Feature Name'] = datasetName + '_' + featureMetadata['Feature Name Original']
	
	# Append dataset name to 'Sample File Name'
	sampleMetadata['Sample File Name'] = datasetName + '_' + sampleMetadata['Sample File Name']

	return intensityData	, featureMetadata, sampleMetadata


def _matchDatasets(self, intensityData, featureMetadata, sampleMetadata):
	""" Helper function to match new dataset to existing """
	
	# NOTE: keep ONLY samples that are in all datasets, otherwise correlation structure inaccurate!

	# Set up new intensityData to be filled
	ns1, nv1 = self.dataset.intensityData.shape
	ns2, nv2 = intensityData.shape
	intensityDataNew = np.zeros([ns1+ns2, nv1+nv2])
	sampleDataIndexIX1 = []
	sampleDataIndexIX2 = []
	intensityDataIndex = 0

	# Determine 'Targeted Feature Number' for starting index
	tfn_ix = np.max(self.dataset.featureMetadata['Targeted Feature Number']) + 1
	if np.isnan(tfn_ix):
		tfn_ix=0

	# Update 'Targeted Feature Number' if new dataset is this type
	if featureMetadata['Data Type'][0] == 'Targeted':
		featureMetadata['Targeted Feature Number'] = featureMetadata['Targeted Feature Number'] + tfn_ix

	# Create merged list of all sample IDs
	sampleIDs_all = np.unique(self.dataset.sampleMetadata['Sample ID'].append(sampleMetadata['Sample ID']))

	for sampleID in sampleIDs_all:
		ix1 = self.dataset.sampleMetadata[sampleID == self.dataset.sampleMetadata['Sample ID']].index
		ix2 = sampleMetadata[sampleID == sampleMetadata['Sample ID']].index

		# If sampleID present in both datasets - match sampleMetadata to existing
		if (not ix1.empty) & (not ix2.empty):
			intensityDataNew[intensityDataIndex, 0:nv1] = self.dataset.intensityData[ix1, :]
			intensityDataNew[intensityDataIndex, nv1:nv1+nv2] = intensityData[ix2, :]
			sampleDataIndexIX1.append(ix1[0])
			sampleDataIndexIX2.append(ix2[0])
			intensityDataIndex = intensityDataIndex + 1

	# Sort new sampleMetadata
	self.dataset.sampleMetadata = self.dataset.sampleMetadata.loc[sampleDataIndexIX1,:]
	self.dataset.sampleMetadata.reset_index(drop=True, inplace=True)
	sampleMetadata = sampleMetadata.loc[sampleDataIndexIX2,:]
	sampleMetadata.reset_index(drop=True, inplace=True)
	self.dataset.sampleMetadata['Sample File Name'] = self.dataset.sampleMetadata['Sample File Name'] + ';' + sampleMetadata['Sample File Name']

	# Append new featureMetadata
	self.dataset.featureMetadata = self.dataset.featureMetadata.append(featureMetadata, sort=False)
	self.dataset.featureMetadata.reset_index(drop=True, inplace=True)

	# Overwrite intensityData
	self.dataset.intensityData = intensityDataNew[0:intensityDataIndex,:]#nsIX,:]

	# TODO sort NMR so ppm ascending?

	return (self)


def _deleteDataset(self, datasetToDelete):
	""" Delete existing dataset """
	
	# Find features corresponding to dataset
	featureMask = self.dataset.featureMetadata['Dataset Name'] == datasetToDelete
	
	# Find samples corresponding to dataset (matches datasetToDelete name in 'Sample File Name' column)
	allSamples = self.dataset.sampleMetadata['Sample File Name'].str.split(";", expand=True)
	sampleMask = []
	
	for col in allSamples.columns:
		if allSamples.loc[0, col].startswith(datasetToDelete):
			sampleMask.append(col)

	allSamples.drop(columns=sampleMask, inplace=True)	
	
	# If no samples or feature remain, reset dataset
	if (sum(featureMask)==len(featureMask) and allSamples.shape[1]==0):
		
		# Delete dataset
		del(self.dataset)
		
		# Reset Attributes['istocsyDatasetDetails']
		self.Attributes['istocsyDatasetDetails'] = [None] * 2
		
	else:
		
		# Remove features from intensityData
		self.dataset.intensityData = self.dataset.intensityData[:,~featureMask.values]		
			
		# Remove features from featureMetadata
		self.dataset.featureMetadata = self.dataset.featureMetadata.loc[~featureMask.values]
		self.dataset.featureMetadata.reset_index(drop=True, inplace=True)
	
		# Remove sample names from sampleMetadata
		self.dataset.sampleMetadata['Sample File Name'] = allSamples[allSamples.columns].apply(lambda row: '; '.join(row.values.astype(str)), axis=1)

		# Update numbers in Attributes['istocsyDatasetDetails']
		self.Attributes['istocsyDatasetDetails'][0], self.Attributes['istocsyDatasetDetails'][1] = self.dataset.intensityData.shape	
				
	# Update Attributes['datasetsDetails']
	self.Attributes['datasetsDetails'] = [i for i in self.Attributes['datasetsDetails'] if i[0] != datasetToDelete]


def _loadAnnotations(self):
	""" Load annotations csv file """

	# Check input
	if (self.Attributes['annotationFilePath'] is None):
		raise TypeError('Annotation file path must be set')

	# Import annotation file
	annotationData = pandas.read_csv(self.Attributes['annotationFilePath'], index_col=False)

	# Either create or append to existing data
	if not hasattr(self, 'annotationData'):

		self.annotationData = pandas.DataFrame(None, columns=['Annotation', 'Retention Time', 'm/z', 'ppm'])

	self.annotationData = self.annotationData.append(annotationData, sort=False)

	self.annotationData.reset_index(drop=True, inplace=True)

	# Ensure columns set to right data type
	try:
		self.annotationData['Annotation'] = self.annotationData['Annotation'].astype(str)
		self.annotationData['ppm'] = self.annotationData['ppm'].astype(np.float64)
		self.annotationData['Retention Time'] = self.annotationData['Retention Time'].astype(np.float64)
		self.annotationData['m/z'] = self.annotationData['m/z'].astype(np.float64)

	except:

		raise ValueError('ALERT: please check fields in ' + self.Attributes['annotationDataFile'])
		_displayMessage('ALERT: please check fields in ' + self.Attributes['annotationDataFile'])


def _matchAnnotations(self):
	""" Match annotations csv file to data """

	# TODO do not match to targeted data? Although OK for now, validation stages!

	# Do not run match to annotation file again if already matched
	mask = self.dataset.featureMetadata['Feature Name'].str.contains("_annotationMatch_")

	for i in range(self.annotationData.shape[0]):

		# LC-MS annotation
		if np.isfinite(self.annotationData.loc[i, 'Retention Time']):

			temp = (self.dataset.featureMetadata.loc[~mask, 'Retention Time'] >= self.annotationData.loc[i, 'Retention Time'] - self.Attributes['rtThreshold']) & (self.dataset.featureMetadata.loc[~mask, 'Retention Time'] <= self.annotationData.loc[i, 'Retention Time'] + self.Attributes['rtThreshold']) & (np.multiply(np.divide(np.abs(self.dataset.featureMetadata.loc[~mask, 'm/z'] - self.annotationData.loc[i, 'm/z']), self.annotationData.loc[i, 'm/z']), 1000000) <= self.Attributes['mzThreshold'])

		# NMR annotation
		else:

			temp = (self.dataset.featureMetadata.loc[~mask, 'ppm'] >= self.annotationData.loc[i, 'ppm'] - self.Attributes['ppmThreshold']) & (self.dataset.featureMetadata.loc[~mask, 'ppm'] <= self.annotationData.loc[i, 'ppm'] + self.Attributes['ppmThreshold'])

		# Append feature name with annotataion match
		if (sum(temp)>=1):
			temp = temp.index[temp==True]
			self.dataset.featureMetadata.loc[temp, 'Feature Name'] = self.dataset.featureMetadata.loc[temp, 'Feature Name'] + '_annotationMatch_' + self.annotationData.loc[i, 'Annotation']


def _findNearest(featureMetadata, Xon, Yon, Xvalue, Yvalue):
	""" Find the nearest point under the click

	:param pandas.dataFrame featureMetadata: feature metadata, must contain 'Retention Time' and 'm/z' columns
	:param float Xvalue: x axis value of point
	:param float Yvalue: y axis value of point
	"""

	xtol = np.sort(featureMetadata[Xon])
	xtol = np.median(np.sort(xtol))
	ytol = np.sort(featureMetadata[Yon])
	ytol = np.median(np.sort(ytol))
	x = 0
	y = 0

	temp = (featureMetadata[Xon] >= Xvalue - x) & (featureMetadata[Xon] <= Xvalue + x) & (featureMetadata[Yon] >= Yvalue - y) & (featureMetadata[Yon] <= Yvalue + y)

	while sum(temp==True) == 0:

		x = x + xtol
		y = y + ytol

		temp = (featureMetadata[Xon] >= Xvalue - x) & (featureMetadata[Xon] <= Xvalue + x) & (featureMetadata[Yon] >= Yvalue - y) & (featureMetadata[Yon] <= Yvalue + y)

	test = featureMetadata.index[temp].values

	return test[0]


def _applySampleMask(self, applyMask, threshold=None):
    """
    Returns sampleMask - mask of which samples correlation values should be calculated on

    Any samples with intensity < threshold will be masked
    """

    if applyMask == "All samples":

        sampleMask = True

    else:

        # Extract driver peak intensity values for all samples
        xVals = self.dataset.intensityData[:,self.Attributes['driver']]

        # Calculate relative values
        xVals = xVals/np.nanmax(xVals)

        # SampleMask is false for any samples with intensity < threshold
        sampleMask = xVals >= threshold

    return sampleMask


def _calcCorrelation(X, driverIX=None, correlationMethod='pearson', sampleMask=None):
	"""
	Calculates the specified correlation and correction for multiple tests (if required)

	Code from:
		scipy.stats import pearsonr, spearmanr, kendalltau
		statsmodels.stats.multitest import multipletests

	See relevant documentation for details of allowed methods (listed in drop down menu in ISTOCSY app)

	:param numpy.ndarray X: intensity data for all features to calculate correlation to
	:param numpy.ndarray Y: intensity data for driver feature
	:param str correlationMethod: correlation method, one of 'pearson', 'spearman', 'kendalltau'
	"""

	if driverIX is not None:

		# Apply sampleMask if required
		if sampleMask is not None:
			X=X[sampleMask,:]

		# Fastest correlation method
		cVect = np.zeros(X.shape[1])

		if correlationMethod == 'pearson':
			for col in np.arange(X.shape[1]):
				cVect[col], pVal = pearsonr(X[:,col], X[:,driverIX])

		elif correlationMethod == 'spearman':
			for col in np.arange(X.shape[1]):
				cVect[col], pVal = spearmanr(X[:,col], X[:,driverIX])

		else:
			for col in np.arange(X.shape[1]):
				cVect[col], pVal = kendalltau(X[:,col], X[:,driverIX])

	else:

		cVect = np.zeros([X.shape[1], X.shape[1]])

		if correlationMethod == 'pearson':
			for col in range(X.shape[1]):
				for col2 in range(col, X.shape[1]):
					cVal, pVal = pearsonr(X[:,col], X[:,col2])
					cVect[col,col2] = cVal
					cVect[col2,col] = cVal

		elif correlationMethod == 'spearman':
			for col in range(X.shape[1]):
				for col2 in range(col, X.shape[1]):
					cVal, pVal = spearmanr(X[:,col], X[:,col2])
					cVect[col,col2] = cVal
					cVect[col2,col] = cVal

		else:
			for col in range(X.shape[1]):
				for col2 in range(col, X.shape[1]):
					cVal, pVal = kendalltau(X[:,col], X[:,col2])
					cVect[col,col2] = cVal
					cVect[col2,col] = cVal

	# Convert nan values to zero
	cVect[np.isnan(cVect)] = 0

	return cVect

def _dropStructuralSetInfo(self):
	""" Delete any exisiting structural set info """
	
	try:
		self.dataset.featureMetadata.drop(columns=['Set', 'SortedIX', 'Average Set Correlation'], inplace=True)
	except:
		pass


def _findStructuralSets(self):
	"""
	Finds sets of features in featureTable which are resulting from the same compound (in theory!)

	Features in the same structural set are defined as those which:
		- correlate with >= attributes['structuralThreshold']
		- are within a defined retention time window (attributes['rtThreshold'])

	Clusters are defined using networkx

	:param pandas.dataFrame featureTable feature metadata, must contain 'Retention Time', and 'Correlation' columns
	:param numpy.ndarray intensityData: intensity data for all features in featureTable
	:param int driverIX: index of driver feature
	:param dictionary attributes: settings, must contain 'structuralThreshold', 'rtThreshold', 'correlationMethod'
	"""

	# Delete columns from existing featureMetadata if has been run previously
	_dropStructuralSetInfo(self)

	# Extract features above correlation threshold only
	featureTable = self.dataset.featureMetadata[self.dataset.featureMetadata['Feature Mask']].copy()

	# Return correlation between all features above threshold
	C = _calcCorrelation(self.dataset.intensityData[:,self.dataset.featureMetadata['Feature Mask']], correlationMethod=self.Attributes['correlationMethod'])

	# Calculate difference in RT
	RT = np.expand_dims(featureTable['Retention Time'].values, axis=1)
	RT = np.tile(RT, featureTable.shape[0])
	R = np.abs(RT - np.transpose(RT))

	# Set R to zero for NMR/Targeted features
	R[np.isnan(R)] = 0

	# Boolean matrices for correlation and RT passing thresholds
	Cpass = C >= self.Attributes['structuralThreshold']
	Rpass = R <= self.Attributes['rtThreshold']

	# Feature connections passing both threshold
	O = Cpass & Rpass

	# Cluster
	G = nx.from_numpy_matrix(O)
	temp = list(nx.connected_components(G))

	# Extract unique sets from clustering network
	setix = 1
	for i in np.arange(len(temp)):
		for j in np.arange(featureTable.shape[0]):
			if j in temp[i]:
				featureTable.loc[featureTable.index[j], 'Set'] = setix
		setix = setix+1

	# Set as int
	featureTable['Set'] = featureTable['Set'].astype(int)

	# Driver should be in Set 1
	driverSet = featureTable.loc[self.Attributes['driver'], 'Set']
	switchD = featureTable['Set'] == driverSet
	featureTable.loc[featureTable.index[featureTable['Set'] == 1], 'Set'] = driverSet
	featureTable.loc[featureTable.index[switchD==True], 'Set'] = 1

	# Sort by average correlation to driver, then by RT
	sets = np.unique(featureTable['Set'])

	for i in sets:
		setAv = np.mean(featureTable.loc[featureTable['Set']==i, 'Correlation'])
		featureTable.loc[featureTable['Set']==i, 'Average Set Correlation'] = setAv

#	featureTable.sort_values(['Average Set Correlation','Retention Time'], ascending=[False, True], inplace=True)
	featureTable.sort_values(['Set','Retention Time'], ascending=[True, True], inplace=True)

	# Add index for plotting
	featureTable['SortedIX'] = np.arange(featureTable.shape[0])

	# save results to featureMetadata table
	self.dataset.featureMetadata = self.dataset.featureMetadata.merge(featureTable[['Set', 'SortedIX', 'Average Set Correlation']], how='left', left_index=True, right_index=True)


def _displayMessage(messageText):
	"""
	Creates a message box containing messageText

	:param str messageText: text for display
	"""

	message = QMessageBox()
	message.setText(messageText)
	message.exec()


def _writeOutput(self, mask, unittest=False):
	""" Export correlated feature list to csv with screenshot of app """

	featureMetadata = self.dataset.featureMetadata.copy()
	savePath = os.path.join(self.Attributes['saveDir'], self.Attributes['saveName'])

	if mask is not None:
		featureMetadata = featureMetadata.loc[mask,:]
	else:
		savePath = savePath + '_allFeatures'

	# Save output
	featureMetadata.to_csv(savePath + '.csv', encoding='utf-8')

	# Save screen shot of app (falls over in testing so only when running for real)
	if unittest is False:
		printer = QPrinter(QPrinter.HighResolution)
		printer.setOutputFileName(savePath + '_screenshot.pdf')
		printer.setOutputFormat(QPrinter.PdfFormat)
		size = self.size()
		printer.setPaperSize(QSizeF(size.width(), size.height()), QPrinter.DevicePixel) # QPrinter.DevicePixel
		printer.setFullPage(True)
		self.render(printer)

	# Export RANSAC outliers
	if hasattr(self, 'RANSAC'):

		self.RANSAC['outliers'].to_csv(savePath.replace('_allFeatures', '') + '_RANSACoutliers.csv', encoding='utf-8')


def _writeData(self):
	""" Export full ISTOCSY dataset """

	# Export intensity data
	np.savetxt(os.path.join(self.Attributes['saveDir'], 'ISTOCSY_dataset_intensityData.csv'), self.dataset.intensityData, delimiter=",")

	# Export sample metadata
	sampleMetadata = self.dataset.sampleMetadata.copy()
	try:
		columnsToRemove = ['Sample Mask']
		sampleMetadata.drop(columnsToRemove, axis=1, inplace=True)
	except:
		pass

	sampleMetadata.to_csv(os.path.join(self.Attributes['saveDir'], 'ISTOCSY_dataset_sampleMetadata.csv'), encoding='utf-8')

	# Export feature metadata (removing feature correlation specific info)
	featureMetadata = self.dataset.featureMetadata.copy()
	try:
		columnsToRemove = ['Correlation', 'Feature Mask', 'Set', 'SortedIX', 'Average Set Correlation']
		featureMetadata.drop(columnsToRemove, axis=1, inplace=True)
	except:
		pass

	featureMetadata.to_csv(os.path.join(self.Attributes['saveDir'], 'ISTOCSY_dataset_featureMetadata.csv'), encoding='utf-8')


def _loadBatchFile(self):
	""" Load batch file """

	# Check input
	if (self.Attributes['batchFilePath'] is None):
		raise TypeError('Batch file path must be set')

	self.batchData = pandas.read_csv(self.Attributes['batchFilePath'], index_col=False)#index_col=0)

	# Ensure columns set to right data type
	try:
		self.batchData['Drivers'] = self.batchData['Driver'].astype(str)

	except:

		raise ValueError('ALERT: ' + self.Attributes['batchFilePath'] + ' must contain "Driver" field')
		_displayMessage('ALERT: ' + self.Attributes['batchFilePath'] + ' must contain "Driver" field')


def _fitRANSAC(driverIntensity, driverPairIntensity, degree=1):
	""" Fits RANSAC between two sets of intensity values - returns fit, outliers, parameters """

	# Fit RANSAC
	xcubic = PolynomialFeatures(degree=degree, include_bias=True)

	xdata = xcubic.fit_transform(driverIntensity.reshape(-1, 1))

	ransac = RANSACRegressor(LinearRegression())

	ransac.fit(xdata, driverPairIntensity)

	ransacLine = (ransac.predict(xcubic.fit_transform(driverIntensity.reshape(-1, 1)))).squeeze()

	ransacInliers = ransac.inlier_mask_

	ransacPlotOrder = np.argsort(driverIntensity)
    
    # CAZ check this

	# Calculate the devaition from regression at each point
	deviation = np.sqrt((driverPairIntensity - (ransac.estimator_.coef_[1] * driverIntensity + ransac.estimator_.intercept_))**2)

	# Extract parameters intercept | slope | SSE
	ransacParams = [ransac.estimator_.intercept_, ransac.estimator_.coef_[1], sum(deviation)]

	return ransacLine, ransacInliers, ransacPlotOrder, ransacParams


def _applyFitRANSAC(self):
	""" Applys _fitRANSAC between driver and all features correlating above threshold with driver """

	# Extract feature metadata for features passing correlation
	tempTable = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Feature Mask'],:].copy()

    # Plot only non masked samples
	intensityData = self.dataset.intensityData[self.dataset.sampleMetadata['Sample Mask'],:]
	sampleMetadata = self.dataset.sampleMetadata.loc[self.dataset.sampleMetadata['Sample Mask'],:].copy()

	# Set up
	nv = tempTable.shape[0]
	outliers = sampleMetadata[['Sample ID', 'Sample File Name']].copy()
	lineFit = sampleMetadata[['Sample ID', 'Sample File Name']].copy()
	plotOrder = sampleMetadata[['Sample ID', 'Sample File Name']].copy()

	# Generate data for each feature
	for i in np.arange(nv):

		if tempTable.index[i] == self.Attributes['driver']:
			continue

		featurePairName = self.dataset.featureMetadata.loc[tempTable.index[i], 'Feature Name']

		xVals = intensityData[:, tempTable.index[i]]
		xVals = xVals/np.nanmax(xVals)

		yVals = intensityData[:, self.Attributes['driver']]
		yVals = yVals/np.nanmax(yVals)

		# fit RANSAC
		ransacLine, ransacInliers, ransacPlotOrder, ransacParams = _fitRANSAC(xVals, yVals, self.Attributes['RANSACdegree'])

        # Save outliers
		outliers.loc[:, featurePairName] = ~ransacInliers
		lineFit.loc[:, featurePairName] = ransacLine
		plotOrder.loc[:, featurePairName] = ransacPlotOrder

		self.dataset.featureMetadata.loc[tempTable.index[i], 'RANSAC Intercept'] = ransacParams[0]
		self.dataset.featureMetadata.loc[tempTable.index[i], 'RANSAC Slope'] = ransacParams[1]
		self.dataset.featureMetadata.loc[tempTable.index[i], 'RANSAC SSE'] = ransacParams[2]

	self.RANSAC = {
            'outliers': outliers,
            'lineFit': lineFit,
            'plotOrder': plotOrder,
            }
