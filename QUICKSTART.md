# Quick Start Guide

Get up and running with Config Manager in 5 minutes!

## 1. Installation

```bash
pip install config-manager
```

## 2. Create Your First Configuration

Create `config/app.yaml`:
```yaml
app:
  name: "My Application"
  debug: false
  version: "1.0.0"

database:
  host: "localhost"
  port: 5432
  name: "myapp"

# Environment-specific overrides
development:
  app:
    debug: true
  database:
    name: "myapp_dev"

production:
  database:
    host: "prod-db.example.com"
    ssl: true
```

## 3. Load and Use Configuration

```python
from config_manager import ConfigManager

# Create configuration manager
config = ConfigManager()

# Load configuration file
config.load_file("config/app.yaml")

# Set environment (development, staging, production)
config.set_environment("development")

# Apply environment variable overrides
config.apply_env_overrides()

# Access configuration values
app_name = config.get("app.name")
db_host = config.get("database.host", "localhost")
debug_mode = config.get("app.debug", False)

print(f"App: {app_name}")
print(f"Database: {db_host}")
print(f"Debug: {debug_mode}")
```

## 4. Environment Variable Overrides

Set environment variables with `CONFIG_` prefix:
```bash
export CONFIG_DATABASE_HOST=override-host
export CONFIG_APP_DEBUG=true
```

Your configuration will automatically use these values!

## 5. Validate Configuration

Add validation rules:
```python
# Add validation rules
config.add_validation_rule("database.port", "port")
config.add_validation_rule("database.host", "required") 

# Validate
errors = config.validate()
if errors:
    print("Configuration errors:", errors)
else:
    print("✅ Configuration is valid!")
```

## 6. Use the CLI

```bash
# Validate configuration files
config-manager validate config/app.yaml --env production

# Show merged configuration
config-manager show config/app.yaml --env development --format json

# Convert between formats
config-manager convert config/app.yaml config/app.json --format json

# List all configuration keys
config-manager keys config/app.yaml --pattern "database.*"
```

## Next Steps

- 📖 Read the [full documentation](README.md)
- 🔍 Explore [examples](examples/)
- 🧪 Check out [advanced features](README.md#advanced-usage)
- 🛠️ See [CLI documentation](README.md#cli-usage)

## Common Patterns

### Multi-File Configuration
```python
config = ConfigManager()
config.load_file("config/base.yaml")      # Base configuration
config.load_file("config/database.json")  # Database settings
config.load_file("config/services.toml")  # External services
```

### Environment-Specific Loading
```python
import os

config = ConfigManager()
config.load_file("config/base.yaml")

# Load environment-specific file if it exists
env = os.getenv('APP_ENV', 'development')
env_file = f"config/{env}.yaml"
if os.path.exists(env_file):
    config.load_file(env_file)

config.set_environment(env)
```

### Dictionary-Style Access
```python
# Access like a dictionary
app_name = config["app.name"]
config["new.setting"] = "value"

# Check if key exists
if "optional.feature" in config:
    feature = config["optional.feature"]
```

That's it! You're now ready to use Config Manager for professional configuration management. 🚀