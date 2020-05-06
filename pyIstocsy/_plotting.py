#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive plotting functions for runISTOCSY.py

Created on Thu Feb  8 15:02:12 2018

@author: cs401
"""
import numpy as np
import plotly
import plotly.graph_objs as go
import matplotlib
from _utilities import _calcCorrelation
import webbrowser
import os
import textwrap
from itertools import compress

def plotScatter(self, colourBy='Correlation', mask=None, savePath='plotScatter', autoOpen=True):
	"""
	Generate plotly interactive html plot of m/z vs. RT coloured by correlation to driver

	:param pandas.dataFrame tempTable: data to plot, must contain 'Feature Name', 'Retention Time' and 'm/z' columns
	:param pandas.ndarray cVect: vector of correlation to driver data to color points
	:param bool mask: feature mask
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	featureTable = self.dataset.featureMetadata

	# Masks for each data type
	MSmask = featureTable['Data Type'].values == 'LC-MS'
	NMRmask = featureTable['Data Type'].values == 'NMR'
	TargetedMask = featureTable['Data Type'].values == 'Targeted'
	
	# Number of data types (for plotting overall plot)
	nTypes = len(np.unique(featureTable['Data Type']))
	
	if (nTypes==1) and (autoOpen==True):
		autoOpenSingle=True
	else:
		autoOpenSingle=False
	
	# Hovertext
	try:
		hovertext = ["%s; Cor: %.4f; Set: %s" % i for i in zip(featureTable['Feature Name'], featureTable['Correlation'], featureTable['Set'].astype(str))]
	except:
		hovertext = ["%s; Cor: %.4f" % i for i in zip(featureTable['Feature Name'], featureTable['Correlation'])]
		
	# Universal settings
	cVect = featureTable[colourBy].values
	cVect[np.isnan(cVect)] = 0

	if colourBy=='Correlation':
		colorscale = 'RdBu_r'
		title = 'Correlation to ' + self.Attributes['saveName']
		maxcol = 1
		mincol = -1
		alphas = (((abs(cVect) - np.min(abs(cVect))) * (1 - 0.2)) / (maxcol - np.min(abs(cVect)))) + 0.2

	else:
		colorscale =  'jet'
		title = 'Putative structural sets from ' + self.Attributes['saveName']
		maxcol = np.nanmax(cVect)
		mincol = np.nanmin(cVect[cVect!=0])
		alphas = np.ones(cVect.shape)

	if mask is None:
		savePath = savePath + '_allFeatures'

	figures = []

	# MS data
	if (sum(MSmask) != 0):

		# Set up
		data = []

		if mask is not None:
			MSmask = np.logical_and(mask, MSmask)

		plotData = go.Scatter(
			x = featureTable.loc[MSmask,'Retention Time'].values,
			y = featureTable.loc[MSmask, 'm/z'].values,
			mode = 'markers',
			marker = dict(
				colorscale = colorscale,
				cmin = mincol,
				cmax = maxcol,
				color = cVect[MSmask],
				opacity = alphas[MSmask],
				showscale = True,
				),
			text = list(compress(hovertext, MSmask)),
			hoverinfo = 'x, y, text',
			showlegend = False
			)

		data.append(plotData)

		# Add annotation
		layout = {
			'xaxis' : dict(
				title = 'Retention Time',
                automargin = True,
				),
			'yaxis' : dict(
				title = 'm/z',
                automargin = True,
				),
			'title' : title + ' LC-MS',
			'hovermode' : 'closest',
			'bargap' : 0,
			'barmode' : 'stack',
			'plot_bgcolor' : 'rgba(0,0,0,0)'
		}

		# Plot figure
		figure = go.Figure(data=data, layout=layout)
		plotly.offline.plot(figure, filename = savePath +'_LC-MS.html', auto_open=autoOpenSingle)

		# Append to figures to create one overall
		if nTypes>1:			
			temp = os.path.split(savePath)
			figures.append("  <object data=\"" + temp[1] +'_LC-MS.html'+"\" width=\"800\" height=\"500\"></object>"+"\n")


	# NMR data
	if (sum(NMRmask) != 0):

		# Set up
		data = []

		Yvals = self.dataset.intensityData[:,NMRmask]
		minY = np.nanmin(Yvals, axis=0)
		midY = np.nanmedian(Yvals, axis=0)
		maxY = np.nanmax(Yvals, axis=0) - minY

		# Bar starts at minimum spectral intensity
		BARmin = go.Bar(
			x = self.dataset.featureMetadata.loc[NMRmask, 'ppm'],
			y = minY,
			marker = dict(
				color = 'white',
				line = dict(
					color = 'white'
					),
				),
			hoverinfo = 'skip',
			showlegend = False
			)
		data.append(BARmin)

		# Bar ends at maximum spectral intensity
		
		# For correlation - coloured by correlation
		if colourBy == 'Correlation':
			BARmax = go.Bar(
				x = self.dataset.featureMetadata.loc[NMRmask, 'ppm'],
				y = maxY,
				marker = dict(
					colorscale = colorscale,
					cmin = mincol,
					cmax = maxcol,
					color = cVect[NMRmask],
					opacity = alphas[NMRmask],
					showscale = True,
					),
				text = list(compress(hovertext, NMRmask)),
				hoverinfo = 'text',
				showlegend = False
				)
			data.append(BARmax)
				
		# Add line for median spectral intensity
		MIDline = go.Scattergl(
			x = self.dataset.featureMetadata.loc[NMRmask, 'ppm'],
			y = midY,
			mode = 'lines',
			line = dict(
				color = 'grey',
				width = 1							 
					 ),
			hoverinfo = 'skip',
			name = 'Median spectrum',
			showlegend = True
			)
		data.append(MIDline)	
			
		# For correlation - red line for features above correlation threshold
		if colourBy == 'Correlation':
			
			# Get colour for correlation of 1
			cmap = matplotlib.cm.get_cmap(colorscale)
			norm = matplotlib.colors.Normalize(vmin=mincol, vmax=maxcol)
			c = matplotlib.colors.rgb2hex(cmap(norm(1)))
			
			# Get mask for NMR features
			corrMask = featureTable['Feature Mask'].values
			NMRmaskPass = ~corrMask[NMRmask]
			
			# Set those masked to nan for plotting				
			midY[NMRmaskPass] = np.nan
			
			CORRline = go.Scattergl(
				 x = self.dataset.featureMetadata.loc[NMRmask, 'ppm'],
				 y = midY,
				 mode = 'lines',
				 line = dict(
					color = c,
					width = 1							 
						 ),
				 hoverinfo = 'skip',
				 name = 'Features correlating to driver > threshold',
				 showlegend = True,
				 connectgaps = False
				 )
			data.append(CORRline)
		
		# For structural sets - line and bars coloured by set
		else:
		
			for i in np.arange(1, int(maxcol)+1):
			
				# Get colour
				cmap = matplotlib.cm.get_cmap(colorscale)
				norm = matplotlib.colors.Normalize(vmin=mincol, vmax=maxcol)
				c = matplotlib.colors.rgb2hex(cmap(norm(i)))	
				
				mask = cVect==i
				NMRmaskPass = mask[NMRmask]
				
				# Get Yvals - set those masked to nan for plotting				
				midY = np.median(Yvals, axis=0)
				midY[~NMRmaskPass] = np.nan
				
				# Plot line
				SETline = go.Scattergl(
					 x = self.dataset.featureMetadata.loc[NMRmask, 'ppm'],
					 y = midY,
					 legendgroup = 'set'+str(i),
					 mode = 'lines',
					 line = dict(
						color = c,
						width = 1							 
							 ),
					 hoverinfo = 'skip',
					 showlegend = False,
					 connectgaps = False
					 )
				data.append(SETline)
				
				# Plot bar
				SETbar = go.Bar(
					x = self.dataset.featureMetadata.loc[NMRmaskPass, 'ppm'],
					y = maxY[NMRmaskPass],
					legendgroup = 'set'+str(i),
					marker = dict(
						color = c,
						opacity = 0.8,
						line = dict(
							color = c,
							),
						),
					text = list(compress(hovertext, NMRmaskPass)),
					hoverinfo = 'text',
					name = 'Set: ' + str(i),
					showlegend = True
					)
				data.append(SETbar)

		# Add annotation
		layout = {
			'xaxis' : dict(
				title = chr(948)+ '1H',
				autorange = 'reversed',
                automargin = True,
				),
			'yaxis' : dict(
				title = 'Intensity (min - median - max)',
                automargin = True,
				),
			'title' : title + ' NMR',
			'hovermode' : 'closest',
			'bargap' : 0,
			'barmode' : 'stack',
			'plot_bgcolor' : 'rgba(0,0,0,0)',
			'legend' : dict(
				traceorder = 'normal',
				x = 0.7,
				y = 1
				)
		}

		# Plot figure
		figure = go.Figure(data=data, layout=layout)
		plotly.offline.plot(figure, filename = savePath +'_NMR.html', auto_open=autoOpenSingle)

		# Append to figures to create one overall
		if nTypes>1:	
			temp = os.path.split(savePath)
			figures.append("  <object data=\""+ temp[1] +'_NMR.html'+"\" width=\"800\" height=\"500\"></object>"+"\n")


	# Targeted data
	if (sum(TargetedMask != 0)):

		# Set up
		data = []

		if mask is not None:
			TargetedMask = np.logical_and(mask, TargetedMask)

		plotData = go.Scatter(
			x = featureTable.loc[TargetedMask, 'Targeted Feature Number'].values,
			y = featureTable.loc[TargetedMask, 'Relative Intensity'].values,
			mode = 'markers',
			marker = dict(
				colorscale = colorscale,
				cmin = mincol,
				cmax = maxcol,
				color = cVect[TargetedMask],
				opacity = alphas[TargetedMask],
				showscale = True,
				),
			text = list(compress(hovertext, TargetedMask)),
			hoverinfo = 'x, y, text',
			showlegend = False
			)
		data.append(plotData)

		# Add annotation
		layout = {
			'xaxis' : dict(
				title = 'Targeted Feature Number',
                automargin = True,
				),
			'yaxis' : dict(
				title = 'Relative Intensity (' + self.Attributes['relativeIntensityMetric'] + ')',
                automargin = True,
				),
			'title' : title + ' Targeted',
			'hovermode' : 'closest',
			'bargap' : 0,
			'barmode' : 'stack',
			'plot_bgcolor' : 'rgba(0,0,0,0)'
		}

		# Plot figure
		figure = go.Figure(data=data, layout=layout)
		plotly.offline.plot(figure, filename = savePath +'_Targeted.html', auto_open=autoOpenSingle)

		# Append to figures to create one overall
		if nTypes>1:	
			temp = os.path.split(savePath)
			figures.append("  <object data=\""+ temp[1] +'_Targeted.html'+"\" width=\"800\" height=\"500\"></object>"+"\n")


	# Plot overall figure
	if nTypes>1:
		figures_to_html(figures, filename = savePath +'.html')

		if autoOpen==True:
			webbrowser.open('file://'+savePath +'.html', new=2)


def plotHeatmap(self, savePath='plotHeatmap', autoOpen=True):
	"""
	Interactive heatmap

	:param pandas.core.frame.DataFrame tempTable: data to plot, must contain 'Feature Name' column
	:param numpy.ndarray intensityData: MS intensity data, rows for samples, columns for variables
	:param str correlationMethod: any allowed correlation method (see _utilities)
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Extract feature metadata and intensity data for features passing correlation
	plotTable = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Feature Mask'],:].copy()

	# Sort (defined in _utilities._findStructuralSets - by average set correlation to driver)
	plotTable = plotTable.sort_values(['SortedIX'])

	intensityData = self.dataset.intensityData[:,plotTable.index]

	# Calculate the correlation between all features
	cMatrix = _calcCorrelation(intensityData, correlationMethod=self.Attributes['correlationMethod'])

	# Generate text for legend
	legendtext = ["%s (Set %.f)" % i for i in zip(plotTable['Feature Name'], plotTable['Set'])]

	data = []

	DATAplot = go.Heatmap(
		z=cMatrix,
		x=plotTable['Feature Name'],
		y=plotTable['Feature Name'],
		colorscale='RdBu_r',
		zmin = np.nanmin(cMatrix),
		zmax = np.nanmax(cMatrix)
		)
	data.append(DATAplot)

	layout = {
		'title' : 'Heatmap between ' + plotTable.loc[self.Attributes['driver'], 'Feature Name'] + ' and each correlated feature',
		'xaxis' : dict(
			tickvals = [k for k in range(0, plotTable.shape[0]+1)],
			ticktext = legendtext,
            automargin = True,
			),
		'yaxis' : dict(
			tickvals = [k for k in range(0, plotTable.shape[0]+1)],
			ticktext = legendtext,
            automargin = True,
			),
		'margin' : dict(
			b = 120,
			l = 200,
			r = 140
			),
		'plot_bgcolor' : 'rgba(0,0,0,0)'	
	}

	# Plot figure
	figure = go.Figure(data=data, layout=layout)
	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)


def plotCorrelationScatter(self, sampleIDs='Sample ID', savePath='plotCorrelationScatter', autoOpen=True):
	"""
	Generate plotly interactive html plot of feature intensity between driver feature and all detected features coloured by structural set

	:param pandas.dataFrame tempTable: data to plot, must contain 'Feature Name', 'Retention Time' and 'm/z' columns
	:param int driverIX: index of driver feature
	:param numpy.ndarray intensityData: MS intensity data, rows for samples, columns for variables
	:param numpy.ndarray setcVectAlphas: color of each point (colour of point in set)
	:param str savePath: path/name to save plot to/as
	:param bool autoOpen: flag as to whether to automatically open html figure
	"""

	# Extract feature metadata for features passing correlation
	tempTable = self.dataset.featureMetadata.loc[self.dataset.featureMetadata['Feature Mask'],:].copy()

	# Sort (defined in _utilities._findStructuralSets - by average set correlation to driver)
	tempTable = tempTable.sort_values(['SortedIX'])

    # Plot only non masked samples
	intensityData = self.dataset.intensityData[self.dataset.sampleMetadata['Sample Mask'],:]
	sampleMetadata = self.dataset.sampleMetadata.loc[self.dataset.sampleMetadata['Sample Mask']]

	driverIX = self.Attributes['driver']

	# Set up
	data = []
	nv = tempTable.shape[0]

	# Generate text for legend
	legendtext = ["%s; Set: %.f; Cor: %.2f" % i for i in zip(tempTable['Feature Name'], tempTable['Set'], tempTable['Correlation'])]

	for i in np.arange(len(legendtext)):
		legendtext[i] = '<br>'.join(textwrap.wrap(legendtext[i], width=60))

	# Get colours
	cmap = matplotlib.cm.get_cmap('jet')
	norm = matplotlib.colors.Normalize(vmin=np.nanmin(tempTable['Set']), vmax=np.nanmax(tempTable['Set']))

	# get RANSAC values
	if hasattr(self, 'RANSAC'):
		ransacLine = self.RANSAC['lineFit']
		ransacOutliers = self.RANSAC['outliers']
		ransacPlotOrder = self.RANSAC['plotOrder']

	# Generate data for each feature
	for i in np.arange(nv):

		if tempTable.index[i] == driverIX:
			continue

		featureName = tempTable.loc[tempTable.index[i], 'Feature Name']

		c = matplotlib.colors.rgb2hex(cmap(norm(tempTable.loc[tempTable.index[i], 'Set'])))

		xVals = intensityData[:,tempTable.index[i]]
		xVals = xVals/np.nanmax(xVals)

		yVals = intensityData[:,driverIX]
		yVals = yVals/np.nanmax(yVals)

		FEATUREplot = go.Scatter(
			x = xVals,
			y = yVals,
			legendgroup = 'Feature'+str(i),
			mode = 'markers',
			marker = dict(
				color = c,
				symbol = 'circle',
				),
			name = legendtext[i],
			text = sampleMetadata[sampleIDs],
			hoverinfo = 'x, y, text',
			showlegend = True,
			)

		data.append(FEATUREplot)
		
		if hasattr(self, 'RANSAC'):

			RANSACplot = go.Scatter(
				x = xVals[ransacPlotOrder.loc[:, featureName].values],
				y = ransacLine.loc[ransacPlotOrder.loc[:, featureName].values, featureName].values,
				legendgroup = 'Feature'+str(i),
				mode = 'lines',
				marker = dict(
					color = c
					),
	#			name = legendtext[i] + ' RANSAC fit',
				hoverinfo = 'x, y',
				showlegend = False
				)
	
			data.append(RANSACplot)
	
			if any(ransacOutliers==False):
				RANSACoutliers = go.Scatter(
					x = xVals[ransacOutliers.loc[:, featureName].values],
					y = yVals[ransacOutliers.loc[:, featureName].values],
					legendgroup = 'Feature'+str(i),
					mode = 'markers',
					marker = dict(
						color = c,
						symbol = 'circle',
						line = dict(
							width = 2,
							color = 'red'
							)
						),
	#				name = legendtext[i] + ' RANSAC outliers',
					text = sampleMetadata.loc[ransacOutliers.loc[:, featureName].values,sampleIDs],
					hoverinfo = 'x, y, text',
					showlegend = False#True,
					)
	
				data.append(RANSACoutliers)

	layout = {
		'xaxis' : dict(
			title = 'Selected feature (intensity scaled)',
			range = [0, 1.3],
            automargin = True,
			),
		'yaxis' : dict(
			title = 'Driver feature (intensity scaled)',
            automargin = True,
			),
		'title' : 'Scatter plot between ' + tempTable.loc[driverIX, 'Feature Name'] + ' and each correlated feature',
		'legend' : dict(
			yanchor = 'middle',
			xanchor = 'right'
			),
		'hovermode' : 'closest',
		'plot_bgcolor' : 'rgba(0,0,0,0)'
	}

	# Plot figure
	figure = go.Figure(data=data, layout=layout)
	plotly.offline.plot(figure, filename = savePath +'.html', auto_open=autoOpen)


def figures_to_html(figs, filename="dashboard.html"):
	dashboard = open(filename, 'w')
	dashboard.write("<html><head></head><body>" + "\n")
	for fig in figs:
		dashboard.write(fig)
		dashboard.write("\n")
	dashboard.write("</body></html>" + "\n")