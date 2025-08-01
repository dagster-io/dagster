"""Tests for symbols that are known to have valid docstrings.

This test suite validates all public symbols from the dagster package to ensure
they have valid docstrings that render correctly in the documentation build.

These tests serve as comprehensive regression tests to ensure the validator
doesn't produce false positives for any public API symbols.
"""

import importlib
import inspect

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
    """Get all public symbols from the dagster package, excluding problematic imports."""
    dagster_module = importlib.import_module("dagster")

    # Symbols that should be excluded from testing (imports from other modules that cause issues)
    EXCLUDED_SYMBOLS = {
        "sys",  # Conflicts with built-in sys module, not actually part of Dagster's public API
    }

    public_symbols = []
    for name in dir(dagster_module):
        if not name.startswith("_") and name not in EXCLUDED_SYMBOLS:
            public_symbols.append(name)

    return [f"dagster.{name}" for name in sorted(public_symbols)]


def _get_all_dagster_public_class_methods():
    """Get all @public methods from @public classes in the dagster package."""
    from automation.dagster_docs.public_symbol_utils import get_public_methods_from_class

    dagster_module = importlib.import_module("dagster")

    # Symbols that should be excluded from testing (imports from other modules that cause issues)
    EXCLUDED_SYMBOLS = {
        "sys",  # Conflicts with built-in sys module, not actually part of Dagster's public API
    }

    methods = []
    for name in dir(dagster_module):
        if not name.startswith("_") and name not in EXCLUDED_SYMBOLS:
            try:
                symbol = getattr(dagster_module, name)
                # Only process classes (not functions, constants, etc.)
                if inspect.isclass(symbol):
                    # Get all @public methods from this class
                    class_dotted_path = f"dagster.{name}"
                    class_methods = get_public_methods_from_class(symbol, class_dotted_path)
                    methods.extend(class_methods)
            except Exception:
                # Skip symbols that can't be accessed
                continue

    return sorted(methods)


class TestKnownValidSymbols:
    """Test symbols that are known to have valid docstrings."""

    # Using function-based validation approach

    @pytest.mark.parametrize("symbol_path", _get_all_dagster_public_symbols())
    def test_all_public_symbol_docstrings(self, symbol_path):
        """Test that all public dagster symbols have valid docstrings.

        This test validates every public symbol in the dagster package to ensure:
        1. The symbol can be imported successfully
        2. The docstring has valid RST/Google-style formatting (unless in skip list)
        3. No syntax errors that would break documentation builds

        Symbols with known docstring issues are maintained in SYMBOL_EXCLUDE_LIST
        and should be addressed in separate PRs.

        Args:
            symbol_path: Dotted path to the symbol to test
        """
        # Skip validation for symbols with known issues - check before validation
        # to avoid import errors for symbols that are known to be problematic
        if symbol_path in SYMBOL_EXCLUDE_LIST:
            print(f"Skipping known problematic symbol: {symbol_path}")  # noqa: T201
            return

        result = validate_symbol_docstring(symbol_path)

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

    def test_nonexistent_symbol_produces_error(self):
        """Test that attempting to validate a non-existent symbol produces an error."""
        result = validate_symbol_docstring("dagster.nonexistent_symbol_name")

        assert not result.parsing_successful
        assert result.has_errors()
        assert "Failed to import symbol" in result.errors[0]
        assert not result.is_valid()

    def test_symbol_with_no_docstring(self):
        """Test that symbols without docstrings produce warnings but are still valid."""
        # Most internal symbols don't have docstrings, which should produce a warning
        # but not an error (since missing docstrings don't break the docs build)
        result = validate_symbol_docstring("dagster._utils")  # Internal module

        # Should be importable
        assert result.parsing_successful

        # Should have a warning about missing docstring
        assert result.has_warnings()

        # Should still be considered valid (warnings don't fail validation)
        assert result.is_valid()

    @pytest.mark.parametrize("method_path", _get_all_dagster_public_class_methods())
    def test_all_public_class_method_docstrings(self, method_path):
        """Test that all @public methods on Dagster classes have valid docstrings.

        This test validates every @public method on all classes in the dagster package to ensure:
        1. The method can be imported successfully
        2. The docstring has valid RST/Google-style formatting
        3. No syntax errors that would break documentation builds

        This provides comprehensive coverage of method docstrings across the entire Dagster codebase.

        Args:
            method_path: Dotted path to the method to test (e.g., 'dagster.AssetExecutionContext.log')
        """
        result = validate_symbol_docstring(method_path)

        # The method should be importable - this is the core requirement
        assert result.parsing_successful, f"Failed to parse {method_path}: {result.errors}"

        # All @public methods should have valid docstrings
        assert result.is_valid(), (
            f"@public method {method_path} should have valid docstring but got errors: {result.errors}. "
            f"Method docstrings must follow the same standards as top-level symbols."
        )

        # Log warnings for awareness
        if result.has_warnings():
            print(f"Docstring warnings for {method_path}: {result.warnings}")  # noqa: T201


class TestDocstringTextValidation:
    """Test validation of raw docstring text."""

    # Using function-based validation approach

    def test_valid_google_style_docstring(self):
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

        result = validate_docstring_text(docstring, "test.function")

        assert result.is_valid()
        assert not result.has_errors()
        # May have warnings but that's OK for a valid docstring

    def test_docstring_with_sphinx_roles(self):
        """Test that docstrings using Sphinx roles are handled correctly."""
        docstring = '''"""A function that references other symbols.

        This function uses :py:class:`SomeClass` and calls :func:`other_function`.
        See also :py:meth:`SomeClass.method` for more details.

        Args:
            param: A parameter of type :py:class:`SomeType`.

        Returns:
            An instance of :py:class:`ReturnType`.
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should not have errors because Sphinx roles are filtered out
        assert result.is_valid()
        assert not result.has_errors()

    def test_docstring_with_literalinclude_directive(self):
        """Test that docstrings using literalinclude directive are handled correctly."""
        docstring = '''"""Configuration for DagsterInstance.

        Examples:

        .. literalinclude:: ../config/dagster.yaml
           :caption: dagster.yaml
           :language: YAML

        The configuration includes various settings.
        """'''

        result = validate_docstring_text(docstring, "test.class")

        # Should not have errors because literalinclude directive is filtered out
        assert result.is_valid()
        assert not result.has_errors()
