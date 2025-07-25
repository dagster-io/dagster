"""Tests for file-relative line number reporting in docstring validation."""

from automation.docstring_lint.validator import DocstringValidator


class TestFileRelativeLineNumbers:
    """Test that validation reports file-relative line numbers, not docstring-relative."""

    def test_validate_symbol_reports_file_relative_line_numbers(self):
        """Test that when validating a symbol, line numbers are relative to the file, not the docstring."""
        validator = DocstringValidator()

        # Test with AssetKey which has "Argsz:" on line 48 of the file
        # The docstring starts around line 34, so "Argsz:" is at docstring line ~15
        # But we want the error to report line 48 (file-relative)
        result = validator.validate_symbol_docstring("dagster.AssetKey")

        assert result.has_errors()

        # Find the error about "Argsz:"
        section_error = None
        for error in result.errors:
            if "Argsz:" in error and "Args:" in error:
                section_error = error
                break

        assert section_error is not None, f"Expected error about 'Argsz:' but got: {result.errors}"

        # The error should contain "(line 48)" not "(line 15)" or similar docstring-relative number
        assert "(line 48)" in section_error, (
            f"Expected '(line 48)' in error, but got: {section_error}"
        )

    def test_validate_docstring_text_with_symbol_info_reports_file_relative_lines(self):
        """Test validate_docstring_text when provided with symbol location info."""
        validator = DocstringValidator()

        # Create a docstring with an error - simpler format that will trigger section header error
        docstring = """This is a test function.

Argsz:
    param: Description"""

        # If the docstring starts at line 10 in a file, then the error on docstring line 3
        # should be reported as file line 12 (10 + 3 - 1, since docstring line 1 is file line 10)
        result = validator.validate_docstring_text(
            docstring, "test.symbol", docstring_start_line=10
        )

        assert result.has_errors()

        # Find the section header error
        section_error = None
        for error in result.errors:
            if "Argsz:" in error:
                section_error = error
                break

        assert section_error is not None, f"Expected error about 'Argsz:' but got: {result.errors}"

        # Should report line 12 (file-relative), not line 3 (docstring-relative)
        assert "(line 12)" in section_error, (
            f"Expected '(line 12)' in error, but got: {section_error}"
        )

    def test_validate_docstring_text_without_symbol_info_reports_docstring_relative_lines(self):
        """Test that validate_docstring_text without symbol info still works with docstring-relative lines."""
        validator = DocstringValidator()

        # Create a docstring with an error on line 3 of the docstring
        docstring = """This is a test function.

Argsz:
    param: Description"""

        # When no docstring_start_line is provided, should fall back to docstring-relative
        result = validator.validate_docstring_text(docstring, "test.symbol")

        assert result.has_errors()

        # Find the section header error
        section_error = None
        for error in result.errors:
            if "Argsz:" in error:
                section_error = error
                break

        assert section_error is not None, f"Expected error about 'Argsz:' but got: {result.errors}"

        # Should report line 3 (docstring-relative) since no start line was provided
        assert "(line 3)" in section_error, (
            f"Expected '(line 3)' in error, but got: {section_error}"
        )

    def test_multiple_errors_all_use_file_relative_lines(self):
        """Test that multiple errors in a docstring all use file-relative line numbers."""
        validator = DocstringValidator()

        # Create a docstring with multiple errors
        docstring = """This is a test function.

Argsz:
    param: Description
    
Returnz:
    Description"""

        # If docstring starts at file line 20
        result = validator.validate_docstring_text(
            docstring, "test.symbol", docstring_start_line=20
        )

        assert result.has_errors()
        assert len(result.errors) >= 2

        # Check that errors have file-relative line numbers
        error_lines = []
        for error in result.errors:
            if "(line " in error:
                line_part = error.split("(line ")[1].split(")")[0]
                error_lines.append(int(line_part))

        # Should have file-relative line numbers (20+3-1=22, 20+6-1=25)
        assert 22 in error_lines, f"Expected line 22 in errors, got lines: {error_lines}"
        assert 25 in error_lines, f"Expected line 25 in errors, got lines: {error_lines}"
