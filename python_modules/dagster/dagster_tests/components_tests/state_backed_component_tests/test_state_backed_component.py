import asyncio
import json
import random
import shutil
from pathlib import Path
from typing import Optional

import dagster as dg
import pytest
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.component_tree import ComponentTreeException
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster.components.utils.defs_state import DefsStateConfig, ResolvedDefsStateConfig
from dagster_shared.serdes.objects.models.defs_state_info import (
    DefsStateManagementType,
    get_code_server_metadata_key,
)


class MyStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    defs_state_key: Optional[str] = None
    defs_state: ResolvedDefsStateConfig = DefsStateConfig.versioned_state_storage()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return self.defs_state

    def get_defs_state_key(self) -> str:
        return self.defs_state_key or super().get_defs_state_key()

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
        @dg.op
        def refresh_state_op():
            asyncio.run(self.refresh_state())

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
def test_simple_state_backed_component(storage_location: DefsStateManagementType) -> None:
    with instance_for_test() as instance, create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
                "attributes": {"defs_state": {"type": storage_location.value}},
            },
            defs_path="foo",
        )

        # initial load, no state written, so use "initial"
        with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
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

        # reload the definitions, state should be the same
        with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            # metadata should remain the same
            assert spec.metadata["state_value"] == original_metadata_value

            # now execute the job to refresh the state
            refresh_job = defs.get_job_def("state_refresh_job_foo")
            refresh_job.execute_in_process(instance=instance)

        # now we reload the definitions, state should be updated to something random
        with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            new_metadata_value = spec.metadata["state_value"]
            assert new_metadata_value != original_metadata_value


def test_code_server_state_backed_component() -> None:
    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
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

        with scoped_definitions_load_context(
            load_type=DefinitionsLoadType.INITIALIZATION,
        ):
            with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
                specs = defs.get_all_asset_specs()
                spec = specs[0]
                original_metadata_value = spec.metadata["state_value"]
                # should automatically load
                assert original_metadata_value != "initial"

                repo = defs.get_repository_def()
                assert repo.repository_load_data is not None

            load_context = DefinitionsLoadContext.get()
            assert load_context.load_type == DefinitionsLoadType.INITIALIZATION
            pending_metadata = load_context.get_pending_reconstruction_metadata()
            key = get_code_server_metadata_key("MyStateBackedComponent")
            assert pending_metadata.keys() == {"defs-state-[MyStateBackedComponent]"}
            # last bit is random
            assert '{"value": "bar_' in pending_metadata[key]
            assert load_context.defs_state_info is not None

        # now simulate the reconstruction process
        with scoped_definitions_load_context(
            load_type=DefinitionsLoadType.RECONSTRUCTION,
            repository_load_data=RepositoryLoadData(
                cacheable_asset_data={},
                reconstruction_metadata=pending_metadata,
                defs_state_info=load_context.defs_state_info,
            ),
        ):
            with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
                specs = defs.get_all_asset_specs()
                spec = specs[0]
                assert spec.metadata["state_value"] == original_metadata_value
                assert "bar_" in spec.metadata["state_value"]


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

        with scoped_definitions_load_context(
            load_type=DefinitionsLoadType.INITIALIZATION,
        ):
            with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
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

        with pytest.raises(
            ComponentTreeException,
            match="MyStateBackedComponent",
        ):
            with sandbox.build_all_defs():
                pass

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
