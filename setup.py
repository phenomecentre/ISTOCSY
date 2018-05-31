from setuptools import setup, find_packages

setup(name='ISTOCSY',
	version='1.0.0',
	description='National Phenome Centre toolbox',
	url='https://github.com/phenomecentre/npyc-toolbox',
	author='Caroline Sands',
	author_email='caroline.sands01@imperial.ac.uk',
	license='MIT',
	packages=find_packages(),
	install_requires=[
		"numpy>=1.14.3",
		"statsmodels>=0.9.0",
		"setuptools>=39.1.0",
		"matplotlib>=2.2.2",
		"networkx>=2.1",
		"pandas>=0.23.0",
		"plotly>=2.6.0",
		"pyqtgraph>=0.10.0",
		"scipy>=1.1.0",
		"PyQt5>=5.10.1",
		"nPYc>=1.0.4",
		"pyChemometrics>=0.1",
		"ipython==6.2.1"
	],
	classifiers = [
		"Programming Language :: Python",
		"Programming Language :: Python :: 3.6",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Topic :: Scientific/Engineering :: Bio-Informatics",
		],
	long_description = """\
		ISTOCSY
		-------

		.. image:: https://travis-ci.org/phenomecentre/nPYc-Toolbox.svg?branch=master
		   :target: https://travis-ci.org/phenomecentre/nPYc-Toolbox

		.. image:: https://readthedocs.org/projects/npyc-toolbox/badge/?version=latest
		   :target: http://npyc-toolbox.readthedocs.io/en/latest/?badge=latest
		   :alt: Documentation Status

		.. image:: https://codecov.io/gh/phenomecentre/nPYc-Toolbox/branch/master/graph/badge.svg
		   :target: https://codecov.io/gh/phenomecentre/nPYc-Toolbox

		|

		ISTOCSY is a python library for interactively exploring the correlations between features in mass spectrometry datasets

		Documentation can be found on `Read the Docs <http://npyc-toolbox.readthedocs.io/en/latest/?badge=latest>`_.

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

		The nPYc toolbox is `developed <https://github.com/phenomecentre/ISTOCSY>`_ by the Caroline Sands at `The National Phenome Centre <http://phenomecentre.org/>`_ at `Imperial College London <http://imperial.ac.uk/>`_.
		""",
		documentation='http://npyc-toolbox.readthedocs.io/en/latest/?badge=stable',
		include_package_data=True,
		zip_safe=False
	)
