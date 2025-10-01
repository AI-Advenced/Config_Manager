"""
Loaders module for Config Manager

This module contains all the file format loaders for different configuration formats.
Each loader implements the BaseLoader interface and handles a specific file format.
"""

from .base import BaseLoader
from .yaml_loader import YAMLLoader
from .json_loader import JSONLoader
from .toml_loader import TOMLLoader

__all__ = [
    'BaseLoader',
    'YAMLLoader',
    'JSONLoader',
    'TOMLLoader'
]