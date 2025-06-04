from unittest.mock import Mock, patch

import pytest
from dagster_dg_core.utils import resolve_wildcard_modules


def test_resolve_wildcard_modules_no_wildcards():
    """Test that modules without wildcards are returned as-is."""
    modules = ["foo.bar", "baz.qux"]
    result = resolve_wildcard_modules(modules)
    assert result == ["foo.bar", "baz.qux"]


def test_resolve_wildcard_modules_empty_list():
    """Test that empty list returns empty list."""
    result = resolve_wildcard_modules([])
    assert result == []


@patch("dagster_dg_core.utils.pkgutil.iter_modules")
@patch("dagster_dg_core.utils.importlib.import_module")
def test_resolve_wildcard_modules_single_wildcard(mock_import, mock_iter_modules):
    """Test resolving a single wildcard pattern."""
    # Mock top-level modules
    mock_iter_modules.return_value = [
        (None, "foo", False),
        (None, "bar", False),
        (None, "baz", False),
    ]

    # Mock successful imports
    mock_import.return_value = Mock()

    result = resolve_wildcard_modules(["*"])

    # Should have tried to import all discovered modules
    expected_calls = [((module,),) for module in ["foo", "bar", "baz"]]
    mock_import.assert_has_calls(
        [pytest.mock.call(call[0][0]) for call in expected_calls], any_order=True
    )

    assert set(result) == {"foo", "bar", "baz"}


@patch("dagster_dg_core.utils.pkgutil.iter_modules")
@patch("dagster_dg_core.utils.importlib.import_module")
def test_resolve_wildcard_modules_nested_wildcard(mock_import, mock_iter_modules):
    """Test resolving a nested wildcard pattern."""
    # Mock submodules for foo package
    mock_parent_module = Mock()
    mock_parent_module.__path__ = ["/fake/path/foo"]

    def mock_import_side_effect(module_name):
        if module_name == "foo":
            return mock_parent_module
        elif module_name in ["foo.utils", "foo.helpers"]:
            return Mock()
        else:
            raise ImportError(f"No module named '{module_name}'")

    mock_import.side_effect = mock_import_side_effect

    # Mock iter_modules to return submodules for foo
    def mock_iter_modules_side_effect(path=None):
        if path == ["/fake/path/foo"]:
            return [
                (None, "utils", False),
                (None, "helpers", False),
                (None, "nonexistent", False),  # This will fail import
            ]
        return []

    mock_iter_modules.side_effect = mock_iter_modules_side_effect

    result = resolve_wildcard_modules(["foo.*"])

    # Should only include modules that can be imported
    assert set(result) == {"foo.utils", "foo.helpers"}


@patch("dagster_dg_core.utils.pkgutil.iter_modules")
@patch("dagster_dg_core.utils.importlib.import_module")
def test_resolve_wildcard_modules_mixed_patterns(mock_import, mock_iter_modules):
    """Test resolving mixed wildcard and literal patterns."""
    # Mock top-level modules
    mock_iter_modules.return_value = [
        (None, "foo", False),
        (None, "bar", False),
    ]

    # Mock successful imports
    def mock_import_side_effect(module_name):
        if module_name in ["foo", "bar", "explicit.module"]:
            return Mock()
        else:
            raise ImportError(f"No module named '{module_name}'")

    mock_import.side_effect = mock_import_side_effect

    result = resolve_wildcard_modules(["explicit.module", "*"])

    # Should include both explicit and resolved wildcard modules
    assert set(result) == {"explicit.module", "foo", "bar"}


@patch("dagster_dg_core.utils.pkgutil.iter_modules")
@patch("dagster_dg_core.utils.importlib.import_module")
def test_resolve_wildcard_modules_import_failure(mock_import, mock_iter_modules):
    """Test that modules that fail to import are excluded."""
    # Mock top-level modules
    mock_iter_modules.return_value = [
        (None, "good_module", False),
        (None, "bad_module", False),
    ]

    def mock_import_side_effect(module_name):
        if module_name == "good_module":
            return Mock()
        else:
            raise ImportError(f"No module named '{module_name}'")

    mock_import.side_effect = mock_import_side_effect

    result = resolve_wildcard_modules(["*"])

    # Should only include modules that imported successfully
    assert result == ["good_module"]


def test_resolve_wildcard_modules_deduplication():
    """Test that duplicate modules are removed while preserving order."""
    modules = ["foo.bar", "baz.qux", "foo.bar"]
    result = resolve_wildcard_modules(modules)
    assert result == ["foo.bar", "baz.qux"]


@patch("dagster_dg_core.utils.pkgutil.iter_modules")
@patch("dagster_dg_core.utils.importlib.import_module")
def test_resolve_wildcard_modules_complex_pattern(mock_import, mock_iter_modules):
    """Test resolving a complex wildcard pattern with multiple segments."""
    # Mock the parent module
    mock_parent_module = Mock()
    mock_parent_module.__path__ = ["/fake/path/foo"]

    def mock_import_side_effect(module_name):
        if module_name == "foo":
            return mock_parent_module
        elif module_name == "foo.core.models":
            return Mock()
        else:
            raise ImportError(f"No module named '{module_name}'")

    mock_import.side_effect = mock_import_side_effect

    # Mock submodules
    def mock_iter_modules_side_effect(path=None):
        if path == ["/fake/path/foo"]:
            return [(None, "core", False)]
        return []

    mock_iter_modules.side_effect = mock_iter_modules_side_effect

    result = resolve_wildcard_modules(["foo.*.models"])

    # Should find foo.core.models
    assert result == ["foo.core.models"]
