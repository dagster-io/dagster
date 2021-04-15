import os
import tempfile

import pytest
from dagster import (
    AssetMaterialization,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    Field,
    IOManagerDefinition,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    reexecute_pipeline,
    resource,
    solid,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.context.input import InputContext
from dagster.core.execution.context.output import OutputContext
from dagster.core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster.core.storage.io_manager import IOManager, io_manager
from dagster.core.storage.mem_io_manager import InMemoryIOManager, mem_io_manager


def test_io_manager_with_config():
    @solid
    def my_solid(_):
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.upstream_output.config["some_config"] == "some_value"
            return 1

        def handle_output(self, context, obj):
            assert context.config["some_config"] == "some_value"

    @io_manager(output_config_schema={"some_config": str})
    def configurable_io_manager(_):
        return MyIOManager()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": configurable_io_manager})])
    def my_pipeline():
        my_solid()

    run_config = {"solids": {"my_solid": {"outputs": {"result": {"some_config": "some_value"}}}}}
    result = execute_pipeline(my_pipeline, run_config=run_config)
    assert result.success


def test_io_manager_with_optional_config():
    @solid
    def my_solid(_):
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            pass

        def handle_output(self, context, obj):
            pass

    @io_manager(output_config_schema={"some_config": Field(str, is_required=False)})
    def configurable_io_manager(_):
        return MyIOManager()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": configurable_io_manager})])
    def my_pipeline():
        my_solid()

    result = execute_pipeline(my_pipeline)
    assert result.success


def test_io_manager_with_required_resource_keys():
    @solid
    def my_solid(_):
        pass

    class MyIOManager(IOManager):
        def __init__(self, prefix):
            self._prefix = prefix

        def load_input(self, context):
            assert context.resources.foo_resource == "foo"
            return self._prefix + "bar"

        def handle_output(self, _context, obj):
            pass

    @io_manager(required_resource_keys={"foo_resource"})
    def io_manager_requires_resource(init_context):
        return MyIOManager(init_context.resources.foo_resource)

    @resource
    def foo_resource(_):
        return "foo"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": io_manager_requires_resource,
                    "foo_resource": foo_resource,
                }
            )
        ]
    )
    def my_pipeline():
        my_solid()

    result = execute_pipeline(my_pipeline)
    assert result.success


def define_pipeline(manager, metadata_dict):
    @solid(output_defs=[OutputDefinition(metadata=metadata_dict.get("solid_a"))])
    def solid_a(_context):
        return [1, 2, 3]

    @solid(output_defs=[OutputDefinition(metadata=metadata_dict.get("solid_b"))])
    def solid_b(_context, _df):
        return 1

    @pipeline(mode_defs=[ModeDefinition("local", resource_defs={"io_manager": manager})])
    def my_pipeline():
        solid_b(solid_a())

    return my_pipeline


def test_result_output():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})
        pipeline_def = define_pipeline(default_io_manager, {})

        result = execute_pipeline(pipeline_def)
        assert result.success

        # test output_value
        assert result.result_for_solid("solid_a").output_value() == [1, 2, 3]
        assert result.result_for_solid("solid_b").output_value() == 1


def test_fs_io_manager_reexecution():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})
        pipeline_def = define_pipeline(default_io_manager, {})
        instance = DagsterInstance.ephemeral()

        result = execute_pipeline(pipeline_def, instance=instance)
        assert result.success

        re_result = reexecute_pipeline(
            pipeline_def,
            result.run_id,
            instance=instance,
            step_selection=["solid_b"],
        )

        # re-execution should yield asset_store_operation events instead of intermediate events
        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, re_result.event_list))
        assert len(loaded_input_events) == 1
        assert loaded_input_events[0].event_specific_data.upstream_step_key == "solid_a"


def test_can_reexecute():
    pipeline_def = define_pipeline(fs_io_manager, {})
    plan = create_execution_plan(pipeline_def)
    assert plan.artifacts_persisted


def execute_pipeline_with_steps(pipeline_def, step_keys_to_execute=None):
    plan = create_execution_plan(pipeline_def, step_keys_to_execute=step_keys_to_execute)
    with DagsterInstance.ephemeral() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            step_keys_to_execute=step_keys_to_execute,
        )
        return execute_plan(plan, InMemoryPipeline(pipeline_def), instance, pipeline_run)


def test_step_subset_with_custom_paths():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = custom_path_fs_io_manager.configured({"base_dir": tmpdir_path})
        # pass hardcoded file path via metadata
        test_metadata_dict = {
            "solid_a": {"path": "a"},
            "solid_b": {"path": "b"},
        }

        pipeline_def = define_pipeline(default_io_manager, test_metadata_dict)
        events = execute_pipeline_with_steps(pipeline_def)
        for evt in events:
            assert not evt.is_failure

        # when a path is provided via io manager, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations
        step_subset_events = execute_pipeline_with_steps(
            pipeline_def, step_keys_to_execute=["solid_b"]
        )
        for evt in step_subset_events:
            assert not evt.is_failure
        # only the selected step subset was executed
        assert set([evt.step_key for evt in step_subset_events]) == {"solid_b"}

        # Asset Materialization events
        step_materialization_events = list(
            filter(lambda evt: evt.is_step_materialization, step_subset_events)
        )
        assert len(step_materialization_events) == 1
        assert os.path.join(tmpdir_path, test_metadata_dict["solid_b"]["path"]) == (
            step_materialization_events[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )


def test_multi_materialization():
    class DummyIOManager(IOManager):
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

    @io_manager
    def dummy_io_manager(_):
        return DummyIOManager()

    @solid(output_defs=[OutputDefinition(io_manager_key="my_io_manager")])
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_io_manager": dummy_io_manager})])
    def my_pipeline():
        solid_b(solid_a())

    result = execute_pipeline(my_pipeline)
    assert result.success
    # Asset Materialization events
    step_materialization_events = list(
        filter(lambda evt: evt.is_step_materialization, result.event_list)
    )
    assert len(step_materialization_events) == 2


def test_different_io_managers():
    @solid(
        output_defs=[OutputDefinition(io_manager_key="my_io_manager")],
    )
    def solid_a(_context):
        return 1

    @solid()
    def solid_b(_context, a):
        assert a == 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_io_manager": mem_io_manager})])
    def my_pipeline():
        solid_b(solid_a())

    assert execute_pipeline(my_pipeline).success


@io_manager
def my_io_manager(_):
    pass


def test_set_io_manager_and_intermediate_storage():
    from dagster import intermediate_storage, fs_intermediate_storage

    @intermediate_storage()
    def my_intermediate_storage(_):
        pass

    with pytest.raises(DagsterInvariantViolationError):

        @pipeline(
            mode_defs=[
                ModeDefinition(
                    resource_defs={"io_manager": my_io_manager},
                    intermediate_storage_defs=[my_intermediate_storage, fs_intermediate_storage],
                )
            ]
        )
        def my_pipeline():
            pass

        execute_pipeline(my_pipeline)


def test_set_io_manager_configure_intermediate_storage():
    with pytest.raises(DagsterInvariantViolationError):

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": my_io_manager})])
        def my_pipeline():
            pass

        execute_pipeline(my_pipeline, run_config={"intermediate_storage": {"filesystem": {}}})


def test_io_manager_key_intermediate_storage():
    called = {"called": False}

    @io_manager
    def custom_io_manager(_):
        class CustomIOManager(IOManager):
            def handle_output(self, _, _obj):
                called["called"] = True

            def load_input(self, _):
                pass

        return CustomIOManager()

    @solid(output_defs=[OutputDefinition(io_manager_key="my_key")])
    def solid1(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_key": custom_io_manager})])
    def my_pipeline():
        solid1()

    execute_pipeline(my_pipeline, run_config={"intermediate_storage": {"filesystem": {}}})
    assert called["called"]


def test_fan_in():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        @solid
        def input_solid1(_):
            return 1

        @solid
        def input_solid2(_):
            return 2

        @solid
        def solid1(_, input1):
            assert input1 == [1, 2]

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": default_io_manager})])
        def my_pipeline():
            solid1(input1=[input_solid1(), input_solid2()])

        execute_pipeline(my_pipeline)


def test_fan_in_skip():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        @solid(output_defs=[OutputDefinition(name="skip", is_required=False)])
        def skip(_):
            return
            yield  # pylint: disable=unreachable

        @solid
        def one(_):
            return 1

        @solid
        def receiver(_, input1):
            assert input1 == [1]

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": default_io_manager})])
        def my_pipeline():
            receiver(input1=[one(), skip()])

        assert execute_pipeline(my_pipeline).success


def test_configured():
    @io_manager(
        config_schema={"base_dir": str},
        description="abc",
        output_config_schema={"path": str},
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def an_io_manager(_):
        pass

    configured_io_manager = an_io_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_io_manager, IOManagerDefinition)
    assert configured_io_manager.description == an_io_manager.description
    assert configured_io_manager.output_config_schema == an_io_manager.output_config_schema
    assert configured_io_manager.input_config_schema == an_io_manager.input_config_schema
    assert configured_io_manager.required_resource_keys == an_io_manager.required_resource_keys
    assert configured_io_manager.version is None


def test_mem_io_manager_execution():
    mem_io_manager_instance = InMemoryIOManager()
    output_context = OutputContext(
        step_key="step_key",
        name="output_name",
        pipeline_name="foo",
    )
    mem_io_manager_instance.handle_output(output_context, 1)
    input_context = InputContext(
        pipeline_name="foo",
        upstream_output=output_context,
    )
    assert mem_io_manager_instance.load_input(input_context) == 1


def test_io_manager_resources_on_context():
    @resource
    def foo_resource(_):
        return "foo"

    @io_manager(required_resource_keys={"foo_resource"})
    def io_manager_reqs_resources(init_context):
        assert init_context.resources.foo_resource == "foo"

        class InternalIOManager(IOManager):
            def handle_output(self, context, obj):
                assert context.resources.foo_resource == "foo"

            def load_input(self, context):
                assert context.resources.foo_resource == "foo"

        return InternalIOManager()

    @solid(
        input_defs=[
            InputDefinition("_manager_input", root_manager_key="io_manager_reqs_resources")
        ],
        output_defs=[
            OutputDefinition(dagster_type=str, io_manager_key="io_manager_reqs_resources")
        ],
    )
    def big_solid(_, _manager_input):
        return "manager_input"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager_reqs_resources": io_manager_reqs_resources,
                    "foo_resource": foo_resource,
                }
            )
        ]
    )
    def basic_pipeline():
        big_solid()

    result = execute_pipeline(basic_pipeline)

    assert result.success


def test_mem_io_managers_result_for_solid():
    @solid
    def one(_):
        return 1

    @solid
    def add_one(_, x):
        return x + 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": mem_io_manager})])
    def my_pipeline():
        add_one(one())

    result = execute_pipeline(my_pipeline)
    assert result.success
    assert result.result_for_solid("one").output_value() == 1
    assert result.result_for_solid("add_one").output_value() == 2


def test_mode_missing_io_manager():
    @solid(output_defs=[OutputDefinition(io_manager_key="missing_io_manager")])
    def my_solid(_):
        return 1

    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline
        def _my_pipeline():
            my_solid()


def test_hardcoded_io_manager():
    @solid
    def basic_solid(_):
        return 5

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(InMemoryIOManager())
                }
            )
        ]
    )
    def basic_pipeline():
        basic_solid()

    result = execute_pipeline(basic_pipeline)
    assert result.success
    assert result.output_for_solid("basic_solid") == 5
