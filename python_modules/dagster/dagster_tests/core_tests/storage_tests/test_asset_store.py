import os
import pickle

from dagster import (
    DagsterInstance,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    resource,
    seven,
    solid,
)
from dagster.core.definitions.events import AssetMaterialization, AssetStoreOperationType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.storage.asset_store import (
    AssetStore,
    custom_path_filesystem_asset_store,
    default_filesystem_asset_store,
    mem_asset_store,
)


def define_asset_pipeline(asset_store, asset_metadata_dict):
    @solid(
        output_defs=[
            OutputDefinition(
                asset_store_key="default_fs_asset_store",
                asset_metadata=asset_metadata_dict.get("solid_a"),
            )
        ],
    )
    def solid_a(_context):
        return [1, 2, 3]

    @solid(
        output_defs=[
            OutputDefinition(
                asset_store_key="default_fs_asset_store",
                asset_metadata=asset_metadata_dict.get("solid_b"),
            )
        ],
    )
    def solid_b(_context, _df):
        return 1

    @pipeline(
        mode_defs=[ModeDefinition("local", resource_defs={"default_fs_asset_store": asset_store})]
    )
    def asset_pipeline():
        solid_b(solid_a())

    return asset_pipeline


def test_default_asset_store():
    with seven.TemporaryDirectory() as tmpdir_path:
        default_asset_store = default_filesystem_asset_store.configured({"base_dir": tmpdir_path})
        pipeline_def = define_asset_pipeline(default_asset_store, {})

        result = execute_pipeline(pipeline_def)
        assert result.success

        asset_store_operation_events = list(
            filter(lambda evt: evt.is_asset_store_operation, result.event_list)
        )

        assert len(asset_store_operation_events) == 3
        # SET ASSET for step "solid_a.compute" output "result"
        assert (
            asset_store_operation_events[0].event_specific_data.op
            == AssetStoreOperationType.SET_ASSET
        )
        filepath_a = os.path.join(tmpdir_path, result.run_id, "solid_a.compute", "result")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        # GET ASSET for step "solid_b.compute" input "_df"
        assert (
            asset_store_operation_events[1].event_specific_data.op
            == AssetStoreOperationType.GET_ASSET
        )
        assert (
            StepOutputHandle("solid_a.compute", "result")
            == asset_store_operation_events[1].event_specific_data.step_output_handle
        )

        # SET ASSET for step "solid_b.compute" output "result"
        assert (
            asset_store_operation_events[2].event_specific_data.op
            == AssetStoreOperationType.SET_ASSET
        )
        filepath_b = os.path.join(tmpdir_path, result.run_id, "solid_b.compute", "result")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == 1


def execute_pipeline_with_steps(pipeline_def, step_keys_to_execute=None):
    plan = create_execution_plan(pipeline_def, step_keys_to_execute=step_keys_to_execute)
    with DagsterInstance.ephemeral() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def, step_keys_to_execute=step_keys_to_execute,
        )
        return execute_plan(plan, instance, pipeline_run)


def test_step_subset_with_custom_paths():
    with seven.TemporaryDirectory() as tmpdir_path:
        default_asset_store = custom_path_filesystem_asset_store
        # pass hardcoded file path via asset_metadata
        test_asset_metadata_dict = {
            "solid_a": {"path": os.path.join(tmpdir_path, "a")},
            "solid_b": {"path": os.path.join(tmpdir_path, "b")},
        }

        pipeline_def = define_asset_pipeline(default_asset_store, test_asset_metadata_dict)
        events = execute_pipeline_with_steps(pipeline_def)
        for evt in events:
            assert not evt.is_failure

        # when a path is provided via asset store, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations
        step_subset_events = execute_pipeline_with_steps(
            pipeline_def, step_keys_to_execute=["solid_b.compute"]
        )
        for evt in step_subset_events:
            assert not evt.is_failure
        # only the selected step subset was executed
        assert set([evt.step_key for evt in step_subset_events]) == {"solid_b.compute"}

        # Asset Materialization events
        step_materialization_events = list(
            filter(lambda evt: evt.is_step_materialization, step_subset_events)
        )
        assert len(step_materialization_events) == 1
        assert test_asset_metadata_dict["solid_b"]["path"] == (
            step_materialization_events[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )


def test_asset_store_multi_materialization():
    class DummyAssetStore(AssetStore):
        def __init__(self):
            self.values = {}

        def set_asset(self, _context, step_output_handle, obj, _asset_metadata):
            self.values[step_output_handle] = obj

            yield AssetMaterialization(asset_key="yield_one")
            yield AssetMaterialization(asset_key="yield_two")

        def get_asset(self, _context, step_output_handle, _asset_metadata):
            return self.values[step_output_handle]

    @resource
    def dummy_asset_store(_):
        return DummyAssetStore()

    @solid(output_defs=[OutputDefinition(asset_store_key="store")],)
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"store": dummy_asset_store})])
    def asset_pipeline():
        solid_b(solid_a())

    result = execute_pipeline(asset_pipeline)
    assert result.success
    # Asset Materialization events
    step_materialization_events = list(
        filter(lambda evt: evt.is_step_materialization, result.event_list)
    )
    assert len(step_materialization_events) == 2


def test_different_asset_stores():
    @solid(output_defs=[OutputDefinition(asset_store_key="store")],)
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"store": mem_asset_store})])
    def asset_pipeline():
        solid_b(solid_a())

    assert execute_pipeline(asset_pipeline).success
