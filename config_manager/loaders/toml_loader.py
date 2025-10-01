"""
TOML configuration file loader.

This module provides a loader for TOML configuration files.
Uses tomllib (Python 3.11+) or tomli for reading, and tomli_w for writing.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Union, List
from .base import BaseLoader

# Support Python 3.11+ with built-in tomllib, otherwise use tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("tomli is required for Python < 3.11. Install with: pip install tomli")

try:
    import tomli_w
except ImportError:
    raise ImportError("tomli_w is required for TOML writing. Install with: pip install tomli-w")


class TOMLLoader(BaseLoader):
    """
    Loader for TOML configuration files.
    
    Supports .toml file extension.
    Uses tomllib/tomli for reading and tomli_w for writing.
    """
    
    def load(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a TOML configuration file.
        
        Args:
            file_path: Path to the TOML file
            
        Returns:
            Dictionary containing the parsed TOML data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If TOML parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                data = tomllib.load(file)
                return data if data is not None else {}
        except Exception as e:
            raise ValueError(f"TOML parsing error in {file_path}: {e}")
    
    def dump(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save data to a TOML file.
        
        Args:
            data: Configuration data to save
            file_path: Path where to save the TOML file
            
        Raises:
            IOError: If writing to file fails
            ValueError: If data cannot be serialized to TOML
        """
        file_path = Path(file_path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'wb') as file:
                tomli_w.dump(data, file)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error serializing data to TOML: {e}")
        except Exception as e:
            raise IOError(f"Error writing TOML file {file_path}: {e}")
    
    @property
    def supported_extensions(self) -> List[str]:
        """Return supported TOML file extensions."""
        return ['.toml']