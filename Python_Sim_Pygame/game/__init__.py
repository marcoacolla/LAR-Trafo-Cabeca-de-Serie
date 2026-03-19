"""
Game module - Contains core game logic and utilities.
"""

from .config import *
from .collision import *
from .accelerometer import *
from .input_handler import InputHandler
from .rendering import *
from .initialization import *

__all__ = [
    'InputHandler',
]
