"""
The `nPYc-Toolbox <https://github.com/phenomecentre/nPYc-Toolbox>`_ defines objects for representing, and implements functions to manipulate and display, metabolic profiling datasets.
"""
__version__ = '1.0.0'

from .runISTOCSY import main as runISTOCSY

__all__ = ['runISTOCSY']
