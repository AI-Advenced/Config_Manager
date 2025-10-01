"""
Tests for environment management functionality.
"""

import pytest
import os
from config_manager.env import Environment, EnvironmentManager


class TestEnvironment:
    """Test suite for Environment enum."""
    
    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"
    
    def test_from_string_basic(self):
        """Test creating Environment from basic string values."""
        assert Environment.from_string("development") == Environment.DEVELOPMENT
        assert Environment.from_string("staging") == Environment.STAGING
        assert Environment.from_string("production") == Environment.PRODUCTION
        assert Environment.from_string("testing") == Environment.TESTING
    
    def test_from_string_aliases(self):
        """Test creating Environment from alias strings."""
        # Development aliases
        assert Environment.from_string("dev") == Environment.DEVELOPMENT
        assert Environment.from_string("develop") == Environment.DEVELOPMENT
        assert Environment.from_string("local") == Environment.DEVELOPMENT
        
        # Staging aliases
        assert Environment.from_string("stage") == Environment.STAGING
        assert Environment.from_string("preprod") == Environment.STAGING
        assert Environment.from_string("pre-production") == Environment.STAGING
        
        # Production aliases
        assert Environment.from_string("prod") == Environment.PRODUCTION
        assert Environment.from_string("live") == Environment.PRODUCTION
        
        # Testing aliases
        assert Environment.from_string("test") == Environment.TESTING
        assert Environment.from_string("ci") == Environment.TESTING
    
    def test_from_string_case_insensitive(self):
        """Test case insensitive environment string parsing."""
        assert Environment.from_string("DEVELOPMENT") == Environment.DEVELOPMENT
        assert Environment.from_string("Dev") == Environment.DEVELOPMENT
        assert Environment.from_string("PROD") == Environment.PRODUCTION
        assert Environment.from_string("Staging") == Environment.STAGING
    
    def test_from_string_whitespace(self):
        """Test handling whitespace in environment strings."""
        assert Environment.from_string("  development  ") == Environment.DEVELOPMENT
        assert Environment.from_string("\\tprod\\n") == Environment.PRODUCTION
    
    def test_from_string_invalid(self):
        """Test invalid environment string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown environment"):
            Environment.from_string("invalid_env")
        
        with pytest.raises(ValueError, match="Unknown environment"):
            Environment.from_string("unknown")
    
    def test_string_representation(self):
        """Test string representation of Environment."""
        assert str(Environment.DEVELOPMENT) == "development"
        assert str(Environment.PRODUCTION) == "production"


class TestEnvironmentManager:
    """Test suite for EnvironmentManager."""
    
    def setup_method(self):
        """Set up test environment."""
        # Save original environment variables
        self.original_env = os.environ.get('APP_ENV')
        self.original_custom_env = os.environ.get('CUSTOM_ENV')
        
        # Clear test environment variables
        for key in list(os.environ.keys()):
            if key.startswith('CONFIG_'):
                del os.environ[key]
    
    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment variables
        if self.original_env is not None:
            os.environ['APP_ENV'] = self.original_env
        elif 'APP_ENV' in os.environ:
            del os.environ['APP_ENV']
            
        if self.original_custom_env is not None:
            os.environ['CUSTOM_ENV'] = self.original_custom_env
        elif 'CUSTOM_ENV' in os.environ:
            del os.environ['CUSTOM_ENV']
        
        # Clean up test CONFIG_ variables
        for key in list(os.environ.keys()):
            if key.startswith('CONFIG_'):
                del os.environ[key]
    
    def test_default_initialization(self):
        """Test default EnvironmentManager initialization."""
        manager = EnvironmentManager()
        assert manager.env_var_name == 'APP_ENV'
        assert manager._current_env is None
    
    def test_custom_env_var_name(self):
        """Test EnvironmentManager with custom environment variable name."""
        manager = EnvironmentManager('CUSTOM_ENV')
        assert manager.env_var_name == 'CUSTOM_ENV'
    
    def test_current_environment_default(self):
        """Test current environment detection with default."""
        # No environment variable set
        if 'APP_ENV' in os.environ:
            del os.environ['APP_ENV']
        
        manager = EnvironmentManager()
        assert manager.current_environment == Environment.DEVELOPMENT
    
    def test_current_environment_from_env_var(self):
        """Test current environment detection from environment variable."""
        os.environ['APP_ENV'] = 'production'
        
        manager = EnvironmentManager()
        assert manager.current_environment == Environment.PRODUCTION
    
    def test_current_environment_invalid_fallback(self):
        """Test fallback to development for invalid environment variable."""
        os.environ['APP_ENV'] = 'invalid_environment'
        
        manager = EnvironmentManager()
        assert manager.current_environment == Environment.DEVELOPMENT
    
    def test_set_environment_enum(self):
        """Test setting environment with Environment enum."""
        manager = EnvironmentManager()
        manager.set_environment(Environment.STAGING)
        
        assert manager.current_environment == Environment.STAGING
    
    def test_set_environment_string(self):
        """Test setting environment with string."""
        manager = EnvironmentManager()
        manager.set_environment("production")
        
        assert manager.current_environment == Environment.PRODUCTION
    
    def test_set_environment_invalid_string(self):
        """Test setting invalid environment string raises ValueError."""
        manager = EnvironmentManager()
        
        with pytest.raises(ValueError):
            manager.set_environment("invalid_env")
    
    def test_environment_helper_methods(self):
        """Test environment check helper methods."""
        manager = EnvironmentManager()
        
        manager.set_environment(Environment.DEVELOPMENT)
        assert manager.is_development()
        assert not manager.is_production()
        assert not manager.is_staging()
        assert not manager.is_testing()
        
        manager.set_environment(Environment.PRODUCTION)
        assert not manager.is_development()
        assert manager.is_production()
        assert not manager.is_staging()
        assert not manager.is_testing()
        
        manager.set_environment(Environment.STAGING)
        assert not manager.is_development()
        assert not manager.is_production()
        assert manager.is_staging()
        assert not manager.is_testing()
        
        manager.set_environment(Environment.TESTING)
        assert not manager.is_development()
        assert not manager.is_production()
        assert not manager.is_staging()
        assert manager.is_testing()
    
    def test_get_env_overrides_basic(self):
        """Test basic environment variable overrides."""
        os.environ['CONFIG_DATABASE_HOST'] = 'env-host'
        os.environ['CONFIG_APP_DEBUG'] = 'true'
        os.environ['CONFIG_SERVER_PORT'] = '8080'
        
        manager = EnvironmentManager()
        overrides = manager.get_env_overrides()
        
        assert overrides['database']['host'] == 'env-host'
        assert overrides['app']['debug'] is True
        assert overrides['server']['port'] == 8080
    
    def test_get_env_overrides_nested_keys(self):
        """Test environment overrides with nested keys."""
        os.environ['CONFIG_DATABASE_POOL_SIZE'] = '20'
        os.environ['CONFIG_CACHE_REDIS_HOST'] = 'redis-server'
        os.environ['CONFIG_AUTH_JWT_SECRET'] = 'secret-key'
        
        manager = EnvironmentManager()
        overrides = manager.get_env_overrides()
        
        assert overrides['database']['pool']['size'] == 20
        assert overrides['cache']['redis']['host'] == 'redis-server'
        assert overrides['auth']['jwt']['secret'] == 'secret-key'
    
    def test_get_env_overrides_custom_prefix(self):
        """Test environment overrides with custom prefix."""
        os.environ['MYAPP_DATABASE_HOST'] = 'custom-host'
        os.environ['MYAPP_DEBUG'] = 'false'
        
        manager = EnvironmentManager()
        overrides = manager.get_env_overrides('MYAPP_')
        
        assert overrides['database']['host'] == 'custom-host'
        assert overrides['debug'] is False
    
    def test_get_env_overrides_type_conversion(self):
        """Test type conversion for environment variable values."""
        # Boolean values
        os.environ['CONFIG_BOOL_TRUE_1'] = 'true'
        os.environ['CONFIG_BOOL_TRUE_2'] = 'True'
        os.environ['CONFIG_BOOL_TRUE_3'] = 'yes'
        os.environ['CONFIG_BOOL_TRUE_4'] = '1'
        os.environ['CONFIG_BOOL_TRUE_5'] = 'on'
        os.environ['CONFIG_BOOL_TRUE_6'] = 'enabled'
        
        os.environ['CONFIG_BOOL_FALSE_1'] = 'false'
        os.environ['CONFIG_BOOL_FALSE_2'] = 'False'
        os.environ['CONFIG_BOOL_FALSE_3'] = 'no'
        os.environ['CONFIG_BOOL_FALSE_4'] = '0'
        os.environ['CONFIG_BOOL_FALSE_5'] = 'off'
        os.environ['CONFIG_BOOL_FALSE_6'] = 'disabled'
        
        # Numeric values
        os.environ['CONFIG_INT_VALUE'] = '42'
        os.environ['CONFIG_FLOAT_VALUE'] = '3.14'
        os.environ['CONFIG_SCIENTIFIC'] = '1.5e10'
        
        # String values
        os.environ['CONFIG_STRING_VALUE'] = 'hello world'
        os.environ['CONFIG_EMPTY_VALUE'] = ''
        
        manager = EnvironmentManager()
        overrides = manager.get_env_overrides()
        
        # Test boolean conversions
        assert overrides['bool']['true']['1'] is True
        assert overrides['bool']['true']['2'] is True
        assert overrides['bool']['true']['3'] is True
        assert overrides['bool']['true']['4'] is True
        assert overrides['bool']['true']['5'] is True
        assert overrides['bool']['true']['6'] is True
        
        assert overrides['bool']['false']['1'] is False
        assert overrides['bool']['false']['2'] is False
        assert overrides['bool']['false']['3'] is False
        assert overrides['bool']['false']['4'] is False
        assert overrides['bool']['false']['5'] is False
        assert overrides['bool']['false']['6'] is False
        
        # Test numeric conversions
        assert overrides['int']['value'] == 42
        assert isinstance(overrides['int']['value'], int)
        
        assert overrides['float']['value'] == 3.14
        assert isinstance(overrides['float']['value'], float)
        
        assert overrides['scientific'] == 1.5e10
        assert isinstance(overrides['scientific'], float)
        
        # Test string values
        assert overrides['string']['value'] == 'hello world'
        assert overrides['empty']['value'] == ''
    
    def test_get_env_overrides_caching(self):
        """Test environment overrides caching."""
        os.environ['CONFIG_TEST_KEY'] = 'test_value'
        
        manager = EnvironmentManager()
        
        # First call should compute overrides
        overrides1 = manager.get_env_overrides(cache=True)
        
        # Second call should use cache (even if env vars change)
        os.environ['CONFIG_TEST_KEY'] = 'changed_value'
        overrides2 = manager.get_env_overrides(cache=True)
        
        assert overrides1 == overrides2
        assert overrides1['test']['key'] == 'test_value'
        
        # Clear cache and get fresh overrides
        manager.clear_cache()
        overrides3 = manager.get_env_overrides(cache=True)
        
        assert overrides3['test']['key'] == 'changed_value'
    
    def test_get_env_overrides_no_cache(self):
        """Test environment overrides without caching."""
        os.environ['CONFIG_TEST_KEY'] = 'initial_value'
        
        manager = EnvironmentManager()
        
        overrides1 = manager.get_env_overrides(cache=False)
        
        # Change environment variable
        os.environ['CONFIG_TEST_KEY'] = 'updated_value'
        
        overrides2 = manager.get_env_overrides(cache=False)
        
        assert overrides1['test']['key'] == 'initial_value'
        assert overrides2['test']['key'] == 'updated_value'
    
    def test_cache_cleared_on_environment_change(self):
        """Test that cache is cleared when environment changes."""
        os.environ['CONFIG_TEST_KEY'] = 'test_value'
        
        manager = EnvironmentManager()
        
        # Get cached overrides
        manager.get_env_overrides(cache=True)
        assert manager._env_overrides_cache is not None
        
        # Change environment should clear cache
        manager.set_environment(Environment.PRODUCTION)
        assert manager._env_overrides_cache is None
    
    def test_get_environment_config_key(self):
        """Test getting environment-specific configuration key."""
        manager = EnvironmentManager()
        
        manager.set_environment(Environment.DEVELOPMENT)
        key = manager.get_environment_config_key("database.host")
        assert key == "development.database.host"
        
        manager.set_environment(Environment.PRODUCTION)
        key = manager.get_environment_config_key("app.debug")
        assert key == "production.app.debug"
    
    def test_clear_cache_method(self):
        """Test manual cache clearing."""
        os.environ['CONFIG_TEST_KEY'] = 'test_value'
        
        manager = EnvironmentManager()
        manager.get_env_overrides(cache=True)
        
        assert manager._env_overrides_cache is not None
        
        manager.clear_cache()
        assert manager._env_overrides_cache is None