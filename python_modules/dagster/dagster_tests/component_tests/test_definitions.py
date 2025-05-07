from typing import TYPE_CHECKING, cast

import pytest
from dagster import AssetSpec, Definitions
from dagster._core.errors import DagsterInvariantViolationError
from dagster.components import ComponentLoadContext
from dagster.components.definitions import definitions
from dagster_shared import check

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


def test_definitions_decorator_without_context():
    """Test the basic usage of @definitions without context."""

    @definitions
    def my_defs():
        return Definitions(assets=[AssetSpec(key="asset1")])

    result = my_defs()
    assert isinstance(result, Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1
    asset_def = cast("AssetsDefinition", assets[0])
    assert asset_def.key.path[0] == "asset1"


def test_definitions_decorator_with_context():
    """Test the usage of @definitions with context."""

    @definitions(has_context_arg=True)
    def my_defs_with_context(context: ComponentLoadContext):
        assert isinstance(context, ComponentLoadContext)
        return Definitions(assets=[AssetSpec(key="asset1")])

    context = ComponentLoadContext.for_test()
    result = my_defs_with_context(context)
    assert isinstance(result, Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1
    asset_def = cast("AssetsDefinition", assets[0])
    assert asset_def.key.path[0] == "asset1"


def test_definitions_decorator_invalid_signature():
    """Test that the decorator enforces correct function signatures."""
    # Test invalid signature for context-free case
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Function must accept no parameters when has_context_arg=False",
    ):

        @definitions  # type: ignore
        def invalid_defs(context: ComponentLoadContext):
            return Definitions()

    # Test invalid signature for context-requiring case
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Function must accept exactly one ComponentLoadContext parameter when has_context_arg=True",
    ):

        @definitions(has_context_arg=True)  # type: ignore
        def invalid_defs_with_context():
            return Definitions()


def test_definitions_decorator_return_type():
    """Test that the decorator enforces correct return types."""

    @definitions  # type: ignore
    def invalid_return():
        return "not a definitions object"

    with pytest.raises(
        DagsterInvariantViolationError,
        match="DefinitionsLoader must return a Definitions or RepositoryDefinition object",
    ):
        invalid_return()


def test_definitions_decorator_with_context_using_context():
    """Test that the decorator works when the context is actually used in the function."""

    @definitions(has_context_arg=True)
    def my_defs_with_context(context: ComponentLoadContext):
        assert isinstance(context, ComponentLoadContext)
        return Definitions(
            assets=[
                AssetSpec(
                    key="asset1",
                )
            ]
        )

    context = ComponentLoadContext.for_test()
    result = my_defs_with_context(context)
    assert isinstance(result, Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1

    assert check.inst(next(iter(assets)), AssetSpec).key.path[0] == "asset1"
