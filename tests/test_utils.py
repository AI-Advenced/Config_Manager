"""
Tests for utility functions.
"""

import pytest
from config_manager.utils import (
    deep_merge, 
    get_nested_value, 
    set_nested_value,
    has_nested_key,
    flatten_dict,
    unflatten_dict,
    filter_dict_by_prefix
)


class TestDeepMerge:
    """Test suite for deep_merge function."""
    
    def test_merge_simple_dicts(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        
        result = deep_merge(base, overlay)
        
        expected = {"a": 1, "b": 3, "c": 4}
        assert result == expected
        
        # Original dicts should not be modified
        assert base == {"a": 1, "b": 2}
        assert overlay == {"b": 3, "c": 4}
    
    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        base = {
            "app": {"name": "MyApp", "version": "1.0"},
            "database": {"host": "localhost", "port": 5432}
        }
        overlay = {
            "app": {"debug": True, "version": "2.0"},
            "cache": {"ttl": 3600}
        }
        
        result = deep_merge(base, overlay)
        
        expected = {
            "app": {"name": "MyApp", "version": "2.0", "debug": True},
            "database": {"host": "localhost", "port": 5432},
            "cache": {"ttl": 3600}
        }
        assert result == expected
    
    def test_merge_deeply_nested_dicts(self):
        """Test merging deeply nested dictionaries."""
        base = {
            "level1": {
                "level2": {
                    "level3": {"a": 1, "b": 2},
                    "other": "value"
                }
            }
        }
        overlay = {
            "level1": {
                "level2": {
                    "level3": {"b": 3, "c": 4}
                }
            }
        }
        
        result = deep_merge(base, overlay)
        
        expected = {
            "level1": {
                "level2": {
                    "level3": {"a": 1, "b": 3, "c": 4},
                    "other": "value"
                }
            }
        }
        assert result == expected
    
    def test_merge_replace_non_dict_values(self):
        """Test that non-dict values are replaced, not merged."""
        base = {"key": [1, 2, 3]}
        overlay = {"key": [4, 5]}
        
        result = deep_merge(base, overlay)
        
        expected = {"key": [4, 5]}
        assert result == expected
    
    def test_merge_dict_over_non_dict(self):
        """Test merging dict over non-dict value."""
        base = {"key": "string_value"}
        overlay = {"key": {"nested": "dict"}}
        
        result = deep_merge(base, overlay)
        
        expected = {"key": {"nested": "dict"}}
        assert result == expected
    
    def test_merge_empty_dicts(self):
        """Test merging with empty dictionaries."""
        base = {"a": 1}
        overlay = {}
        
        result = deep_merge(base, overlay)
        assert result == {"a": 1}
        
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}
        
        result = deep_merge({}, {})
        assert result == {}


class TestGetNestedValue:
    """Test suite for get_nested_value function."""
    
    def test_get_simple_key(self):
        """Test getting simple top-level key."""
        data = {"key": "value"}
        
        result = get_nested_value(data, "key")
        assert result == "value"
    
    def test_get_nested_key(self):
        """Test getting nested key with dot notation."""
        data = {
            "app": {
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            }
        }
        
        assert get_nested_value(data, "app.database.host") == "localhost"
        assert get_nested_value(data, "app.database.port") == 5432
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns default."""
        data = {"existing": "value"}
        
        result = get_nested_value(data, "nonexistent")
        assert result is None
        
        result = get_nested_value(data, "nonexistent", "default")
        assert result == "default"
    
    def test_get_partial_path_exists(self):
        """Test getting key where partial path exists but not full path."""
        data = {"app": {"name": "MyApp"}}
        
        result = get_nested_value(data, "app.database.host", "default")
        assert result == "default"
    
    def test_get_custom_separator(self):
        """Test getting nested value with custom separator."""
        data = {"app": {"db": {"host": "localhost"}}}
        
        result = get_nested_value(data, "app/db/host", separator="/")
        assert result == "localhost"
    
    def test_get_non_dict_intermediate(self):
        """Test getting value when intermediate path is not a dict."""
        data = {"app": "string_value"}
        
        result = get_nested_value(data, "app.nested.key", "default")
        assert result == "default"


class TestSetNestedValue:
    """Test suite for set_nested_value function."""
    
    def test_set_simple_key(self):
        """Test setting simple top-level key."""
        data = {}
        set_nested_value(data, "key", "value")
        
        assert data == {"key": "value"}
    
    def test_set_nested_key(self):
        """Test setting nested key with dot notation."""
        data = {}
        set_nested_value(data, "app.database.host", "localhost")
        
        expected = {
            "app": {
                "database": {
                    "host": "localhost"
                }
            }
        }
        assert data == expected
    
    def test_set_existing_nested_structure(self):
        """Test setting value in existing nested structure."""
        data = {
            "app": {
                "name": "MyApp",
                "database": {"port": 5432}
            }
        }
        
        set_nested_value(data, "app.database.host", "localhost")
        
        expected = {
            "app": {
                "name": "MyApp",
                "database": {
                    "port": 5432,
                    "host": "localhost"
                }
            }
        }
        assert data == expected
    
    def test_set_override_non_dict(self):
        """Test setting value that overrides non-dict intermediate."""
        data = {"app": "string_value"}
        set_nested_value(data, "app.database.host", "localhost")
        
        expected = {
            "app": {
                "database": {
                    "host": "localhost"
                }
            }
        }
        assert data == expected
    
    def test_set_custom_separator(self):
        """Test setting nested value with custom separator."""
        data = {}
        set_nested_value(data, "app/db/host", "localhost", separator="/")
        
        expected = {
            "app": {
                "db": {
                    "host": "localhost"
                }
            }
        }
        assert data == expected


class TestHasNestedKey:
    """Test suite for has_nested_key function."""
    
    def test_has_existing_key(self):
        """Test checking for existing keys."""
        data = {
            "app": {
                "database": {
                    "host": "localhost"
                }
            }
        }
        
        assert has_nested_key(data, "app") is True
        assert has_nested_key(data, "app.database") is True
        assert has_nested_key(data, "app.database.host") is True
    
    def test_has_nonexistent_key(self):
        """Test checking for non-existent keys."""
        data = {"app": {"name": "MyApp"}}
        
        assert has_nested_key(data, "nonexistent") is False
        assert has_nested_key(data, "app.nonexistent") is False
        assert has_nested_key(data, "app.database.host") is False
    
    def test_has_key_non_dict_intermediate(self):
        """Test checking key with non-dict intermediate value."""
        data = {"app": "string_value"}
        
        assert has_nested_key(data, "app") is True
        assert has_nested_key(data, "app.nested") is False
    
    def test_has_key_custom_separator(self):
        """Test checking key with custom separator."""
        data = {"app": {"db": {"host": "localhost"}}}
        
        assert has_nested_key(data, "app/db/host", separator="/") is True
        assert has_nested_key(data, "app/db/port", separator="/") is False


class TestFlattenDict:
    """Test suite for flatten_dict function."""
    
    def test_flatten_simple_dict(self):
        """Test flattening simple dictionary."""
        data = {"a": 1, "b": 2}
        
        result = flatten_dict(data)
        
        expected = {"a": 1, "b": 2}
        assert result == expected
    
    def test_flatten_nested_dict(self):
        """Test flattening nested dictionary."""
        data = {
            "app": {
                "name": "MyApp",
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            },
            "debug": True
        }
        
        result = flatten_dict(data)
        
        expected = {
            "app.name": "MyApp",
            "app.database.host": "localhost",
            "app.database.port": 5432,
            "debug": True
        }
        assert result == expected
    
    def test_flatten_custom_separator(self):
        """Test flattening with custom separator."""
        data = {"app": {"db": {"host": "localhost"}}}
        
        result = flatten_dict(data, separator="/")
        
        expected = {"app/db/host": "localhost"}
        assert result == expected
    
    def test_flatten_with_prefix(self):
        """Test flattening with prefix."""
        data = {"db": {"host": "localhost"}}
        
        result = flatten_dict(data, prefix="config")
        
        expected = {"config.db.host": "localhost"}
        assert result == expected
    
    def test_flatten_empty_dict(self):
        """Test flattening empty dictionary."""
        result = flatten_dict({})
        assert result == {}


class TestUnflattenDict:
    """Test suite for unflatten_dict function."""
    
    def test_unflatten_simple_dict(self):
        """Test unflattening simple dictionary."""
        flat_data = {"a": 1, "b": 2}
        
        result = unflatten_dict(flat_data)
        
        expected = {"a": 1, "b": 2}
        assert result == expected
    
    def test_unflatten_nested_keys(self):
        """Test unflattening dictionary with nested keys."""
        flat_data = {
            "app.name": "MyApp",
            "app.database.host": "localhost",
            "app.database.port": 5432,
            "debug": True
        }
        
        result = unflatten_dict(flat_data)
        
        expected = {
            "app": {
                "name": "MyApp",
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            },
            "debug": True
        }
        assert result == expected
    
    def test_unflatten_custom_separator(self):
        """Test unflattening with custom separator."""
        flat_data = {"app/db/host": "localhost"}
        
        result = unflatten_dict(flat_data, separator="/")
        
        expected = {"app": {"db": {"host": "localhost"}}}
        assert result == expected
    
    def test_flatten_unflatten_roundtrip(self):
        """Test that flatten and unflatten are inverse operations."""
        original = {
            "app": {
                "name": "MyApp",
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            },
            "debug": True
        }
        
        flattened = flatten_dict(original)
        unflattened = unflatten_dict(flattened)
        
        assert unflattened == original


class TestFilterDictByPrefix:
    """Test suite for filter_dict_by_prefix function."""
    
    def test_filter_basic_prefix(self):
        """Test filtering dictionary by prefix."""
        data = {
            "app.name": "MyApp",
            "app.version": "1.0",
            "database.host": "localhost",
            "database.port": 5432
        }
        
        result = filter_dict_by_prefix(data, "app")
        
        expected = {
            "app.name": "MyApp",
            "app.version": "1.0"
        }
        assert result == expected
    
    def test_filter_with_remove_prefix(self):
        """Test filtering with prefix removal."""
        data = {
            "app.name": "MyApp",
            "app.version": "1.0",
            "database.host": "localhost"
        }
        
        result = filter_dict_by_prefix(data, "app", remove_prefix=True)
        
        expected = {
            "name": "MyApp",
            "version": "1.0"
        }
        assert result == expected
    
    def test_filter_exact_match(self):
        """Test filtering includes exact prefix matches."""
        data = {
            "app": "application",
            "app.name": "MyApp",
            "other": "value"
        }
        
        result = filter_dict_by_prefix(data, "app")
        
        expected = {
            "app": "application",
            "app.name": "MyApp"
        }
        assert result == expected
    
    def test_filter_custom_separator(self):
        """Test filtering with custom separator."""
        data = {
            "app/name": "MyApp",
            "app/version": "1.0",
            "db/host": "localhost"
        }
        
        result = filter_dict_by_prefix(data, "app", separator="/")
        
        expected = {
            "app/name": "MyApp",
            "app/version": "1.0"
        }
        assert result == expected
    
    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        data = {
            "database.host": "localhost",
            "cache.ttl": 3600
        }
        
        result = filter_dict_by_prefix(data, "app")
        
        assert result == {}
    
    def test_filter_empty_dict(self):
        """Test filtering empty dictionary."""
        result = filter_dict_by_prefix({}, "app")
        assert result == {}