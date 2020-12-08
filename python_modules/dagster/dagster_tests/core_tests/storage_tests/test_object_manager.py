import os

import pytest
from dagster import (
    AssetMaterialization,
    DagsterInstance,
    DagsterInvariantViolationError,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    reexecute_pipeline,
    seven,
    solid,
)
from dagster.core.definitions.events import AssetStoreOperationType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.storage.asset_store import mem_asset_store
from dagster.core.storage.fs_object_manager import custom_path_fs_object_manager, fs_object_manager
from dagster.core.storage.object_manager import ObjectManager, object_manager


def test_object_manager_with_config():
    @solid
    def my_solid(_):
        pass

    class MyObjectManager(ObjectManager):
        def load_input(self, context):
            assert context.upstream_output.config["some_config"] == "some_value"
            return 1

        def handle_output(self, context, obj):
            assert context.config["some_config"] == "some_value"

    @object_manager(output_config_schema={"some_config": str})
    def configurable_object_manager(_):
        return MyObjectManager()

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"object_manager": configurable_object_manager})]
    )
    def my_pipeline():
        my_solid()

    run_config = {"solids": {"my_solid": {"outputs": {"result": {"some_config": "some_value"}}}}}
    result = execute_pipeline(my_pipeline, run_config=run_config)
    assert result.output_for_solid("my_solid") == 1


def define_pipeline(manager, metadata_dict):
    @solid(output_defs=[OutputDefinition(metadata=metadata_dict.get("solid_a"),)],)
    def solid_a(_context):
        return [1, 2, 3]

    @solid(output_defs=[OutputDefinition(metadata=metadata_dict.get("solid_b"),)],)
    def solid_b(_context, _df):
        return 1

    @pipeline(mode_defs=[ModeDefinition("local", resource_defs={"object_manager": manager})])
    def my_pipeline():
        solid_b(solid_a())

    return my_pipeline


def test_result_output():
    with seven.TemporaryDirectory() as tmpdir_path:
        asset_store = fs_object_manager.configured({"base_dir": tmpdir_path})
        pipeline_def = define_pipeline(asset_store, {})

        result = execute_pipeline(pipeline_def)
        assert result.success

        # test output_value
        assert result.result_for_solid("solid_a").output_value() == [1, 2, 3]
        assert result.result_for_solid("solid_b").output_value() == 1


def test_default_object_manager_reexecution():
    with seven.TemporaryDirectory() as tmpdir_path:
        default_asset_store = fs_object_manager.configured({"base_dir": tmpdir_path})
        pipeline_def = define_pipeline(default_asset_store, {})
        instance = DagsterInstance.ephemeral()

        result = execute_pipeline(pipeline_def, instance=instance)
        assert result.success

        re_result = reexecute_pipeline(
            pipeline_def, result.run_id, instance=instance, step_selection=["solid_b.compute"],
        )

        # re-execution should yield asset_store_operation events instead of intermediate events
        get_asset_events = list(
            filter(
                lambda evt: evt.is_asset_store_operation
                and AssetStoreOperationType(evt.event_specific_data.op)
                == AssetStoreOperationType.GET_ASSET,
                re_result.event_list,
            )
        )
        assert len(get_asset_events) == 1
        assert get_asset_events[0].event_specific_data.step_key == "solid_a.compute"


def execute_pipeline_with_steps(pipeline_def, step_keys_to_execute=None):
    plan = create_execution_plan(pipeline_def, step_keys_to_execute=step_keys_to_execute)
    with DagsterInstance.ephemeral() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def, step_keys_to_execute=step_keys_to_execute,
        )
        return execute_plan(plan, instance, pipeline_run)


def test_step_subset_with_custom_paths():
    with seven.TemporaryDirectory() as tmpdir_path:
        asset_store = custom_path_fs_object_manager
        # pass hardcoded file path via asset_metadata
        test_asset_metadata_dict = {
            "solid_a": {"path": os.path.join(tmpdir_path, "a")},
            "solid_b": {"path": os.path.join(tmpdir_path, "b")},
        }

        pipeline_def = define_pipeline(asset_store, test_asset_metadata_dict)
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


def test_multi_materialization():
    class DummyObjectManager(ObjectManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_run_scoped_output_identifier())
            self.values[keys] = obj

            yield AssetMaterialization(asset_key="yield_one")
            yield AssetMaterialization(asset_key="yield_two")

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_run_scoped_output_identifier())
            return self.values[keys]

        def has_asset(self, context):
            keys = tuple(context.get_run_scoped_output_identifier())
            return keys in self.values

    @object_manager
    def dummy_object_manager(_):
        return DummyObjectManager()

    @solid(output_defs=[OutputDefinition(manager_key="my_object_manager")])
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_object_manager": dummy_object_manager})])
    def my_pipeline():
        solid_b(solid_a())

    result = execute_pipeline(my_pipeline)
    assert result.success
    # Asset Materialization events
    step_materialization_events = list(
        filter(lambda evt: evt.is_step_materialization, result.event_list)
    )
    assert len(step_materialization_events) == 2


def test_different_object_managers():
    @solid(output_defs=[OutputDefinition(manager_key="my_object_manager")],)
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_object_manager": mem_asset_store})])
    def my_pipeline():
        solid_b(solid_a())

    assert execute_pipeline(my_pipeline).success


@object_manager
def my_object_manager(_):
    pass


def test_set_object_manager_and_intermediate_storage():
    from dagster import intermediate_storage, fs_intermediate_storage

    @intermediate_storage()
    def my_intermediate_storage(_):
        pass

    with pytest.raises(DagsterInvariantViolationError):

        @pipeline(
            mode_defs=[
                ModeDefinition(
                    resource_defs={"object_manager": my_object_manager},
                    intermediate_storage_defs=[my_intermediate_storage, fs_intermediate_storage],
                )
            ]
        )
        def my_pipeline():
            pass

        execute_pipeline(my_pipeline)


def test_set_asset_store_configure_intermediate_storage():
    with pytest.raises(DagsterInvariantViolationError):

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": my_object_manager})])
        def my_pipeline():
            pass

        execute_pipeline(my_pipeline, run_config={"intermediate_storage": {"filesystem": {}}})


def test_fan_in():
    with seven.TemporaryDirectory() as tmpdir_path:
        asset_store = fs_object_manager.configured({"base_dir": tmpdir_path})

        @solid
        def input_solid1(_):
            return 1

        @solid
        def input_solid2(_):
            return 2

        @solid
        def solid1(_, input1):
            assert input1 == [1, 2]

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": asset_store})])
        def my_pipeline():
            solid1(input1=[input_solid1(), input_solid2()])

        execute_pipeline(my_pipeline)


def get_fake_solid():
    @solid
    def fake_solid(_):
        pass

    return fake_solid
