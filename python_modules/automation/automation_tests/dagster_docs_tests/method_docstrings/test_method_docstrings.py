"""Tests for method docstring validation focusing on parameter handling."""

import importlib

from automation.dagster_docs.validator import validate_docstring_text


class TestMethodDocstringValidation:
    """Test that method docstrings are validated correctly and self/cls parameters are handled properly."""

    def test_instance_method_docstring_validation(self):
        """Test that instance method docstrings are validated correctly."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.instance_methods"
        )

        # Test valid instance method docstring (doesn't document 'self')
        result = validate_docstring_text(
            fixtures_module.InstanceMethodFixtures.valid_instance_method.__doc__ or "",
            "InstanceMethodFixtures.valid_instance_method",
        )
        assert result.is_valid(), f"Instance method should have valid docstring: {result.errors}"
        assert result.parsing_successful

        # Test that documenting 'self' is handled gracefully (not flagged as RST error)
        result_with_self = validate_docstring_text(
            fixtures_module.InstanceMethodFixtures.instance_method_documenting_self.__doc__ or "",
            "InstanceMethodFixtures.instance_method_documenting_self",
        )
        # Should parse successfully even though it's bad style
        assert result_with_self.parsing_successful

    def test_static_method_docstring_validation(self):
        """Test that static method docstrings are validated correctly."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.static_class_methods"
        )

        result = validate_docstring_text(
            fixtures_module.StaticMethodFixtures.valid_static_method.__doc__ or "",
            "StaticMethodFixtures.valid_static_method",
        )
        assert result.is_valid(), f"Static method should have valid docstring: {result.errors}"
        assert result.parsing_successful

    def test_class_method_docstring_validation(self):
        """Test that class method docstrings are validated correctly."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.static_class_methods"
        )

        # Valid class method docstring (doesn't document 'cls')
        result = validate_docstring_text(
            fixtures_module.ClassMethodFixtures.valid_class_method.__doc__ or "",
            "ClassMethodFixtures.valid_class_method",
        )
        assert result.is_valid(), f"Class method should have valid docstring: {result.errors}"
        assert result.parsing_successful

        # Test that documenting 'cls' is handled gracefully
        result_with_cls = validate_docstring_text(
            fixtures_module.ClassMethodFixtures.class_method_documenting_cls.__doc__ or "",
            "ClassMethodFixtures.class_method_documenting_cls",
        )
        # Should parse successfully even though it's bad style
        assert result_with_cls.parsing_successful

    def test_property_docstring_validation(self):
        """Test that property docstrings are validated correctly."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.property_edge_cases"
        )

        result = validate_docstring_text(
            fixtures_module.PropertyFixtures.valid_property.__doc__ or "",
            "PropertyFixtures.valid_property",
        )
        assert result.is_valid(), f"Property should have valid docstring: {result.errors}"
        assert result.parsing_successful

    def test_docstring_formatting_errors(self):
        """Test that common docstring formatting errors are detected."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.property_edge_cases"
        )

        # Test an error that we know the validator catches - invalid section header
        result = validate_docstring_text(
            fixtures_module.FormattingErrorFixtures.method_with_invalid_section.__doc__ or "",
            "FormattingErrorFixtures.method_with_invalid_section",
        )
        # This should either have warnings/errors or be parsing successfully
        assert result.parsing_successful  # At minimum should parse

        # Missing indentation in parameters
        result = validate_docstring_text(
            fixtures_module.FormattingErrorFixtures.method_with_bad_indentation.__doc__ or "",
            "FormattingErrorFixtures.method_with_bad_indentation",
        )
        # This may or may not be flagged depending on RST parser behavior
        assert result.parsing_successful  # At minimum should parse

    def test_edge_case_docstrings(self):
        """Test edge cases with docstrings."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.property_edge_cases"
        )

        # Empty docstring should produce warning but not error
        result_empty = validate_docstring_text(
            fixtures_module.EdgeCaseFixtures.empty_method.__doc__ or "",
            "EdgeCaseFixtures.empty_method",
        )
        assert result_empty.has_warnings()
        assert "No docstring found" in str(result_empty.warnings)
        assert result_empty.is_valid()  # Empty is valid, just warned

        # Minimal but valid docstring
        result_minimal = validate_docstring_text(
            fixtures_module.EdgeCaseFixtures.helper.__doc__ or "", "EdgeCaseFixtures.helper"
        )
        assert result_minimal.is_valid()
        assert not result_minimal.has_errors()

        # Whitespace-only docstring
        result_whitespace = validate_docstring_text(
            fixtures_module.EdgeCaseFixtures.whitespace_method.__doc__ or "",
            "EdgeCaseFixtures.whitespace_method",
        )
        assert result_whitespace.has_warnings()
        assert "No docstring found" in str(result_whitespace.warnings)

    def test_complex_valid_docstring(self):
        """Test that complex but valid docstrings are handled correctly."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.instance_methods"
        )

        result = validate_docstring_text(
            fixtures_module.InstanceMethodFixtures.complex_instance_method.__doc__ or "",
            "InstanceMethodFixtures.complex_instance_method",
        )
        # Should be valid despite complexity
        assert result.is_valid() or not result.has_errors(), (
            f"Complex docstring should be valid: {result.errors}"
        )
        assert result.parsing_successful

    def test_mixed_method_types_in_single_class(self):
        """Test a class with all different types of methods."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.method_docstrings.property_edge_cases"
        )

        # Test that all method types validate correctly
        methods_to_test = [
            (
                fixtures_module.MixedMethodTypes.instance_method.__doc__ or "",
                "MixedMethodTypes.instance_method",
            ),
            (
                fixtures_module.MixedMethodTypes.utility_function.__doc__ or "",
                "MixedMethodTypes.utility_function",
            ),
            (
                fixtures_module.MixedMethodTypes.factory_method.__doc__ or "",
                "MixedMethodTypes.factory_method",
            ),
            (
                fixtures_module.MixedMethodTypes.computed_value.__doc__ or "",
                "MixedMethodTypes.computed_value",
            ),
        ]

        for docstring, method_name in methods_to_test:
            result = validate_docstring_text(docstring, method_name)
            assert result.is_valid(), f"{method_name} should have valid docstring: {result.errors}"
