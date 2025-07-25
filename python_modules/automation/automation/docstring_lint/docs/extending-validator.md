# Extending the Docstring Validator

This guide documents common patterns for extending the docstring validation system with new features, parameters, and error handling.

## Adding New Parameters to `validate_docstring_text()`

### Pattern: Context Parameter Addition

When adding new context parameters to enhance validation:

```python
def validate_docstring_text(
    self, 
    docstring: str, 
    symbol_path: str = "unknown",
    # New context parameters
    file_path: Optional[str] = None,
    docstring_start_line: Optional[int] = None,
    # Future parameters would go here
) -> ValidationResult:
```

**Key Steps:**

1. **Add optional parameters** with sensible defaults (usually `None`)
2. **Update docstring** with clear parameter descriptions
3. **Pass parameters through the pipeline** to helper methods
4. **Update calling code** in `validate_symbol_docstring()` to provide context
5. **Maintain backward compatibility** by making all new parameters optional

### Example Implementation

```python
# 1. Add parameters to main method
def validate_docstring_text(self, docstring: str, symbol_path: str = "unknown", 
                          file_path: Optional[str] = None, 
                          docstring_start_line: Optional[int] = None) -> ValidationResult:
    
    # 2. Pass context to helper methods
    result = self._check_docstring_structure(docstring, result, docstring_start_line)
    
    # 3. Use context in error processing
    if line_num is not None and docstring_start_line is not None:
        line_num = docstring_start_line + line_num - 1

# 4. Update caller to provide context
def validate_symbol_docstring(self, dotted_path: str) -> ValidationResult:
    symbol_info = SymbolImporter.import_symbol(dotted_path)
    file_path = symbol_info.file_path if symbol_info else None
    docstring_start_line = symbol_info.line_number if symbol_info else None
    
    return self.validate_docstring_text(docstring, dotted_path, file_path, docstring_start_line)
```

## Passing Context Information Through the Validation Pipeline

### Pattern: Context Threading

Context information should flow through the validation pipeline in a consistent way:

```
validate_docstring_text() 
  ├── RST validation (with context for line conversion)
  ├── _check_docstring_structure(docstring, result, context_params)
  └── Helper methods (_extract_line_number, _enhance_error_message)
```

### Implementation Guidelines

1. **Pass context parameters explicitly** rather than storing as instance variables
2. **Use Optional types** for context that may not always be available
3. **Provide fallback behavior** when context is missing
4. **Document the context flow** in method docstrings

```python
def _check_docstring_structure(
    self, 
    docstring: str, 
    result: ValidationResult, 
    docstring_start_line: Optional[int] = None
) -> ValidationResult:
    """Check basic docstring structure issues.
    
    Args:
        docstring: The docstring text to check
        result: The current validation result
        docstring_start_line: Optional line number where the docstring starts in the file
        
    Returns:
        Updated validation result with structure check issues
    """
    for i, line in enumerate(lines, 1):
        # Calculate file-relative line number if we have the context
        file_line_number = i
        if docstring_start_line is not None:
            file_line_number = docstring_start_line + i - 1
        
        # Use file_line_number in error reporting
        result = result.with_error(f"Error message", file_line_number)
```

## Handling Both RST Parsing Errors and Structure Check Errors

### Two Error Sources Pattern

The validator handles errors from two different sources that require different processing:

#### 1. RST Parsing Errors (from docutils)
- **Format**: `<string>:5: (ERROR/3) Content block expected...`
- **Processing**: Extract line number with `_extract_line_number()`
- **Enhancement**: Apply `_enhance_error_message()` for better user feedback
- **Line Conversion**: Convert docstring-relative to file-relative in main validation loop

```python
# RST error processing pattern
for line in warnings_text.strip().split("\n"):
    if line.strip():
        line_num = self._extract_line_number(line)
        # Convert to file-relative line number if we have the context
        if line_num is not None and docstring_start_line is not None:
            line_num = docstring_start_line + line_num - 1
        enhanced_message = self._enhance_error_message(line)
        
        if should_be_error:
            result = result.with_error(f"RST syntax: {enhanced_message}", line_num)
```

#### 2. Structure Check Errors (from custom validation)
- **Format**: Direct line number from enumeration
- **Processing**: Calculate file-relative line number immediately
- **Enhancement**: Context-aware error messages

```python
# Structure error processing pattern
for i, line in enumerate(lines, 1):
    # Calculate file-relative line number if we have the context
    file_line_number = i
    if docstring_start_line is not None:
        file_line_number = docstring_start_line + i - 1
    
    # Report errors with file-relative line numbers
    if error_condition:
        result = result.with_error(f"Structure error: {message}", file_line_number)
```

### Unified Error Handling Pattern

Both error types should result in consistent line number reporting:

```python
def _extract_line_number(self, warning_line: str) -> Optional[int]:
    """Extract line number from a docutils warning message."""
    # Handle "(line N)" format
    if "(line" in warning_line:
        try:
            return int(warning_line.split("(line")[1].split(")")[0])
        except (IndexError, ValueError):
            pass
    
    # Handle "<string>:N:" format from RST errors
    if "<string>:" in warning_line:
        try:
            parts = warning_line.split("<string>:")[1].split(":", 1)
            return int(parts[0])
        except (IndexError, ValueError):
            pass
    
    return None
```

## Testing Strategies for Validation Changes

### Pattern: Comprehensive Test Coverage

When adding new validation features, follow this testing pattern:

#### 1. Test Structure
```python
class TestNewValidationFeature:
    """Test the new validation feature with comprehensive coverage."""
    
    def test_feature_with_context(self):
        """Test feature when context information is available."""
        
    def test_feature_without_context(self):
        """Test feature when context information is missing."""
        
    def test_feature_edge_cases(self):
        """Test edge cases and error conditions."""
```

#### 2. Context Testing Pattern
```python
def test_error_line_numbers_are_file_relative(self):
    """Test that errors report file-relative line numbers when context is provided."""
    validator = DocstringValidator()
    
    # Prepare test docstring with known error location
    docstring = textwrap.dedent('''
        Function with error.
        
        Malformed section:
            This error should be at docstring line 4, file line 7
    ''').strip()
    
    # Provide file context
    docstring_start_line = 4  # Docstring starts at file line 4
    result = validator.validate_docstring_text(
        docstring, "test.symbol", None, docstring_start_line
    )
    
    # Verify file-relative line number (4 + 4 - 1 = 7)
    assert result.has_errors()
    error_message = result.errors[0]
    assert "(line 7)" in error_message
    assert "(line 4)" not in error_message  # Should not be docstring-relative
```

#### 3. Backward Compatibility Testing
```python
def test_backward_compatibility(self):
    """Test that existing code works without providing new parameters."""
    validator = DocstringValidator()
    
    # Old calling pattern should still work
    result = validator.validate_docstring_text(docstring, "test.symbol")
    
    # Should work but without enhanced context
    assert result is not None
```

#### 4. Error Format Testing
```python
def test_multiple_error_formats(self):
    """Test that different error formats are handled correctly."""
    validator = DocstringValidator()
    
    # Test RST errors (format: <string>:N:)
    rst_docstring = '''
    .. code-block:: python
    Missing blank line
    '''
    
    # Test structure errors (format: direct line numbers)
    structure_docstring = '''
    Invalid section header:
        content
    '''
    
    # Both should report consistent line number formats
```

### Testing Best Practices

1. **Test both with and without context** to ensure backward compatibility
2. **Use realistic docstring examples** that mirror actual usage
3. **Verify specific line numbers** rather than just checking for errors
4. **Test error message format consistency** across different error types
5. **Include edge cases** like empty context, invalid line numbers, etc.
6. **Mock external dependencies** when testing symbol import functionality

### Example Test Setup Pattern

```python
def setup_test_docstring_with_context(docstring_content: str, start_line: int):
    """Helper to create consistent test setup."""
    validator = DocstringValidator()
    docstring = textwrap.dedent(docstring_content).strip()
    return validator.validate_docstring_text(
        docstring, "test.symbol", None, start_line
    )

def assert_file_relative_line_number(result: ValidationResult, expected_line: int):
    """Helper to verify file-relative line number reporting."""
    assert result.has_errors(), f"Expected errors but got none: {result}"
    error_message = result.errors[0]
    assert f"(line {expected_line})" in error_message, (
        f"Expected line {expected_line}, got: {error_message}"
    )
```

This pattern ensures consistent, thorough testing of validation enhancements while maintaining backward compatibility and clear error reporting.