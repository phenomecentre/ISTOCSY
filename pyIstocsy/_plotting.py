#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive plotting functions for runISTOCSY.py

Created on Thu Feb  8 15:02:12 2018

@author: cs401
"""

from matplotlib.colors import rgb2hex
import numpy as np
import plotly
import plotly.graph_objs as go
from ._utilities import _calcCorrelation


def plotCorrelation(tempTable, cVect, mask, savePath='plotCorrelation', autoOpen=True):
	"""
	Generate plotly interactive html plot of m/z vs. RT coloured by correlation to driver

	:param pandas.dataFrame tempTable: data to plot, must contain 'Feature Name', 'Retention Time' and 'm/z' columns
	:param pandas.ndarray cVect: vector of correlation to driver data to color points
	:param bool mask: feature mask
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Set up
	data = []
	Xvals = tempTable['Retention Time'].values
	Yvals = tempTable['m/z'].values
	feature = tempTable['Feature Name']

	if mask is not None:
		cVect = cVect[mask]
		Xvals = Xvals[mask]
		Yvals = Yvals[mask]
		feature = feature[mask]

	C_str = ["%.4f" % i for i in cVect] # Format text for tooltips
	maxcol = np.max(abs(cVect))

	hovertext = ["%s; Cor: %s" % i for i in zip(feature, C_str)] # Text for tooltips

	# Convert cVect to a value between 0.1 and 1 - to set the alpha of each point relative to loading weight
	alphas = (((abs(cVect) - np.min(abs(cVect))) * (1 - 0.2)) / (maxcol - np.min(abs(cVect)))) + 0.2

	LOADSplot = go.Scatter(
		x = Xvals,
		y = Yvals,
		mode = 'markers',
		marker = dict(
			colorscale = 'RdBu',
			cmin = -maxcol,
			cmax = maxcol,
			color = cVect,
			opacity = alphas,
			showscale = True,
			),
		text = hovertext,
		hoverinfo = 'x, y, text',
		showlegend = False
		)

	data.append(LOADSplot)

	# Add annotation
	layout = {
		'xaxis' : dict(
			title = 'Retention Time',
			),
		'yaxis' : dict(
			title = 'm/z'
			),
		'title' : 'Correlation to selected peak',
		'hovermode' : 'closest',
		'bargap' : 0,
		'barmode' : 'stack'
	}

	figure = go.Figure(data=data, layout=layout)
	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)


def plotScatter(tempTable, xName, yName, setcVectAlphas, title='', savePath='plotScatter', autoOpen=True):
	"""
	Generate plotly interactive html plot of m/z vs. RT coloured by correlation to driver

	:param pandas.dataFrame tempTable: data to plot, must contain 'Feature Name', xName and yName columns
	:param str xName: column in tempTable to plot on x axis
	:param str yName: column in tempTable to plot on y axis
	:param numpy.ndarray setcVectAlphas: color of each point (colour of point in set)
	:param str title: title of plot
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Save text to show in tooltips
	classes = tempTable['Set']
	hovertext = tempTable['Feature Name'].str.cat(classes.astype(str), sep='; Set: ')

	data = []

	# Plot by set
	uniq, indices = np.unique(classes, return_inverse=True)

	for i in range(len(uniq)):

		c = setcVectAlphas[indices == i, :]
		c = rgb2hex(c[0,:3])

		DATAplot = go.Scatter(

			x = tempTable[xName].values[indices == i],
			y = tempTable[yName].values[indices == i],
			mode = 'markers',
			marker = dict(
				color = c,
				symbol = 'circle',
				),
			text = hovertext[indices == i],
			hoverinfo = 'text',
			name = 'Set ' + str(uniq[i]),
			showlegend = True
			)
		data.append(DATAplot)

	layout = {
		'xaxis' : dict(
			title = xName
			),
		'yaxis' : dict(
			title = yName
			),
		'title' : title,
		'legend' : dict(
			yanchor='middle',
			xanchor='right'
			),
		'hovermode' : 'closest'
	}


	figure = go.Figure(data=data, layout=layout)

	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)


def plotHeatmap(tempTable, intensityData, correlationMethod='pearson', savePath='plotHeatmap', autoOpen=True):
	"""
	Interactive heatmap

	:param pandas.core.frame.DataFrame tempTable: data to plot, must contain 'Feature Name' column
	:param numpy.ndarray intensityData: MS intensity data, rows for samples, columns for variables
	:param str correlationMethod: any allowed correlation method (see _utilities)
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Set up
	nv = tempTable.shape[0]

	# Generate text for legend
	legendtext = ["%s (Set %.f)" % i for i in zip(tempTable['Feature Name'], tempTable['Set'])]


	# Calculate the correlation between all features
	cMatrix = np.ndarray([nv, nv])

	for i in np.arange(nv):
		delcVect = _calcCorrelation(intensityData[:,tempTable.index], intensityData[:,tempTable.index[i]], correlationMethod=correlationMethod)
		cMatrix[i,:] = delcVect[0]

	data = []

	DATAplot = go.Heatmap(
		z=cMatrix,
		x=tempTable['Feature Name'],
		y=tempTable['Feature Name'],
		colorscale='RdBu'
#		zmin=0,
#		zmax=1
		)

	data.append(DATAplot)

	layout = {
		'title' : 'Heatmap',
		'xaxis' : dict(
			tickvals = [k for k in range(0,nv+1)],
			ticktext = legendtext
			),
		'yaxis' : dict(
			tickvals = [k for k in range(0,nv+1)],
			ticktext = legendtext
			),
		'margin' : dict(
			b = 120,
			l = 200,
			r = 140)
	}

	figure = go.Figure(data=data, layout=layout)
	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)


def plotCorrelationScatter(tempTable, driverIX, intensityData, setcVectAlphas, savePath='plotCorrelationScatter', autoOpen=True):
	"""
	Generate plotly interactive html plot of feature intensity between driver feature and all detected features coloured by structural set

	:param pandas.dataFrame tempTable: data to plot, must contain 'Feature Name', 'Retention Time' and 'm/z' columns
	:param int driverIX: index of driver feature
	:param numpy.ndarray intensityData: MS intensity data, rows for samples, columns for variables
	:param numpy.ndarray setcVectAlphas: color of each point (colour of point in set)
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Set up
	data = []
	nv = tempTable.shape[0]

	# Generate text for legend
	legendtext = ["%s; Set: %.f; Cor: %.2f" % i for i in zip(tempTable['Feature Name'], tempTable['Set'], tempTable['Correlation'])]

	# Generate data for each feature
	for i in np.arange(nv):

		c = rgb2hex(setcVectAlphas[i,:3])

		xVals = intensityData[:,tempTable.index[i]]
		xVals = xVals/np.max(xVals)

		yVals = intensityData[:,driverIX]
		yVals = yVals/np.max(yVals)

		FEATUREplot = go.Scatter(
			x = xVals,
			y = yVals,
			mode = 'markers',
			marker = dict(
				colorscale = 'Portland',
				color = c,
				symbol = 'circle',
				),
			name = legendtext[i],
			showlegend = True,
			)

		data.append(FEATUREplot)

	layout = {
		'xaxis' : dict(
			title = 'Selected feature (relative intensity)',
			range = [0, 1.3]
			),
		'yaxis' : dict(
			title = 'Driver feature (relative intensity)',
			),
		'title' : 'Scatter plot between driver and each correlated feature',
		'legend' : dict(
			yanchor = 'middle',
			xanchor = 'right'
			)
	}

	figure = go.Figure(data=data, layout=layout)
	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)