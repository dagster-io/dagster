# Docstring Validation System

## Overview

The docstring validation system in Dagster ensures that all public APIs have properly formatted docstrings that can be rendered correctly in documentation. The system processes Python symbols through several stages to validate both content and structure.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Symbol Import   │───▶│ File Reading     │───▶│ Content Process │
│                 │    │                  │    │                 │
│ • Resolve path  │    │ • AST parsing    │    │ • Napoleon      │
│ • Get file info │    │ • Extract source │    │ • Google→RST    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Error Reporting │◀───│ Structure Check  │◀───│ RST Validation  │
│                 │    │                  │    │                 │
│ • File-relative │    │ • Section header │    │ • Docutils      │
│ • Line numbers  │    │ • Indentation    │    │ • Syntax check  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Key Components

### SymbolImporter
- **Purpose**: Resolves dotted paths (e.g., `dagster.asset`) to Python symbols
- **Key method**: `import_symbol()` returns `SymbolInfo` with file location
- **File location**: Uses `inspect.getfile()` and `inspect.getsourcelines()`

### DocstringValidator  
- **Purpose**: Orchestrates the validation pipeline
- **Key methods**:
  - `validate_symbol_docstring()`: Entry point for symbol validation
  - `validate_docstring_text()`: Validates raw docstring content
  - `_check_docstring_structure()`: Custom structure validation

### ValidationResult
- **Purpose**: Immutable result object for collecting errors/warnings
- **Key methods**: `with_error()`, `with_warning()` for adding issues
- **Line numbers**: Automatically appended as `(line N)` to messages

## Line Number Handling

### The Challenge
Line numbers must be reported relative to the source file, not the processed docstring content. This is complex because:

1. **AST provides symbol location**: `function_def.lineno` (where function starts)
2. **AST provides docstring location**: `docstring_node.lineno` (where docstring starts)  
3. **Processed content is normalized**: `inspect.getdoc()` removes leading/trailing whitespace
4. **Structure validation uses content lines**: 1-indexed lines within processed docstring

### The Solution
```python
# File line calculation
file_line = docstring_start_line + content_line - 1

# Where:
# - docstring_start_line: from AST docstring_node.lineno  
# - content_line: 1-indexed line within processed docstring content
# - file_line: actual line number in source file
```

### Example
```python
# Source file (lines 100-110)
100  def asset():
101      """This is a docstring.
102      
103      Args:
104          param: Description
105      """
106      pass

# AST parsing results:
# - function_def.lineno = 100
# - docstring_node.lineno = 101

# Processed docstring content (after inspect.getdoc):
# Line 1: "This is a docstring."
# Line 2: ""  
# Line 3: "Args:"
# Line 4: "    param: Description"

# Error on "Args:" line:
# - content_line = 3
# - file_line = 101 + 3 - 1 = 103 ✓
```

## Validation Pipeline

### 1. Symbol Import
```python
symbol_info = SymbolImporter.import_symbol("dagster.asset")
# Returns: SymbolInfo with file_path, line_number, name, etc.
```

### 2. File Reading  
```python
docstring, docstring_start_line = self._read_docstring_from_file(dotted_path)
# Uses AST to extract raw docstring and its starting line number
```

### 3. Content Processing
```python
# Napoleon converts Google-style docstrings to RST
napoleon_docstring = GoogleDocstring(docstring)
processed_rst = str(napoleon_docstring)
```

### 4. RST Validation
```python
# Docutils validates RST syntax
docutils.core.publish_doctree(processed_rst, settings_overrides=settings)
# Warnings/errors are captured and enhanced with helpful messages
```

### 5. Structure Validation
```python
# Custom validation for section headers, indentation, etc.
result = self._check_docstring_structure(docstring, result, file_path, docstring_start_line)
```

## Common Validation Errors

### Section Header Issues
- **Invalid headers**: `Argsxkx:` instead of `Args:`
- **Case errors**: `args:` instead of `Args:`
- **Missing colons**: `Args` instead of `Args:`

### RST Syntax Issues  
- **Unexpected indentation**: Often caused by malformed section headers
- **Block quote errors**: Missing blank lines after sections
- **Code block errors**: Missing blank lines after directives

### Enhancement Features
- **Smart suggestions**: "Did you mean 'Args:'?" for `Argsxkx:`
- **Helpful context**: Explanations of common RST issues
- **Sphinx role filtering**: Ignores unknown roles like `:py:class:` that are valid in full builds

## Testing the System

### Manual Testing
```bash
# Test a specific symbol
cd python_modules/automation
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset

# Test changed files
python -m automation.docs_cli.main check docstrings --changed
```

### Unit Testing
```bash
# Run validation tests
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_validator.py

# Run line number tests  
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_file_relative_line_numbers.py
```

## Development Workflow

1. **Understand the validation pipeline**: Read this documentation first
2. **Write failing tests**: Create tests that demonstrate the desired behavior  
3. **Implement changes**: Modify the validator logic
4. **Verify with existing tests**: Ensure no regressions
5. **Manual verification**: Test with real symbols like `dagster.asset`
6. **Run linting**: Always run `make ruff` after Python changes

## Extension Points

### Adding New Validation Rules
1. **Structure checks**: Add logic to `_check_docstring_structure()`
2. **RST enhancements**: Add patterns to `_enhance_error_message()`
3. **Section headers**: Update `ALLOWED_SECTION_HEADERS` set

### Debugging Tips
- **Line number issues**: Check the `calculate_file_line_number()` helper
- **AST problems**: Verify `_read_docstring_from_file()` finds the right function
- **Content issues**: Check that `inspect.getdoc()` normalization is handled correctly