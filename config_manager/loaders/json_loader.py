"""
JSON configuration file loader.

This module provides a loader for JSON configuration files using the standard json library.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union, List
from .base import BaseLoader


class JSONLoader(BaseLoader):
    """
    Loader for JSON configuration files.
    
    Supports .json file extension.
    Provides pretty-printing with proper indentation when saving.
    """
    
    def load(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON configuration file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the parsed JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If JSON parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Ensure we always return a dictionary
                if not isinstance(data, dict):
                    raise ValueError(f"JSON root must be an object, got {type(data).__name__}")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing error in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading JSON file {file_path}: {e}")
    
    def dump(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save data to a JSON file.
        
        Args:
            data: Configuration data to save
            file_path: Path where to save the JSON file
            
        Raises:
            IOError: If writing to file fails
            ValueError: If data cannot be serialized to JSON
        """
        file_path = Path(file_path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(
                    data, 
                    file, 
                    indent=2, 
                    ensure_ascii=False,
                    sort_keys=False,
                    separators=(',', ': ')
                )
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error serializing data to JSON: {e}")
        except Exception as e:
            raise IOError(f"Error writing JSON file {file_path}: {e}")
    
    @property
    def supported_extensions(self) -> List[str]:
        """Return supported JSON file extensions."""
        return ['.json']