# Troubleshooting Guide

## Common Issues and Solutions

### Import and Module Errors

#### "Could not import symbol 'dagster.nonexistent'"

**Problem**: Symbol doesn't exist or has been moved/renamed.

**Solution**:

```bash
# Verify symbol exists
python -c "from dagster import nonexistent"  # Should fail

# Check symbol availability
python -c "import dagster; print(dir(dagster))" | grep symbol_name

# Use correct dotted path
dagster-docs dagster._core.definitions.asset.asset
```

#### "Not in a git repository"

**Problem**: Running `--changed` option outside git repository.

**Solution**:

```bash
# Ensure you're in Dagster repository root
cd /path/to/dagster
git status  # Should show git status

# Or use alternative validation methods
dagster-docs check docstrings --symbol dagster.asset
```

#### "Could not find dagster repository root"

**Problem**: Commands can't locate `python_modules/` directory.

**Solution**:

```bash
# Run from Dagster repository root
cd /path/to/dagster
ls python_modules/  # Should show dagster directories

# Check current directory structure
pwd
ls -la
```

### Validation Errors

#### "Napoleon processing failed"

**Problem**: Docstring contains syntax that breaks Google-style parsing.

**Error Example**:

```
ERROR: Napoleon processing failed: Unexpected character at line 5
```

**Solution**:

```python
# BAD: Malformed Google-style section
def bad_function():
    """Function with bad docstring.

    Args
        param: Description  # Missing colon after Args
    """

# GOOD: Properly formatted section
def good_function():
    """Function with good docstring.

    Args:
        param: Description
    """
```

#### "RST syntax: Error in 'code-block' directive"

**Problem**: Missing blank line after RST directive.

**Error Example**:

```
ERROR: RST syntax: Error in "code-block" directive: missing blank line after directive
```

**Solution**:

```python
def fix_code_block():
    """Function with code example.

    Example:
        .. code-block:: python

            # Need blank line above this code
            result = my_function()
    """
```

#### "Invalid section header: 'args:'. Did you mean 'Args:'?"

**Problem**: Incorrect capitalization in section headers.

**Solution**:

```python
def fix_capitalization():
    """Function with proper section headers.

    Args:    # Not: args:, Arguments:, or ARGS:
        param: Description

    Returns: # Not: returns:, Return, or RETURNS:
        Result description
    """
```

### Public API Validation Errors

#### "Symbol marked @public but not documented in RST files"

**Problem**: Symbol has `@public` decorator but no RST documentation.

**Solution**:

1. **Add RST documentation**:

   ```rst
   # In docs/sphinx/sections/api/apidocs/dagster.rst
   .. autofunction:: dagster.my_symbol
   ```

2. **Or remove @public decorator** if not truly public:

   ```python
   # Remove @public if internal-only
   def internal_function():
       pass
   ```

3. **Or add to exclude list** temporarily:
   ```python
   # In exclude_lists.py
   EXCLUDE_MISSING_RST = {
       # ... existing entries
       "dagster.my_symbol",
   }
   ```

#### "Symbol documented in RST but missing @public decorator"

**Problem**: Symbol is documented but lacks `@public` decorator.

**Solution**:

1. **Add @public decorator**:

   ```python
   from dagster._annotations import public

   @public
   def my_function():
       pass
   ```

2. **Or remove RST documentation** if not public:
   ```rst
   # Remove from RST file if internal-only
   # .. autofunction:: dagster.internal_function
   ```

#### "Symbol marked @public but not available as top-level export"

**Problem**: Symbol has `@public` decorator but isn't exported in `__init__.py`.

**Solution**:

1. **Add to top-level exports**:

   ```python
   # In dagster/__init__.py or library/__init__.py
   from ._core.my_module import my_symbol

   __all__ = [
       # ... existing exports
       "my_symbol",
   ]
   ```

2. **Or determine if symbol should be public** - may need to remove `@public`.

### Watch Mode Issues

#### "Watch mode not detecting changes"

**Problem**: File watcher not triggering on file modifications.

**Debugging**:

```bash
# Enable verbose mode to see file events
dagster-docs dagster.asset --watch --verbose

# Check file permissions
ls -la /path/to/watched/file.py

# Try editing file with different editor
```

**Solution**:

- Ensure file is being saved properly
- Try different text editor (some editors use atomic writes)
- Check file system permissions

#### "Watch mode validation fails after file change"

**Problem**: File changes break imports or syntax.

**Solution**:

- Fix syntax errors in the modified file
- Ensure imports are still valid after changes
- Check that symbol still exists at expected location

### Performance Issues

#### "Validation is very slow"

**Problem**: Large codebase takes long time to validate.

**Solutions**:

```bash
# Use more targeted validation
dagster-docs check docstrings --changed  # Instead of --all

# Validate specific package
dagster-docs check docstrings --package dagster_aws

# Use single symbol validation for development
dagster-docs dagster.asset  # Instead of full package
```

#### "Out of memory during validation"

**Problem**: System runs out of memory on large validation.

**Solution**:

- Use package-specific validation instead of `--all`
- Increase system memory if possible
- Consider validating libraries separately

### Path and File Issues

#### "Permission denied" errors

**Problem**: Cannot read files or directories.

**Solution**:

```bash
# Check file permissions
ls -la python_modules/dagster/

# Ensure proper file ownership
chown -R user:group python_modules/

# Check if files are locked by other processes
lsof python_modules/dagster/file.py
```

#### "File not found" errors in RST parsing

**Problem**: RST files reference non-existent files.

**Solution**:

```bash
# Check RST file structure
ls docs/sphinx/sections/api/apidocs/

# Verify paths in error messages
ls -la path/mentioned/in/error
```

## Debugging Techniques

### Enable Verbose Output

```bash
# Get detailed error traces
dagster-docs dagster.asset --verbose

# See file system events in watch mode
dagster-docs dagster.asset --watch --verbose
```

### Manual Rule Testing

```python
# Test individual validation rules
from automation.dagster_docs.docstring_rules import create_section_header_validator
from automation.dagster_docs.docstring_rules.base import ValidationContext, ValidationResult

# Create test context
context = ValidationContext(
    docstring="Test docstring with args: section",
    symbol_path="test.symbol",
    processed_rst="Processed content"
)

# Test rule
result = ValidationResult.create("test.symbol")
validator = create_section_header_validator()
result = validator(context, result)

print("Errors:", result.errors)
print("Warnings:", result.warnings)
```

### Check Symbol Resolution

```python
# Manually test symbol import
from automation.dagster_docs.validator import SymbolImporter

try:
    symbol_info = SymbolImporter.import_symbol("dagster.asset")
    print(f"Found: {symbol_info.name}")
    print(f"Module: {symbol_info.module}")
    print(f"File: {symbol_info.file_path}")
    print(f"Docstring: {symbol_info.docstring[:100]}...")
except Exception as e:
    print(f"Import failed: {e}")
```

### Test RST Processing

```python
# Test Napoleon processing
from sphinx.ext.napoleon import GoogleDocstring
from sphinx.util.docutils import docutils_namespace

docstring = """Test function.

Args:
    param: Parameter description

Returns:
    Result description
"""

try:
    with docutils_namespace():
        napoleon = GoogleDocstring(docstring)
        rst_content = str(napoleon)
        print("Converted RST:")
        print(rst_content)
except Exception as e:
    print(f"Napoleon processing failed: {e}")
```

### Debug Public API Discovery

```python
# Test AST parsing for @public symbols
import ast

code = '''
from dagster._annotations import public

@public
def my_function():
    """My function."""
    pass

def internal_function():
    """Internal function."""
    pass
'''

tree = ast.parse(code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        has_public = any(
            (isinstance(d, ast.Name) and d.id == "public") or
            (isinstance(d, ast.Attribute) and d.attr == "public")
            for d in node.decorator_list
        )
        print(f"Function {node.name}: @public = {has_public}")
```

## Error Message Reference

### Common Error Patterns

| Error Pattern                    | Meaning                        | Solution                             |
| -------------------------------- | ------------------------------ | ------------------------------------ |
| `Could not import symbol`        | Symbol doesn't exist or moved  | Verify symbol path, check spelling   |
| `Napoleon processing failed`     | Invalid Google-style docstring | Fix docstring format                 |
| `RST syntax: Error in directive` | Missing blank lines in RST     | Add blank line after directives      |
| `Invalid section header`         | Wrong capitalization/format    | Use proper case: `Args:`, `Returns:` |
| `missing_rst`                    | @public symbol not in RST      | Add RST docs or remove @public       |
| `missing_public`                 | RST symbol missing @public     | Add @public decorator                |
| `missing_export`                 | @public symbol not exported    | Add to **init**.py exports           |

### Exit Codes

- **0**: Success, no issues found
- **1**: Validation errors or issues found
- **2**: Usage error, invalid arguments, or system error

## Getting Help

### Internal Debugging

```bash
# Check system state
python -c "import automation.dagster_docs; print('Module loads successfully')"

# Test basic functionality
dagster-docs --help

# Verify environment
python -c "import sphinx, click, dagster; print('Dependencies available')"
```

### Log Analysis

```bash
# Capture full output for analysis
dagster-docs check exports --all > validation.log 2>&1

# Filter specific error types
grep "missing_rst" validation.log
grep "ERROR:" validation.log
```

### Environment Issues

```bash
# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"

# Verify Dagster installation
python -c "import dagster; print(dagster.__file__)"

# Check working directory
pwd
ls python_modules/  # Should show dagster structure
```

This troubleshooting guide covers the most common issues encountered when using the dagster_docs validation system. For issues not covered here, check the source code in the relevant modules or enable verbose output for additional debugging information.
