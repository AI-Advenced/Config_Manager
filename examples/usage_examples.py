#!/usr/bin/env python3
"""
Usage examples for Config Manager.

This file demonstrates various ways to use the Config Manager library
for loading, merging, validating, and accessing configuration data.
"""

import os
from pathlib import Path
from config_manager import ConfigManager, Environment


def basic_usage_example():
    """Basic usage - loading and accessing configuration."""
    print("=== Basic Usage Example ===")
    
    # Initialize configuration manager
    config = ConfigManager()
    
    # Load configuration files (order matters - later files override earlier ones)
    config.load_file("configs/base.yaml")
    config.load_file("configs/database.json")
    config.load_file("configs/services.toml")
    
    # Access configuration values using dot notation
    app_name = config.get("app.name", "Default App")
    db_host = config.get("database.host", "localhost")
    
    print(f"App Name: {app_name}")
    print(f"Database Host: {db_host}")
    print(f"Database Port: {config.get('database.port')}")
    
    # Check if keys exist
    if config.has("app.debug"):
        print(f"Debug Mode: {config.get('app.debug')}")
    
    # Dictionary-style access
    print(f"App Version: {config['app.version']}")
    
    print()


def environment_specific_example():
    """Environment-specific configuration example."""
    print("=== Environment-Specific Configuration ===")
    
    config = ConfigManager()
    config.load_file("configs/base.yaml")
    
    # Test different environments
    environments = ["development", "staging", "production"]
    
    for env in environments:
        config.set_environment(env)
        
        print(f"\n{env.upper()} Environment:")
        print(f"  Debug: {config.get('app.debug')}")
        print(f"  Database: {config.get('database.name')}")
        print(f"  Log Level: {config.get('logging.level')}")
        print(f"  SSL: {config.get('database.ssl')}")
    
    print()


def environment_variables_example():
    """Environment variable overrides example."""
    print("=== Environment Variables Override ===")
    
    # Set some environment variables
    os.environ['CONFIG_DATABASE_HOST'] = 'override.example.com'
    os.environ['CONFIG_APP_DEBUG'] = 'true'
    os.environ['CONFIG_DATABASE_PORT'] = '3306'
    
    config = ConfigManager()
    config.load_file("configs/base.yaml")
    config.apply_env_overrides()  # Apply environment variable overrides
    
    print("After applying environment variable overrides:")
    print(f"  Database Host: {config.get('database.host')}")
    print(f"  Database Port: {config.get('database.port')}")
    print(f"  App Debug: {config.get('app.debug')}")
    
    # Clean up
    del os.environ['CONFIG_DATABASE_HOST']
    del os.environ['CONFIG_APP_DEBUG']
    del os.environ['CONFIG_DATABASE_PORT']
    
    print()


def validation_example():
    """Configuration validation example."""
    print("=== Configuration Validation ===")
    
    config = ConfigManager()
    config.load_file("configs/base.yaml")
    config.set_environment("production")
    
    # Add validation rules
    config.add_validation_rule("database.host", "required")
    config.add_validation_rule("database.port", "port")
    config.add_validation_rule("api.base_url", "url")
    config.add_validation_rule("email.from_address", "email")
    
    # Add custom validation rules
    config.validator.add_min_length_rule("app.secret_key", 16)
    config.validator.add_range_rule("database.pool_size", 1, 100)
    config.validator.add_choices_rule("logging.level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    
    # Perform validation
    errors = config.validate()
    
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid!")
    
    print()


def advanced_merging_example():
    """Advanced configuration merging example."""
    print("=== Advanced Configuration Merging ===")
    
    # Load multiple files to demonstrate merging behavior
    config = ConfigManager()
    
    print("Loading base configuration...")
    config.load_file("configs/base.yaml")
    
    print("Loading database configuration (will merge/override)...")
    config.load_file("configs/database.json")
    
    print("Loading services configuration (will merge/override)...")
    config.load_file("configs/services.toml")
    
    # Show the merged result
    print("\nMerged database configuration:")
    db_config = config.get("database")
    if isinstance(db_config, dict):
        for key, value in db_config.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for nested_key, nested_value in value.items():
                    print(f"    {nested_key}: {nested_value}")
            else:
                print(f"  {key}: {value}")
    
    print()


def configuration_management_example():
    """Configuration management operations example."""
    print("=== Configuration Management Operations ===")
    
    config = ConfigManager()
    config.load_file("configs/base.yaml")
    
    # Set new values
    config.set("app.new_feature", True)
    config.set("custom.nested.value", "custom setting")
    
    # Update multiple values
    config.update({
        "app.maintenance_mode": True,
        "cache.ttl": 7200,
        "logging.max_size": "20MB"
    })
    
    # Get all keys
    print("All configuration keys:")
    keys = config.keys()
    for key in sorted(keys)[:10]:  # Show first 10 keys
        print(f"  {key}")
    print(f"  ... and {len(keys) - 10} more keys")
    
    # Iterate over configuration items
    print("\nSome configuration values:")
    count = 0
    for key, value in config.items():
        if count < 5:
            print(f"  {key}: {value}")
            count += 1
        else:
            break
    
    # Save configuration to file
    print("\nSaving merged configuration to output.yaml...")
    config.save_to_file("output.yaml", format_override="yaml")
    
    print()


def directory_loading_example():
    """Loading entire directories example."""
    print("=== Directory Loading Example ===")
    
    config = ConfigManager()
    
    # Load all configuration files from a directory
    configs_dir = Path("configs")
    if configs_dir.exists():
        print(f"Loading all config files from {configs_dir}/")
        config.load_directory(configs_dir, recursive=False)
        
        print(f"Loaded {len(config.loaded_files)} files:")
        for file_path in config.loaded_files:
            print(f"  - {file_path.name}")
        
        # Show some merged configuration
        print(f"\nTotal configuration keys: {len(config.keys())}")
    else:
        print("Configs directory not found")
    
    print()


def error_handling_example():
    """Error handling and edge cases example."""
    print("=== Error Handling Example ===")
    
    config = ConfigManager()
    
    try:
        # Try to load a non-existent file
        config.load_file("nonexistent.yaml")
    except FileNotFoundError as e:
        print(f"Expected error: {e}")
    
    # Load valid config
    config.load_file("configs/base.yaml")
    
    # Try to access non-existent key with default
    missing_value = config.get("non.existent.key", "default_value")
    print(f"Missing key with default: {missing_value}")
    
    # Check if key exists before accessing
    if "non.existent.key" in config:
        print("This won't print")
    else:
        print("Key doesn't exist (as expected)")
    
    try:
        # This will raise KeyError since key doesn't exist
        _ = config["non.existent.key"]
    except KeyError as e:
        print(f"Expected KeyError: {e}")
    
    print()


def cli_simulation_example():
    """Simulate CLI usage programmatically."""
    print("=== CLI Simulation Example ===")
    
    # This demonstrates what the CLI does internally
    from config_manager.cli import validate_command, show_command
    
    # Simulate command line arguments for validation
    class Args:
        def __init__(self):
            self.files = ["configs/base.yaml"]
            self.environment = "production"
            self.env_prefix = "CONFIG_"
            self.validate_rules = ["database.port:port", "api.base_url:url"]
            self.show_stats = True
            self.verbose = False
    
    args = Args()
    
    print("Simulating CLI validation...")
    result = validate_command(args)
    print(f"Validation result: {'PASSED' if result == 0 else 'FAILED'}")
    
    print()


def main():
    """Run all examples."""
    print("Config Manager - Usage Examples")
    print("=" * 50)
    print()
    
    try:
        basic_usage_example()
        environment_specific_example()
        environment_variables_example()
        validation_example()
        advanced_merging_example()
        configuration_management_example()
        directory_loading_example()
        error_handling_example()
        cli_simulation_example()
        
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Change to the examples directory to run examples
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    main()