"""
HDMI Matrix Control Library

A library for controlling HDMI matrix switches over HTTP
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import HDMIMatrixClient
from .exceptions import (
    MatrixConnectionError,
    MatrixControlException,
    MatrixCommandError,
)

__all__ = [
    "HDMIMatrixClient",
    "MatrixControlException",
    "MatrixConnectionError",
    "MatrixCommandError",
]
