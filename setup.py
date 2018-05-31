from setuptools import setup, find_packages

setup(name='nPYc',
	version='1.0.4',
	description='National Phenome Centre toolbox',
	url='https://github.com/phenomecentre/npyc-toolbox',
	author='National Phenome Centre',
	author_email='phenomecentre@imperial.ac.uk',
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
		"pyChemometrics>=0.1"
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
		Toolbox for preprocessing of metabolic profiling datasets
		---------------------------------------------------------

		.. image:: https://travis-ci.org/phenomecentre/nPYc-Toolbox.svg?branch=master
		   :target: https://travis-ci.org/phenomecentre/nPYc-Toolbox

		.. image:: https://readthedocs.org/projects/npyc-toolbox/badge/?version=latest
		   :target: http://npyc-toolbox.readthedocs.io/en/latest/?badge=latest
		   :alt: Documentation Status

		.. image:: https://codecov.io/gh/phenomecentre/nPYc-Toolbox/branch/master/graph/badge.svg
		   :target: https://codecov.io/gh/phenomecentre/nPYc-Toolbox

		|

		The nPYc toolbox offers functions for the import, preprocessing, and QC of metabolic profiling datasets.

		Documentation can be found on `Read the Docs <http://npyc-toolbox.readthedocs.io/en/latest/?badge=latest>`_.

		Imports
		 - Peak-picked LC-MS data (XCMS, Progenesis QI)
		 - Raw NMR spectra (Bruker format)
		 - Targeted datasets (TargetLynx, Bruker BI-LISA & BI-Quant-Ur)

		Provides
		 - Batch *&* drift correction for LC-MS datasets
		 - Feature filtering by RSD and linearity of response
		 - Calculation of spectral line-width in NMR
		 - PCA of datasets
		 - Visualisation of datasets

		Exports
		 - Basic tabular csv
		 - `ISA-TAB <http://isa-tools.org>`_

		The nPYc toolbox is `developed <https://github.com/phenomecentre/npyc-toolbox>`_ by the informatics team at `The National Phenome Centre <http://phenomecentre.org/>`_ at `Imperial College London <http://imperial.ac.uk/>`_.
		""",
		documentation='http://npyc-toolbox.readthedocs.io/en/latest/?badge=stable',
		include_package_data=True,
		zip_safe=False
	)
