# Testing Docstring Validation

This guide covers patterns and best practices for testing the docstring validation system.

## Test Categories

### 1. Unit Tests for Core Logic
Test individual components in isolation:
- `ValidationResult` behavior
- Error message formatting  
- Line number calculations
- Section header detection

### 2. Integration Tests
Test the full validation pipeline:
- Symbol import → docstring extraction → validation → reporting
- File-based validation with real Python files
- End-to-end CLI testing

### 3. Regression Tests
Test specific bugs and edge cases:
- Known problematic docstrings
- Real symbols from the Dagster codebase
- Historical issues that were fixed

## Common Test Patterns

### Testing Line Number Reporting

#### Pattern: Docstring-Relative Line Numbers
```python
def test_docstring_relative_line_numbers():
    """Test line numbers when no file info is available."""
    validator = DocstringValidator()
    
    docstring = '''Function with error.
    
    Line 2 of content.
    Line 3 of content.
    
    Argsxkx:  # Error on line 5
        param: Description
    '''
    
    result = validator.validate_docstring_text(docstring, "test.function")
    
    # Find the error message
    errors = [e for e in result.errors if "Argsxkx" in e]
    assert len(errors) == 1
    assert "(line 5)" in errors[0]  # Should be docstring-relative
```

#### Pattern: File-Relative Line Numbers  
```python
def test_file_relative_line_numbers():
    """Test line numbers when file info is provided."""
    validator = DocstringValidator()
    
    docstring = '''Function with error.
    
    Argsxkx:  # Error on line 3 of content
        param: Description
    '''
    
    # Simulate file context
    docstring_start_line = 200  # Docstring starts at line 200 in file
    result = validator.validate_docstring_text(
        docstring, "test.function", 
        file_path="/fake/path.py",
        docstring_start_line=docstring_start_line
    )
    
    errors = [e for e in result.errors if "Argsxkx" in e]
    assert len(errors) == 1
    
    # Should be file-relative: 200 + 3 - 1 = 202
    assert "(line 202)" in errors[0]
```

### Testing Section Header Validation

#### Pattern: Invalid Section Headers
```python
def test_invalid_section_header_detection():
    """Test detection of corrupted section headers."""
    validator = DocstringValidator()
    
    test_cases = [
        ("Argsxkx:", "Args:"),      # Corruption
        ("args:", "Args:"),         # Wrong case  
        ("Args", "Args:"),          # Missing colon
        ("Arguments :", "Args:"),   # Extra space
    ]
    
    for invalid_header, expected_suggestion in test_cases:
        docstring = f'''Function with bad header.
        
        {invalid_header}
            param: Description
        '''
        
        result = validator.validate_docstring_text(docstring, "test.function")
        
        # Should detect the error and suggest correction
        assert result.has_errors() or result.has_warnings()
        messages = result.errors + result.warnings
        header_messages = [m for m in messages if invalid_header in m]
        assert len(header_messages) >= 1
        
        # Should suggest the correct header
        assert expected_suggestion in header_messages[0]
```

#### Pattern: Valid Section Headers
```python
def test_valid_section_headers():
    """Test that valid headers don't trigger errors."""
    validator = DocstringValidator()
    
    valid_headers = [
        "Args:", "Arguments:", "Parameters:",
        "Returns:", "Return:", "Yields:", "Yield:",
        "Raises:", "Examples:", "Example:",
        "Note:", "Notes:", "Warning:", "Warnings:",
        "See Also:", "Attributes:",
        "Example usage:", "Example definition:",
    ]
    
    for header in valid_headers:
        docstring = f'''Function with valid header.
        
        {header}
            Some content here.
        '''
        
        result = validator.validate_docstring_text(docstring, "test.function")
        
        # Should not have section header errors
        header_errors = [
            e for e in result.errors 
            if "section header" in e.lower() and header in e
        ]
        assert len(header_errors) == 0, f"False positive for {header}"
```

### Testing Real Symbols

#### Pattern: Symbol-Based Testing
```python
def test_real_symbol_validation():
    """Test validation of actual symbols from the codebase."""
    validator = DocstringValidator()
    
    # Test a symbol that should validate successfully
    result = validator.validate_symbol_docstring("dagster.OpDefinition")
    assert result.is_valid(), f"Unexpected errors: {result.errors}"
    
    # Test a symbol with known issues (if any)
    result = validator.validate_symbol_docstring("dagster.asset")
    if not result.is_valid():
        # Verify specific expected errors
        expected_errors = ["Invalid section header: 'Argsxkx:'"]
        for expected in expected_errors:
            assert any(expected in error for error in result.errors), \
                f"Expected error '{expected}' not found in {result.errors}"
```

#### Pattern: File-Based Testing with Temporary Files
```python
import tempfile
from pathlib import Path

def test_temporary_file_validation():
    """Test validation using temporary Python files."""
    test_code = '''
def example_function():
    """Function with validation error.
    
    This is line 4 of the file.
    This is line 5 of the file.
    
    Argsxkx:  # Error on line 7 of the file
        param: Description
    """
    return "test"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        # Note: This pattern requires additional setup to make the symbol importable
        # In practice, testing real symbols is usually more practical
        pass
    finally:
        Path(temp_file).unlink(missing_ok=True)
```

### Testing Error Message Quality

#### Pattern: Error Message Content
```python
def test_error_message_quality():
    """Test that error messages are helpful and actionable."""
    validator = DocstringValidator()
    
    docstring = '''Function with bad section header.
    
    Argsxkx:
        param: Description
    '''
    
    result = validator.validate_docstring_text(docstring, "test.function")
    
    assert result.has_errors()
    error_message = result.errors[0]
    
    # Should identify the problem clearly
    assert "Invalid section header" in error_message
    assert "Argsxkx" in error_message
    
    # Should provide helpful suggestion
    assert "Did you mean 'Args:'?" in error_message
    
    # Should include line number for navigation
    assert "(line " in error_message
```

#### Pattern: RST Enhancement Testing
```python
def test_rst_error_enhancement():
    """Test that RST errors are enhanced with helpful context."""
    validator = DocstringValidator()
    
    # Test code-block directive error
    docstring = '''Function with RST error.
    
    .. code-block:: python
    print("missing blank line")
    '''
    
    result = validator.validate_docstring_text(docstring, "test.function")
    
    if result.has_errors():
        rst_errors = [e for e in result.errors if "code-block" in e]
        if rst_errors:
            # Should provide enhanced explanation
            assert "blank line" in rst_errors[0].lower()
            assert "directive" in rst_errors[0].lower()
```

## Test Organization

### File Structure
```
automation_tests/docstring_lint_tests/
├── test_validator.py                 # Core validator tests
├── test_file_relative_line_numbers.py  # Line number handling tests  
├── test_section_headers.py           # Section header validation tests
├── test_rst_validation.py            # RST syntax validation tests
├── test_real_symbols.py              # Tests against real codebase symbols
└── test_cli_integration.py           # End-to-end CLI tests
```

### Test Naming Conventions
```python
# Unit tests: test_{component}_{behavior}
def test_validation_result_with_error():
def test_validator_empty_docstring():
def test_line_number_calculation():

# Integration tests: test_{workflow}_{scenario}  
def test_symbol_validation_success():
def test_file_validation_with_errors():

# Regression tests: test_{issue_description}
def test_args_typo_detection():
def test_file_line_numbers_reported():
```

## Manual Testing Workflow

### CLI Testing Commands
```bash
# Test specific symbol (most common during development) 
cd python_modules/automation
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset

# Test changed files (during development)
python -m automation.docs_cli.main check docstrings --changed

# Test specific package
python -m automation.docs_cli.main check docstrings --package=dagster

# Test with verbose output for debugging
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset -v
```

### Debugging Test Failures

#### Add Debug Output
```python
def test_with_debug():
    validator = DocstringValidator()
    result = validator.validate_docstring_text(docstring, "test.function")
    
    # Debug output for investigation
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Parsing successful: {result.parsing_successful}")
    
    # Your assertions here
```

#### Isolate the Problem
```python
def test_minimal_reproduction():
    """Create the smallest possible test case that reproduces the issue."""
    validator = DocstringValidator()
    
    # Start with minimal case
    docstring = "Argsxkx:"
    result = validator.validate_docstring_text(docstring, "test.function")
    
    # Gradually add complexity until you reproduce the issue
```

## Performance Testing

### Timing Tests
```python
import time

def test_validation_performance():
    """Ensure validation completes in reasonable time."""
    validator = DocstringValidator()
    
    # Large docstring for stress testing
    large_docstring = "Function with large docstring.\n" + "\n".join([
        f"Line {i} of content." for i in range(1000)
    ])
    
    start_time = time.time()
    result = validator.validate_docstring_text(large_docstring, "test.function")
    elapsed = time.time() - start_time
    
    assert elapsed < 1.0, f"Validation took too long: {elapsed}s"
```

### Memory Usage Tests
```python
import tracemalloc

def test_memory_usage():
    """Ensure validation doesn't leak memory."""
    validator = DocstringValidator()
    
    tracemalloc.start()
    
    # Validate many docstrings
    for i in range(100):
        docstring = f"Function {i} docstring."
        validator.validate_docstring_text(docstring, f"test.function_{i}")
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Peak memory should be reasonable (< 10MB for this test)
    assert peak < 10 * 1024 * 1024, f"Peak memory usage too high: {peak} bytes"
```

## Test Data Management

### Fixture Files
For complex test cases, store docstrings in separate files:

```python
# test_fixtures/bad_docstring.py
def example_function():
    """Function with multiple issues.
    
    args:  # Wrong case
        param1: Description
        param2 Description  # Missing colon
        
    Returnz:  # Typo
        Something useful
    """
    pass
```

### Parameterized Tests
```python
import pytest

@pytest.mark.parametrize("invalid_header,expected_suggestion", [
    ("Argsxkx:", "Args:"),
    ("args:", "Args:"), 
    ("ARGS:", "Args:"),
    ("Arguments :", "Arguments:"),
])
def test_section_header_suggestions(invalid_header, expected_suggestion):
    validator = DocstringValidator()
    docstring = f"Function.\n\n{invalid_header}\n    param: Description"
    result = validator.validate_docstring_text(docstring, "test.function")
    
    messages = result.errors + result.warnings
    assert any(expected_suggestion in msg for msg in messages)
```

This testing guide provides comprehensive patterns for validating the docstring validation system itself, ensuring that changes maintain quality and don't introduce regressions.