"""Tests for symbols that are known to have valid docstrings.

This test suite validates all public symbols from the dagster package to ensure
they have valid docstrings that render correctly in the documentation build.

These tests serve as comprehensive regression tests to ensure the validator
doesn't produce false positives for any public API symbols.
"""

import importlib

import pytest
from automation.docstring_lint.validator import DocstringValidator

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
    "dagster.sys",  # Import issue (conflicts with built-in sys)
}


def _get_all_dagster_public_symbols():
    """Get all public symbols from the dagster package."""
    dagster_module = importlib.import_module("dagster")
    public_symbols = [name for name in dir(dagster_module) if not name.startswith("_")]
    return [f"dagster.{name}" for name in sorted(public_symbols)]


class TestKnownValidSymbols:
    """Test symbols that are known to have valid docstrings."""

    @pytest.fixture
    def validator(self):
        """Provide a DocstringValidator instance for tests."""
        return DocstringValidator()

    @pytest.mark.parametrize("symbol_path", _get_all_dagster_public_symbols())
    def test_all_public_symbol_docstrings(self, validator, symbol_path):
        """Test that all public dagster symbols have valid docstrings.

        This test validates every public symbol in the dagster package to ensure:
        1. The symbol can be imported successfully
        2. The docstring has valid RST/Google-style formatting (unless in skip list)
        3. No syntax errors that would break documentation builds

        Symbols with known docstring issues are maintained in SYMBOLS_WITH_KNOWN_DOCSTRING_ISSUES
        and should be addressed in separate PRs.

        Args:
            validator: DocstringValidator instance
            symbol_path: Dotted path to the symbol to test
        """
        # Skip validation for symbols with known issues - check before validation
        # to avoid import errors for symbols that are known to be problematic
        if symbol_path in SYMBOL_EXCLUDE_LIST:
            print(f"Skipping known problematic symbol: {symbol_path}")  # noqa: T201
            return

        result = validator.validate_symbol_docstring(symbol_path)

        # The symbol should be importable - this is the core requirement
        assert result.parsing_successful, f"Failed to parse {symbol_path}: {result.errors}"

        # All symbols should have valid docstrings
        assert result.is_valid(), (

            f"Symbol {symbol_path} should have valid docstring but got errors: {result.errors}. "
            f"If this is a known issue, add it to SYMBOL_EXCLUDE_LIST."

        )

        # Log warnings for awareness
        if result.has_warnings():
            print(f"Docstring warnings for {symbol_path}: {result.warnings}")  # noqa: T201

    def test_nonexistent_symbol_produces_error(self, validator):
        """Test that attempting to validate a non-existent symbol produces an error."""
        result = validator.validate_symbol_docstring("dagster.nonexistent_symbol_name")

        assert not result.parsing_successful
        assert result.has_errors()
        assert "Failed to import symbol" in result.errors[0]
        assert not result.is_valid()

    def test_symbol_with_no_docstring(self, validator):
        """Test that symbols without docstrings produce warnings but are still valid."""
        # Most internal symbols don't have docstrings, which should produce a warning
        # but not an error (since missing docstrings don't break the docs build)
        result = validator.validate_symbol_docstring("dagster._utils")  # Internal module

        # Should be importable
        assert result.parsing_successful

        # Should have a warning about missing docstring
        assert result.has_warnings()

        # Should still be considered valid (warnings don't fail validation)
        assert result.is_valid()


class TestDocstringTextValidation:
    """Test validation of raw docstring text."""

    @pytest.fixture
    def validator(self):
        """Provide a DocstringValidator instance for tests."""
        return DocstringValidator()

    def test_valid_google_style_docstring(self, validator):
        """Test that a well-formed Google-style docstring validates successfully."""
        docstring = '''"""Create a definition for how to compute an asset.

        A software-defined asset is the combination of an asset key, a function,
        and a set of upstream assets that are provided as inputs.

        Args:
            name (Optional[str]): The name of the asset. If not provided, defaults
                to the name of the decorated function.
            key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's
                key is the concatenation of the key_prefix and the asset's name.
            metadata (Optional[Dict[str, Any]]): A dict of metadata entries for the asset.

        Returns:
            AssetsDefinition: The asset definition.

        Examples:
            .. code-block:: python

                @asset
                def my_asset():
                    return 5
        """'''

        result = validator.validate_docstring_text(docstring, "test.function")

        assert result.is_valid()
        assert not result.has_errors()
        # May have warnings but that's OK for a valid docstring

    def test_docstring_with_sphinx_roles(self, validator):
        """Test that docstrings using Sphinx roles are handled correctly."""
        docstring = '''"""A function that references other symbols.

        This function uses :py:class:`SomeClass` and calls :func:`other_function`.
        See also :py:meth:`SomeClass.method` for more details.

        Args:
            param: A parameter of type :py:class:`SomeType`.

        Returns:
            An instance of :py:class:`ReturnType`.
        """'''

        result = validator.validate_docstring_text(docstring, "test.function")

        # Should not have errors because Sphinx roles are filtered out
        assert result.is_valid()
        assert not result.has_errors()

    def test_docstring_with_literalinclude_directive(self, validator):
        """Test that docstrings using literalinclude directive are handled correctly."""
        docstring = '''"""Configuration for DagsterInstance.

        Example configuration:

        .. literalinclude:: ../config/dagster.yaml
           :caption: dagster.yaml
           :language: YAML

        The configuration includes various settings.
        """'''

        result = validator.validate_docstring_text(docstring, "test.class")

        # Should not have errors because literalinclude directive is filtered out
        assert result.is_valid()
        assert not result.has_errors()
