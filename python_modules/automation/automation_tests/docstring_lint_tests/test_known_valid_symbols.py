"""Tests for symbols that are known to have valid docstrings.

This test suite validates all the Dagster symbols that were tested during the
development of the docstring validation tool and confirmed to render correctly
on https://docs.dagster.io/api/dagster.

These tests serve as regression tests to ensure the validator doesn't produce
false positives for docstrings that are known to work correctly in the full
Sphinx build environment.
"""

import pytest
from automation.docstring_lint.validator import DocstringValidator


class TestKnownValidSymbols:
    """Test symbols that are known to have valid docstrings."""

    @pytest.fixture
    def validator(self):
        """Provide a DocstringValidator instance for tests."""
        return DocstringValidator()

    @pytest.mark.parametrize(
        "symbol_path",
        [
            # Core decorators and functions
            "dagster.asset",
            "dagster.job",
            "dagster.op",
            "dagster.graph",
            "dagster.resource",
            "dagster.schedule",
            "dagster.sensor",
            "dagster.multi_asset",
            # Core classes
            "dagster.AssetKey",
            "dagster.OpDefinition",
            "dagster.JobDefinition",
            "dagster.GraphDefinition",
            "dagster.ResourceDefinition",
            "dagster.DagsterInstance",
            "dagster.AssetMaterialization",
            "dagster.AssetObservation",
            "dagster.Output",
            "dagster.In",
            "dagster.Out",
            "dagster.Config",
            "dagster.Field",
            "dagster.RetryPolicy",
            "dagster.RunRequest",
            "dagster.SkipReason",
            "dagster.Failure",
            "dagster.HookContext",
            # Context builders
            "dagster.build_hook_context",
            "dagster.build_op_context",
        ],
    )
    def test_known_valid_symbol_docstrings(self, validator, symbol_path):
        """Test that known valid symbols pass docstring validation.

        These symbols have been manually verified to:
        1. Render correctly on https://docs.dagster.io/api/dagster
        2. Build successfully in the full Sphinx documentation build
        3. Have properly formatted Google-style docstrings

        Args:
            validator: DocstringValidator instance
            symbol_path: Dotted path to the symbol to test
        """
        result = validator.validate_symbol_docstring(symbol_path)

        # The symbol should be importable
        assert result.parsing_successful, f"Failed to parse {symbol_path}: {result.errors}"

        # The symbol should have valid docstring syntax (no errors)
        assert result.is_valid(), (
            f"Symbol {symbol_path} should have valid docstring but got errors: {result.errors}"
        )

        # We allow warnings (e.g., for missing docstrings on some symbols)
        # but errors indicate real parsing issues that would break the docs build
        if result.has_warnings():
            print(f"Warnings for {symbol_path}: {result.warnings}")  # noqa: T201

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
