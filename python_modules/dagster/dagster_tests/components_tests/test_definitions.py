import tempfile
from pathlib import Path
from typing import cast

import dagster as dg
import pytest
from dagster import ComponentLoadContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.component.app_managed_state import (
    AppManagedComponentEntry,
    write_app_managed_component_entry,
)
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.component_tree import ComponentTree, LegacyAutoloadingComponentTree
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


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

    @dg.definitions
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
    defs = LegacyAutoloadingComponentTree.for_project(dagster_test_path).build_defs()

    repo_def = defs.get_repository_def()
    asset = repo_def.asset_graph.get(dg.AssetKey("first_yaml"))
    assert asset is not None
    assert asset.metadata["dagster/component_origin"]
    assert (
        asset.metadata["dagster/component_origin"].instance.__class__.__name__
        == "SimpleAssetComponent"
    )

    asset = repo_def.asset_graph.get(dg.AssetKey("solo_yaml"))
    assert asset is not None
    assert asset.metadata["dagster/component_origin"]
    assert (
        asset.metadata["dagster/component_origin"].instance.__class__.__name__
        == "SimpleAssetComponent"
    )

    asset = repo_def.asset_graph.get(dg.AssetKey("first_py"))
    assert asset is not None
    assert asset.metadata["dagster/component_origin"]
    assert asset.metadata["dagster/component_origin"].instance.__class__.__name__ == "PyComponent"

    asset = repo_def.asset_graph.get(dg.AssetKey("solo_py"))
    assert asset is not None
    assert asset.metadata["dagster/component_origin"]
    assert (
        asset.metadata["dagster/component_origin"].instance.__class__.__name__
        == "FunctionComponent"
    )

    repo_snap = RepositorySnap.from_def(repo_def)
    assert repo_snap.component_tree

    inst_map = {snap.key: snap.full_type_name for snap in repo_snap.component_tree.leaf_instances}
    assert inst_map == {
        # ``FunctionComponent`` is re-exported from the top-level ``dagster``
        # package, so it resolves to its canonical entry-point name rather than
        # the deep defining-module path.
        "python/component.py[only]": "dagster.FunctionComponent",
        "yaml[0]": "dagster_test.components.simple_asset.SimpleAssetComponent",
        "composites/python/component.py[first]": "dagster_test.dg_defs.composites.python.component.PyComponent",
        "composites/python/component.py[second]": "dagster_test.dg_defs.composites.python.component.PyComponent",
        "composites/yaml[0]": "dagster_test.components.simple_asset.SimpleAssetComponent",
        "composites/yaml[1]": "dagster_test.components.simple_asset.SimpleAssetComponent",
        # The tree now surfaces the app-managed aggregate container and the
        # implicit ``PythonFileComponent`` for each ``__init__.py``.
        "APP_ROOT": "dagster.components.core.defs_module.AppManagedDefinitionsComponent",
        "__init__.py": "dagster.components.core.defs_module.PythonFileComponent",
        "composites/__init__.py": "dagster.components.core.defs_module.PythonFileComponent",
        "composites/python/__init__.py": "dagster.components.core.defs_module.PythonFileComponent",
    }


class SnapTestStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Minimal state-backed component shared by ``test_component_tree_snap_with_app_managed_components``.

    Defined at module scope so it is importable by its fully qualified name,
    which is what the app-managed component decl uses to rehydrate the class.
    """

    defs_state_key: str | None = None
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.versioned_state_storage()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = self.__class__.__name__
        if self.defs_state_key is not None:
            default_key = f"{default_key}[{self.defs_state_key}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        return dg.Definitions(assets=[dg.AssetSpec(key=f"asset_for_{self.defs_state_key}")])

    async def write_state_to_path(self, state_path: Path) -> None:
        state_path.write_text("ok", encoding="utf-8")


def test_component_tree_snap_with_app_managed_components() -> None:
    """Mixed filesystem + app-managed components should both appear as snap
    leaves, with ``is_app_managed`` set only on the app-managed entry and each
    leaf carrying its own ``defs_state_key``.
    """
    typename = f"{SnapTestStateBackedComponent.__module__}.{SnapTestStateBackedComponent.__name__}"

    with (
        tempfile.TemporaryDirectory() as state_dir,
        instance_for_test(
            overrides={
                "defs_state_storage": {
                    "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                    "class": "UPathDefsStateStorage",
                    "config": {"base_path": state_dir},
                }
            }
        ) as instance,
        create_defs_folder_sandbox() as sandbox,
    ):
        storage = check.inst(instance.defs_state_storage, UPathDefsStateStorage)

        # Filesystem-based instance scaffolded under defs/fs_component/defs.yaml.
        sandbox.scaffold_component(
            component_cls=SnapTestStateBackedComponent,
            defs_yaml_contents={
                "type": typename,
                "attributes": {"defs_state_key": "fs_key"},
            },
            defs_path="fs_component",
        )

        # App-managed instance lives only in DefsStateStorage; the wrapper decl
        # appears alongside the filesystem decl under the unified root.
        write_app_managed_component_entry(
            storage,
            "test_loc",
            "app_component",
            AppManagedComponentEntry(
                component_type=typename,
                attributes="defs_state_key: app_managed_key\n",
            ),
        )

        with (
            sandbox.build_component_tree(code_location_name="test_loc") as tree,
            scoped_definitions_load_context(),
        ):
            defs = tree.build_defs()
            repo_def = defs.get_repository_def()
            repo_snap = RepositorySnap.from_def(repo_def)

        assert repo_snap.component_tree is not None
        leaves = list(repo_snap.component_tree.leaf_instances)

        app_managed_leaves = [leaf for leaf in leaves if leaf.app_managed]
        fs_leaves = [leaf for leaf in leaves if not leaf.app_managed]

        assert len(app_managed_leaves) == 1, leaves
        assert len(fs_leaves) == 1, leaves

        app_leaf = app_managed_leaves[0]
        assert app_leaf.key == "app_component"
        assert app_leaf.full_type_name == typename
        assert app_leaf.defs_state_key == "SnapTestStateBackedComponent[app_managed_key]"
        assert (
            app_leaf.defs_state_management_type == DefsStateManagementType.VERSIONED_STATE_STORAGE
        )

        fs_leaf = fs_leaves[0]
        assert fs_leaf.full_type_name == typename
        assert fs_leaf.defs_state_key == "SnapTestStateBackedComponent[fs_key]"
