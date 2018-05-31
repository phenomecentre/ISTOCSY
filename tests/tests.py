#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for runISTOCSY.py

Testing all plotting and utility functions

Created on Fri May 25 15:23:13 2018

@author: cs401
"""
import unittest
import sys
import os
import tempfile
sys.path.append("..")
from pyIstocsy._utilities import _loadCSV, _findNearest, _shiftedColorMap, _calcCorrelation, _findStructuralSets
from pyIstocsy._plotting import plotCorrelation, plotScatter, plotHeatmap
import numpy as np
import pandas
from scipy.stats import pearsonr, spearmanr, kendalltau
from statsmodels.stats.multitest import multipletests
import matplotlib

intensityDataFile = 'test_data/intensityData.csv'
featureMetadataFile = 'test_data/featureData.csv'

featureMetadata = pandas.read_csv(featureMetadataFile)
intensityData = np.genfromtxt(intensityDataFile, delimiter=',')

class test_utilities(unittest.TestCase):
	""" test code in _utilities.py """
	
	def test_loadCSV(self):
		
		_loadCSV(self, intensityDataFile, featureMetadataFile)
		
		np.testing.assert_equal(self.dataset.intensityData, intensityData)
		
		pandas.util.testing.assert_frame_equal(self.dataset.featureMetadata, featureMetadata, check_dtype=False)
		
	
	def test_findNearest(self):
		
		testOutput = _findNearest(featureMetadata, 1, 75.8542)
		self.assertTrue(testOutput == 0)
		

	def test_shiftedColorMap(self):
		
		new_cmap = _shiftedColorMap(matplotlib.pyplot.cm.RdYlBu_r, start=0.0, midpoint=0.8, stop=1.0)
		
		# Test shift is working as it should
		self.assertEqual(new_cmap(0.0), matplotlib.pyplot.cm.RdYlBu_r(0.0))
		self.assertEqual(new_cmap(0.8), matplotlib.pyplot.cm.RdYlBu_r(0.5))
		self.assertEqual(new_cmap(1.0), matplotlib.pyplot.cm.RdYlBu_r(1.0))
		
		
	def test_calcCorrelation(self):
		
		# Test correlation and FDR values
		
		# Generate correct values for each correlation method
		nv = intensityData.shape[1]		
		pearson_r = np.zeros(nv)
		pearson_p = np.zeros(nv)
		spearman_r = np.zeros(nv)
		spearman_p = np.zeros(nv)
		kendall_r = np.zeros(nv)
		kendall_p = np.zeros(nv)
		
		for col in range(intensityData.shape[1]):
			pearson_r[col], pearson_p[col] = pearsonr(intensityData[:,col], intensityData[:,0])
			spearman_r[col], spearman_p[col] = spearmanr(intensityData[:,col], intensityData[:,0])
			kendall_r[col], kendall_p[col] = kendalltau(intensityData[:,col], intensityData[:,0])
		
		# Generate correct values for bonferroni correction method
		qVect = multipletests(pearson_p, method='bonferroni')
		qVect = qVect[1]

		# Test against _calcCorrelation function
		
		# Pearson
		testOutput = _calcCorrelation(intensityData, intensityData[:,0], correlationMethod='pearson', correctionMethod='bonferroni')
		np.testing.assert_allclose(testOutput[0], pearson_r, err_msg='pearson correlation calculations not correct')
		np.testing.assert_allclose(testOutput[1], pearson_p, err_msg='pearson correlation pvalue calculations not correct')
		np.testing.assert_allclose(testOutput[2], qVect, err_msg='pearson correlation bonferroni corrected calculations not correct')
		
		# Spearman
		testOutput = _calcCorrelation(intensityData, intensityData[:,0], correlationMethod='spearman', correctionMethod=None)
		np.testing.assert_allclose(testOutput[0], spearman_r, err_msg='spearman correlation calculations not correct')
		np.testing.assert_allclose(testOutput[1], spearman_p, err_msg='spearman correlation pvalue calculations not correct')
		self.assertTrue(testOutput[2] == None)

		# Kendalls-Tau
		testOutput = _calcCorrelation(intensityData, intensityData[:,0], correlationMethod='kendalltau', correctionMethod=None)
		np.testing.assert_allclose(testOutput[0], kendall_r, err_msg='kendalltau correlation calculations not correct')
		np.testing.assert_allclose(testOutput[1], kendall_p, err_msg='kendalltau correlation pvalue calculations not correct')	
		
	
	def test_findStructuralSets(self):
		
		# Set up as default attributes
		attributes = {
			'correlationMethod': 'pearson',
			'correlationKind': 'relative',
			'correctionMethod': None,
			'correlationThreshold': 0.8,
			'structuralThreshold': 0.9,
			'rtThreshold': None,
			'showAllFeatures': True,
			}
		
		featureMetadataTemp = featureMetadata.copy(deep=True)
		corrTemp = _calcCorrelation(intensityData, intensityData[:,0], correlationMethod='pearson', correctionMethod='bonferroni')
		featureMetadataTemp['Correlation'] = corrTemp[0]
		
		tempTable = _findStructuralSets(featureMetadataTemp, intensityData, attributes)
		
		np.testing.assert_array_equal(tempTable['Set'].values, np.array([1, 2, 3, 4, 3, 5, 3, 6, 6, 6]))
		
		# Set up with rtThreshold
		attributes['rtThreshold'] = 0.1
		
		tempTable = _findStructuralSets(featureMetadataTemp, intensityData, attributes)
		
		np.testing.assert_array_equal(tempTable['Set'].values, np.array([1, 2, 3, 4, 5, 6, 7, 8, 8, 9]))



class test_plotting(unittest.TestCase):
	""" test code in _plotting.py """	

	def test_plotCorrelation(self):

		with tempfile.TemporaryDirectory() as tmpdirname:

			plotCorrelation(featureMetadata, np.random.rand(featureMetadata.shape[0], 1), None, savePath=os.path.join(tmpdirname, 'correlationPlot'), autoOpen=False)

			expectedPath = os.path.join(tmpdirname, 'correlationPlot.html')
			self.assertTrue(os.path.exists(expectedPath))
	
	def test_plotScatter(self):
		
		with tempfile.TemporaryDirectory() as tmpdirname:
			
			featureMetadataTemp = featureMetadata.copy(deep=True)
			featureMetadataTemp['Set'] = 1
			
			setcVectAlphas = np.zeros([featureMetadataTemp.shape[0], 4])
			plotScatter(featureMetadataTemp, 'Retention Time', 'm/z', setcVectAlphas, title='', savePath=os.path.join(tmpdirname, 'scatterPlot'), autoOpen=False)

			expectedPath = os.path.join(tmpdirname, 'scatterPlot.html')
			self.assertTrue(os.path.exists(expectedPath))
			
	def test_plotHeatmap(self):
		
		with tempfile.TemporaryDirectory() as tmpdirname:
			
			featureMetadataTemp = featureMetadata.copy(deep=True)
			featureMetadataTemp['Set'] = 1
				
			plotHeatmap(featureMetadataTemp, intensityData, correlationMethod='pearson', savePath=os.path.join(tmpdirname, 'heatmapPlot'), autoOpen=False)

			expectedPath = os.path.join(tmpdirname, 'heatmapPlot.html')
			self.assertTrue(os.path.exists(expectedPath))
		
		

if __name__ == '__main__':
	unittest.main()

