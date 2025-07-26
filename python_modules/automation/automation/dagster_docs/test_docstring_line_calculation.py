"""Tests for accurate docstring line number calculation using AST parsing.

These tests specifically target the bug where functions with decorators or
multi-line signatures had incorrect docstring start line calculations.
"""

from automation.dagster_docs.validator import _find_docstring_start_line, validate_symbol_docstring


def test_find_docstring_start_line_with_decorators():
    """Test that _find_docstring_start_line correctly handles functions with decorators."""
    import os
    import tempfile

    # Create a test file with a function that has decorators (similar to dagster.asset)
    test_code = '''
@decorator1
@decorator2(param="value")
@decorator3(
    param1="value1",
    param2="value2"
)
def my_function(
    arg1: str,
    arg2: int = 42,
    *args,
    **kwargs
):
    """This is the docstring.
    
    It starts on line 14, not on line 8 (the def line) or line 2 (first decorator).
    
    Args:
        arg1: First argument
        arg2: Second argument with default
    """
    return "test"
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        # The function definition line would be detected by inspect as line 7 (def my_function)
        # But the docstring actually starts at line 14
        actual_docstring_line = _find_docstring_start_line(temp_file_path, "my_function", 7)

        # Count lines to verify - docstring starts with """This is the docstring.
        lines = test_code.split("\n")
        expected_line = None
        for i, line in enumerate(lines, 1):
            if '"""This is the docstring.' in line:
                expected_line = i
                break

        assert expected_line is not None, "Could not find expected docstring in test code"
        assert actual_docstring_line == expected_line, (
            f"Expected line {expected_line}, got {actual_docstring_line}"
        )

    finally:
        os.unlink(temp_file_path)


def test_find_docstring_start_line_simple_function():
    """Test that _find_docstring_start_line works with simple functions too."""
    import os
    import tempfile

    test_code = '''
def simple_function():
    """Simple docstring on line 3."""
    return "test"
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        actual_docstring_line = _find_docstring_start_line(temp_file_path, "simple_function", 2)
        assert actual_docstring_line == 3, f"Expected line 3, got {actual_docstring_line}"

    finally:
        os.unlink(temp_file_path)


def test_find_docstring_start_line_no_docstring():
    """Test that _find_docstring_start_line returns None for functions without docstrings."""
    import os
    import tempfile

    test_code = """
def no_docstring_function():
    return "test"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        actual_docstring_line = _find_docstring_start_line(
            temp_file_path, "no_docstring_function", 2
        )
        assert actual_docstring_line is None, f"Expected None, got {actual_docstring_line}"

    finally:
        os.unlink(temp_file_path)


def test_find_docstring_start_line_multiple_functions():
    """Test that _find_docstring_start_line picks the right function when there are multiple with the same name."""
    import os
    import tempfile

    test_code = '''
def duplicate_name():
    """First function docstring on line 3."""
    return "first"

class MyClass:
    def duplicate_name(self):
        """Second function docstring on line 8."""
        return "second"
        
def duplicate_name():
    """Third function docstring on line 12."""
    return "third"
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        # When searching near line 2, should find the first function
        actual_line_1 = _find_docstring_start_line(temp_file_path, "duplicate_name", 2)
        assert actual_line_1 == 3, f"Expected line 3, got {actual_line_1}"

        # When searching near line 12, should find the third function
        actual_line_3 = _find_docstring_start_line(temp_file_path, "duplicate_name", 12)
        assert actual_line_3 == 12, f"Expected line 12, got {actual_line_3}"

    finally:
        os.unlink(temp_file_path)


def test_validate_symbol_docstring_line_numbers_integration():
    """Integration test to verify that the full validation pipeline reports correct line numbers."""
    import importlib.util
    import os
    import sys
    import tempfile

    # Create a test module with a function that has an error at a specific line
    test_code = '''
"""Test module for line number validation."""

def dummy_decorator(func):
    return func

@dummy_decorator  
def test_function(
    arg1: str,
    arg2: int = 42
):
    """Test function with intentional docstring error.
    
    This function has a malformed section header to test line number reporting.
    
    arguments:
        arg1: This should be "Args:" not "arguments:"
        arg2: Second argument
        
    Returns:
        str: Some return value
    """
    return "test"
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    # Create a temporary module name
    module_name = f"test_module_{id(f)}"

    try:
        # Import the temporary module
        spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Validate the function
        symbol_path = f"{module_name}.test_function"
        result = validate_symbol_docstring(symbol_path)

        # Should have errors
        assert result.has_errors(), f"Expected errors, got: {result.errors}"

        # Find the section header error
        section_error = None
        for error in result.errors:
            if "arguments:" in error and ("Args:" in error or "Arguments:" in error):
                section_error = error
                break

        assert section_error is not None, f"Expected section header error, got: {result.errors}"

        # The error should contain the correct line number and filename
        assert f"{os.path.basename(temp_file_path)}:line" in section_error, (
            f"Expected filename:line format in: {section_error}"
        )

        # Extract the reported line number
        filename = os.path.basename(temp_file_path)
        line_marker = f"{filename}:line "
        start = section_error.find(line_marker) + len(line_marker)
        end = section_error.find(")", start)
        reported_line = int(section_error[start:end])

        # Find the actual line where "arguments:" appears
        lines = test_code.split("\n")
        actual_line = None
        for i, line in enumerate(lines, 1):
            if "arguments:" in line:
                actual_line = i
                break

        assert actual_line is not None, "Could not find 'arguments:' in test code"
        assert reported_line == actual_line, f"Expected line {actual_line}, got {reported_line}"

    finally:
        os.unlink(temp_file_path)
        if module_name in sys.modules:
            del sys.modules[module_name]


def test_real_dagster_asset_function():
    """Test that the real dagster.asset function works correctly with the fix."""
    # This test verifies that we can validate the real dagster.asset function without errors
    # (assuming it has valid docstrings)
    result = validate_symbol_docstring("dagster.asset")

    # The dagster.asset function should have valid docstrings (after our fix above)
    assert result.is_valid(), (
        f"dagster.asset should be valid, got errors: {result.errors}, warnings: {result.warnings}"
    )


def test_find_docstring_start_line_multiline_decorators():
    """Test that _find_docstring_start_line correctly handles multi-line decorators."""
    import os
    import tempfile

    # Create a test file with complex multi-line decorators (similar to dagster patterns)
    test_code = '''
from typing import overload

@beta_param(param="resource_defs")
@beta_param(param="io_manager_def")
@beta_param(param="backfill_policy")
@hidden_param(
    param="non_argument_deps",
    breaking_version="2.0.0",
    additional_warn_text="use `deps` instead.",
)
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead.",
)
@hidden_param(
    param="legacy_freshness_policy",
    breaking_version="1.12.0",
    additional_warn_text="use freshness checks instead.",
)
@public
@hidden_param(
    param="compute_kind",
    emit_runtime_warning=False,
    breaking_version="1.10.0",
)
def complex_decorated_function(
    compute_fn=None,
    *,
    name=None,
    key_prefix=None,
    ins=None,
    deps=None,
    metadata=None,
):
    """Complex function with many multi-line decorators.
    
    This docstring should be found at the correct line despite many decorators.
    
    Args:
        compute_fn: The computation function
        name: Asset name
        key_prefix: Key prefix
        ins: Asset inputs
        deps: Dependencies
        metadata: Metadata
        
    Returns:
        The asset definition
    """
    return "test"
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        # The function definition starts around line 26, but the docstring starts much later
        actual_docstring_line = _find_docstring_start_line(
            temp_file_path, "complex_decorated_function", 26
        )

        # Find the expected line by counting where the docstring actually starts
        lines = test_code.split("\n")
        expected_line = None
        for i, line in enumerate(lines, 1):
            if '"""Complex function with many multi-line decorators.' in line:
                expected_line = i
                break

        assert expected_line is not None, "Could not find expected docstring in test code"
        assert actual_docstring_line == expected_line, (
            f"Expected line {expected_line}, got {actual_docstring_line}"
        )

    finally:
        os.unlink(temp_file_path)


def test_find_docstring_start_line_overload_functions():
    """Test that _find_docstring_start_line correctly handles @overload functions."""
    import os
    import tempfile

    # Create a test file with @overload functions (common in type-heavy codebases)
    test_code = '''
from typing import overload, Union

@overload
def overloaded_function(x: int) -> int:
    """First overload docstring.
    
    Args:
        x: An integer
        
    Returns:
        An integer
    """
    ...

@overload 
def overloaded_function(x: str) -> str:
    """Second overload docstring.
    
    Args:
        x: A string
        
    Returns:
        A string  
    """
    ...

def overloaded_function(x: Union[int, str]) -> Union[int, str]:
    """Main implementation docstring.
    
    This is the actual implementation that handles both cases.
    
    Args:
        x: Either an int or str
        
    Returns:
        The same type as input
    """
    return x

@overload
def another_overloaded_function(x: int, y: int) -> int: ...

@overload
def another_overloaded_function(x: str, y: str) -> str: ...

def another_overloaded_function(x, y):
    """Another overloaded function implementation.
    
    This function has overloads but only the main implementation has a docstring.
    
    Args:
        x: First argument
        y: Second argument
        
    Returns:
        Combined result
    """
    return x + y
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    try:
        # Test finding the first overload docstring
        first_overload_line = _find_docstring_start_line(temp_file_path, "overloaded_function", 4)

        # Test finding the main implementation docstring (should pick the closest one when searching near line 28)
        main_impl_line = _find_docstring_start_line(temp_file_path, "overloaded_function", 28)

        # Test finding the second overloaded function (the one with only implementation docstring)
        # Search from line 47 where the actual implementation is defined
        another_impl_line = _find_docstring_start_line(
            temp_file_path, "another_overloaded_function", 47
        )

        # Find expected lines by searching the test code
        lines = test_code.split("\n")

        expected_first_overload = None
        expected_main_impl = None
        expected_another_impl = None

        for i, line in enumerate(lines, 1):
            if '"""First overload docstring.' in line:
                expected_first_overload = i
            elif '"""Main implementation docstring.' in line:
                expected_main_impl = i
            elif '"""Another overloaded function implementation.' in line:
                expected_another_impl = i

        assert expected_first_overload is not None, "Could not find first overload docstring"
        assert expected_main_impl is not None, "Could not find main implementation docstring"
        assert expected_another_impl is not None, "Could not find another implementation docstring"

        assert first_overload_line == expected_first_overload, (
            f"Expected first overload at line {expected_first_overload}, got {first_overload_line}"
        )
        assert main_impl_line == expected_main_impl, (
            f"Expected main impl at line {expected_main_impl}, got {main_impl_line}"
        )
        assert another_impl_line == expected_another_impl, (
            f"Expected another impl at line {expected_another_impl}, got {another_impl_line}"
        )

    finally:
        os.unlink(temp_file_path)


def test_validate_overload_function_line_numbers_integration():
    """Integration test for @overload functions with the full validation pipeline.

    Note: Python only keeps the main implementation docstring at runtime, not the @overload signatures.
    This test verifies that line numbers are correctly reported for the actual implementation.
    """
    import importlib.util
    import os
    import sys
    import tempfile

    # Create a test module with @overload functions that have an error in the main implementation
    test_code = '''
"""Test module for @overload function validation."""

from typing import overload, Union

@overload
def test_overload_function(x: int) -> int:
    """First overload signature (not visible at runtime)."""
    ...

@overload
def test_overload_function(x: str) -> str:
    """Second overload signature (not visible at runtime)."""
    ...

def test_overload_function(x: Union[int, str]) -> Union[int, str]:
    """Main implementation with error.
    
    This is the implementation that's actually validated since Python
    discards @overload signatures at runtime.
    
    arguments:
        x: This should be "Args:" not "arguments:" 
        
    Returns:
        Same type as input
    """
    return x
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        temp_file_path = f.name

    # Create a temporary module name
    module_name = f"test_overload_module_{id(f)}"

    try:
        # Import the temporary module
        spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Validate the function - should pick up the main implementation with the error
        symbol_path = f"{module_name}.test_overload_function"
        result = validate_symbol_docstring(symbol_path)

        # Should have errors from the main implementation
        assert result.has_errors(), f"Expected errors, got: {result.errors}"

        # Find the section header error
        section_error = None
        for error in result.errors:
            if "arguments:" in error and ("Args:" in error or "Arguments:" in error):
                section_error = error
                break

        assert section_error is not None, f"Expected section header error, got: {result.errors}"

        # The error should contain the correct line number and filename
        assert f"{os.path.basename(temp_file_path)}:line" in section_error, (
            f"Expected filename:line format in: {section_error}"
        )

        # Extract and verify the line number points to the main implementation
        filename = os.path.basename(temp_file_path)
        line_marker = f"{filename}:line "
        start = section_error.find(line_marker) + len(line_marker)
        end = section_error.find(")", start)
        reported_line = int(section_error[start:end])

        # Find the actual line where "arguments:" appears in the main implementation
        lines = test_code.split("\n")
        actual_line = None
        for i, line in enumerate(lines, 1):
            if "arguments:" in line:
                actual_line = i
                break

        assert actual_line is not None, "Could not find 'arguments:' in test code"
        assert reported_line == actual_line, f"Expected line {actual_line}, got {reported_line}"

    finally:
        os.unlink(temp_file_path)
        if module_name in sys.modules:
            del sys.modules[module_name]


def test_line_calculation_fallback():
    """Test that the fallback calculation works when AST parsing fails."""
    import os
    import tempfile

    # Create a file with invalid Python syntax to trigger AST parsing failure
    invalid_code = """
def broken_syntax(
    # Missing closing parenthesis and other syntax errors
    return "test"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(invalid_code)
        temp_file_path = f.name

    try:
        # Should return None when AST parsing fails
        result = _find_docstring_start_line(temp_file_path, "broken_syntax", 2)
        assert result is None, f"Expected None for invalid syntax, got {result}"

    finally:
        os.unlink(temp_file_path)
