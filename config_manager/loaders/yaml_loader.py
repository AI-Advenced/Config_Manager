"""
YAML configuration file loader.

This module provides a loader for YAML configuration files using PyYAML.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Union, List
from .base import BaseLoader


class YAMLLoader(BaseLoader):
    """
    Loader for YAML configuration files.
    
    Supports both .yaml and .yml file extensions.
    Uses PyYAML's safe_load for security.
    """
    
    def load(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a YAML configuration file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the parsed YAML data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If YAML parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                # Return empty dict if file is empty or contains only None
                return data if data is not None else {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading YAML file {file_path}: {e}")
    
    def dump(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save data to a YAML file.
        
        Args:
            data: Configuration data to save
            file_path: Path where to save the YAML file
            
        Raises:
            IOError: If writing to file fails
        """
        file_path = Path(file_path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(
                    data, 
                    file, 
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False
                )
        except Exception as e:
            raise IOError(f"Error writing YAML file {file_path}: {e}")
    
    @property
    def supported_extensions(self) -> List[str]:
        """Return supported YAML file extensions."""
        return ['.yaml', '.yml']