# Development Workflow for Docstring Validation

This guide outlines the recommended workflow for making changes to the docstring validation system.

## Quick Reference

### Essential Commands
```bash
# Test a specific symbol (most common during development)
cd python_modules/automation
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset

# Run validation tests
pytest python_modules/automation/automation_tests/docstring_lint_tests/

# Run linting (MANDATORY after any Python changes)
make ruff

# Run type checking
make pyright
```

### Critical Files
- **Core validator**: `automation/docstring_lint/validator.py`
- **CLI entry point**: `automation/docs_cli/commands/check.py`  
- **Test suite**: `automation_tests/docstring_lint_tests/`
- **Section headers**: `validator.py:ALLOWED_SECTION_HEADERS`

## Development Workflow

### 1. Understanding the Problem

Before making changes, ensure you understand:
- **What validation error needs to be added/fixed?**
- **Where in the pipeline should the change go?**
  - Symbol import issues → `SymbolImporter`
  - File reading issues → `_read_docstring_from_file()`
  - RST syntax issues → RST validation section
  - Section header issues → `_check_docstring_structure()`
  - Line number issues → Line number calculation logic

### 2. Write Failing Tests First

Create tests that demonstrate the desired behavior:

```python
# automation_tests/docstring_lint_tests/test_your_feature.py
def test_new_validation_rule():
    """Test the new validation rule you're implementing."""
    validator = DocstringValidator()
    
    # Create a docstring that should trigger your new rule
    docstring = '''Function with the issue you're fixing.
    
    ProblemPatternHere:
        content: description
    '''
    
    result = validator.validate_docstring_text(docstring, "test.function")
    
    # Assert the expected behavior
    assert result.has_errors()  # or has_warnings()
    errors = [e for e in result.errors if "expected text" in e]
    assert len(errors) == 1
    assert "helpful suggestion" in errors[0]
```

**Run the test to confirm it fails:**
```bash
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_your_feature.py -v
```

### 3. Implement the Change

Make your changes to the appropriate component:

#### For Section Header Changes
```python
# In validator.py

# 1. Update ALLOWED_SECTION_HEADERS if needed
ALLOWED_SECTION_HEADERS = {
    # existing headers...
    "New Header:",  # Add new allowed header
}

# 2. Add validation logic in _check_docstring_structure()
def _check_docstring_structure(self, docstring, result, file_path=None, docstring_start_line=None):
    # ... existing logic ...
    
    # Add your new validation rule
    if your_condition:
        result = result.with_error(
            "Your helpful error message",
            calculate_file_line_number(i)  # Use this for file-relative line numbers
        )
```

#### For RST Enhancement Changes
```python
# In validator.py, update _enhance_error_message()
def _enhance_error_message(self, warning_line: str) -> str:
    # ... existing enhancements ...
    
    # Add your new enhancement pattern
    if "your error pattern" in warning_line:
        return "Your enhanced, helpful error message with context"
    
    return warning_line  # Don't forget the fallback
```

### 4. Test Your Changes

**Run your specific test:**
```bash
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_your_feature.py -v
```

**Run the full validation test suite:**
```bash
pytest python_modules/automation/automation_tests/docstring_lint_tests/ -v
```

**Test manually with real symbols:**
```bash
cd python_modules/automation
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset
```

### 5. Verify No Regressions

**Run existing tests to ensure no regressions:**
```bash
# Core validator tests
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_validator.py

# Line number tests (if you changed line number logic)
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_file_relative_line_numbers.py

# Any other relevant test files
```

### 6. Code Quality Checks

**MANDATORY: Run linting and formatting:**
```bash
make ruff
```

**Run type checking (recommended):**
```bash
make pyright
```

**If there are linting issues, fix them and re-run tests:**
```bash
# After fixing linting issues
pytest python_modules/automation/automation_tests/docstring_lint_tests/test_your_feature.py
```

### 7. Manual Verification

Test your changes against real symbols to ensure they work in practice:

```bash
# Test symbols known to have issues
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset

# Test symbols that should validate cleanly
python -m automation.docs_cli.main check docstrings --symbol=dagster.OpDefinition

# Test against changed files if you're fixing a specific issue
python -m automation.docs_cli.main check docstrings --changed
```

### 8. Documentation Updates

If you're adding new validation rules or changing behavior:

**Update the appropriate documentation:**
- Add new section headers to this guide
- Document new error patterns and their solutions
- Update examples if the error messages changed

## Common Development Scenarios

### Adding a New Section Header

1. **Add to allowed list:**
   ```python
   ALLOWED_SECTION_HEADERS = {
       # ... existing headers ...
       "My New Header:",
   }
   ```

2. **Test that it's now allowed:**
   ```python
   def test_new_header_allowed():
       docstring = '''Function with new header.
       
       My New Header:
           content here
       '''
       result = validator.validate_docstring_text(docstring, "test.function")
       # Should not have section header errors
       assert not any("section header" in e.lower() for e in result.errors)
   ```

### Fixing Line Number Reporting

1. **Identify where the error is generated:**
   - Look for `result.with_error()` or `result.with_warning()` calls
   - Check if they're passing line numbers correctly

2. **Ensure file information is available:**
   ```python
   # In _check_docstring_structure(), always use:
   calculate_file_line_number(i)  # Not just 'i'
   ```

3. **Test both scenarios:**
   ```python
   # Test docstring-relative (no file info)
   result = validator.validate_docstring_text(docstring, "test.function")
   
   # Test file-relative (with file info)
   result = validator.validate_docstring_text(
       docstring, "test.function", "/fake/path.py", 100
   )
   ```

### Improving Error Messages

1. **Find the current error generation:**
   ```python
   # Look for patterns like:
   result = result.with_error(f"Current message: {problem}")
   ```

2. **Enhance with helpful context:**
   ```python
   result = result.with_error(
       f"Current message: {problem}. "
       f"Try this solution: {suggestion}. "
       f"Common cause: {explanation}"
   )
   ```

3. **Test the message quality:**
   ```python
   def test_error_message_helpful():
       # ... trigger the error ...
       assert "helpful suggestion" in result.errors[0]
       assert "explanation" in result.errors[0]
   ```

## Debugging Tips

### Investigation Workflow

1. **Reproduce the issue manually:**
   ```bash
   python -m automation.docs_cli.main check docstrings --symbol=problematic.symbol
   ```

2. **Create a minimal test case:**
   ```python
   def test_debug_issue():
       validator = DocstringValidator()
       
       # Minimal docstring that reproduces the problem
       docstring = "Minimal case"
       result = validator.validate_docstring_text(docstring, "test.function")
       
       # Add debug output
       print(f"Errors: {result.errors}")
       print(f"Warnings: {result.warnings}")
   ```

3. **Add debugging to the validator:**
   ```python
   # Temporarily add to _check_docstring_structure()
   print(f"Processing line {i}: '{line}'")
   print(f"Stripped: '{stripped}'")
   print(f"Leading spaces: {leading_spaces}")
   ```

### Common Issues and Solutions

**Problem: Test passes but manual testing fails**
- Solution: Check that your test case matches the real-world scenario
- Check: Are you testing the right validation path?

**Problem: Line numbers are wrong**
- Solution: Verify `calculate_file_line_number()` is being used
- Check: Is `docstring_start_line` being passed correctly?

**Problem: Changes don't take effect**
- Solution: Restart your Python session (imports are cached)
- Check: Are you editing the right file?

**Problem: Tests are flaky**
- Solution: Check for order dependencies or shared state
- Check: Are you using absolute imports in tests?

## Performance Considerations

### When Making Changes

**AST parsing changes:**
- Test with large files to ensure reasonable performance
- Consider caching implications for batch operations

**Regex changes:**
- Test with long docstrings to avoid catastrophic backtracking
- Use `re.compile()` for patterns used multiple times

**Line number calculation changes:**
- Ensure O(1) complexity for individual line calculations
- Avoid re-parsing files unnecessarily

### Performance Testing
```python
import time

def test_performance_regression():
    """Ensure changes don't significantly slow down validation."""
    validator = DocstringValidator()
    
    # Create a substantial test case
    large_docstring = "Function.\n" + "\n".join([f"Line {i}." for i in range(100)])
    
    start_time = time.time()
    result = validator.validate_docstring_text(large_docstring, "test.function")
    elapsed = time.time() - start_time
    
    # Should complete quickly (adjust threshold as needed)
    assert elapsed < 0.1, f"Validation too slow: {elapsed}s"
```

## Release Checklist

Before considering your changes complete:

- [ ] All new tests pass
- [ ] All existing tests still pass  
- [ ] Manual testing confirms the fix works
- [ ] `make ruff` passes without issues
- [ ] `make pyright` passes (or shows no new errors)
- [ ] Error messages are helpful and actionable
- [ ] Line numbers are reported correctly
- [ ] Performance impact is acceptable
- [ ] Documentation is updated if needed

This workflow ensures that changes to the docstring validation system are robust, well-tested, and maintain the quality of error reporting that developers depend on.