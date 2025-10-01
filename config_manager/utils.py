"""
Utility functions for configuration management.

This module provides helper functions for deep merging dictionaries,
accessing nested values with dot notation, and flattening nested structures.
"""

from typing import Dict, Any, Optional, Union, List
from copy import deepcopy


def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Values from overlay take precedence over values in base.
    Nested dictionaries are merged recursively, while other types are replaced.
    
    Args:
        base: Base dictionary
        overlay: Dictionary to merge on top of base
        
    Returns:
        New dictionary with merged values
        
    Example:
        >>> base = {"db": {"host": "localhost", "port": 5432}}
        >>> overlay = {"db": {"host": "remote", "ssl": True}}
        >>> result = deep_merge(base, overlay)
        >>> print(result)
        {"db": {"host": "remote", "port": 5432, "ssl": True}}
    """
    result = deepcopy(base)
    
    for key, value in overlay.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            # Recursively merge nested dictionaries
            result[key] = deep_merge(result[key], value)
        else:
            # Replace with new value (deep copy to avoid references)
            result[key] = deepcopy(value)
    
    return result


def get_nested_value(data: Dict[str, Any], key_path: str, 
                    default: Any = None, separator: str = '.') -> Any:
    """
    Retrieve a nested value using dot notation.
    
    Args:
        data: Dictionary to search in
        key_path: Dot-separated path to the value (e.g., 'database.host')
        default: Default value if key is not found
        separator: Character used to separate nested keys
        
    Returns:
        The value at the specified path, or default if not found
        
    Example:
        >>> data = {"database": {"host": "localhost", "port": 5432}}
        >>> host = get_nested_value(data, 'database.host')
        >>> print(host)  # "localhost"
        >>> missing = get_nested_value(data, 'database.ssl', False)
        >>> print(missing)  # False
    """
    keys = key_path.split(separator)
    current_data = data
    
    try:
        for key in keys:
            if not isinstance(current_data, dict):
                return default
            current_data = current_data[key]
        return current_data
    except (KeyError, TypeError):
        return default


def set_nested_value(data: Dict[str, Any], key_path: str, 
                    value: Any, separator: str = '.') -> None:
    """
    Set a nested value using dot notation.
    
    Creates intermediate dictionaries if they don't exist.
    
    Args:
        data: Dictionary to modify (modified in place)
        key_path: Dot-separated path to set (e.g., 'database.host')
        value: Value to set
        separator: Character used to separate nested keys
        
    Example:
        >>> data = {}
        >>> set_nested_value(data, 'database.host', 'localhost')
        >>> print(data)  # {"database": {"host": "localhost"}}
    """
    keys = key_path.split(separator)
    current_data = data
    
    # Navigate to the parent of the target key, creating dicts as needed
    for key in keys[:-1]:
        if key not in current_data:
            current_data[key] = {}
        elif not isinstance(current_data[key], dict):
            # Replace non-dict values with empty dict
            current_data[key] = {}
        current_data = current_data[key]
    
    # Set the final value
    current_data[keys[-1]] = value


def has_nested_key(data: Dict[str, Any], key_path: str, separator: str = '.') -> bool:
    """
    Check if a nested key exists using dot notation.
    
    Args:
        data: Dictionary to check
        key_path: Dot-separated path to check
        separator: Character used to separate nested keys
        
    Returns:
        True if the key exists, False otherwise
    """
    keys = key_path.split(separator)
    current_data = data
    
    try:
        for key in keys:
            if not isinstance(current_data, dict) or key not in current_data:
                return False
            current_data = current_data[key]
        return True
    except (KeyError, TypeError):
        return False


def flatten_dict(data: Dict[str, Any], separator: str = '.', 
                prefix: str = '') -> Dict[str, Any]:
    """
    Flatten a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to flatten
        separator: Character to use for separating nested keys
        prefix: Prefix for keys (used internally for recursion)
        
    Returns:
        Flattened dictionary with dot-separated keys
        
    Example:
        >>> nested = {"database": {"host": "localhost", "credentials": {"user": "admin"}}}
        >>> flat = flatten_dict(nested)
        >>> print(flat)
        {
            "database.host": "localhost",
            "database.credentials.user": "admin"
        }
    """
    result = {}
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value
    
    return result


def unflatten_dict(flat_data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    Convert a flattened dictionary back to nested structure.
    
    Args:
        flat_data: Flattened dictionary with dot-separated keys
        separator: Character used to separate nested keys
        
    Returns:
        Nested dictionary structure
        
    Example:
        >>> flat = {"database.host": "localhost", "database.port": 5432}
        >>> nested = unflatten_dict(flat)
        >>> print(nested)
        {"database": {"host": "localhost", "port": 5432}}
    """
    result = {}
    
    for key_path, value in flat_data.items():
        set_nested_value(result, key_path, value, separator)
    
    return result


def filter_dict_by_prefix(data: Dict[str, Any], prefix: str, 
                         remove_prefix: bool = False, separator: str = '.') -> Dict[str, Any]:
    """
    Filter a flattened dictionary by key prefix.
    
    Args:
        data: Dictionary to filter
        prefix: Prefix to filter by
        remove_prefix: Whether to remove the prefix from resulting keys
        separator: Character used to separate nested keys
        
    Returns:
        Filtered dictionary
    """
    result = {}
    prefix_with_sep = f"{prefix}{separator}"
    
    for key, value in data.items():
        if key.startswith(prefix_with_sep) or key == prefix:
            if remove_prefix and key.startswith(prefix_with_sep):
                new_key = key[len(prefix_with_sep):]
            else:
                new_key = key
            result[new_key] = value
    
    return result