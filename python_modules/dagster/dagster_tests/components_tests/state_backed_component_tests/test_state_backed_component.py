import asyncio
import contextlib
import json
import random
import shutil
from pathlib import Path
from typing import Optional

import dagster as dg
import pytest
from dagster._core.definitions.definitions_load_context import DefinitionsLoadType
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.component_tree_state import DuplicateDefsStateKeyWarning
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster.components.utils.project_paths import get_code_server_metadata_key
from dagster_shared.serdes.objects.models.defs_state_info import (
    CODE_SERVER_STATE_VERSION,
    LOCAL_STATE_VERSION,
    DefsStateManagementType,
)


class MyStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    defs_state_key: Optional[str] = None
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.versioned_state_storage()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = self.__class__.__name__
        if self.defs_state_key is not None:
            default_key = f"{default_key}[{self.defs_state_key}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            value = "initial"
        else:
            with open(state_path) as f:
                state = json.load(f)
            value = state["value"]

        @dg.asset(
            name=f"the_asset_{context.component_path.file_path.stem}",
            metadata={"state_value": value},
        )
        def the_asset():
            return dg.MaterializeResult(metadata={"foo": value})

        return dg.Definitions(assets=[the_asset])

    async def write_state_to_path(self, state_path: Path):
        with open(state_path, "w") as f:
            json.dump({"value": f"bar_{random.randint(1000, 9999)}"}, f)

    def _get_state_refresh_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        project_root = context.project_root

        @dg.op
        def refresh_state_op():
            asyncio.run(self.refresh_state(project_root))

        @dg.job(name=f"state_refresh_job_{context.component_path.file_path.stem}")
        def state_refresh_job():
            refresh_state_op()

        return dg.Definitions(jobs=[state_refresh_job])

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions.merge(
            super().build_defs(context),
            self._get_state_refresh_defs(context),
        )


@pytest.mark.parametrize(
    "storage_location",
    [
        DefsStateManagementType.LOCAL_FILESYSTEM,
        DefsStateManagementType.VERSIONED_STATE_STORAGE,
    ],
)
@pytest.mark.parametrize(
    "key",
    [
        None,
        "CustomDefsStateKey",
    ],
)
def test_simple_state_backed_component(
    storage_location: DefsStateManagementType, key: Optional[str]
) -> None:
    expected_key = key or "MyStateBackedComponent"
    with instance_for_test() as instance, create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {
                    "defs_state": {"type": storage_location.value, **({"key": key} if key else {})}
                },
            },
            defs_path="foo",
        )

        state_storage = DefsStateStorage.get()
        assert state_storage
        # add some state versions for other unrelated keys, should not show up in the load context
        state_storage.set_latest_version("RandomKey1", LOCAL_STATE_VERSION)
        state_storage.set_latest_version("RandomKey2", CODE_SERVER_STATE_VERSION)
        state_storage.set_latest_version("RandomKey3", "xyz")

        # initial load, no state written, so use "initial"
        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]

            # the state value is set to some random number
            original_metadata_value = spec.metadata["state_value"]
            assert original_metadata_value == "initial"  # hardcoded in the component

            # materialize the asset, the random number should be preserved
            result = dg.materialize([defs.get_assets_def(spec.key)], instance=instance)
            assert result.success
            mats = result.asset_materializations_for_node("the_asset_foo")
            assert len(mats) == 1
            assert mats[0].metadata["foo"] == dg.TextMetadataValue(original_metadata_value)

            # should register that the key was accessed (but has no version)
            assert load_context.accessed_defs_state_info
            assert load_context.accessed_defs_state_info.info_mapping.keys() == {expected_key}
            assert load_context.accessed_defs_state_info.get_version(expected_key) is None

        # reload the definitions, state should be the same
        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            # metadata should remain the same
            assert spec.metadata["state_value"] == original_metadata_value

            # now execute the job to refresh the state
            refresh_job = defs.get_job_def("state_refresh_job_foo")
            refresh_job.execute_in_process(instance=instance)

            # same as above
            assert load_context.accessed_defs_state_info
            assert load_context.accessed_defs_state_info.info_mapping.keys() == {expected_key}
            assert load_context.accessed_defs_state_info.get_version(expected_key) is None

        # now we reload the definitions, state should be updated to something random
        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            new_metadata_value = spec.metadata["state_value"]
            assert new_metadata_value != original_metadata_value

            # should have version information available
            assert load_context.accessed_defs_state_info
            assert load_context.accessed_defs_state_info.info_mapping.keys() == {expected_key}
            assert load_context.accessed_defs_state_info.get_version(expected_key) is not None


@pytest.mark.parametrize(
    "instance_available",
    [True, False],
)
def test_code_server_state_backed_component(instance_available: bool) -> None:
    instance_cm = contextlib.nullcontext() if instance_available else instance_for_test()
    with instance_cm, create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {
                    "defs_state": {
                        "type": DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS.value
                    }
                },
            },
            defs_path="foo",
        )

        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            original_metadata_value = spec.metadata["state_value"]
            # should automatically load
            assert original_metadata_value != "initial"

            repo = defs.get_repository_def()
            assert repo.repository_load_data is not None

            assert load_context.load_type == DefinitionsLoadType.INITIALIZATION
            pending_metadata = load_context.get_pending_reconstruction_metadata()
            key = get_code_server_metadata_key("MyStateBackedComponent")
            assert pending_metadata.keys() == {"defs-state-[MyStateBackedComponent]"}
            # last bit is random
            assert '{"value": "bar_' in pending_metadata[key]
            assert load_context.accessed_defs_state_info is not None

        # now simulate the reconstruction process
        with scoped_definitions_load_context(
            load_type=DefinitionsLoadType.RECONSTRUCTION,
            repository_load_data=RepositoryLoadData(
                cacheable_asset_data={},
                reconstruction_metadata=pending_metadata,
                defs_state_info=load_context.accessed_defs_state_info,
            ),
        ):
            with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
                specs = defs.get_all_asset_specs()
                spec = specs[0]
                assert spec.metadata["state_value"] == original_metadata_value
                assert "bar_" in spec.metadata["state_value"]


@pytest.mark.parametrize(
    "instance_available",
    [True, False],
)
def test_local_filesystem_state_backed_component(instance_available: bool) -> None:
    instance_cm = contextlib.nullcontext() if instance_available else instance_for_test()
    with instance_cm, create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {
                    "defs_state": {
                        "type": DefsStateManagementType.LOCAL_FILESYSTEM.value,
                    }
                },
            },
            defs_path="foo",
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            # will not automatically load
            assert spec.metadata["state_value"] == "initial"

            # now execute the job to refresh the state
            refresh_job = defs.get_job_def("state_refresh_job_foo")
            refresh_job.execute_in_process()  # note: ephemeral instance

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            new_state_value = spec.metadata["state_value"]
            # state should be updated to something random
            assert new_state_value != "initial"
            assert new_state_value.startswith("bar_")

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]

            # state should be the same as before
            assert spec.metadata["state_value"] == new_state_value


@pytest.mark.parametrize(
    "storage_location",
    [
        DefsStateManagementType.LOCAL_FILESYSTEM,
        DefsStateManagementType.VERSIONED_STATE_STORAGE,
        DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS,
    ],
)
def test_dev_mode_state_backed_component(storage_location: DefsStateManagementType) -> None:
    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        # we're in dev mode
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {"defs_state": {"type": storage_location.value}},
            },
            defs_path="foo",
        )

        with scoped_definitions_load_context() as load_context:
            # nothing accessed yet
            assert load_context.accessed_defs_state_info is None

            with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
                assert load_context.accessed_defs_state_info is not None
                assert load_context.accessed_defs_state_info.info_mapping.keys() == {
                    "MyStateBackedComponent"
                }
                specs = defs.get_all_asset_specs()
                spec = specs[0]
                metadata_value = spec.metadata["state_value"]
                # should automatically load
                assert metadata_value != "initial"


def test_multiple_components() -> None:
    with instance_for_test(), create_defs_folder_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
            },
            defs_path="first",
        )

        second_component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
            },
            defs_path="second",
        )

        # Should emit a warning but not raise an error when components share the same defs state key
        with pytest.warns(
            DuplicateDefsStateKeyWarning, match="Multiple components have the same defs state key"
        ):
            with sandbox.build_all_defs() as defs:
                # Both components should still load successfully
                assert len(defs.get_all_asset_specs()) == 2

        # now update the defs_state_key
        shutil.rmtree(second_component_path)
        sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {"defs_state_key": "MyStateBackedComponent_but_different"},
            },
            defs_path="second",
        )

        with sandbox.build_all_defs() as defs:
            assert len(defs.get_all_asset_specs()) == 2


def test_two_components_sharing_same_state_key() -> None:
    """Test that two components can share the same state key with a warning."""
    with instance_for_test(), create_defs_folder_sandbox() as sandbox:
        # Create two components with the same state key by explicitly setting it
        sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {"defs_state_key": "shared_key"},
            },
            defs_path="component_a",
        )

        sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {"defs_state_key": "shared_key"},
            },
            defs_path="component_b",
        )

        # Should emit a warning but not raise an error
        with pytest.warns(
            DuplicateDefsStateKeyWarning,
            match="Multiple components have the same defs state key: MyStateBackedComponent\\[shared_key\\]",
        ):
            with sandbox.build_all_defs() as defs:
                # Both components should load successfully
                specs = defs.get_all_asset_specs()
                assert len(specs) == 2
                # Verify both assets were created
                assert any("component_a" in spec.key.to_user_string() for spec in specs)
                assert any("component_b" in spec.key.to_user_string() for spec in specs)


def test_state_backed_component_migration_from_versioned_to_local_storage() -> None:
    """Test migrating a component from versioned state storage to local storage.

    This test demonstrates:
    1. Start with versioned storage, no state available (initial value)
    2. Run update state job to populate versioned storage
    3. Reload with versioned storage, should have updated value
    4. Switch to local storage, should reset to initial value
    5. Load with DAGSTER_IS_DEV_CLI set, should force local refresh
    """
    with instance_for_test() as instance, create_defs_folder_sandbox() as sandbox:
        # Step 1: Start with versioned storage, no state available
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {
                    "defs_state": {
                        "type": DefsStateManagementType.VERSIONED_STATE_STORAGE.value,
                    }
                },
            },
            defs_path="migration_test",
        )

        # Initial load with versioned storage - should be "initial"
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            initial_metadata_value = spec.metadata["state_value"]
            assert initial_metadata_value == "initial"

            # Step 2: Run the update state job to populate versioned storage
            refresh_job = defs.get_job_def("state_refresh_job_migration_test")
            refresh_job.execute_in_process(instance=instance)

        # Step 3: Reload with versioned storage - should have updated value
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            versioned_metadata_value = spec.metadata["state_value"]
            assert versioned_metadata_value != "initial"
            assert versioned_metadata_value != initial_metadata_value

        # Step 4: Switch to local storage - should reset to initial value
        sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {
                    "defs_state": {
                        "type": DefsStateManagementType.LOCAL_FILESYSTEM.value,
                    }
                },
            },
            defs_path="migration_test",
        )

        # Load with local storage - should be back to "initial"
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            local_metadata_value = spec.metadata["state_value"]
            assert local_metadata_value == "initial"

        # Step 5: Load with DAGSTER_IS_DEV_CLI set - should force local refresh
        with (
            environ({"DAGSTER_IS_DEV_CLI": "1"}),
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
        ):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            dev_metadata_value = spec.metadata["state_value"]
            # Should have a non-initial value due to forced refresh in dev mode
            assert dev_metadata_value != "initial"
            # Should be different from the versioned value since it's a new random value
            assert dev_metadata_value != versioned_metadata_value
