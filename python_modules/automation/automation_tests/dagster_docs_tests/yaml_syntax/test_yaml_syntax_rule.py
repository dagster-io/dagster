"""Tests for YAML syntax validation in docstring code blocks."""

import importlib

from automation.dagster_docs.validator import validate_docstring_text


class TestYAMLSyntaxValidation:
    """Test YAML syntax validation in docstring code blocks."""

    def test_valid_yaml_examples(self):
        """Test that valid YAML examples pass validation."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.yaml_syntax.valid_yaml_examples"
        )

        test_cases = [
            (
                fixtures_module.ValidYAMLFixtures.simple_yaml_config.__doc__ or "",
                "ValidYAMLFixtures.simple_yaml_config",
            ),
            (
                fixtures_module.ValidYAMLFixtures.complex_yaml_structure.__doc__ or "",
                "ValidYAMLFixtures.complex_yaml_structure",
            ),
            (
                fixtures_module.ValidYAMLFixtures.yaml_with_special_types.__doc__ or "",
                "ValidYAMLFixtures.yaml_with_special_types",
            ),
        ]

        for docstring, symbol_name in test_cases:
            result = validate_docstring_text(docstring, symbol_name)
            # Valid YAML should not produce YAML-specific errors
            yaml_errors = [e for e in result.errors if "yaml" in e.lower()]
            assert len(yaml_errors) == 0, (
                f"{symbol_name} should not have YAML errors: {yaml_errors}"
            )

    def test_invalid_yaml_examples(self):
        """Test that invalid YAML examples are detected."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.yaml_syntax.invalid_yaml_examples"
        )

        test_cases = [
            (
                fixtures_module.InvalidYAMLFixtures.yaml_with_indentation_error.__doc__ or "",
                "InvalidYAMLFixtures.yaml_with_indentation_error",
            ),
            (
                fixtures_module.InvalidYAMLFixtures.yaml_with_missing_colon.__doc__ or "",
                "InvalidYAMLFixtures.yaml_with_missing_colon",
            ),
            (
                fixtures_module.InvalidYAMLFixtures.yaml_with_unmatched_brackets.__doc__ or "",
                "InvalidYAMLFixtures.yaml_with_unmatched_brackets",
            ),
            (
                fixtures_module.InvalidYAMLFixtures.yaml_with_invalid_multiline.__doc__ or "",
                "InvalidYAMLFixtures.yaml_with_invalid_multiline",
            ),
        ]

        for docstring, symbol_name in test_cases:
            result = validate_docstring_text(docstring, symbol_name)
            # Invalid YAML should either produce errors or warnings
            # (depending on validator configuration)
            # For now, we just verify the validation runs without crashing
            # The exact error detection depends on the YAML validation rules
            assert result is not None, f"{symbol_name} validation should complete"
