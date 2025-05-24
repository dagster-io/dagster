from typing import TYPE_CHECKING, cast

import pytest
from dagster import AssetSpec, ComponentLoadContext, Definitions
from dagster._core.errors import DagsterInvariantViolationError
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

    @definitions
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
    # Test invalid signature with multiple parameters
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Function must accept either no parameters or exactly one ComponentLoadContext parameter",
    ):

        @definitions  # type: ignore
        def invalid_defs(context: ComponentLoadContext, extra_param: str):
            return Definitions()


def test_definitions_decorator_return_type():
    """Test that the decorator enforces correct return types."""

    @definitions  # type: ignore
    def invalid_return():
        return "not a definitions object"

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Function must return a Definitions or RepositoryDefinition object",
    ):
        invalid_return()


def test_definitions_decorator_with_context_using_context():
    """Test that the decorator works when the context is actually used in the function."""

    @definitions
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
