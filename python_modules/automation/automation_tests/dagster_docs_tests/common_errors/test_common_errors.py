"""Tests for common docstring errors that should be caught by the validator.

This test suite validates that the docstring validator correctly identifies
common mistakes when writing Google-style docstrings and RST syntax errors.
These tests ensure the validator catches issues that would break documentation
builds or result in poor rendering.
"""

import importlib

from automation.dagster_docs.validator import validate_docstring_text


class TestSectionHeaderErrors:
    """Test detection of incorrect section headers."""

    def test_incorrect_section_capitalization(self):
        """Test detection of incorrectly capitalized section headers."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.section_header_errors"
        )

        result = validate_docstring_text(
            fixtures_module.SectionHeaderErrorFixtures.incorrect_capitalization.__doc__ or "",
            "SectionHeaderErrorFixtures.incorrect_capitalization",
        )

        # Should detect malformed section headers
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "malformed section header" in messages or "rst syntax" in messages

    def test_missing_colon_in_section_header(self):
        """Test detection of section headers missing colons."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.section_header_errors"
        )

        result = validate_docstring_text(
            fixtures_module.SectionHeaderErrorFixtures.missing_colons.__doc__ or "",
            "SectionHeaderErrorFixtures.missing_colons",
        )

        # Should detect RST syntax errors for malformed headers
        assert result.has_warnings() or result.has_errors()

    def test_incorrect_section_names(self):
        """Test detection of common incorrect section names."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.section_header_errors"
        )

        result = validate_docstring_text(
            fixtures_module.SectionHeaderErrorFixtures.incorrect_section_names.__doc__ or "",
            "SectionHeaderErrorFixtures.incorrect_section_names",
        )

        # Should detect malformed section headers
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "malformed section header" in messages or "rst syntax" in messages

    def test_double_colon_section_headers(self):
        """Test detection of section headers with double colons."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.section_header_errors"
        )

        result = validate_docstring_text(
            fixtures_module.SectionHeaderErrorFixtures.double_colon_headers.__doc__ or "",
            "SectionHeaderErrorFixtures.double_colon_headers",
        )

        # Should detect RST syntax issues
        assert result.has_warnings() or result.has_errors()


class TestIndentationErrors:
    """Test detection of incorrect indentation in docstrings."""

    def test_incorrect_parameter_indentation(self):
        """Test detection of incorrect parameter description indentation."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.indentation_errors"
        )

        result = validate_docstring_text(
            fixtures_module.IndentationErrorFixtures.incorrect_parameter_indentation.__doc__ or "",
            "IndentationErrorFixtures.incorrect_parameter_indentation",
        )

        # Should detect indentation issues in RST processing
        assert result.has_warnings() or result.has_errors()

    def test_mixed_indentation_levels(self):
        """Test detection of mixed indentation levels."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.indentation_errors"
        )

        result = validate_docstring_text(
            fixtures_module.IndentationErrorFixtures.mixed_indentation_levels.__doc__ or "",
            "IndentationErrorFixtures.mixed_indentation_levels",
        )

        # Should detect indentation inconsistencies
        assert result.has_warnings() or result.has_errors()

    def test_section_content_not_indented(self):
        """Test detection of section content that's not properly indented."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.indentation_errors"
        )

        result = validate_docstring_text(
            fixtures_module.IndentationErrorFixtures.section_content_not_indented.__doc__ or "",
            "IndentationErrorFixtures.section_content_not_indented",
        )

        # Should detect indentation issues
        assert result.has_warnings() or result.has_errors()


class TestParameterDescriptionErrors:
    """Test detection of malformed parameter descriptions."""

    def test_missing_parameter_descriptions(self):
        """Test detection of parameters without descriptions."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.parameter_errors"
        )

        result = validate_docstring_text(
            fixtures_module.ParameterErrorFixtures.missing_parameter_descriptions.__doc__ or "",
            "ParameterErrorFixtures.missing_parameter_descriptions",
        )

        # This might produce warnings but shouldn't break validation
        # The function should still be considered valid for RST syntax
        assert result.parsing_successful

    def test_malformed_type_annotations(self):
        """Test detection of malformed type annotations in parameters."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.parameter_errors"
        )

        result = validate_docstring_text(
            fixtures_module.ParameterErrorFixtures.malformed_type_annotations.__doc__ or "",
            "ParameterErrorFixtures.malformed_type_annotations",
        )

        # Should detect RST syntax issues from malformed parentheses
        assert result.has_warnings() or result.has_errors()

    def test_inconsistent_parameter_format(self):
        """Test detection of inconsistent parameter formatting."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.parameter_errors"
        )

        result = validate_docstring_text(
            fixtures_module.ParameterErrorFixtures.inconsistent_parameter_format.__doc__ or "",
            "ParameterErrorFixtures.inconsistent_parameter_format",
        )

        # Should still be valid RST but may have warnings about formatting
        assert result.parsing_successful


class TestRSTSyntaxErrors:
    """Test detection of invalid RST syntax in docstrings."""

    def test_malformed_code_blocks(self):
        """Test detection of malformed code blocks."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.rst_syntax_errors"
        )

        result = validate_docstring_text(
            fixtures_module.RSTSyntaxErrorFixtures.malformed_code_blocks.__doc__ or "",
            "RSTSyntaxErrorFixtures.malformed_code_blocks",
        )

        # Should detect RST syntax error
        assert result.has_warnings() or result.has_errors()

    def test_misspelled_directive_name(self):
        """Test detection of misspelled directive names with correct syntax."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.rst_syntax_errors"
        )

        result = validate_docstring_text(
            fixtures_module.RSTSyntaxErrorFixtures.misspelled_directive_name.__doc__ or "",
            "RSTSyntaxErrorFixtures.misspelled_directive_name",
        )

        # Should detect unknown directive error
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "unknown directive" in messages or "code-kjdfkdblock" in messages

    def test_unmatched_backticks(self):
        """Test detection of unmatched backticks."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.rst_syntax_errors"
        )

        result = validate_docstring_text(
            fixtures_module.RSTSyntaxErrorFixtures.unmatched_backticks.__doc__ or "",
            "RSTSyntaxErrorFixtures.unmatched_backticks",
        )

        # Should detect RST markup errors
        assert result.has_warnings() or result.has_errors()

    def test_malformed_lists(self):
        """Test detection of malformed lists."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.rst_syntax_errors"
        )

        result = validate_docstring_text(
            fixtures_module.RSTSyntaxErrorFixtures.malformed_lists.__doc__ or "",
            "RSTSyntaxErrorFixtures.malformed_lists",
        )

        # Should detect list formatting issues
        assert result.has_warnings() or result.has_errors()

    def test_malformed_links(self):
        """Test detection of malformed links and references."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.rst_syntax_errors"
        )

        result = validate_docstring_text(
            fixtures_module.RSTSyntaxErrorFixtures.malformed_links.__doc__ or "",
            "RSTSyntaxErrorFixtures.malformed_links",
        )

        # Should detect link syntax errors
        assert result.has_warnings() or result.has_errors()


class TestStructuralErrors:
    """Test detection of structural issues in docstrings."""

    def test_empty_sections(self):
        """Test detection of empty sections."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.structural_errors"
        )

        result = validate_docstring_text(
            fixtures_module.StructuralErrorFixtures.empty_sections.__doc__ or "",
            "StructuralErrorFixtures.empty_sections",
        )

        # Should detect empty sections or comment-only content
        assert result.has_warnings() or result.has_errors()

    def test_duplicate_sections(self):
        """Test detection of duplicate sections."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.structural_errors"
        )

        result = validate_docstring_text(
            fixtures_module.StructuralErrorFixtures.duplicate_sections.__doc__ or "",
            "StructuralErrorFixtures.duplicate_sections",
        )

        # Should detect duplicate section headers
        assert result.has_warnings() or result.has_errors()

    def test_sections_in_wrong_order(self):
        """Test that unusual section ordering doesn't break parsing."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.structural_errors"
        )

        result = validate_docstring_text(
            fixtures_module.StructuralErrorFixtures.sections_in_wrong_order.__doc__ or "",
            "StructuralErrorFixtures.sections_in_wrong_order",
        )

        # Should still be valid RST (section order is not enforced by RST)
        assert result.parsing_successful


class TestComplexErrorCombinations:
    """Test combinations of multiple errors in single docstrings."""

    def test_multiple_error_types(self):
        """Test docstring with multiple types of errors."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.complex_error_combinations"
        )

        result = validate_docstring_text(
            fixtures_module.ComplexErrorCombinationFixtures.multiple_error_types.__doc__ or "",
            "ComplexErrorCombinationFixtures.multiple_error_types",
        )

        # Should detect multiple errors
        assert result.has_errors() or result.has_warnings()

        # Should have multiple error/warning messages
        total_issues = len(result.errors) + len(result.warnings)
        assert total_issues >= 2  # Should find multiple issues

    def test_nested_formatting_errors(self):
        """Test deeply nested formatting errors."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.common_errors.complex_error_combinations"
        )

        result = validate_docstring_text(
            fixtures_module.ComplexErrorCombinationFixtures.nested_formatting_errors.__doc__ or "",
            "ComplexErrorCombinationFixtures.nested_formatting_errors",
        )

        # Should detect multiple nested errors
        assert result.has_errors() or result.has_warnings()

        # Should find several issues
        total_issues = len(result.errors) + len(result.warnings)
        assert total_issues >= 3  # Should find multiple nested issues
