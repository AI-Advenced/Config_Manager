"""
Core configuration manager.

This module provides the main ConfigManager class that orchestrates
all configuration loading, merging, validation, and access functionality.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Iterator
from .loaders import YAMLLoader, JSONLoader, TOMLLoader, BaseLoader
from .env import EnvironmentManager, Environment
from .validators import ConfigValidator, ValidationRule, ConfigValidationError
from .utils import deep_merge, get_nested_value, set_nested_value, has_nested_key


class ConfigManager:
    """
    Main configuration manager class.
    
    Provides a comprehensive interface for loading, merging, validating,
    and accessing configuration data from multiple sources and formats.
    
    Features:
    - Multi-format support (YAML, JSON, TOML)
    - Environment-specific configurations
    - Environment variable overrides
    - Configuration validation
    - Intelligent merging with precedence
    - Dot-notation key access
    """
    
    def __init__(self, env_var_name: str = 'APP_ENV'):
        """
        Initialize the configuration manager.
        
        Args:
            env_var_name: Environment variable name for environment detection
        """
        self.config_data: Dict[str, Any] = {}
        self.env_manager = EnvironmentManager(env_var_name)
        self.validator = ConfigValidator()
        
        # Register file format loaders
        self.loaders: Dict[str, BaseLoader] = {}
        self._register_loaders()
        
        # Track loaded files for reload functionality
        self.loaded_files: List[Path] = []
        
        # Cache for resolved configuration (cleared on data changes)
        self._resolved_cache: Optional[Dict[str, Any]] = None
    
    def _register_loaders(self):
        """Register all available configuration file loaders."""
        loaders = [YAMLLoader(), JSONLoader(), TOMLLoader()]
        
        for loader in loaders:
            for extension in loader.supported_extensions:
                self.loaders[extension.lower()] = loader
    
    def load_file(self, file_path: Union[str, Path], 
                  encoding: str = 'utf-8') -> 'ConfigManager':
        """
        Load a configuration file and merge it with existing configuration.
        
        Files loaded later take precedence over earlier files.
        
        Args:
            file_path: Path to configuration file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Self for method chaining
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported or parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine loader based on file extension
        extension = file_path.suffix.lower()
        if extension not in self.loaders:
            supported_formats = list(self.loaders.keys())
            raise ValueError(f"Unsupported file format: {extension}. "
                           f"Supported formats: {supported_formats}")
        
        loader = self.loaders[extension]
        
        try:
            file_data = loader.load(file_path)
        except Exception as e:
            raise ValueError(f"Error loading configuration from {file_path}: {e}")
        
        # Merge with existing configuration (file_data takes precedence)
        self.config_data = deep_merge(self.config_data, file_data)
        self.loaded_files.append(file_path)
        
        # Clear resolved cache since data changed
        self._resolved_cache = None
        
        return self
    
    def load_directory(self, directory: Union[str, Path], 
                      pattern: str = "*", 
                      recursive: bool = False,
                      sort_files: bool = True) -> 'ConfigManager':
        """
        Load all supported configuration files from a directory.
        
        Args:
            directory: Directory path to scan
            pattern: Glob pattern for file matching (default: "*")
            recursive: Whether to search subdirectories
            sort_files: Whether to sort files before loading (for consistent order)
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If directory doesn't exist
        """
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")
        
        # Collect configuration files
        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)
        
        # Filter supported files and sort if requested
        config_files = [
            file_path for file_path in files
            if file_path.is_file() and file_path.suffix.lower() in self.loaders
        ]
        
        if sort_files:
            config_files.sort()
        
        # Load files in order
        for file_path in config_files:
            self.load_file(file_path)
        
        return self
    
    def load_dict(self, config_dict: Dict[str, Any]) -> 'ConfigManager':
        """
        Load configuration from a dictionary.
        
        Args:
            config_dict: Dictionary to merge with current configuration
            
        Returns:
            Self for method chaining
        """
        self.config_data = deep_merge(self.config_data, config_dict)
        self._resolved_cache = None
        return self
    
    def set_environment(self, environment: Union[str, Environment]) -> 'ConfigManager':
        """
        Set the current environment.
        
        This affects which environment-specific configurations are used.
        
        Args:
            environment: Environment name or Environment enum
            
        Returns:
            Self for method chaining
        """
        self.env_manager.set_environment(environment)
        self._resolved_cache = None  # Clear cache since environment changed
        return self
    
    def apply_env_overrides(self, prefix: str = 'CONFIG_') -> 'ConfigManager':
        """
        Apply configuration overrides from environment variables.
        
        Environment variables with the specified prefix will override
        corresponding configuration values.
        
        Args:
            prefix: Environment variable prefix to look for
            
        Returns:
            Self for method chaining
        """
        overrides = self.env_manager.get_env_overrides(prefix)
        if overrides:
            self.config_data = deep_merge(self.config_data, overrides)
            self._resolved_cache = None
        
        return self
    
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value with environment-specific resolution.
        
        Resolution order:
        1. Environment-specific value (e.g., 'production.database.host')
        2. General value (e.g., 'database.host')
        3. Default value
        
        Args:
            key_path: Dot-separated path to the configuration value
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get('database.host', 'localhost')
            >>> config.get('app.debug', False)
        """
        # First check for environment-specific value
        env_key = self.env_manager.get_environment_config_key(key_path)
        env_value = get_nested_value(self.config_data, env_key)
        
        if env_value is not None:
            return env_value
        
        # Fall back to general value
        return get_nested_value(self.config_data, key_path, default)
    
    def set(self, key_path: str, value: Any) -> 'ConfigManager':
        """
        Set a configuration value.
        
        Args:
            key_path: Dot-separated path to set
            value: Value to set
            
        Returns:
            Self for method chaining
        """
        set_nested_value(self.config_data, key_path, value)
        self._resolved_cache = None
        return self
    
    def has(self, key_path: str) -> bool:
        """
        Check if a configuration key exists.
        
        Checks both environment-specific and general keys.
        
        Args:
            key_path: Dot-separated path to check
            
        Returns:
            True if key exists, False otherwise
        """
        # Check environment-specific key first
        env_key = self.env_manager.get_environment_config_key(key_path)
        if has_nested_key(self.config_data, env_key):
            return True
        
        # Check general key
        return has_nested_key(self.config_data, key_path)
    
    def delete(self, key_path: str) -> 'ConfigManager':
        """
        Delete a configuration key.
        
        Args:
            key_path: Dot-separated path to delete
            
        Returns:
            Self for method chaining
        """
        keys = key_path.split('.')
        current_data = self.config_data
        
        # Navigate to parent of target key
        try:
            for key in keys[:-1]:
                current_data = current_data[key]
            
            # Delete the target key if it exists
            if keys[-1] in current_data:
                del current_data[keys[-1]]
                self._resolved_cache = None
        except (KeyError, TypeError):
            pass  # Key doesn't exist, nothing to delete
        
        return self
    
    def update(self, updates: Dict[str, Any]) -> 'ConfigManager':
        """
        Update configuration with multiple values.
        
        Args:
            updates: Dictionary of key_path -> value mappings
            
        Returns:
            Self for method chaining
        """
        for key_path, value in updates.items():
            self.set(key_path, value)
        
        return self
    
    def get_resolved_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get the fully resolved configuration.
        
        Returns the complete configuration with environment-specific
        values resolved and merged.
        
        Args:
            use_cache: Whether to use cached result
            
        Returns:
            Resolved configuration dictionary
        """
        if use_cache and self._resolved_cache is not None:
            return self._resolved_cache
        
        # Start with base configuration
        resolved = dict(self.config_data)
        
        # Apply environment-specific overrides
        env_key = self.env_manager.current_environment.value
        if env_key in resolved:
            env_config = resolved.pop(env_key)
            if isinstance(env_config, dict):
                resolved = deep_merge(resolved, env_config)
        
        if use_cache:
            self._resolved_cache = resolved
        
        return resolved
    
    def validate(self, raise_on_error: bool = False) -> List[str]:
        """
        Validate the current configuration.
        
        Args:
            raise_on_error: Whether to raise exception on validation errors
            
        Returns:
            List of validation error messages
            
        Raises:
            ConfigValidationError: If raise_on_error=True and validation fails
        """
        resolved_config = self.get_resolved_config()
        return self.validator.validate(resolved_config, raise_on_error)
    
    def add_validation_rule(self, key_path: str, 
                           rule: Union[ValidationRule, str], 
                           **kwargs) -> 'ConfigManager':
        """
        Add a validation rule for a configuration key.
        
        Args:
            key_path: Dot-separated path to validate
            rule: ValidationRule instance or built-in rule name
            **kwargs: Additional arguments for built-in rules
            
        Returns:
            Self for method chaining
        """
        self.validator.add_rule(key_path, rule, **kwargs)
        return self
    
    def remove_validation_rule(self, key_path: str, 
                              rule_name: Optional[str] = None) -> 'ConfigManager':
        """
        Remove validation rule(s) for a key path.
        
        Args:
            key_path: Configuration key path
            rule_name: Specific rule to remove (None for all)
            
        Returns:
            Self for method chaining
        """
        self.validator.remove_rule(key_path, rule_name)
        return self
    
    def to_dict(self, resolved: bool = True) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Args:
            resolved: Whether to return resolved configuration
            
        Returns:
            Configuration dictionary
        """
        if resolved:
            return dict(self.get_resolved_config())
        else:
            return dict(self.config_data)
    
    def save_to_file(self, file_path: Union[str, Path], 
                     format_override: Optional[str] = None,
                     resolved: bool = True) -> None:
        """
        Save configuration to a file.
        
        Args:
            file_path: Path where to save the file
            format_override: Force specific format (yaml, json, toml)
            resolved: Whether to save resolved configuration
            
        Raises:
            ValueError: If format is not supported
        """
        file_path = Path(file_path)
        
        # Determine format
        if format_override:
            extension = f".{format_override.lower()}"
        else:
            extension = file_path.suffix.lower()
        
        if extension not in self.loaders:
            supported_formats = list(self.loaders.keys())
            raise ValueError(f"Unsupported format: {extension}. "
                           f"Supported: {supported_formats}")
        
        loader = self.loaders[extension]
        data = self.to_dict(resolved=resolved)
        
        loader.dump(data, file_path)
    
    def reload(self) -> 'ConfigManager':
        """
        Reload all previously loaded files.
        
        Clears current configuration and reloads all files in the same order.
        
        Returns:
            Self for method chaining
        """
        files_to_reload = self.loaded_files.copy()
        
        # Clear current state
        self.config_data = {}
        self.loaded_files = []
        self._resolved_cache = None
        
        # Reload all files
        for file_path in files_to_reload:
            if file_path.exists():
                self.load_file(file_path)
        
        return self
    
    def clear(self) -> 'ConfigManager':
        """
        Clear all configuration data.
        
        Returns:
            Self for method chaining
        """
        self.config_data = {}
        self.loaded_files = []
        self._resolved_cache = None
        return self
    
    def keys(self, resolved: bool = True) -> List[str]:
        """
        Get all configuration keys (flattened with dot notation).
        
        Args:
            resolved: Whether to use resolved configuration
            
        Returns:
            List of all configuration keys
        """
        from .utils import flatten_dict
        
        config = self.get_resolved_config() if resolved else self.config_data
        flat_config = flatten_dict(config)
        return list(flat_config.keys())
    
    def items(self, resolved: bool = True) -> Iterator[tuple]:
        """
        Iterate over configuration key-value pairs.
        
        Args:
            resolved: Whether to use resolved configuration
            
        Yields:
            (key_path, value) tuples
        """
        config = self.get_resolved_config() if resolved else self.config_data
        
        def _iter_items(data, prefix=''):
            for key, value in data.items():
                key_path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    yield from _iter_items(value, key_path)
                else:
                    yield (key_path, value)
        
        yield from _iter_items(config)
    
    # Magic methods for dict-like access
    def __getitem__(self, key: str) -> Any:
        """Allow config['key'] access."""
        value = self.get(key)
        if value is None and not self.has(key):
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow config['key'] = value assignment."""
        self.set(key, value)
    
    def __delitem__(self, key: str) -> None:
        """Allow del config['key']."""
        if not self.has(key):
            raise KeyError(key)
        self.delete(key)
    
    def __contains__(self, key: str) -> bool:
        """Allow 'key' in config checks."""
        return self.has(key)
    
    def __len__(self) -> int:
        """Return number of top-level keys."""
        return len(self.get_resolved_config())
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over top-level keys."""
        return iter(self.get_resolved_config().keys())
    
    def __str__(self) -> str:
        """String representation of configuration."""
        import json
        try:
            return json.dumps(self.get_resolved_config(), indent=2, default=str)
        except Exception:
            return repr(self.config_data)
    
    def __repr__(self) -> str:
        """Detailed representation."""
        num_files = len(self.loaded_files)
        num_keys = len(self.keys())
        env = self.env_manager.current_environment.value
        return (f"ConfigManager(files={num_files}, keys={num_keys}, "
                f"env={env})")