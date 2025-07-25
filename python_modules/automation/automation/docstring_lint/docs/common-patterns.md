# Common Patterns for Docstring Validation

This document catalogs reusable patterns and code templates for common docstring validation tasks.

## Context Parameter Passing

### Pattern: File Location Context

When you need to pass file location information through the validation pipeline:

```python
# Standard context parameters
file_path: Optional[str] = None           # Path to source file
docstring_start_line: Optional[int] = None # Line where docstring begins in file

# Usage in validation method
def validate_docstring_text(
    self, 
    docstring: str, 
    symbol_path: str = "unknown",
    file_path: Optional[str] = None,
    docstring_start_line: Optional[int] = None
) -> ValidationResult:
    # Pass context to helper methods
    result = self._check_docstring_structure(docstring, result, docstring_start_line)
    
    # Use context in line number conversion
    if line_num is not None and docstring_start_line is not None:
        file_line_num = docstring_start_line + line_num - 1
        result = result.with_error(message, file_line_num)
    else:
        result = result.with_error(message, line_num)  # Fallback to docstring-relative
```

### Pattern: Symbol Context

When passing symbol metadata for enhanced error reporting:

```python
# Retrieve symbol context
try:
    symbol_info = SymbolImporter.import_symbol(dotted_path)
    file_path = symbol_info.file_path if symbol_info else None
    docstring_start_line = symbol_info.line_number if symbol_info else None
except (ImportError, AttributeError):
    file_path = None
    docstring_start_line = None

# Use context in validation
return self.validate_docstring_text(
    docstring, dotted_path, file_path, docstring_start_line
)
```

### Pattern: Context-Aware Helper Methods

Structure helper methods to accept and use context:

```python
def _helper_method(
    self, 
    primary_data: str, 
    result: ValidationResult,
    # Context parameters at the end
    docstring_start_line: Optional[int] = None,
    additional_context: Optional[str] = None
) -> ValidationResult:
    """Helper method that uses context for enhanced processing.
    
    Args:
        primary_data: Main data to process
        result: Current validation result
        docstring_start_line: Optional context for line number conversion
        additional_context: Optional additional context
    """
    # Use context when available, fallback when not
    if docstring_start_line is not None:
        # Enhanced behavior with context
        pass
    else:
        # Fallback behavior without context
        pass
```

## Error Message Enhancement Workflows

### Pattern: Multi-Stage Error Processing

Process errors through multiple enhancement stages:

```python
def process_error_with_enhancements(self, raw_error: str, context: dict) -> str:
    """Apply multiple enhancement stages to error messages."""
    # Stage 1: Extract basic information
    line_num = self._extract_line_number(raw_error)
    
    # Stage 2: Apply context-specific enhancements
    enhanced_message = self._enhance_error_message(raw_error)
    
    # Stage 3: Convert line numbers if context available
    if line_num is not None and context.get('docstring_start_line'):
        file_line_num = context['docstring_start_line'] + line_num - 1
        enhanced_message = self._add_line_number(enhanced_message, file_line_num)
    
    # Stage 4: Add context-specific suggestions
    enhanced_message = self._add_contextual_suggestions(enhanced_message, context)
    
    return enhanced_message
```

### Pattern: Error Classification and Enhancement

Classify errors by type and apply appropriate enhancements:

```python
def _enhance_error_message(self, error_line: str) -> str:
    """Enhance error messages based on error type classification."""
    
    # Classify error type
    if 'Error in "code-block" directive' in error_line:
        return self._enhance_code_block_error(error_line)
    elif "Unexpected indentation" in error_line:
        return self._enhance_indentation_error(error_line)  
    elif "Block quote ends without a blank line" in error_line:
        return self._enhance_block_quote_error(error_line)
    else:
        return error_line  # Return unchanged if no enhancement available

def _enhance_code_block_error(self, error_line: str) -> str:
    """Enhance code-block directive errors with specific guidance."""
    if "maximum 1 argument(s) allowed" in error_line:
        return (
            'Error in "code-block" directive: missing blank line after directive. '
            "RST directives like '.. code-block:: python' require an empty line "
            "before the code content begins."
        )
    return error_line

def _enhance_indentation_error(self, error_line: str) -> str:
    """Enhance indentation errors with section header guidance."""
    return (
        "Unexpected indentation. This often indicates a malformed section header. "
        "Check that section headers like 'Args:', 'Returns:', 'Raises:' are formatted correctly "
        "and that content under them is properly indented."
    )
```

## Multi-Format Line Number Extraction

### Pattern: Universal Line Number Extractor

Handle multiple line number formats in a single method:

```python
def _extract_line_number(self, message: str) -> Optional[int]:
    """Extract line number from various message formats.
    
    Supports:
    - "(line N)" format from structure validation
    - "<string>:N:" format from RST parsing
    - "file.py:N:" format from file-based errors
    """
    # Format 1: (line N)
    if "(line" in message:
        try:
            return int(message.split("(line")[1].split(")")[0])
        except (IndexError, ValueError):
            pass
    
    # Format 2: <string>:N:
    if "<string>:" in message:
        try:
            parts = message.split("<string>:")[1].split(":", 1)
            return int(parts[0])
        except (IndexError, ValueError):
            pass
    
    # Format 3: filename.py:N:
    import re
    file_line_match = re.search(r'\.py:(\d+):', message)
    if file_line_match:
        try:
            return int(file_line_match.group(1))
        except ValueError:
            pass
    
    return None
```

### Pattern: Line Number Conversion Utilities

Provide utilities for common line number conversions:

```python
def calculate_file_line_number(
    docstring_line: int, 
    docstring_start_line: Optional[int]
) -> int:
    """Convert docstring-relative line number to file-relative.
    
    Args:
        docstring_line: Line number within the docstring (1-based)
        docstring_start_line: Line where docstring starts in file (1-based)
    
    Returns:
        File-relative line number, or docstring-relative if no context
    """
    if docstring_start_line is None:
        return docstring_line  # Fall back to docstring-relative
    
    return docstring_start_line + docstring_line - 1

def extract_and_convert_line_number(
    message: str, 
    docstring_start_line: Optional[int]
) -> tuple[Optional[int], str]:
    """Extract line number from message and convert to file-relative.
    
    Returns:
        Tuple of (converted_line_number, original_message)
    """
    original_line = self._extract_line_number(message)
    if original_line is None:
        return None, message
    
    file_line = calculate_file_line_number(original_line, docstring_start_line)
    return file_line, message
```

## Test Setup for Docstring Validation

### Pattern: Standardized Test Setup

Create consistent test environments for docstring validation:

```python
class DocstringTestHelper:
    """Helper class for standardized docstring testing."""
    
    @staticmethod
    def create_test_docstring(content: str) -> str:
        """Create a properly formatted test docstring."""
        return textwrap.dedent(content).strip()
    
    @staticmethod
    def setup_validator_with_context(
        docstring: str, 
        symbol_path: str = "test.symbol",
        docstring_start_line: int = 1,
        file_path: Optional[str] = None
    ) -> ValidationResult:
        """Setup validator with standard context."""
        validator = DocstringValidator()
        return validator.validate_docstring_text(
            docstring, symbol_path, file_path, docstring_start_line
        )
    
    @staticmethod
    def assert_error_at_line(result: ValidationResult, expected_line: int, error_substring: str = ""):
        """Assert that an error occurs at the expected line."""
        assert result.has_errors(), f"Expected errors but got none: {result}"
        
        matching_errors = [
            e for e in result.errors 
            if f"(line {expected_line})" in e and (not error_substring or error_substring in e)
        ]
        
        assert matching_errors, (
            f"No error found at line {expected_line} with substring '{error_substring}'. "
            f"Errors: {result.errors}"
        )
```

### Pattern: Test Data Builders

Build test data with known line number positions:

```python
class DocstringTestBuilder:
    """Builder for creating test docstrings with predictable line positions."""
    
    def __init__(self, start_line: int = 1):
        self.start_line = start_line
        self.lines = []
    
    def add_line(self, content: str = "") -> 'DocstringTestBuilder':
        """Add a line to the docstring."""
        self.lines.append(content)
        return self
    
    def add_error_at_line(self, line_num: int, error_content: str) -> 'DocstringTestBuilder':
        """Add content that will generate an error at a specific line."""
        while len(self.lines) < line_num - 1:
            self.lines.append("")
        
        if line_num <= len(self.lines):
            self.lines[line_num - 1] = error_content
        else:
            self.lines.append(error_content)
        
        return self
    
    def build(self) -> tuple[str, int]:
        """Build the docstring and return it with the start line."""
        docstring = "\n".join(self.lines)
        return docstring, self.start_line
    
    def build_and_validate(self, symbol_path: str = "test.symbol") -> ValidationResult:
        """Build and validate the docstring."""
        docstring, start_line = self.build()
        return DocstringTestHelper.setup_validator_with_context(
            docstring, symbol_path, start_line
        )

# Usage example
def test_specific_error_location():
    result = (DocstringTestBuilder(start_line=5)
              .add_line("Function description.")
              .add_line("")
              .add_line("Some content.")
              .add_error_at_line(4, "args:")  # Malformed section header
              .add_line("    param: description")
              .build_and_validate())
    
    # Error should be at file line 8 (start_line=5 + docstring_line=4 - 1)
    DocstringTestHelper.assert_error_at_line(result, 8, "args:")
```

### Pattern: Parameterized Error Testing

Test multiple error scenarios systematically:

```python
import pytest

@pytest.mark.parametrize("docstring_content,start_line,expected_file_line,error_substring", [
    # Test case format: (docstring, start_line, expected_error_line, error_text)
    ("Function.\n\nargs:\n    param: desc", 1, 3, "args:"),
    ("Function.\n\nargs:\n    param: desc", 10, 12, "args:"),  # Different start line
    ("Function.\n\nArgsxyz:\n    param: desc", 5, 7, "Argsxyz:"),  # Corrupted header
])
def test_error_line_numbers(docstring_content, start_line, expected_file_line, error_substring):
    """Test that errors are reported at correct file-relative line numbers."""
    result = DocstringTestHelper.setup_validator_with_context(
        docstring_content, "test.symbol", start_line
    )
    
    DocstringTestHelper.assert_error_at_line(result, expected_file_line, error_substring)
```

### Pattern: Mock Symbol Info for Testing

Create mock symbol information for comprehensive testing:

```python
from unittest.mock import Mock, patch

def create_mock_symbol_info(file_path: str = "/test/file.py", line_number: int = 10):
    """Create mock SymbolInfo for testing."""
    mock_info = Mock()
    mock_info.file_path = file_path
    mock_info.line_number = line_number
    mock_info.dotted_path = "test.symbol" 
    mock_info.docstring = "Test docstring"
    return mock_info

def test_with_mock_symbol_info():
    """Test validation with mocked symbol information."""
    mock_info = create_mock_symbol_info("/path/to/file.py", 15)
    
    with patch('automation.docstring_lint.validator.SymbolImporter.import_symbol', 
               return_value=mock_info):
        validator = DocstringValidator()
        result = validator.validate_symbol_docstring("test.symbol")
        
        # Validate that file context was used correctly
        # (specific assertions depend on the test scenario)
```

These patterns provide reusable templates for common docstring validation tasks, ensuring consistency and reducing development time for new features.