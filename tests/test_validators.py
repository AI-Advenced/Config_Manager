"""
Tests for configuration validation functionality.
"""

import pytest
from config_manager.validators import (
    ValidationRule, 
    ConfigValidator, 
    ConfigValidationError
)


class TestValidationRule:
    """Test suite for ValidationRule class."""
    
    def test_validation_rule_creation(self):
        """Test creating a validation rule."""
        def is_positive(value):
            return int(value) > 0
        
        rule = ValidationRule(
            name="positive_number",
            validator_func=is_positive,
            error_message="must be a positive number",
            description="Validates that a number is positive"
        )
        
        assert rule.name == "positive_number"
        assert rule.error_message == "must be a positive number"
        assert rule.description == "Validates that a number is positive"
    
    def test_validation_rule_validate_pass(self):
        """Test validation rule that passes."""
        def is_even(value):
            return int(value) % 2 == 0
        
        rule = ValidationRule("even", is_even, "must be even")
        
        assert rule.validate(42) is True
        assert rule.validate(0) is True
        assert rule.validate("8") is True
    
    def test_validation_rule_validate_fail(self):
        """Test validation rule that fails."""
        def is_even(value):
            return int(value) % 2 == 0
        
        rule = ValidationRule("even", is_even, "must be even")
        
        assert rule.validate(43) is False
        assert rule.validate(1) is False
        assert rule.validate("7") is False
    
    def test_validation_rule_exception_handling(self):
        """Test validation rule handles exceptions gracefully."""
        def strict_int(value):
            return int(value) > 0  # Will raise ValueError for non-numeric strings
        
        rule = ValidationRule("strict_int", strict_int, "must be a positive integer")
        
        # Should return False when exception is raised
        assert rule.validate("not_a_number") is False
        assert rule.validate(None) is False
        assert rule.validate([1, 2, 3]) is False
    
    def test_validation_rule_string_representation(self):
        """Test string representation of validation rule."""
        rule = ValidationRule(
            "test_rule",
            lambda x: True,
            "test error message",
            "test description"
        )
        
        str_repr = str(rule)
        assert "ValidationRule(test_rule)" in str_repr
        assert "test description" in str_repr


class TestConfigValidator:
    """Test suite for ConfigValidator class."""
    
    def test_validator_initialization(self):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator()
        
        assert len(validator.rules) == 0
        assert len(validator.built_in_rules) > 0
        
        # Check that built-in rules exist
        assert 'url' in validator.built_in_rules
        assert 'port' in validator.built_in_rules
        assert 'email' in validator.built_in_rules
        assert 'required' in validator.built_in_rules
    
    def test_add_built_in_rule(self):
        """Test adding built-in validation rules."""
        validator = ConfigValidator()
        
        validator.add_rule("database.port", "port")
        validator.add_rule("api.url", "url")
        validator.add_rule("admin.email", "email")
        
        assert "database.port" in validator.rules
        assert "api.url" in validator.rules
        assert "admin.email" in validator.rules
        
        assert len(validator.rules["database.port"]) == 1
        assert validator.rules["database.port"][0].name == "port"
    
    def test_add_custom_rule(self):
        """Test adding custom validation rules."""
        def is_uppercase(value):
            return str(value).isupper()
        
        custom_rule = ValidationRule("uppercase", is_uppercase, "must be uppercase")
        
        validator = ConfigValidator()
        validator.add_rule("app.name", custom_rule)
        
        assert "app.name" in validator.rules
        assert validator.rules["app.name"][0] == custom_rule
    
    def test_add_multiple_rules_same_key(self):
        """Test adding multiple rules to the same key path."""
        validator = ConfigValidator()
        
        validator.add_rule("server.port", "port")
        validator.add_rule("server.port", "required")
        
        assert len(validator.rules["server.port"]) == 2
        
        rule_names = [rule.name for rule in validator.rules["server.port"]]
        assert "port" in rule_names
        assert "required" in rule_names
    
    def test_add_unknown_built_in_rule(self):
        """Test adding unknown built-in rule raises ValueError."""
        validator = ConfigValidator()
        
        with pytest.raises(ValueError, match="Unknown built-in rule"):
            validator.add_rule("test.key", "nonexistent_rule")
    
    def test_remove_rule_specific(self):
        """Test removing specific validation rule."""
        validator = ConfigValidator()
        validator.add_rule("test.key", "port")
        validator.add_rule("test.key", "required")
        
        assert len(validator.rules["test.key"]) == 2
        
        validator.remove_rule("test.key", "port")
        
        assert len(validator.rules["test.key"]) == 1
        assert validator.rules["test.key"][0].name == "required"
    
    def test_remove_rule_all(self):
        """Test removing all rules for a key path."""
        validator = ConfigValidator()
        validator.add_rule("test.key", "port")
        validator.add_rule("test.key", "required")
        
        assert "test.key" in validator.rules
        
        validator.remove_rule("test.key")
        
        assert "test.key" not in validator.rules
    
    def test_remove_rule_nonexistent_key(self):
        """Test removing rule from non-existent key does nothing."""
        validator = ConfigValidator()
        
        # Should not raise an error
        validator.remove_rule("nonexistent.key")
        validator.remove_rule("nonexistent.key", "some_rule")
    
    def test_validate_success(self):
        """Test validation that passes."""
        config_data = {
            "database": {"port": 5432},
            "api": {"url": "https://api.example.com"},
            "admin": {"email": "admin@example.com"}
        }
        
        validator = ConfigValidator()
        validator.add_rule("database.port", "port")
        validator.add_rule("api.url", "url")
        validator.add_rule("admin.email", "email")
        
        errors = validator.validate(config_data)
        assert len(errors) == 0
    
    def test_validate_failures(self):
        """Test validation with failures."""
        config_data = {
            "database": {"port": 99999},  # Invalid port
            "api": {"url": "not-a-url"},  # Invalid URL
            "admin": {"email": "invalid-email"}  # Invalid email
        }
        
        validator = ConfigValidator()
        validator.add_rule("database.port", "port")
        validator.add_rule("api.url", "url")
        validator.add_rule("admin.email", "email")
        
        errors = validator.validate(config_data)
        assert len(errors) == 3
        
        assert any("database.port" in error for error in errors)
        assert any("api.url" in error for error in errors)
        assert any("admin.email" in error for error in errors)
    
    def test_validate_missing_keys(self):
        """Test validation with missing keys."""
        config_data = {
            "database": {"port": 5432}
            # Missing required keys
        }
        
        validator = ConfigValidator()
        validator.add_rule("database.port", "port")
        validator.add_rule("required.key", "required")
        validator.add_rule("optional.key", "url")  # Not required
        
        errors = validator.validate(config_data)
        
        # Should only have error for the required key
        assert len(errors) == 1
        assert "required.key" in errors[0]
        assert "Required key is missing" in errors[0]
    
    def test_validate_with_raise_on_error(self):
        """Test validation with raise_on_error flag."""
        config_data = {
            "database": {"port": "invalid_port"}
        }
        
        validator = ConfigValidator()
        validator.add_rule("database.port", "port")
        
        # Should not raise by default
        errors = validator.validate(config_data, raise_on_error=False)
        assert len(errors) == 1
        
        # Should raise when flag is set
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config_data, raise_on_error=True)
        
        assert len(exc_info.value.errors) == 1
        assert "database.port" in exc_info.value.errors[0]
    
    def test_validate_key_specific(self):
        """Test validating specific key path."""
        config_data = {
            "good": {"port": 8080},
            "bad": {"port": "invalid"}
        }
        
        validator = ConfigValidator()
        validator.add_rule("good.port", "port")
        validator.add_rule("bad.port", "port")
        
        # Validate specific keys
        good_errors = validator.validate_key("good.port", config_data)
        bad_errors = validator.validate_key("bad.port", config_data)
        
        assert len(good_errors) == 0
        assert len(bad_errors) == 1
    
    def test_get_rules_for_key(self):
        """Test getting rules for a specific key."""
        validator = ConfigValidator()
        validator.add_rule("test.key", "port")
        validator.add_rule("test.key", "required")
        
        rules = validator.get_rules_for_key("test.key")
        assert len(rules) == 2
        
        rule_names = [rule.name for rule in rules]
        assert "port" in rule_names
        assert "required" in rule_names
        
        # Non-existent key
        rules = validator.get_rules_for_key("nonexistent.key")
        assert len(rules) == 0
    
    def test_list_all_rules(self):
        """Test getting summary of all rules."""
        validator = ConfigValidator()
        validator.add_rule("database.port", "port")
        validator.add_rule("database.port", "required")
        validator.add_rule("api.url", "url")
        
        all_rules = validator.list_all_rules()
        
        assert "database.port" in all_rules
        assert "api.url" in all_rules
        
        assert set(all_rules["database.port"]) == {"port", "required"}
        assert all_rules["api.url"] == ["url"]
    
    def test_create_custom_rule(self):
        """Test creating custom validation rule."""
        def is_positive(value):
            return float(value) > 0
        
        validator = ConfigValidator()
        rule = validator.create_custom_rule(
            "positive",
            is_positive,
            "must be positive",
            "Ensures value is positive"
        )
        
        assert rule.name == "positive"
        assert rule.error_message == "must be positive"
        assert rule.description == "Ensures value is positive"
        assert rule.validate(5.5) is True
        assert rule.validate(-1) is False
    
    def test_convenience_rule_methods(self):
        """Test convenience methods for common validation rules."""
        validator = ConfigValidator()
        
        # Test min/max length rules
        validator.add_min_length_rule("password", 8)
        validator.add_max_length_rule("username", 20)
        
        # Test range rule
        validator.add_range_rule("age", 0, 150)
        
        # Test choices rule
        validator.add_choices_rule("status", ["active", "inactive", "pending"])
        
        # Verify rules were added
        assert "password" in validator.rules
        assert "username" in validator.rules
        assert "age" in validator.rules
        assert "status" in validator.rules
        
        # Test validation
        config_data = {
            "password": "short",  # Too short
            "username": "a" * 25,  # Too long
            "age": 200,  # Out of range
            "status": "invalid"  # Not in choices
        }
        
        errors = validator.validate(config_data)
        assert len(errors) == 4


class TestBuiltInValidators:
    """Test suite for built-in validation rules."""
    
    def test_url_validator(self):
        """Test URL validation rule."""
        validator = ConfigValidator()
        url_rule = validator.built_in_rules['url']
        
        # Valid URLs
        assert url_rule.validate("https://example.com") is True
        assert url_rule.validate("http://localhost:8080") is True
        assert url_rule.validate("ftp://files.example.com") is True
        
        # Invalid URLs
        assert url_rule.validate("not-a-url") is False
        assert url_rule.validate("http://") is False
        assert url_rule.validate("example.com") is False  # Missing scheme
        assert url_rule.validate("") is False
    
    def test_port_validator(self):
        """Test port validation rule."""
        validator = ConfigValidator()
        port_rule = validator.built_in_rules['port']
        
        # Valid ports
        assert port_rule.validate(80) is True
        assert port_rule.validate(8080) is True
        assert port_rule.validate("443") is True
        assert port_rule.validate(1) is True
        assert port_rule.validate(65535) is True
        
        # Invalid ports
        assert port_rule.validate(0) is False
        assert port_rule.validate(65536) is False
        assert port_rule.validate(-1) is False
        assert port_rule.validate("not-a-port") is False
        assert port_rule.validate("") is False
    
    def test_email_validator(self):
        """Test email validation rule."""
        validator = ConfigValidator()
        email_rule = validator.built_in_rules['email']
        
        # Valid emails
        assert email_rule.validate("user@example.com") is True
        assert email_rule.validate("test.email+tag@domain.co.uk") is True
        assert email_rule.validate("admin@localhost") is True
        
        # Invalid emails
        assert email_rule.validate("not-an-email") is False
        assert email_rule.validate("@example.com") is False
        assert email_rule.validate("user@") is False
        assert email_rule.validate("user@.com") is False
        assert email_rule.validate("") is False
    
    def test_required_validator(self):
        """Test required validation rule."""
        validator = ConfigValidator()
        required_rule = validator.built_in_rules['required']
        
        # Valid (non-empty) values
        assert required_rule.validate("some text") is True
        assert required_rule.validate(42) is True
        assert required_rule.validate([1, 2, 3]) is True
        assert required_rule.validate({"key": "value"}) is True
        assert required_rule.validate(False) is True  # False is not empty
        
        # Invalid (empty) values
        assert required_rule.validate(None) is False
        assert required_rule.validate("") is False
        assert required_rule.validate("   ") is False  # Whitespace only
        assert required_rule.validate([]) is False
        assert required_rule.validate({}) is False


class TestConfigValidationError:
    """Test suite for ConfigValidationError exception."""
    
    def test_config_validation_error_creation(self):
        """Test creating ConfigValidationError."""
        errors = [
            "database.port: must be a valid port",
            "api.url: must be a valid URL"
        ]
        
        exception = ConfigValidationError(errors)
        
        assert exception.errors == errors
        assert "Configuration validation failed" in str(exception)
        assert "database.port" in str(exception)
        assert "api.url" in str(exception)
    
    def test_config_validation_error_single_error(self):
        """Test ConfigValidationError with single error."""
        errors = ["single.error: some validation message"]
        
        exception = ConfigValidationError(errors)
        
        assert len(exception.errors) == 1
        assert exception.errors[0] == "single.error: some validation message"