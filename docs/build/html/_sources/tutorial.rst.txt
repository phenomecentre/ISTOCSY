========
Tutorial
========

This document provides a description of how to use ISTOCSY. Note, all code snippets should be run from a Python terminal.


Import runISTOCSY
=================

.. code-block:: python

	import sys
	sys.path.append("/path to runISTOCSY.py code")
	import runISTOCSY


Define the path to a directory in which to save any outputs
===========================================================

NOTE this is optional - the default is to save in current working directory

.. code-block:: python

	saveDir = "/path to where you would like to save the data"


Run csv file format
===================

Define the paths to your intensityData.csv and featureMetadata.csv files:

.. code-block:: python

	intensityDataFile = "/path to intensityData.csv"
	featureMetadataFile = "/path to featureData.csv"


Run ISTOCSY:

.. code-block:: python

	runISTOCSY.main(intensityDataFile=intensityDataFile, featureMetadataFile=featureMetadataFile, saveDir=saveDir)


Run nPYc dataset format
=======================

Run ISTOCSY:

.. code-block:: python

	runISTOCSY.main(dataset=dataset, saveDir=saveDir)


On running ISTOCSY
==================

ISTOCSY will open with the following defaults (obviously data set dependent).

.. figure:: _static/openingscreen.png
	:figwidth: 90%
	:alt: ISTOCSY opening screen

For a detailed description of the attributes of each panel see:
:ref:`Introduction to ISTOCSY`


Running ISTOCSY with a selected driver feature
==============================================

Hovering over the features in the top plot gives their figure names. Left clicking on one your feature of choice (here, for example, on feature ‘1.60_973.0411m/z’) will then update ISTOCSY as follows.

.. figure:: _static/hover.png
	:figwidth: 90%
	:alt: ISTOCSY hover
	

Toggling between 'all' and 'above threshold' features in the correlation plot
=============================================================================

In the correlation plot (top panel), once a driver peak has been selected, you can either show all the features in the data set (coloured by correlation to driver), or, just those which correlate to the driver above the correlation threshold.

Toggling between these two viewing options can be achieved by clicking on the bottom button which will display '**SHOW FEATURES ABOVE THRESHOLD ONLY**' or '**SHOW ALL FEATURES**' depending on current view selected.

Showing all features:

.. figure:: _static/hover.png
	:figwidth: 90%
	:alt: ISTOCSY show all features


Showing only those features above threshold: <CAZ ADD THIS>

.. figure:: _static/hover.png
	:figwidth: 90%
	:alt: ISTOCSY show features above threshold
	

Changing the correlation threshold
==================================

The correlation threshold above which correlations to the driver feature will be shown can be changed by entering a value between -1 and 1 into the text box 'Enter correlation threshold' and clicking the '**SET CORRELATION THRESHOLD**' button below.

For example, to change the threshold from the default (0.8) to 0.7:
<CAZ ADD THIS>

This will update ISTOCSY as follows:
<CAZ ADD THIS>


Exporting
=========

The export button button displays the parameters used (driver feature; correlation threshold) alongside a summary of the results (number of correlating features; number of structural sets). Clicking on this button exports a csv file of the results and a screenshot of the ISTOCSY window to the pre-specified output directory.

Example csv file output:
<CAZ ADD THIS>
