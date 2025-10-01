# Installation Guide

## Quick Installation

### From Source (Development)

1. **Clone or download the project:**
```bash
git clone <repository-url>
cd config_manager
```

2. **Install the library:**
```bash
pip install -e .
```

3. **Verify installation:**
```bash
config-manager --help
```

### From PyPI (when published)

```bash
pip install config-manager
```

## Requirements

- **Python**: 3.8 or higher
- **Dependencies**: PyYAML, tomli (Python < 3.11), tomli-w

## Development Installation

For development work:

```bash
# Install with development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .

# Run tests
pytest

# Format code
black config_manager tests
isort config_manager tests

# Type checking
mypy config_manager
```

## Usage Verification

After installation, test the library:

### CLI Test
```bash
config-manager --help
config-manager validate examples/configs/base.yaml
```

### Python API Test
```python
from config_manager import ConfigManager

config = ConfigManager()
config.load_file("path/to/config.yaml")
config.set_environment("production")

# Access configuration
db_host = config.get("database.host", "localhost")
print(f"Database host: {db_host}")
```

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure the package is installed correctly:
   ```bash
   pip list | grep config-manager
   ```

2. **CLI Command Not Found**: Check if the installation directory is in your PATH:
   ```bash
   which config-manager
   ```

3. **Dependencies Error**: Install required dependencies:
   ```bash
   pip install PyYAML tomli-w
   ```

### Platform-Specific Notes

- **Windows**: Use `python -m config_manager.cli` if the `config-manager` command is not available
- **macOS/Linux**: Ensure your Python bin directory is in PATH

## Uninstallation

```bash
pip uninstall config-manager
```