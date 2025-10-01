"""
Config Manager - Professional Python Configuration Management Library

A comprehensive library for managing configuration files with multi-format support,
environment-specific configurations, validation, and CLI tools.

Features:
- Multi-format support: YAML, JSON, TOML
- Environment management (development, staging, production)
- Intelligent configuration merging with priorities
- Environment variable overrides
- Configuration validation
- CLI interface for validation and display

Example:
    >>> from config_manager import ConfigManager
    >>> config = ConfigManager()
    >>> config.load_file("config.yaml")
    >>> config.set_environment("production")
    >>> db_host = config.get("database.host")
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core import ConfigManager
from .env import Environment, EnvironmentManager
from .validators import ConfigValidator, ValidationRule, ConfigValidationError

__all__ = [
    'ConfigManager',
    'Environment',
    'EnvironmentManager',
    'ConfigValidator',
    'ValidationRule',
    'ConfigValidationError'
]