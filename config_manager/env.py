"""
Environment management for configuration.

This module provides environment-specific configuration handling and 
environment variable overrides.
"""

import os
from enum import Enum
from typing import Optional, Dict, Any, Union
from .utils import set_nested_value


class Environment(Enum):
    """Enumeration of supported environments."""
    
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"
    TESTING = "testing"
    
    @classmethod
    def from_string(cls, env_str: str) -> 'Environment':
        """
        Create an Environment from a string value.
        
        Supports common aliases for environment names.
        
        Args:
            env_str: String representation of environment
            
        Returns:
            Environment enum value
            
        Raises:
            ValueError: If environment string is not recognized
        """
        env_map = {
            # Development aliases
            'dev': cls.DEVELOPMENT,
            'develop': cls.DEVELOPMENT, 
            'development': cls.DEVELOPMENT,
            'local': cls.DEVELOPMENT,
            
            # Staging aliases
            'stage': cls.STAGING,
            'staging': cls.STAGING,
            'preprod': cls.STAGING,
            'pre-production': cls.STAGING,
            
            # Production aliases
            'prod': cls.PRODUCTION,
            'production': cls.PRODUCTION,
            'live': cls.PRODUCTION,
            
            # Testing aliases  
            'test': cls.TESTING,
            'testing': cls.TESTING,
            'ci': cls.TESTING,
        }
        
        normalized_env = env_str.lower().strip()
        if normalized_env in env_map:
            return env_map[normalized_env]
        
        # Try direct enum value match
        try:
            return cls(normalized_env)
        except ValueError:
            raise ValueError(f"Unknown environment: {env_str}. "
                           f"Supported values: {list(env_map.keys())}")
    
    def __str__(self) -> str:
        return self.value


class EnvironmentManager:
    """
    Manager for environment-specific configurations and variable overrides.
    
    Handles:
    - Current environment detection and management
    - Environment variable overrides with configurable prefixes
    - Type conversion for environment variables
    """
    
    def __init__(self, env_var_name: str = 'APP_ENV'):
        """
        Initialize the environment manager.
        
        Args:
            env_var_name: Name of environment variable that specifies current environment
        """
        self.env_var_name = env_var_name
        self._current_env: Optional[Environment] = None
        self._env_overrides_cache: Optional[Dict[str, Any]] = None
    
    @property
    def current_environment(self) -> Environment:
        """
        Get the current environment.
        
        Determines environment from:
        1. Previously set environment (via set_environment)
        2. Environment variable (specified by env_var_name)  
        3. Default to DEVELOPMENT
        
        Returns:
            Current environment
        """
        if self._current_env is None:
            env_str = os.getenv(self.env_var_name, 'development')
            try:
                self._current_env = Environment.from_string(env_str)
            except ValueError:
                # Fallback to development if invalid environment
                self._current_env = Environment.DEVELOPMENT
        
        return self._current_env
    
    def set_environment(self, environment: Union[str, Environment]) -> None:
        """
        Set the current environment.
        
        Args:
            environment: Environment to set (string or Environment enum)
            
        Raises:
            ValueError: If environment string is not recognized
        """
        if isinstance(environment, str):
            environment = Environment.from_string(environment)
        
        self._current_env = environment
        # Clear cache when environment changes
        self._env_overrides_cache = None
    
    def get_env_overrides(self, prefix: str = 'CONFIG_', 
                         cache: bool = True) -> Dict[str, Any]:
        """
        Get configuration overrides from environment variables.
        
        Environment variables with the specified prefix are converted to 
        configuration keys using the following rules:
        - Remove the prefix
        - Convert to lowercase
        - Replace underscores with dots for nested keys
        - Attempt type conversion (bool, int, float, string)
        
        Args:
            prefix: Prefix to look for in environment variable names
            cache: Whether to cache results (cleared when environment changes)
            
        Returns:
            Dictionary with configuration overrides
            
        Example:
            Given environment variables:
            CONFIG_DATABASE_HOST=myhost.com
            CONFIG_DATABASE_PORT=5432
            CONFIG_APP_DEBUG=true
            
            Returns:
            {
                "database": {
                    "host": "myhost.com", 
                    "port": 5432
                },
                "app": {
                    "debug": True
                }
            }
        """
        if cache and self._env_overrides_cache is not None:
            return self._env_overrides_cache
        
        overrides = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to config key format
                config_key = key[len(prefix):].lower().replace('_', '.')
                
                # Convert the value to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Set nested value in overrides dict
                set_nested_value(overrides, config_key, converted_value)
        
        if cache:
            self._env_overrides_cache = overrides
        
        return overrides
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable value to appropriate Python type.
        
        Conversion rules:
        - 'true', 'yes', '1', 'on' (case-insensitive) -> True
        - 'false', 'no', '0', 'off' (case-insensitive) -> False  
        - Numeric strings -> int or float
        - Everything else -> string
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value
        """
        # Handle empty values
        if not value:
            return ""
        
        # Boolean values (case-insensitive)
        lower_value = value.lower()
        if lower_value in ('true', 'yes', '1', 'on', 'enabled'):
            return True
        elif lower_value in ('false', 'no', '0', 'off', 'disabled'):
            return False
        
        # Numeric values
        try:
            # Try integer first
            if '.' not in value and 'e' not in lower_value:
                return int(value)
            else:
                # Try float
                return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def clear_cache(self) -> None:
        """Clear the environment overrides cache."""
        self._env_overrides_cache = None
    
    def get_environment_config_key(self, base_key: str) -> str:
        """
        Get the environment-specific configuration key.
        
        Args:
            base_key: Base configuration key
            
        Returns:
            Environment-prefixed key (e.g., 'production.database.host')
        """
        return f"{self.current_environment.value}.{base_key}"
    
    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.current_environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if current environment is production."""  
        return self.current_environment == Environment.PRODUCTION
    
    def is_staging(self) -> bool:
        """Check if current environment is staging."""
        return self.current_environment == Environment.STAGING
    
    def is_testing(self) -> bool:
        """Check if current environment is testing."""
        return self.current_environment == Environment.TESTING