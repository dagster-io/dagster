import json
import random
from pathlib import Path
from typing import Optional

import dagster as dg
from dagster._core.instance_for_test import instance_for_test
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.testing.utils import create_defs_folder_sandbox


class MyStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            value = "initial"
        else:
            with open(state_path) as f:
                state = json.load(f)
            value = state["value"]

        @dg.asset(metadata={"state_value": value})
        def the_asset():
            return dg.MaterializeResult(metadata={"foo": value})

        return dg.Definitions(assets=[the_asset])

    def write_state_to_path(self, state_path: Path):
        with open(state_path, "w") as f:
            json.dump({"value": f"bar_{random.randint(1000, 9999)}"}, f)

    def _get_state_refresh_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.op
        def refresh_state_op():
            self.refresh_state(context)

        @dg.job
        def state_refresh_job():
            refresh_state_op()

        return dg.Definitions(jobs=[state_refresh_job])

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions.merge(
            super().build_defs(context),
            self._get_state_refresh_defs(context),
        )


def test_simple_state_backed_component() -> None:
    with instance_for_test() as instance, create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=MyStateBackedComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.state_backed_component_tests.test_state_backed_component.MyStateBackedComponent",
            },
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
            mats = result.asset_materializations_for_node("the_asset")
            assert len(mats) == 1
            assert mats[0].metadata["foo"] == dg.TextMetadataValue(original_metadata_value)

        # reload the definitions, state should be the same
        with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            # metadata should remain the same
            assert spec.metadata["state_value"] == original_metadata_value

            # now execute the job to refresh the state
            refresh_job = defs.get_job_def("state_refresh_job")
            refresh_job.execute_in_process(instance=instance)

        # now we reload the definitions, state should be updated to something random
        with sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            spec = specs[0]
            new_metadata_value = spec.metadata["state_value"]
            assert new_metadata_value != original_metadata_value
