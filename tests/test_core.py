"""
Tests for the core ConfigManager functionality.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from config_manager import ConfigManager, Environment, ConfigValidationError


class TestConfigManager:
    """Test suite for ConfigManager class."""
    
    def test_initialization(self):
        """Test ConfigManager initialization."""
        config = ConfigManager()
        assert config.config_data == {}
        assert config.env_manager.env_var_name == 'APP_ENV'
        assert len(config.loaded_files) == 0
    
    def test_custom_env_var_name(self):
        """Test ConfigManager with custom environment variable name."""
        config = ConfigManager(env_var_name='CUSTOM_ENV')
        assert config.env_manager.env_var_name == 'CUSTOM_ENV'
    
    def test_load_json_file(self):
        """Test loading JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "app": {"name": "Test App", "version": "1.0"},
                "database": {"host": "localhost", "port": 5432}
            }, f)
            temp_path = f.name
        
        try:
            config = ConfigManager()
            config.load_file(temp_path)
            
            assert config.get("app.name") == "Test App"
            assert config.get("app.version") == "1.0"
            assert config.get("database.host") == "localhost"
            assert config.get("database.port") == 5432
            assert len(config.loaded_files) == 1
        finally:
            Path(temp_path).unlink()
    
    def test_load_yaml_file(self):
        """Test loading YAML configuration file."""
        yaml_content = """
app:
  name: "YAML Test App"
  debug: true
database:
  host: "yaml-host"
  ssl: false
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = ConfigManager()
            config.load_file(temp_path)
            
            assert config.get("app.name") == "YAML Test App"
            assert config.get("app.debug") is True
            assert config.get("database.host") == "yaml-host"
            assert config.get("database.ssl") is False
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises appropriate error."""
        config = ConfigManager()
        
        with pytest.raises(FileNotFoundError):
            config.load_file("nonexistent_file.json")
    
    def test_load_unsupported_format(self):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"some text content")
            temp_path = f.name
        
        try:
            config = ConfigManager()
            with pytest.raises(ValueError, match="Unsupported file format"):
                config.load_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_file_merge_precedence(self):
        """Test that later files override earlier files."""
        # Create first file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump({
                "database": {"host": "first-host", "port": 5432, "ssl": False}
            }, f1)
            temp_path1 = f1.name
        
        # Create second file (should override)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump({
                "database": {"host": "second-host", "ssl": True}
            }, f2)
            temp_path2 = f2.name
        
        try:
            config = ConfigManager()
            config.load_file(temp_path1)
            config.load_file(temp_path2)
            
            # Second file should override host and ssl, but port should remain
            assert config.get("database.host") == "second-host"
            assert config.get("database.ssl") is True
            assert config.get("database.port") == 5432  # From first file
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()
    
    def test_environment_specific_configuration(self):
        """Test environment-specific configuration resolution."""
        config_data = {
            "app": {"debug": False, "name": "MyApp"},
            "database": {"host": "prod-host"},
            "development": {
                "app": {"debug": True},
                "database": {"host": "dev-host"}
            },
            "production": {
                "database": {"host": "prod-override"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigManager()
            config.load_file(temp_path)
            
            # Test development environment
            config.set_environment("development")
            assert config.get("app.debug") is True
            assert config.get("database.host") == "dev-host"
            assert config.get("app.name") == "MyApp"  # Should fall back to base
            
            # Test production environment
            config.set_environment("production")
            assert config.get("app.debug") is False  # Base value
            assert config.get("database.host") == "prod-override"
            
        finally:
            Path(temp_path).unlink()
    
    def test_environment_variable_overrides(self):
        """Test environment variable overrides."""
        # Set up test environment variables
        os.environ['CONFIG_DATABASE_HOST'] = 'env-host'
        os.environ['CONFIG_APP_DEBUG'] = 'true'
        os.environ['CONFIG_NESTED_DEEP_VALUE'] = '42'
        
        try:
            config = ConfigManager()
            config.load_dict({
                "database": {"host": "original-host"},
                "app": {"debug": False}
            })
            
            # Apply environment overrides
            config.apply_env_overrides()
            
            assert config.get("database.host") == "env-host"
            assert config.get("app.debug") is True
            assert config.get("nested.deep.value") == 42
            
        finally:
            # Clean up environment variables
            for key in ['CONFIG_DATABASE_HOST', 'CONFIG_APP_DEBUG', 'CONFIG_NESTED_DEEP_VALUE']:
                if key in os.environ:
                    del os.environ[key]
    
    def test_get_with_default(self):
        """Test getting values with default fallback."""
        config = ConfigManager()
        config.load_dict({"existing": {"key": "value"}})
        
        # Existing key
        assert config.get("existing.key") == "value"
        
        # Non-existing key with default
        assert config.get("nonexistent.key", "default") == "default"
        
        # Non-existing key without default
        assert config.get("nonexistent.key") is None
    
    def test_set_and_update(self):
        """Test setting and updating configuration values."""
        config = ConfigManager()
        
        # Set individual values
        config.set("app.name", "Test App")
        config.set("database.port", 3306)
        
        assert config.get("app.name") == "Test App"
        assert config.get("database.port") == 3306
        
        # Update multiple values
        config.update({
            "app.version": "2.0",
            "database.host": "updated-host"
        })
        
        assert config.get("app.version") == "2.0"
        assert config.get("database.host") == "updated-host"
    
    def test_has_method(self):
        """Test checking if keys exist."""
        config = ConfigManager()
        config.load_dict({
            "existing": {"nested": {"key": "value"}},
            "development": {"env_key": "env_value"}
        })
        
        assert config.has("existing.nested.key")
        assert not config.has("nonexistent.key")
        
        # Test environment-specific key resolution
        config.set_environment("development")
        assert config.has("env_key")
    
    def test_delete_key(self):
        """Test deleting configuration keys."""
        config = ConfigManager()
        config.load_dict({
            "app": {"name": "Test", "version": "1.0"},
            "database": {"host": "localhost"}
        })
        
        # Delete a key
        config.delete("app.version")
        assert not config.has("app.version")
        assert config.has("app.name")  # Other keys should remain
        
        # Try to delete non-existent key (should not error)
        config.delete("nonexistent.key")
    
    def test_dictionary_access(self):
        """Test dictionary-style access methods."""
        config = ConfigManager()
        config.load_dict({"test": {"key": "value"}})
        
        # __getitem__
        assert config["test.key"] == "value"
        
        # __setitem__
        config["new.key"] = "new_value"
        assert config.get("new.key") == "new_value"
        
        # __contains__
        assert "test.key" in config
        assert "nonexistent.key" not in config
        
        # __delitem__
        del config["test.key"]
        assert "test.key" not in config
        
        # KeyError for non-existent key
        with pytest.raises(KeyError):
            _ = config["nonexistent.key"]
        
        with pytest.raises(KeyError):
            del config["nonexistent.key"]
    
    def test_keys_and_iteration(self):
        """Test getting keys and iteration methods."""
        config = ConfigManager()
        config.load_dict({
            "app": {"name": "Test", "debug": True},
            "database": {"host": "localhost", "port": 5432}
        })
        
        # Test keys() method
        keys = config.keys()
        assert "app.name" in keys
        assert "app.debug" in keys
        assert "database.host" in keys
        assert "database.port" in keys
        
        # Test items() iteration
        items_dict = dict(config.items())
        assert items_dict["app.name"] == "Test"
        assert items_dict["database.port"] == 5432
        
        # Test __len__
        assert len(config) == 2  # Two top-level keys
        
        # Test __iter__
        top_level_keys = list(config)
        assert "app" in top_level_keys
        assert "database" in top_level_keys
    
    def test_save_and_reload(self):
        """Test saving configuration to file and reloading."""
        original_config = {
            "app": {"name": "Test App", "version": "1.0"},
            "database": {"host": "localhost", "port": 5432}
        }
        
        config = ConfigManager()
        config.load_dict(original_config)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            config.save_to_file(temp_path)
            
            # Create new config manager and load saved file
            new_config = ConfigManager()
            new_config.load_file(temp_path)
            
            # Verify data is identical
            assert new_config.get("app.name") == "Test App"
            assert new_config.get("database.port") == 5432
            
        finally:
            Path(temp_path).unlink()
    
    def test_clear_and_reload(self):
        """Test clearing configuration and reload functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name
        
        try:
            config = ConfigManager()
            config.load_file(temp_path)
            config.set("additional", "data")
            
            assert config.get("test") == "data"
            assert config.get("additional") == "data"
            assert len(config.loaded_files) == 1
            
            # Clear configuration
            config.clear()
            assert config.get("test") is None
            assert config.get("additional") is None
            assert len(config.loaded_files) == 0
            
            # Reload should restore original file data but not manual additions
            config.load_file(temp_path)
            config.reload()
            
            assert config.get("test") == "data"
            assert config.get("additional") is None
            
        finally:
            Path(temp_path).unlink()
    
    def test_validation_integration(self):
        """Test validation integration with ConfigManager."""
        config = ConfigManager()
        config.load_dict({
            "database": {"host": "localhost", "port": 5432},
            "api": {"url": "https://api.example.com"},
            "email": "admin@example.com"
        })
        
        # Add validation rules
        config.add_validation_rule("database.port", "port")
        config.add_validation_rule("api.url", "url")
        config.add_validation_rule("email", "email")
        config.add_validation_rule("missing_key", "required")
        
        # Validate
        errors = config.validate()
        
        # Should have one error for missing required key
        assert len(errors) == 1
        assert "missing_key" in errors[0]
        assert "Required key is missing" in errors[0]
        
        # Test validation with raise_on_error
        with pytest.raises(ConfigValidationError):
            config.validate(raise_on_error=True)
    
    def test_resolved_config_caching(self):
        """Test resolved configuration caching behavior."""
        config = ConfigManager()
        config.load_dict({
            "base": "value",
            "production": {"env": "prod_value"}
        })
        
        config.set_environment("production")
        
        # First call should compute and cache
        resolved1 = config.get_resolved_config()
        
        # Second call should use cache
        resolved2 = config.get_resolved_config()
        
        # Should be identical
        assert resolved1 == resolved2
        
        # Modifying config should clear cache
        config.set("new_key", "new_value")
        resolved3 = config.get_resolved_config()
        
        # Should include new key
        assert "new_key" in resolved3
        assert resolved3["new_key"] == "new_value"
    
    def test_string_representations(self):
        """Test string representation methods."""
        config = ConfigManager()
        config.load_dict({"test": {"key": "value"}})
        
        # __str__ should return JSON representation
        str_repr = str(config)
        assert "test" in str_repr
        assert "key" in str_repr
        assert "value" in str_repr
        
        # __repr__ should show summary info
        repr_str = repr(config)
        assert "ConfigManager" in repr_str
        assert "keys=" in repr_str
        assert "env=" in repr_str