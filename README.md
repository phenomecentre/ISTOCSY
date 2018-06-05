# ISTOCSY

[![Build Status](https://travis-ci.com/phenomecentre/ISTOCSY.svg?branch=master)](https://travis-ci.com/phenomecentre/ISTOCSY) [![Documentation Status](https://readthedocs.org/projects/istocsy/badge/?version=latest)](https://istocsy.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/phenomecentre/ISTOCSY/branch/master/graph/badge.svg)](https://codecov.io/gh/phenomecentre/ISTOCSY) ![Python36](https://img.shields.io/badge/python-3.6-blue.svg) [![PyPI](https://img.shields.io/pypi/v/ISTOCSY.svg)](https://pypi.org/project/ISTOCSY/)

* Version 1.0.0

ISTOCSY is a python library for interactively exploring the correlations between features in mass spectrometry datasets.

Imports:
 - Peak-picked LC-MS data (XCMS, Progenesis QI)
 - nPYc dataset objects (https://github.com/phenomecentre/nPYc-Toolbox)

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

To install _via_ [pip](insert web-page when set up), run:

    pip install istocsy 

To install from a local copy of the source, simply navigate to the main package folder and run:

    python setup.py install

Alternatively, using pip and a local copy of the source:

    pip install /ISTOCSY-toolboxDirectory/

Installation with pip allows the usage of the uninstall command

    pip uninstall istocsy


## Documentation
Documentation is hosted on [Read the Docs](https://istocsy.readthedocs.io/en/latest/).

Documentation is generated *via* [Sphinx Autodoc](http://www.sphinx-doc.org/), documentation markup is in [reStructuredText](http://docutils.sourceforge.net/rst.html).

To build the documentation locally, cd into the `docs` directory and run:

    make html


### Testing

Unit testing is managed *via* the [`unittest` framework](https://docs.python.org/3.5/library/unittest.html). Test coverage can be found on [codecov.io](https://codecov.io/gh/phenomecentre/nPYc-Toolbox/).

To run all tests, cd into the `Tests` directory and run:

    python -m unittest discover -v

Individual test modules can be run with:

    python -m `test_filename` -v
