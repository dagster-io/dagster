"""Tests for file-relative line number reporting in docstring validation."""

import tempfile
import textwrap
from pathlib import Path

from automation.docstring_lint.validator import DocstringValidator


class TestFileLineNumbers:
    """Test that validation errors report file-relative line numbers."""

    def test_section_header_error_reports_file_line_number(self):
        """Test that section header errors report line numbers relative to the file, not the docstring."""
        # Create a temporary Python file with a function that has a malformed section header
        test_code = textwrap.dedent('''
            """Module docstring."""

            def example_function(param1, param2):
                """Function with malformed section header.

                This function demonstrates the line number issue.

                arguments:
                    param1: Description of param1
                    param2: Description of param2

                Returns:
                    Description of return value
                """
                return param1 + param2
        ''').strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()
            temp_file_path = f.name

        try:
            # Create a validator and validate the docstring
            validator = DocstringValidator()

            # Extract the docstring manually to simulate what the validator does
            docstring = """Function with malformed section header.

                This function demonstrates the line number issue.

                arguments:
                    param1: Description of param1
                    param2: Description of param2

                Returns:
                    Description of return value"""

            result = validator.validate_docstring_text(docstring, "test.example_function")

            # Find the error about the malformed section header
            section_header_errors = [
                error
                for error in result.errors
                if "Malformed section header" in error and "arguments" in error
            ]

            assert len(section_header_errors) == 1, (
                f"Expected exactly one section header error, got: {result.errors}"
            )

            error_message = section_header_errors[0]

            # The line number should be 9 (relative to the file), not 5 (relative to the docstring)
            # Currently this will fail because it reports line 5 (docstring-relative)
            # After the fix, it should report line 9 (file-relative)
            assert "(line 9)" in error_message, (
                f"Expected file-relative line number 9, got: {error_message}"
            )

            # This assertion will currently fail - that's expected for this test
            assert "(line 5)" not in error_message, (
                f"Should not report docstring-relative line number, got: {error_message}"
            )

        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    def test_multiple_errors_report_correct_file_line_numbers(self):
        """Test that multiple validation errors report correct file-relative line numbers."""
        test_code = textwrap.dedent('''
            """Module docstring."""

            class ExampleClass:
                """Class with multiple docstring issues.

                Some description here.

                arguments:
                    param1: Description

                returns:  # Error on line 11 of file  
                    Description of return value
                """
                
                def method(self, param1):
                    return param1
        ''').strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()
            temp_file_path = f.name

        try:
            validator = DocstringValidator()

            # Extract the docstring manually
            docstring = """Class with multiple docstring issues.

                Some description here.

                arguments:
                    param1: Description

                returns:  # Error on line 11 of file  
                    Description of return value"""

            result = validator.validate_docstring_text(docstring, "test.ExampleClass")

            # Should have two section header errors
            section_header_errors = [
                error for error in result.errors if "Malformed section header" in error
            ]

            assert len(section_header_errors) == 2, (
                f"Expected exactly two section header errors, got: {result.errors}"
            )

            # Check that the errors reference the correct file line numbers
            arguments_errors = [e for e in section_header_errors if "arguments" in e]
            returns_errors = [e for e in section_header_errors if "returns" in e]

            assert len(arguments_errors) == 1, (
                f"Expected one arguments error, got: {arguments_errors}"
            )
            assert len(returns_errors) == 1, f"Expected one returns error, got: {returns_errors}"

            # These assertions will currently fail - that's expected
            assert "(line 8)" in arguments_errors[0], (
                f"Expected arguments error at file line 8, got: {arguments_errors[0]}"
            )
            assert "(line 11)" in returns_errors[0], (
                f"Expected returns error at file line 11, got: {returns_errors[0]}"
            )

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_symbol_validation_with_file_line_numbers(self):
        """Test that validate_symbol_docstring reports file-relative line numbers."""
        # This test will use the actual AssetKey that has the "Argsz:" error
        validator = DocstringValidator()
        result = validator.validate_symbol_docstring("dagster.AssetKey")

        # Find the section header error for "Argsz:"
        section_header_errors = [
            error
            for error in result.errors
            if "Malformed section header" in error and "arguments" in error
        ]

        if section_header_errors:
            error_message = section_header_errors[0]
            # Should report line 48 (the actual file line), not line 15 (docstring-relative)
            assert "(line 48)" in error_message, f"Expected file line 48, got: {error_message}"
            assert "(line 15)" not in error_message, (
                f"Should not report docstring-relative line, got: {error_message}"
            )
