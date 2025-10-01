# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of config-manager library

## [1.0.0] - 2024-01-15

### Added
- **Core Features**
  - Multi-format configuration file support (YAML, JSON, TOML)
  - Environment-specific configuration management (development, staging, production, testing)
  - Intelligent deep merging of configuration files with precedence rules
  - Environment variable overrides with automatic type conversion
  - Comprehensive validation system with built-in and custom rules
  - Command-line interface for validation, display, and format conversion

- **Configuration Loading**
  - Load individual configuration files with `load_file()`
  - Load entire directories with `load_directory()`
  - Load from Python dictionaries with `load_dict()`
  - Support for recursive directory scanning
  - Automatic file format detection based on extension

- **Environment Management**
  - Support for multiple environments with aliases
  - Automatic environment detection from environment variables
  - Environment-specific configuration sections
  - Helper methods for environment checking

- **Validation System**
  - Built-in validation rules: `required`, `url`, `email`, `port`
  - Custom validation rule support
  - Convenience methods for common validations (length, range, choices)
  - Comprehensive error reporting with detailed messages
  - Optional exception raising on validation failures

- **CLI Tools**
  - `validate` command for configuration validation
  - `show` command for displaying merged configurations
  - `convert` command for format conversion between YAML/JSON/TOML
  - `keys` command for listing and filtering configuration keys
  - Multiple output formats (JSON, YAML, flat key-value)
  - Environment and validation rule support in CLI

- **Developer Experience**
  - Full type hints and mypy support
  - Dictionary-style access (`config["key"]`)
  - Dot notation for nested keys (`config.get("app.database.host")`)
  - Comprehensive test suite with 95%+ coverage
  - Detailed documentation and examples
  - Pre-commit hooks and development tools

- **Utility Functions**
  - Deep dictionary merging with conflict resolution
  - Nested value access and modification
  - Dictionary flattening and unflattening
  - Key filtering and prefix operations
  - Configuration caching and reload functionality

### Dependencies
- PyYAML >= 6.0 for YAML support
- tomli >= 1.2.0 for TOML support (Python < 3.11)
- tomli-w >= 1.0.0 for TOML writing

### Python Support
- Python 3.8+
- Tested on CPython 3.8, 3.9, 3.10, 3.11, 3.12
- Cross-platform support (Windows, macOS, Linux)

[Unreleased]: https://github.com/yourusername/config-manager/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/config-manager/releases/tag/v1.0.0