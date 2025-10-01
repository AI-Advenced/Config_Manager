"""
Command Line Interface for Config Manager.

Provides CLI tools for validating, displaying, and managing configuration files.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional

from .core import ConfigManager
from .validators import ConfigValidationError


def setup_logging(verbose: bool = False):
    """Setup logging for CLI operations."""
    import logging
    
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def validate_command(args) -> int:
    """
    Validate configuration files.
    
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        config = ConfigManager()
        
        # Load configuration files
        for file_path in args.files:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ Error: File not found: {file_path}")
                return 1
            
            print(f"📄 Loading: {file_path}")
            config.load_file(file_path)
        
        # Set environment if specified
        if args.environment:
            print(f"🌍 Environment: {args.environment}")
            config.set_environment(args.environment)
        
        # Apply environment variable overrides
        if args.env_prefix:
            print(f"🔧 Applying env overrides with prefix: {args.env_prefix}")
            config.apply_env_overrides(args.env_prefix)
        
        # Add validation rules if specified
        if args.validate_rules:
            _add_validation_rules(config, args.validate_rules)
        
        # Perform validation
        print("🔍 Validating configuration...")
        errors = config.validate()
        
        if errors:
            print(f"\n❌ Validation failed with {len(errors)} error(s):")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            return 1
        else:
            print("\n✅ Configuration is valid!")
            
            if args.show_stats:
                _show_config_stats(config)
            
            return 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def show_command(args) -> int:
    """
    Display configuration.
    
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        config = ConfigManager()
        
        # Load configuration files
        for file_path in args.files:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ Error: File not found: {file_path}")
                return 1
            
            if args.verbose:
                print(f"📄 Loading: {file_path}", file=sys.stderr)
            config.load_file(file_path)
        
        # Set environment if specified
        if args.environment:
            if args.verbose:
                print(f"🌍 Environment: {args.environment}", file=sys.stderr)
            config.set_environment(args.environment)
        
        # Apply environment variable overrides
        if args.env_prefix:
            if args.verbose:
                print(f"🔧 Applying env overrides with prefix: {args.env_prefix}", file=sys.stderr)
            config.apply_env_overrides(args.env_prefix)
        
        # Get configuration data
        if args.resolved:
            config_data = config.get_resolved_config()
        else:
            config_data = config.to_dict(resolved=False)
        
        # Filter by key if specified
        if args.key:
            from .utils import get_nested_value
            value = get_nested_value(config_data, args.key)
            if value is None and args.key not in config:
                print(f"❌ Error: Key '{args.key}' not found")
                return 1
            config_data = {args.key: value}
        
        # Output in requested format
        if args.format == 'json':
            print(json.dumps(config_data, indent=2, ensure_ascii=False, default=str))
        elif args.format == 'yaml':
            import yaml
            print(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))
        elif args.format == 'flat':
            from .utils import flatten_dict
            flat_config = flatten_dict(config_data)
            for key, value in sorted(flat_config.items()):
                print(f"{key}={value}")
        else:
            # Pretty print
            print(json.dumps(config_data, indent=2, ensure_ascii=False, default=str))
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def convert_command(args) -> int:
    """
    Convert configuration between formats.
    
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        config = ConfigManager()
        
        # Load input file
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ Error: Input file not found: {input_path}")
            return 1
        
        print(f"📄 Loading: {input_path}")
        config.load_file(input_path)
        
        # Set environment if specified
        if args.environment:
            config.set_environment(args.environment)
        
        # Apply environment overrides if requested
        if args.env_prefix:
            config.apply_env_overrides(args.env_prefix)
        
        # Determine output format
        output_path = Path(args.output)
        if args.format:
            format_ext = f".{args.format}"
        else:
            format_ext = output_path.suffix.lower()
        
        # Save in target format
        print(f"💾 Saving to: {output_path} (format: {format_ext})")
        config.save_to_file(output_path, format_override=args.format, resolved=args.resolved)
        
        print("✅ Conversion completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def keys_command(args) -> int:
    """
    List all configuration keys.
    
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        config = ConfigManager()
        
        # Load configuration files
        for file_path in args.files:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ Error: File not found: {file_path}")
                return 1
            
            config.load_file(file_path)
        
        # Set environment if specified
        if args.environment:
            config.set_environment(args.environment)
        
        # Apply environment overrides
        if args.env_prefix:
            config.apply_env_overrides(args.env_prefix)
        
        # Get all keys
        keys = config.keys(resolved=args.resolved)
        
        # Filter by pattern if specified
        if args.pattern:
            import re
            pattern = re.compile(args.pattern)
            keys = [key for key in keys if pattern.search(key)]
        
        # Sort and display
        keys.sort()
        for key in keys:
            if args.show_values:
                value = config.get(key)
                print(f"{key}={value}")
            else:
                print(key)
        
        if args.verbose:
            print(f"\nTotal: {len(keys)} keys", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def _add_validation_rules(config: ConfigManager, rules: List[str]):
    """Add validation rules from command line arguments."""
    for rule_spec in rules:
        try:
            # Parse rule specification: key_path:rule_name
            if ':' in rule_spec:
                key_path, rule_name = rule_spec.split(':', 1)
                config.add_validation_rule(key_path, rule_name)
            else:
                print(f"⚠️  Warning: Invalid rule specification: {rule_spec}")
        except Exception as e:
            print(f"⚠️  Warning: Error adding rule {rule_spec}: {e}")


def _show_config_stats(config: ConfigManager):
    """Show configuration statistics."""
    print(f"\n📊 Configuration Statistics:")
    print(f"  • Files loaded: {len(config.loaded_files)}")
    print(f"  • Total keys: {len(config.keys())}")
    print(f"  • Environment: {config.env_manager.current_environment.value}")
    
    # Show loaded files
    if config.loaded_files:
        print(f"  • Loaded files:")
        for file_path in config.loaded_files:
            print(f"    - {file_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Config Manager CLI - Professional configuration management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration files
  config-manager validate config/base.yaml config/production.json --env production
  
  # Show merged configuration  
  config-manager show config/*.yaml --format json --resolved
  
  # Convert YAML to JSON
  config-manager convert config.yaml config.json --format json
  
  # List all configuration keys
  config-manager keys config/*.yaml --pattern "database.*"
  
  # Show specific key value
  config-manager show config.yaml --key database.host
"""
    )
    
    # Global arguments
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate', 
        help='Validate configuration files'
    )
    validate_parser.add_argument('files', nargs='+', 
                               help='Configuration files to validate')
    validate_parser.add_argument('--env', dest='environment', 
                               help='Target environment')
    validate_parser.add_argument('--env-prefix', default='CONFIG_',
                               help='Environment variable prefix (default: CONFIG_)')
    validate_parser.add_argument('--rules', dest='validate_rules', nargs='*',
                               help='Validation rules (format: key:rule_name)')
    validate_parser.add_argument('--stats', dest='show_stats', action='store_true',
                               help='Show configuration statistics')
    
    # Show command
    show_parser = subparsers.add_parser(
        'show',
        help='Display configuration data'
    )
    show_parser.add_argument('files', nargs='+',
                           help='Configuration files to display')
    show_parser.add_argument('--env', dest='environment',
                           help='Target environment')
    show_parser.add_argument('--env-prefix', default='CONFIG_',
                           help='Environment variable prefix (default: CONFIG_)')
    show_parser.add_argument('--format', choices=['json', 'yaml', 'flat'],
                           default='json', help='Output format')
    show_parser.add_argument('--key', help='Show specific key only')
    show_parser.add_argument('--resolved', action='store_true', default=True,
                           help='Show resolved configuration (default)')
    show_parser.add_argument('--raw', action='store_false', dest='resolved',
                           help='Show raw configuration without resolution')
    
    # Convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert configuration between formats'
    )
    convert_parser.add_argument('input', help='Input configuration file')
    convert_parser.add_argument('output', help='Output file path')
    convert_parser.add_argument('--format', choices=['yaml', 'json', 'toml'],
                              help='Output format (auto-detected from extension if not specified)')
    convert_parser.add_argument('--env', dest='environment',
                              help='Target environment for conversion')
    convert_parser.add_argument('--env-prefix', default='CONFIG_',
                              help='Environment variable prefix (default: CONFIG_)')
    convert_parser.add_argument('--resolved', action='store_true', default=True,
                              help='Convert resolved configuration (default)')
    convert_parser.add_argument('--raw', action='store_false', dest='resolved',
                              help='Convert raw configuration without resolution')
    
    # Keys command
    keys_parser = subparsers.add_parser(
        'keys',
        help='List configuration keys'
    )
    keys_parser.add_argument('files', nargs='+',
                           help='Configuration files to analyze')
    keys_parser.add_argument('--env', dest='environment',
                           help='Target environment')
    keys_parser.add_argument('--env-prefix', default='CONFIG_',
                           help='Environment variable prefix (default: CONFIG_)')
    keys_parser.add_argument('--pattern', help='Filter keys by regex pattern')
    keys_parser.add_argument('--values', dest='show_values', action='store_true',
                           help='Show key values')
    keys_parser.add_argument('--resolved', action='store_true', default=True,
                           help='Use resolved configuration (default)')
    keys_parser.add_argument('--raw', action='store_false', dest='resolved',
                           help='Use raw configuration')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'validate':
        return validate_command(args)
    elif args.command == 'show':
        return show_command(args)
    elif args.command == 'convert':
        return convert_command(args)
    elif args.command == 'keys':
        return keys_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())