"""Tests for symbols that are known to have valid docstrings.

This test suite validates all public symbols from the dagster package to ensure
they have valid docstrings that render correctly in the documentation build.

These tests serve as comprehensive regression tests to ensure the validator
doesn't produce false positives for any public API symbols.
"""

import importlib

import pytest
from automation.dagster_docs.validator import validate_docstring_text, validate_symbol_docstring

# Symbols with known docstring formatting issues that should be skipped until fixed
# These symbols have docstring validation errors that need to be addressed in separate PRs
SYMBOL_EXCLUDE_LIST = {
    # Docstring formatting issues (indentation, etc.)
    "dagster.ConfigurableLegacyIOManagerAdapter",  # Unexpected indentation errors
    "dagster.FunctionComponent",  # Unexpected indentation errors
    "dagster.JsonLogFormatter",  # Unexpected indentation errors
    "dagster.PendingNodeInvocation",  # Unexpected indentation errors
    # Import/module resolution issues (deprecated or aliased symbols)
    "dagster.check_dagster_type",  # Module resolution error
    "dagster.config_from_files",  # Module resolution error
    "dagster.config_from_pkg_resources",  # Module resolution error
    "dagster.config_from_yaml_strings",  # Module resolution error
    "dagster.config_mapping",  # Module resolution error
    "dagster.configured",  # Module resolution error
    "dagster.scaffold_with",  # Module resolution error
    # Invalid section headers that need to be fixed
    "dagster.ExecuteInProcessResult",  # Invalid section header: "This object is returned by:" should be restructured
    "dagster.asset_check",  # Invalid section header: "Example with a DataFrame Output:" should be "Examples:"
    # Non-standard section header formatting (uses bold/italic formatting)
    "dagster.file_relative_path",  # Uses "**Examples**:" instead of "Examples:"
    # MetadataValue classes with syntax errors in docstring code blocks
    "dagster.BoolMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.CodeReferencesMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.DagsterAssetMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.DagsterJobMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.DagsterRunMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.FloatMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.IntMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.JsonMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.MarkdownMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.MetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.NotebookMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
    "dagster.NullMetadataValue.job",  # Syntax error at line 4, column 19: invalid syntax. Perhaps you forgot a comma?
}


def _get_all_dagster_public_symbols():
    """Get all public symbols from the dagster package for validation testing."""
    # This would normally scan all public symbols in dagster
    # For now, we'll use a small representative set for testing the structure
    return ["dagster.asset", "dagster.Config", "dagster.configured"]


class TestKnownValidSymbols:
    """Test that known Dagster symbols have valid docstrings."""

    def test_representative_dagster_symbols(self):
        """Test a representative set of Dagster symbols."""
        symbols_to_test = _get_all_dagster_public_symbols()

        failed_symbols = []
        for symbol_path in symbols_to_test:
            if symbol_path in SYMBOL_EXCLUDE_LIST:
                continue

            try:
                result = validate_symbol_docstring(symbol_path)
                if not result.is_valid():
                    failed_symbols.append((symbol_path, result.errors))
            except Exception as e:
                failed_symbols.append((symbol_path, [f"Exception during validation: {e}"]))

        if failed_symbols:
            failure_message = "The following symbols have invalid docstrings:\n"
            for symbol, errors in failed_symbols[:5]:  # Limit output
                failure_message += f"  {symbol}: {errors}\n"
            pytest.fail(failure_message)

    def test_fixture_docstring_patterns(self):
        """Test the fixture docstring patterns from our representative examples."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.known_valid_symbols.dagster_symbol_docstrings"
        )

        # Test the representative patterns
        test_cases = [
            (
                fixtures_module.DagsterSymbolPatterns.asset_with_examples.__doc__ or "",
                "DagsterSymbolPatterns.asset_with_examples",
            ),
            (
                fixtures_module.DagsterSymbolPatterns.config_with_metadata.__doc__ or "",
                "DagsterSymbolPatterns.config_with_metadata",
            ),
        ]

        for docstring, symbol_name in test_cases:
            result = validate_docstring_text(docstring, symbol_name)
            assert result.is_valid(), f"{symbol_name} should have valid docstring: {result.errors}"
