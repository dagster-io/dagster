"""Tests for docstring_lint package.

## Test Organization Structure

The test suite is organized by functional areas to make it easy to navigate
and understand what aspects of the docstring linter are being tested.

### test_validator.py - Core Infrastructure
Tests the fundamental validator classes and data structures:
- `TestValidationResult`: The immutable result record and its operations
- `TestDocstringValidator`: Core validation pipeline and symbol importing

### test_common_errors.py - Error Detection Patterns
Systematic testing of error detection organized by error category:
- `TestSectionHeaderErrors`: Invalid section header formats
- `TestIndentationErrors`: Indentation and whitespace problems
- `TestParameterDescriptionErrors`: Parameter documentation issues
- `TestRSTSyntaxErrors`: RST markup validation errors
- `TestStructuralErrors`: Document structure problems
- `TestComplexErrorCombinations`: Multiple simultaneous errors

### test_method_docstrings.py - Method-Specific Validation
Comprehensive testing of method docstring validation:
- `TestInstanceMethodDocstrings`: Standard class methods
- `TestStaticMethodDocstrings`: Static utility methods
- `TestClassMethodDocstrings`: Factory/constructor methods
- `TestMethodDocstringEdgeCases`: Unusual scenarios and edge cases

### test_known_valid_symbols.py - Integration Testing
End-to-end validation using real symbols from the Dagster codebase.

## Test Pattern Guidelines

### Naming Convention
- Test classes: `Test<AreaBeingTested>` (e.g., `TestSectionHeaderErrors`)
- Test methods: `test_<specific_scenario>` (e.g., `test_malformed_section_header`)
- Fixtures: `validator` - provides `DocstringValidator` instance

### Test Structure Pattern
Most tests follow this pattern:
1. Create docstring content (valid or invalid)
2. Call `validator.validate_docstring_text(docstring, "symbol.path")`
3. Assert expected validation results (errors/warnings/validity)

### Error vs Warning Testing
- **Errors**: Issues that break RST parsing or documentation builds
- **Warnings**: Style issues that don't break functionality
- Tests check both `result.has_errors()` and `result.has_warnings()` appropriately

### Symbol Path Convention
Tests use descriptive fake symbol paths like:
- `"TestClass.method_name"` for method docstrings
- `"test.function"` for function docstrings
- `"test.symbol"` for generic testing

## Running Tests

```bash
# All tests
pytest python_modules/automation/automation_tests/docstring_lint_tests/

# Individual modules
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_validator.py
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_common_errors.py
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_method_docstrings.py
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_known_valid_symbols.py

# Specific test classes
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_method_docstrings.py::TestInstanceMethodDocstrings
```

## Key Validation Concepts

### What Gets Validated
- Google-style docstring format conversion to RST
- RST syntax and markup correctness
- Section header formatting and structure
- Indentation and formatting consistency

### What Should Pass
- Well-formatted Google-style docstrings
- Valid RST markup and directives
- Sphinx roles (automatically filtered in standalone validation)

### What Should Generate Errors/Warnings
- Malformed section headers and RST syntax
- Indentation problems and markup errors
- Missing or empty docstring content
- Unknown directives and broken references

This structure makes it easy to find relevant tests when working on specific
aspects of the docstring validation functionality.
"""
