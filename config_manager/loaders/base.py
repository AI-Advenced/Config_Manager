"""
Base loader interface for configuration file formats.

This module provides the abstract base class that all configuration loaders must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Union, List
from pathlib import Path


class BaseLoader(ABC):
    """
    Abstract base class for all configuration file loaders.
    
    Each loader must implement methods to load and dump configuration data,
    as well as specify which file extensions it supports.
    """
    
    @abstractmethod
    def load(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration data from a file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the loaded configuration data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid or parsing fails
        """
        pass
    
    @abstractmethod
    def dump(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save configuration data to a file.
        
        Args:
            data: Configuration data to save
            file_path: Path where to save the file
            
        Raises:
            IOError: If writing to file fails
            ValueError: If data cannot be serialized
        """
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        List of file extensions supported by this loader.
        
        Returns:
            List of supported file extensions (including the dot, e.g., ['.yaml', '.yml'])
        """
        pass
    
    def supports_file(self, file_path: Union[str, Path]) -> bool:
        """
        Check if this loader supports the given file based on its extension.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file extension is supported, False otherwise
        """
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions