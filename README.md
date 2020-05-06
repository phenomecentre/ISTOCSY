# ISTOCSY

* Version 2.0.0

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
 - Basic tabular csv of all results (feature names, correlations, p-values, FDR corrected q-values, structural sets, etc.)
 - Interactive html plots (plotly)

## Installation

Download or clone ISTOCSY repo, then from inside Python run:

    import sys
	sys.path.append('path to saved ISTOCSY code')
	import runISTOCSY
	runISTOCSY,main()

## Documentation

Documentation in progress - watch this space!

## Testing

Unit testing code in progress - watch this space!