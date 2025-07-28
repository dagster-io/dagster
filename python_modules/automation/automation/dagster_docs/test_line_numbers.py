"""Tests for line number reporting in docstring validation.

These tests verify that error messages report line numbers relative to the file,
not relative to the start of the docstring, and include the filename.
"""

from automation.dagster_docs.validator import validate_docstring_text


def test_line_numbers_are_file_relative():
    """Test that line numbers in error messages are relative to the file."""
    # Import the sample functions to get their actual file line numbers
    import inspect

    from automation.dagster_docs.test_sample_code import function_with_bad_rst

    # Get the actual line numbers where docstrings start
    bad_rst_start_line = inspect.getsourcelines(function_with_bad_rst)[1]

    # Test function_with_bad_rst
    file_path = inspect.getfile(function_with_bad_rst)
    result = validate_docstring_text(
        inspect.getdoc(function_with_bad_rst),
        "test_sample_code.function_with_bad_rst",
        file_path=file_path,
        docstring_start_line=bad_rst_start_line + 1,  # Docstring starts line after function def
    )

    # Should have errors or warnings and they should reference file line numbers
    assert result.has_errors() or result.has_warnings()

    # Find error mentioning the unclosed backtick or inline interpreted text issue
    rst_error = None
    for error in result.errors:
        if (
            "backtick" in error.lower()
            or "unclosed" in error.lower()
            or "interpreted text" in error.lower()
        ):
            rst_error = error
            break

    # If no errors, check warnings (RST issues might be warnings)
    if rst_error is None:
        for warning in result.warnings:
            if (
                "backtick" in warning.lower()
                or "unclosed" in warning.lower()
                or "interpreted text" in warning.lower()
            ):
                rst_error = warning
                break

    assert rst_error is not None, (
        f"Expected RST error/warning, got errors: {result.errors}, warnings: {result.warnings}"
    )

    # The error should mention a line number that's relative to the file
    # The RST parser reported line 3 in the docstring, which should be converted to the correct file line
    # Just check that we have a reasonable file line number and filename format
    assert "test_sample_code.py:line " in rst_error, (
        f"Expected test_sample_code.py:line format in error: {rst_error}"
    )

    # Extract the line number and verify it's reasonable (should be >= function start line)
    start = rst_error.find("test_sample_code.py:line ") + len("test_sample_code.py:line ")
    end = rst_error.find(")", start)
    actual_line = int(rst_error[start:end])
    assert actual_line >= bad_rst_start_line, (
        f"Line number {actual_line} should be >= function start {bad_rst_start_line}"
    )


def test_multiple_errors_have_correct_line_numbers():
    """Test that multiple errors in the same docstring have correct line numbers."""
    import inspect

    from automation.dagster_docs.test_sample_code import function_with_multiple_errors

    start_line = inspect.getsourcelines(function_with_multiple_errors)[1]
    file_path = inspect.getfile(function_with_multiple_errors)

    result = validate_docstring_text(
        inspect.getdoc(function_with_multiple_errors),
        "test_sample_code.function_with_multiple_errors",
        file_path=file_path,
        docstring_start_line=start_line + 1,  # Docstring starts line after function def
    )

    assert result.has_errors() or result.has_warnings()

    # Should have multiple errors/warnings with different line numbers
    line_numbers_found = []
    all_messages = result.errors + result.warnings
    for message in all_messages:
        if "test_sample_code.py:line " in message:
            # Extract line number from error message (new format: filename:line N)
            start = message.find("test_sample_code.py:line ") + len("test_sample_code.py:line ")
            end = message.find(")", start)
            line_num = int(message[start:end])
            line_numbers_found.append(line_num)

    # Should have found multiple different line numbers
    assert len(line_numbers_found) >= 2, (
        f"Expected multiple line numbers, got: {line_numbers_found}"
    )

    # All line numbers should be >= the start of the function
    for line_num in line_numbers_found:
        assert line_num >= start_line, (
            f"Line number {line_num} should be >= function start {start_line}"
        )


def test_section_header_errors_have_correct_line_numbers():
    """Test that section header errors report correct file-relative line numbers."""
    import inspect

    from automation.dagster_docs.test_sample_code import function_with_bad_section_header

    start_line = inspect.getsourcelines(function_with_bad_section_header)[1]
    file_path = inspect.getfile(function_with_bad_section_header)

    result = validate_docstring_text(
        inspect.getdoc(function_with_bad_section_header),
        "test_sample_code.function_with_bad_section_header",
        file_path=file_path,
        docstring_start_line=start_line + 1,  # Docstring starts line after function def
    )

    assert result.has_errors()

    # Look for section header errors
    section_errors = [error for error in result.errors if "section" in error.lower()]
    assert len(section_errors) >= 1, f"Expected section header errors, got: {result.errors}"

    # Check that errors have line numbers and filenames
    for error in section_errors:
        assert "test_sample_code.py:line " in error, (
            f"Error should have filename:line format: {error}"
        )

        # Extract and validate line number (new format: filename:line N)
        start = error.find("test_sample_code.py:line ") + len("test_sample_code.py:line ")
        end = error.find(")", start)
        line_num = int(error[start:end])
        assert line_num >= start_line, (
            f"Line number {line_num} should be >= function start {start_line}"
        )


def test_good_function_has_no_errors():
    """Test that a function with a good docstring has no errors."""
    import inspect

    from automation.dagster_docs.test_sample_code import good_function

    file_path = inspect.getfile(good_function)
    start_line = inspect.getsourcelines(good_function)[1]
    result = validate_docstring_text(
        inspect.getdoc(good_function),
        "test_sample_code.good_function",
        file_path=file_path,
        docstring_start_line=start_line + 1,
    )

    assert not result.has_errors(), f"Good function should have no errors, got: {result.errors}"
    assert result.is_valid(), "Good function should be valid"
