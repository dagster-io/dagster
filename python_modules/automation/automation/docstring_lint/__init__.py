"""Docstring linting and validation tools for Dagster.

This module provides comprehensive docstring validation for Python symbols using
Sphinx's parsing pipeline to ensure documentation quality and consistency across
the Dagster codebase.

## Module Structure

The docstring linter consists of several key components:

### Core Components

1. **validator.py**: Main validation logic
   - `DocstringValidator`: Core validator class that processes docstrings
   - `ValidationResult`: Immutable record containing validation results
   - `SymbolInfo`: Metadata about Python symbols (location, module, etc.)
   - `SymbolImporter`: Utility for importing symbols from dotted paths

2. **cli.py**: Command-line interface
   - Single symbol validation: `python -m automation.docstring_lint dagster.asset`
   - Batch validation: `--all-public` flag for validating all public symbols
   - Watch mode: `--watch` flag for real-time validation during development
   - Verbose mode: `--verbose` for detailed error reporting

3. **watcher.py**: File watching functionality
   - Real-time docstring validation during development
   - Efficient file change detection and validation triggering

## Validation Process

The validator uses a multi-stage validation pipeline:

1. **Napoleon Processing**: Converts Google-style docstrings to RST format
2. **RST Syntax Validation**: Uses docutils to validate RST markup
3. **Structure Checking**: Validates docstring structure and common patterns
4. **Error Enhancement**: Provides helpful error messages for common issues

## Supported Docstring Formats

- **Google-style docstrings** (primary format used in Dagster)
- Basic RST markup validation
- Sphinx role and directive filtering (roles like `:py:class:` are ignored in standalone validation)

## Symbol Support

The linter works with all Python symbols accessible via dotted paths:

### Functions and Methods
- **Functions**: `dagster.asset`, `dagster_dbt.load_assets_from_dbt_project`
- **Instance Methods**: `dagster.OpDefinition.execute_in_process`
- **Static Methods**: `dagster.DagsterInstance.ephemeral`
- **Class Methods**: `dagster.AssetMaterialization.create`

### Classes and Modules
- **Classes**: `dagster.OpDefinition`, `dagster.AssetMaterialization`
- **Modules**: `dagster`, `dagster.core.definitions`

## Error Detection

The validator detects various categories of issues:

### RST Syntax Errors
- Malformed directives (missing `::` in `code-block`)
- Unmatched markup (backticks, quotes)
- Invalid list formatting
- Broken links and references

### Google Docstring Issues
- Malformed section headers (`args:` instead of `Args:`, missing colons, corrupted headers like `Argsjdkfjdk:`) with enhanced error messages linking RST syntax errors to their root cause
- Incorrect indentation in parameter descriptions
- Missing or empty sections

### Structure Problems
- Duplicate sections
- Empty section content
- Inconsistent formatting

## Usage Examples

### Command Line
```bash
# Validate single symbol
python -m automation.docstring_lint dagster.asset

# Validate all public symbols in a module
python -m automation.docstring_lint --all-public dagster.core.definitions

# Watch mode for development
python -m automation.docstring_lint --watch dagster.OpDefinition.execute_in_process
```

### Programmatic Usage
```python
from automation.docstring_lint import DocstringValidator

validator = DocstringValidator()

# Validate raw docstring text
result = validator.validate_docstring_text(docstring_text, "symbol.path")

# Validate imported symbol
result = validator.validate_symbol_docstring("dagster.asset")

# Check results
if result.is_valid():
    print("Docstring is valid!")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

## Integration Points

### Development Workflow
- File watching for real-time feedback during docstring editing
- Integration with development tools via CLI interface
- Batch validation for CI/CD pipelines

### Sphinx Integration
- Path configuration matches Dagster's Sphinx build setup
- Role/directive filtering aligns with actual documentation build
- Error messages help maintain documentation build compatibility

## Configuration

The validator includes several configuration options:

- **Sphinx Role Filtering**: `DO_FILTER_OUT_SPHINX_ROLE_WARNINGS` controls whether
  to filter out unknown Sphinx roles that are valid in full builds
- **Path Setup**: Automatically configures Python paths to match Dagster's structure
- **Error Enhancement**: Provides contextual error messages for common issues

## Performance Characteristics

- **Single Symbol Validation**: Optimized for fast feedback during development
- **Batch Processing**: Efficient validation of entire modules
- **File Watching**: Minimal overhead for real-time validation
- **Import Caching**: Reuses imported modules where possible

## Testing

Comprehensive test suite covers:
- All validation functionality
- Error detection and reporting
- Edge cases and malformed input
- Integration with Sphinx parsing pipeline

See `automation_tests/docstring_lint_tests/` for detailed test examples.
"""

from automation.docstring_lint.validator import DocstringValidator, SymbolInfo, ValidationResult

__all__ = ["DocstringValidator", "SymbolInfo", "ValidationResult"]
