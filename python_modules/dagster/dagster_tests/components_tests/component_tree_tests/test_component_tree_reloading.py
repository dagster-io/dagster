import dagster as dg
import pytest
from dagster.components.core.component_tree import ComponentTreeException
from dagster.components.testing import create_defs_folder_sandbox


class SingletonComponent(dg.Component):
    """Forthright and by the book."""

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # this should only ever be called once
        sentinel_path = context.component_path.file_path / "sentinel.txt"
        assert not sentinel_path.exists()
        sentinel_path.touch()

        return dg.Definitions(assets=[dg.AssetSpec("singleton")])


class DuplicitousComponent(dg.Component):
    """Extremely sneaky."""

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # keeps track of how many times this has been called
        postfix = 0
        while True:
            sentinel_path = context.component_path.file_path / str(postfix)
            if not sentinel_path.exists():
                sentinel_path.touch()
                assert sentinel_path.exists()
                break
            postfix += 1

        return dg.Definitions(assets=[dg.AssetSpec(f"dup_{postfix}")])


def test_reload_component_tree_cached() -> None:
    with create_defs_folder_sandbox() as sandbox:
        singleton_path = sandbox.scaffold_component(
            component_cls=SingletonComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_component_tree_reloading.SingletonComponent",
            },
        )

        duplicitous_path = sandbox.scaffold_component(
            component_cls=DuplicitousComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_component_tree_reloading.DuplicitousComponent",
            },
        )

        with sandbox.build_component_tree() as tree:
            defs1 = tree.build_defs()
            assert len(defs1.get_all_asset_specs()) == 2
            keys = {spec.key for spec in defs1.get_all_asset_specs()}
            assert keys == {dg.AssetKey("singleton"), dg.AssetKey("dup_0")}

            # should be cached, will not trip the singleton assertion
            defs2 = tree.build_defs()
            assert defs1 is defs2

            # ... and so on
            defs3 = tree.build_defs()
            assert defs1 is defs3

            # now invalidate duplicitous
            tree.state_tracker.invalidate_cache_key(
                defs_module_path=tree.defs_module_path,
                component_path=duplicitous_path,
            )

            defs4 = tree.build_defs()
            assert defs1 is not defs4
            keys = {spec.key for spec in defs4.get_all_asset_specs()}
            # now have dup_1 instead of dup0
            assert keys == {dg.AssetKey("singleton"), dg.AssetKey("dup_1")}

            # invalidate duplicitous again
            tree.state_tracker.invalidate_cache_key(
                defs_module_path=tree.defs_module_path,
                component_path=duplicitous_path,
            )

            defs5 = tree.build_defs()
            assert defs1 is not defs5
            keys = {spec.key for spec in defs5.get_all_asset_specs()}
            # now have dup_2 instead of dup0
            assert keys == {dg.AssetKey("singleton"), dg.AssetKey("dup_2")}

            # now invalidate singleton
            tree.state_tracker.invalidate_cache_key(
                defs_module_path=tree.defs_module_path,
                component_path=singleton_path,
            )

            # should raise an exception because we end up calling singleton again
            with pytest.raises(ComponentTreeException):
                tree.build_defs()
