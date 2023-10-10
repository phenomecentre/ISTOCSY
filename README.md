# ISTOCSY

* Version 3.0.0

ISTOCSY is a python library for interactively exploring the correlations between features in metabolomics datasets

Imports:
 - Basic tabular csv of any metabolomics datasets (in format of intensity data, feature metadata, sample metadata)

Provides:
 - Visualisation of all the features in your dataset
 - Ability to explore the correlations driven from any feature of choice
 - Suggestion of structural sets (i.e., features putatively resulting from the same compound)
 - Ability to change the correlation method, threshold, FDR correction method
 - Ability to change the correlation threshold and retention time window for defining structural sets

Exports:
 - Basic tabular csv of all results (feature names, correlations, structural sets, etc.)
 - Interactive html plots (plotly)

## Installation

Download and unzip ISTOCSY code from Git:
https://github.com/phenomecentre/ISTOCSY/archive/refs/heads/pyqt6.zip

### Windows


In a PowerShell terminal window, cd to the unzipped directory and run the batch file
called install_and_run_istocsy.bat

### Mac


In a terminal window, cd to the unzipped directory and run the batch file
called install_and_run_istocsy.sh


