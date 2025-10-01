"""
Tests for configuration file loaders.
"""

import pytest
import tempfile
import json
from pathlib import Path
from config_manager.loaders import YAMLLoader, JSONLoader, TOMLLoader


class TestYAMLLoader:
    """Test suite for YAML loader."""
    
    def test_load_valid_yaml(self):
        """Test loading valid YAML file."""
        yaml_content = """
app:
  name: "Test App"
  debug: true
  version: 1.0
database:
  host: "localhost"
  port: 5432
  credentials:
    username: "admin"
    password: "secret"
features:
  - authentication
  - logging
  - monitoring
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            data = loader.load(temp_path)
            
            assert data["app"]["name"] == "Test App"
            assert data["app"]["debug"] is True
            assert data["app"]["version"] == 1.0
            assert data["database"]["host"] == "localhost"
            assert data["database"]["port"] == 5432
            assert data["database"]["credentials"]["username"] == "admin"
            assert len(data["features"]) == 3
            assert "authentication" in data["features"]
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_yaml(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            data = loader.load(temp_path)
            
            assert data == {}
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_yaml_with_null(self):
        """Test loading YAML file with null content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("null")  # YAML null
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            data = loader.load(temp_path)
            
            assert data == {}
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        invalid_yaml = """
app:
  name: "Test App"
    invalid_indentation: true
database:
  - host: localhost
  port: 5432  # This is incorrectly indented
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            
            with pytest.raises(ValueError, match="YAML parsing error"):
                loader.load(temp_path)
                
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_yaml(self):
        """Test loading non-existent YAML file."""
        loader = YAMLLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.yaml")
    
    def test_dump_yaml(self):
        """Test saving data to YAML file."""
        data = {
            "app": {
                "name": "Test App",
                "debug": True,
                "version": 2.0
            },
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "features": ["auth", "logging"]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            loader.dump(data, temp_path)
            
            # Load back and verify
            loaded_data = loader.load(temp_path)
            assert loaded_data == data
            
        finally:
            Path(temp_path).unlink()
    
    def test_supported_extensions(self):
        """Test YAML loader supported extensions."""
        loader = YAMLLoader()
        extensions = loader.supported_extensions
        
        assert '.yaml' in extensions
        assert '.yml' in extensions
        assert loader.supports_file('config.yaml')
        assert loader.supports_file('config.yml')
        assert not loader.supports_file('config.json')


class TestJSONLoader:
    """Test suite for JSON loader."""
    
    def test_load_valid_json(self):
        """Test loading valid JSON file."""
        data = {
            "app": {
                "name": "JSON Test App",
                "debug": False,
                "version": 1.5
            },
            "database": {
                "host": "json-host",
                "port": 3306,
                "ssl": True
            },
            "list_data": [1, 2, 3, "four"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            loader = JSONLoader()
            loaded_data = loader.load(temp_path)
            
            assert loaded_data == data
            assert loaded_data["app"]["name"] == "JSON Test App"
            assert loaded_data["database"]["ssl"] is True
            assert len(loaded_data["list_data"]) == 4
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        invalid_json = '{"app": {"name": "Test"}, "invalid": }'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name
        
        try:
            loader = JSONLoader()
            
            with pytest.raises(ValueError, match="JSON parsing error"):
                loader.load(temp_path)
                
        finally:
            Path(temp_path).unlink()
    
    def test_load_non_dict_json(self):
        """Test loading JSON file with non-dictionary root."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["this", "is", "a", "list"], f)
            temp_path = f.name
        
        try:
            loader = JSONLoader()
            
            with pytest.raises(ValueError, match="JSON root must be an object"):
                loader.load(temp_path)
                
        finally:
            Path(temp_path).unlink()
    
    def test_dump_json(self):
        """Test saving data to JSON file."""
        data = {
            "app": {"name": "Dump Test", "version": 1.0},
            "features": {"auth": True, "logging": False},
            "numbers": [1, 2, 3.14, 42]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            loader = JSONLoader()
            loader.dump(data, temp_path)
            
            # Load back and verify
            loaded_data = loader.load(temp_path)
            assert loaded_data == data
            
            # Check file is properly formatted
            with open(temp_path, 'r') as f:
                content = f.read()
                assert '"app"' in content  # Should be pretty-printed
                
        finally:
            Path(temp_path).unlink()
    
    def test_supported_extensions(self):
        """Test JSON loader supported extensions."""
        loader = JSONLoader()
        extensions = loader.supported_extensions
        
        assert '.json' in extensions
        assert loader.supports_file('config.json')
        assert not loader.supports_file('config.yaml')


class TestTOMLLoader:
    """Test suite for TOML loader."""
    
    def test_load_valid_toml(self):
        """Test loading valid TOML file."""
        toml_content = """
title = "TOML Test"

[app]
name = "TOML Test App"
debug = true
version = 2.0

[database]
host = "toml-host"
port = 5432
ssl = false

[database.credentials]
username = "admin"
password = "toml-secret"

[features]
auth = true
logging = false
monitoring = true

[[servers]]
name = "server1"
ip = "192.168.1.1"

[[servers]]
name = "server2"
ip = "192.168.1.2"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            temp_path = f.name
        
        try:
            loader = TOMLLoader()
            data = loader.load(temp_path)
            
            assert data["title"] == "TOML Test"
            assert data["app"]["name"] == "TOML Test App"
            assert data["app"]["debug"] is True
            assert data["database"]["host"] == "toml-host"
            assert data["database"]["credentials"]["username"] == "admin"
            assert data["features"]["auth"] is True
            assert len(data["servers"]) == 2
            assert data["servers"][0]["name"] == "server1"
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_toml(self):
        """Test loading empty TOML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            loader = TOMLLoader()
            data = loader.load(temp_path)
            
            assert data == {}
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_toml(self):
        """Test loading invalid TOML file."""
        invalid_toml = """
[app]
name = "Test App"
invalid_key_without_quotes = this will fail
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(invalid_toml)
            temp_path = f.name
        
        try:
            loader = TOMLLoader()
            
            with pytest.raises(ValueError, match="TOML parsing error"):
                loader.load(temp_path)
                
        finally:
            Path(temp_path).unlink()
    
    def test_dump_toml(self):
        """Test saving data to TOML file."""
        data = {
            "title": "Test Config",
            "app": {
                "name": "Test App",
                "debug": False,
                "version": 1.0
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.toml', delete=False) as f:
            temp_path = f.name
        
        try:
            loader = TOMLLoader()
            loader.dump(data, temp_path)
            
            # Load back and verify
            loaded_data = loader.load(temp_path)
            assert loaded_data == data
            
        finally:
            Path(temp_path).unlink()
    
    def test_supported_extensions(self):
        """Test TOML loader supported extensions."""
        loader = TOMLLoader()
        extensions = loader.supported_extensions
        
        assert '.toml' in extensions
        assert loader.supports_file('config.toml')
        assert not loader.supports_file('config.json')


class TestLoaderIntegration:
    """Integration tests for multiple loaders."""
    
    def test_cross_format_consistency(self):
        """Test that same data loaded from different formats is equivalent."""
        test_data = {
            "app": {
                "name": "Cross Format Test",
                "debug": True,
                "version": 1.0
            },
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }
        
        # Create files in different formats
        yaml_content = """
app:
  name: "Cross Format Test"
  debug: true
  version: 1.0
database:
  host: "localhost"
  port: 5432
"""
        
        toml_content = """
[app]
name = "Cross Format Test"
debug = true
version = 1.0

[database]
host = "localhost"
port = 5432
"""
        
        temp_files = []
        
        try:
            # Create JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_files.append(f.name)
            
            # Create YAML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml_content)
                temp_files.append(f.name)
            
            # Create TOML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
                f.write(toml_content)
                temp_files.append(f.name)
            
            # Load with appropriate loaders
            json_loader = JSONLoader()
            yaml_loader = YAMLLoader()
            toml_loader = TOMLLoader()
            
            json_data = json_loader.load(temp_files[0])
            yaml_data = yaml_loader.load(temp_files[1])
            toml_data = toml_loader.load(temp_files[2])
            
            # All should be equivalent
            assert json_data == yaml_data == toml_data == test_data
            
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_loader_directory_creation(self):
        """Test that loaders create parent directories when dumping."""
        test_data = {"test": "data"}
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to save to a nested path that doesn't exist
            nested_path = Path(temp_dir) / "nested" / "subdir" / "config.json"
            
            loader = JSONLoader()
            loader.dump(test_data, nested_path)
            
            # Verify file was created
            assert nested_path.exists()
            
            # Verify data is correct
            loaded_data = loader.load(nested_path)
            assert loaded_data == test_data