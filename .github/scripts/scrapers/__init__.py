"""
Scrapers para obtener el Euribor diario desde múltiples fuentes web
"""

from . import euribordiario
from . import euribor_com_es
from . import expansion

__all__ = ['euribordiario', 'euribor_com_es', 'expansion']
