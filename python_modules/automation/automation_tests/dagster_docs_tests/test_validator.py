"""Tests for the docstring validator core functionality."""

from automation.dagster_docs.validator import (
    ValidationResult,
    validate_docstring_text,
    validate_symbol_docstring,
)


class TestValidationResult:
    """Test ValidationResult record functionality."""

    def test_create_validation_result(self):
        result = ValidationResult.create("test.symbol")
        assert result.symbol_path == "test.symbol"
        assert result.errors == []
        assert result.warnings == []
        assert result.parsing_successful is True

    def test_with_error(self):
        result = ValidationResult.create("test.symbol")
        result_with_error = result.with_error("Test error")

        # Original result unchanged (immutable)
        assert result.errors == []

        # New result has error
        assert result_with_error.errors == ["Test error"]
        assert result_with_error.warnings == []
        assert result_with_error.parsing_successful is True

    def test_with_error_line_number(self):
        result = ValidationResult.create("test.symbol")
        result_with_error = result.with_error("Test error", line_number=42)

        assert result_with_error.errors == ["Test error (line 42)"]

    def test_with_warning(self):
        result = ValidationResult.create("test.symbol")
        result_with_warning = result.with_warning("Test warning")

        # Original result unchanged (immutable)
        assert result.warnings == []

        # New result has warning
        assert result_with_warning.errors == []
        assert result_with_warning.warnings == ["Test warning"]
        assert result_with_warning.parsing_successful is True

    def test_with_parsing_failed(self):
        result = ValidationResult.create("test.symbol")
        result_failed = result.with_parsing_failed()

        # Original result unchanged (immutable)
        assert result.parsing_successful is True

        # New result has parsing failed
        assert result_failed.parsing_successful is False

    def test_chaining_operations(self):
        result = (
            ValidationResult.create("test.symbol")
            .with_error("Error 1")
            .with_warning("Warning 1")
            .with_error("Error 2")
            .with_parsing_failed()
        )

        assert result.errors == ["Error 1", "Error 2"]
        assert result.warnings == ["Warning 1"]
        assert result.parsing_successful is False

    def test_has_errors(self):
        result = ValidationResult.create("test.symbol")
        assert not result.has_errors()

        result_with_error = result.with_error("Test error")
        assert result_with_error.has_errors()

    def test_has_warnings(self):
        result = ValidationResult.create("test.symbol")
        assert not result.has_warnings()

        result_with_warning = result.with_warning("Test warning")
        assert result_with_warning.has_warnings()

    def test_is_valid(self):
        result = ValidationResult.create("test.symbol")
        assert result.is_valid()

        # Warnings don't make it invalid
        result_with_warning = result.with_warning("Test warning")
        assert result_with_warning.is_valid()

        # Errors make it invalid
        result_with_error = result.with_error("Test error")
        assert not result_with_error.is_valid()

        # Parsing failed makes it invalid
        result_failed = result.with_parsing_failed()
        assert not result_failed.is_valid()


class TestDocstringValidator:
    """Test DocstringValidator functionality."""

    def test_empty_docstring(self):
        result = validate_docstring_text("", "test.symbol")

        assert result.symbol_path == "test.symbol"
        assert result.has_warnings()
        assert "No docstring found" in result.warnings[0]
        assert result.is_valid()  # Empty docstring is valid (just warning)

    def test_simple_valid_docstring(self):
        docstring = "This is a simple docstring."
        result = validate_docstring_text(docstring, "test.symbol")

        assert result.symbol_path == "test.symbol"
        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.is_valid()

    def test_google_style_docstring(self):
        docstring = '''"""Function with Google-style docstring.

        Args:
            param1: Description of param1
            param2: Description of param2

        Returns:
            Description of return value

        Examples:
            >>> example_call()
            'result'
        """'''
        result = validate_docstring_text(docstring, "test.symbol")

        assert result.symbol_path == "test.symbol"
        assert not result.has_errors()
        assert result.is_valid()

    def test_malformed_section_header(self):
        docstring = '''"""Function with malformed section header.

        arguments:  # Should be "Args:"
            param1: Description
        """'''
        result = validate_docstring_text(docstring, "test.symbol")

        assert result.symbol_path == "test.symbol"
        assert result.has_warnings()
        # The validator may detect RST issues or section header issues
        warning_text = " ".join(result.warnings).lower()
        assert "malformed section header" in warning_text or "rst syntax" in warning_text, (
            f"Expected section or RST warning, got: {result.warnings}"
        )
        assert result.is_valid()  # Warnings don't make it invalid

    def test_import_symbol_success(self):
        # Test importing a built-in symbol
        result = validate_symbol_docstring("builtins.len")

        assert result.symbol_path == "builtins.len"
        assert result.is_valid()  # len function should have a valid docstring

    def test_import_symbol_failure(self):
        # Test importing a non-existent symbol
        result = validate_symbol_docstring("nonexistent.module.symbol")

        assert result.symbol_path == "nonexistent.module.symbol"
        assert result.has_errors()
        assert "Failed to import symbol" in result.errors[0]
        assert not result.is_valid()

    def test_sphinx_role_filtering(self):
        docstring = '''"""Function using Sphinx roles.

        See :py:class:`SomeClass` and :func:`some_function`.
        """'''
        result = validate_docstring_text(docstring, "test.symbol")

        # Should not have errors because Sphinx roles are filtered out
        assert not result.has_errors()
        assert result.is_valid()

    def test_no_false_positive_for_words_ending_with_period(self):
        """Test that words ending with period (like 'returned.') don't trigger section header warnings."""
        docstring = '''"""Function that explains return behavior.

        Args:
            output_required: Whether the function will always materialize an asset.
                If False, the function can conditionally not yield a result. 
                Note that you must use yield rather than return. return will not respect
                this setting and will always produce an asset materialization, even if None is
                returned.
        """'''
        result = validate_docstring_text(docstring, "test.symbol")

        # Should not have warnings/errors about 'returned.' being a malformed section header
        # Check that no warnings contain section header related messages
        section_header_warnings = [
            w
            for w in result.warnings
            if "malformed section header" in w.lower()
            or "possible malformed section header" in w.lower()
        ]
        section_header_errors = [
            e
            for e in result.errors
            if "malformed section header" in e.lower()
            or "possible malformed section header" in e.lower()
        ]

        assert not section_header_warnings, (
            f"Unexpected section header warnings: {section_header_warnings}"
        )
        assert not section_header_errors, (
            f"Unexpected section header errors: {section_header_errors}"
        )
        assert result.is_valid()

    def test_validates_fix_for_dagster_asset_specific_case(self):
        """Test the specific case from dagster.asset that was causing the false positive."""
        # This is the exact text pattern that was causing the issue
        docstring = '''"""Function with similar pattern to dagster.asset.

        Args:
            output_required: Whether the function will always materialize an asset.
                Defaults to True. If False, the function can conditionally not yield a result.
                If no result is yielded, no output will be materialized to storage and downstream
                assets will not be materialized. Note that for output_required to work at all, you
                must use yield in your asset logic rather than return. return will not respect
                this setting and will always produce an asset materialization, even if None is
                returned.
        """'''
        result = validate_docstring_text(docstring, "test.symbol")

        # The specific fix: should not flag "returned." as a malformed section header
        section_header_warnings = [
            w
            for w in result.warnings
            if "malformed section header" in w.lower() and "returned" in w.lower()
        ]
        section_header_errors = [
            e
            for e in result.errors
            if "malformed section header" in e.lower() and "returned" in e.lower()
        ]

        assert not section_header_warnings, (
            f"Should not flag 'returned.' as malformed: {section_header_warnings}"
        )
        assert not section_header_errors, (
            f"Should not flag 'returned.' as malformed: {section_header_errors}"
        )
        assert result.is_valid()
