"""
Configuration validation system.

This module provides a flexible validation framework for configuration data,
with built-in validators for common use cases and support for custom rules.
"""

import re
from typing import Any, Callable, Optional, List, Dict, Union
from urllib.parse import urlparse
from .utils import get_nested_value


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, errors: List[str]):
        """
        Initialize with list of validation errors.
        
        Args:
            errors: List of validation error messages
        """
        self.errors = errors
        super().__init__(f"Configuration validation failed: {', '.join(errors)}")


class ValidationRule:
    """
    A validation rule that can be applied to configuration values.
    
    Encapsulates a validation function with metadata and error messaging.
    """
    
    def __init__(self, name: str, validator_func: Callable[[Any], bool], 
                 error_message: str, description: str = ""):
        """
        Initialize a validation rule.
        
        Args:
            name: Unique name for the rule
            validator_func: Function that takes a value and returns True if valid
            error_message: Message to show when validation fails
            description: Optional description of what the rule validates
        """
        self.name = name
        self.validator_func = validator_func
        self.error_message = error_message
        self.description = description
    
    def validate(self, value: Any) -> bool:
        """
        Validate a value against this rule.
        
        Args:
            value: Value to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            return self.validator_func(value)
        except Exception:
            # If validation function raises an exception, consider it invalid
            return False
    
    def __str__(self) -> str:
        return f"ValidationRule({self.name}): {self.description or self.error_message}"


class ConfigValidator:
    """
    Configuration validator with support for custom rules and built-in validations.
    
    Provides a flexible system for validating configuration data against
    various rules, with support for nested key paths.
    """
    
    def __init__(self):
        """Initialize the validator with built-in rules."""
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.built_in_rules: Dict[str, ValidationRule] = {}
        self._register_built_in_rules()
    
    def add_rule(self, key_path: str, rule: Union[ValidationRule, str], **kwargs) -> None:
        """
        Add a validation rule for a configuration key path.
        
        Args:
            key_path: Dot-separated path to the configuration key
            rule: ValidationRule instance or name of built-in rule
            **kwargs: Additional arguments for built-in rules
            
        Raises:
            ValueError: If built-in rule name is not found
        """
        if isinstance(rule, str):
            # Use built-in rule
            if rule not in self.built_in_rules:
                available_rules = list(self.built_in_rules.keys())
                raise ValueError(f"Unknown built-in rule '{rule}'. "
                               f"Available rules: {available_rules}")
            rule = self.built_in_rules[rule]
        
        if key_path not in self.rules:
            self.rules[key_path] = []
        
        self.rules[key_path].append(rule)
    
    def remove_rule(self, key_path: str, rule_name: Optional[str] = None) -> None:
        """
        Remove validation rule(s) for a key path.
        
        Args:
            key_path: Configuration key path
            rule_name: Specific rule name to remove (None to remove all)
        """
        if key_path not in self.rules:
            return
        
        if rule_name is None:
            # Remove all rules for this key path
            del self.rules[key_path]
        else:
            # Remove specific rule
            self.rules[key_path] = [
                rule for rule in self.rules[key_path] 
                if rule.name != rule_name
            ]
            
            # Clean up empty rule lists
            if not self.rules[key_path]:
                del self.rules[key_path]
    
    def validate(self, config_data: Dict[str, Any], 
                raise_on_error: bool = False) -> List[str]:
        """
        Validate configuration data against all registered rules.
        
        Args:
            config_data: Configuration dictionary to validate
            raise_on_error: Whether to raise ConfigValidationError if validation fails
            
        Returns:
            List of validation error messages (empty if all valid)
            
        Raises:
            ConfigValidationError: If raise_on_error=True and validation fails
        """
        errors = []
        
        for key_path, rules in self.rules.items():
            value = get_nested_value(config_data, key_path)
            
            # Skip validation if key doesn't exist and it's not required
            if value is None:
                # Check if any rule requires the key to exist
                required_rules = [r for r in rules if getattr(r, 'required', False)]
                if required_rules:
                    errors.append(f"{key_path}: Required key is missing")
                continue
            
            # Apply all rules for this key path
            for rule in rules:
                if not rule.validate(value):
                    errors.append(f"{key_path}: {rule.error_message} (value: {value})")
        
        if raise_on_error and errors:
            raise ConfigValidationError(errors)
        
        return errors
    
    def validate_key(self, key_path: str, config_data: Dict[str, Any]) -> List[str]:
        """
        Validate a specific key path.
        
        Args:
            key_path: Configuration key path to validate
            config_data: Configuration dictionary
            
        Returns:
            List of validation errors for this key
        """
        if key_path not in self.rules:
            return []
        
        errors = []
        value = get_nested_value(config_data, key_path)
        
        if value is None:
            required_rules = [r for r in self.rules[key_path] if getattr(r, 'required', False)]
            if required_rules:
                errors.append(f"{key_path}: Required key is missing")
            return errors
        
        for rule in self.rules[key_path]:
            if not rule.validate(value):
                errors.append(f"{key_path}: {rule.error_message} (value: {value})")
        
        return errors
    
    def get_rules_for_key(self, key_path: str) -> List[ValidationRule]:
        """Get all rules registered for a key path."""
        return self.rules.get(key_path, [])
    
    def list_all_rules(self) -> Dict[str, List[str]]:
        """Get a summary of all registered rules."""
        return {
            key_path: [rule.name for rule in rules]
            for key_path, rules in self.rules.items()
        }
    
    def _register_built_in_rules(self):
        """Register built-in validation rules."""
        
        # URL validation
        def is_valid_url(value):
            try:
                result = urlparse(str(value))
                return all([result.scheme, result.netloc])
            except:
                return False
        
        self.built_in_rules['url'] = ValidationRule(
            "url",
            is_valid_url,
            "must be a valid URL with scheme and netloc",
            "Validates URLs (http://example.com)"
        )
        
        # Port validation
        def is_valid_port(value):
            try:
                port = int(value)
                return 1 <= port <= 65535
            except:
                return False
        
        self.built_in_rules['port'] = ValidationRule(
            "port",
            is_valid_port,
            "must be a valid port number (1-65535)",
            "Validates network port numbers"
        )
        
        # Email validation
        def is_valid_email(value):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, str(value)) is not None
        
        self.built_in_rules['email'] = ValidationRule(
            "email",
            is_valid_email,
            "must be a valid email address",
            "Validates email addresses"
        )
        
        # Required (non-empty) validation
        def is_not_empty(value):
            if value is None:
                return False
            if isinstance(value, str):
                return bool(value.strip())
            if isinstance(value, (list, dict)):
                return len(value) > 0
            return True
        
        self.built_in_rules['required'] = ValidationRule(
            "required", 
            is_not_empty,
            "is required and cannot be empty",
            "Ensures value is not None or empty"
        )
        self.built_in_rules['required'].required = True  # Mark as required rule
        
        # String length validation
        def make_min_length_validator(min_len):
            def validator(value):
                return len(str(value)) >= min_len
            return validator
        
        def make_max_length_validator(max_len):
            def validator(value):
                return len(str(value)) <= max_len
            return validator
        
        # Numeric range validation
        def make_min_value_validator(min_val):
            def validator(value):
                try:
                    return float(value) >= min_val
                except:
                    return False
            return validator
        
        def make_max_value_validator(max_val):
            def validator(value):
                try:
                    return float(value) <= max_val
                except:
                    return False
            return validator
        
        # Choice validation
        def make_choice_validator(choices):
            def validator(value):
                return value in choices
            return validator
        
        # Pattern validation
        def make_pattern_validator(pattern):
            compiled_pattern = re.compile(pattern)
            def validator(value):
                return compiled_pattern.match(str(value)) is not None
            return validator
        
        # Register factory functions for dynamic rules
        self._rule_factories = {
            'min_length': make_min_length_validator,
            'max_length': make_max_length_validator,
            'min_value': make_min_value_validator,
            'max_value': make_max_value_validator,
            'choices': make_choice_validator,
            'pattern': make_pattern_validator,
        }
    
    def create_custom_rule(self, name: str, validator_func: Callable[[Any], bool],
                          error_message: str, description: str = "") -> ValidationRule:
        """
        Create a custom validation rule.
        
        Args:
            name: Name for the rule
            validator_func: Function that validates values
            error_message: Error message when validation fails
            description: Optional description
            
        Returns:
            New ValidationRule instance
        """
        return ValidationRule(name, validator_func, error_message, description)
    
    def add_min_length_rule(self, key_path: str, min_length: int) -> None:
        """Add minimum length validation rule."""
        rule = ValidationRule(
            f"min_length_{min_length}",
            self._rule_factories['min_length'](min_length),
            f"must be at least {min_length} characters long"
        )
        self.add_rule(key_path, rule)
    
    def add_max_length_rule(self, key_path: str, max_length: int) -> None:
        """Add maximum length validation rule."""
        rule = ValidationRule(
            f"max_length_{max_length}",
            self._rule_factories['max_length'](max_length),
            f"must be at most {max_length} characters long"
        )
        self.add_rule(key_path, rule)
    
    def add_range_rule(self, key_path: str, min_val: float, max_val: float) -> None:
        """Add numeric range validation rule."""
        def range_validator(value):
            try:
                num_val = float(value)
                return min_val <= num_val <= max_val
            except:
                return False
        
        rule = ValidationRule(
            f"range_{min_val}_{max_val}",
            range_validator,
            f"must be between {min_val} and {max_val}"
        )
        self.add_rule(key_path, rule)
    
    def add_choices_rule(self, key_path: str, choices: List[Any]) -> None:
        """Add choices validation rule."""
        rule = ValidationRule(
            f"choices_{len(choices)}",
            self._rule_factories['choices'](choices),
            f"must be one of: {choices}"
        )
        self.add_rule(key_path, rule)