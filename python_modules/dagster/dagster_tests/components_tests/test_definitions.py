from pathlib import Path
from typing import cast

import dagster as dg
import pytest
from dagster import ComponentLoadContext
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster.components.core.tree import ComponentTree, LegacyAutoloadingComponentTree
from dagster_shared import check


def test_definitions_decorator_without_context():
    """Test the basic usage of @definitions without context."""

    @dg.definitions
    def my_defs():
        return dg.Definitions(assets=[dg.AssetSpec(key="asset1")])

    result = my_defs()
    assert isinstance(result, dg.Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1
    asset_def = cast("dg.AssetsDefinition", assets[0])
    assert asset_def.key.path[0] == "asset1"


def test_definitions_decorator_with_context():
    """Test the usage of @definitions with context."""

    @dg.definitions
    def my_defs_with_context(context: ComponentLoadContext):
        assert isinstance(context, dg.ComponentLoadContext)
        return dg.Definitions(assets=[dg.AssetSpec(key="asset1")])

    context = ComponentTree.for_test().load_context
    result = my_defs_with_context(context)
    assert isinstance(result, dg.Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1
    asset_def = cast("dg.AssetsDefinition", assets[0])
    assert asset_def.key.path[0] == "asset1"


def test_definitions_decorator_invalid_signature():
    """Test that the decorator enforces correct function signatures."""
    # Test invalid signature with multiple parameters
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Function must accept either no parameters or exactly one ComponentLoadContext parameter",
    ):

        @dg.definitions  # type: ignore
        def invalid_defs(context: ComponentLoadContext, extra_param: str):
            return dg.Definitions()


def test_definitions_decorator_return_type():
    """Test that the decorator enforces correct return types."""

    @dg.definitions  # type: ignore
    def invalid_return():
        return "not a definitions object"

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Function must return a Definitions or RepositoryDefinition object",
    ):
        invalid_return()


def test_definitions_decorator_with_context_using_context():
    """Test that the decorator works when the context is actually used in the function."""

    @dg.definitions
    def my_defs_with_context(context: ComponentLoadContext):
        assert isinstance(context, dg.ComponentLoadContext)
        return dg.Definitions(
            assets=[
                dg.AssetSpec(
                    key="asset1",
                )
            ]
        )

    context = ComponentTree.for_test().load_context
    result = my_defs_with_context(context)
    assert isinstance(result, dg.Definitions)
    assets = list(result.assets or [])
    assert len(assets) == 1

    assert check.inst(next(iter(assets)), dg.AssetSpec).key.path[0] == "asset1"


def test_component_tree():
    dagster_test_path = Path(__file__).joinpath("../../../../dagster-test").resolve()
    assert dagster_test_path.exists()
    defs = LegacyAutoloadingComponentTree.load(dagster_test_path).build_defs()

    repo_snap = RepositorySnap.from_def(defs.get_repository_def())
    assert repo_snap.component_tree

    inst_map = {snap.key: snap.full_type_name for snap in repo_snap.component_tree.leaf_instances}
    assert inst_map == {
        "composites/python/component.py[first]": "dagster_test.dg_defs.composites.python.component.PyComponent",
        "composites/python/component.py[second]": "dagster_test.dg_defs.composites.python.component.PyComponent",
        "composites/yaml[0]": "dagster_test.components.simple_asset.SimpleAssetComponent",
        "composites/yaml[1]": "dagster_test.components.simple_asset.SimpleAssetComponent",
    }
