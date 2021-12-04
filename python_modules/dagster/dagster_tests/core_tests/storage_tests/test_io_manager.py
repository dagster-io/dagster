import os
import tempfile

import mock
import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    Field,
    IOManagerDefinition,
    In,
    InputDefinition,
    ModeDefinition,
    Out,
    OutputDefinition,
    build_input_context,
    build_output_context,
    composite_solid,
    execute_pipeline,
    graph,
    job,
    op,
    pipeline,
    reexecute_pipeline,
    resource,
    solid,
)
from dagster.check import CheckError
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.context.output import get_output_context
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster.core.storage.io_manager import IOManager, io_manager
from dagster.core.storage.mem_io_manager import InMemoryIOManager, mem_io_manager
from dagster.core.system_config.objects import ResolvedRunConfig


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


def test_reexecute_subset_of_subset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral()

        my_fs_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        def my_pipeline_def(should_fail):
            @solid
            def one(_):
                return 1

            @solid
            def plus_two(_, i):
                if should_fail:
                    raise Exception()
                return i + 2

            @solid
            def plus_three(_, i):
                return i + 3

            @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": my_fs_io_manager})])
            def my_pipeline():
                plus_three(plus_two(one()))

            return my_pipeline

        first_result = execute_pipeline(
            my_pipeline_def(should_fail=True), instance=instance, raise_on_error=False
        )
        assert not first_result.success

        first_run_id = first_result.run_id

        second_result = reexecute_pipeline(
            my_pipeline_def(should_fail=False),
            instance=instance,
            parent_run_id=first_run_id,
            step_selection=["plus_two*"],
        )
        assert second_result.success
        assert second_result.result_for_solid("plus_two").output_value() == 3
        second_run_id = second_result.run_id

        # step_context._get_source_run_id should return first_run_id
        third_result = reexecute_pipeline(
            my_pipeline_def(should_fail=False),
            instance=instance,
            parent_run_id=second_run_id,
            step_selection=["plus_two*"],
        )
        assert third_result.success
        assert third_result.result_for_solid("plus_two").output_value() == 3


def test_reexecute_subset_of_subset_with_composite():
    @solid
    def one(_):
        return 1

    @solid
    def plus_two(_, i):
        return i + 2

    @composite_solid
    def one_plus_two():
        return plus_two(one())

    @solid
    def plus_three(_, i):
        return i + 3

    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral()

        my_fs_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": my_fs_io_manager})])
        def my_pipeline():
            plus_three(one_plus_two())

        first_result = execute_pipeline(my_pipeline, instance=instance)
        assert first_result.success
        first_run_id = first_result.run_id

        second_result = reexecute_pipeline(
            my_pipeline,
            instance=instance,
            parent_run_id=first_run_id,
            step_selection=["plus_three"],
        )
        assert second_result.success
        second_run_id = second_result.run_id

        # step_context._get_source_run_id should return first_run_id
        third_result = reexecute_pipeline(
            my_pipeline,
            instance=instance,
            parent_run_id=second_run_id,
            step_selection=["plus_three"],
        )
        assert third_result.success


def execute_pipeline_with_steps(
    instance,
    pipeline_def,
    step_keys_to_execute=None,
    run_id=None,
    parent_run_id=None,
    root_run_id=None,
):
    plan = create_execution_plan(pipeline_def, step_keys_to_execute=step_keys_to_execute)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        run_id=run_id,
        # the backfill flow can inject run group info
        parent_run_id=parent_run_id,
        root_run_id=root_run_id,
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

        instance = DagsterInstance.ephemeral()
        events = execute_pipeline_with_steps(instance, pipeline_def)
        for evt in events:
            assert not evt.is_failure

        run_id = "my_run_id"
        # when a path is provided via io manager, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations
        step_subset_events = execute_pipeline_with_steps(
            instance, pipeline_def, step_keys_to_execute=["solid_b"], run_id=run_id
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

        # test reexecution via backfills (not via re-execution apis)
        another_step_subset_events = execute_pipeline_with_steps(
            instance,
            pipeline_def,
            step_keys_to_execute=["solid_b"],
            parent_run_id=run_id,
            root_run_id=run_id,
        )
        for evt in another_step_subset_events:
            assert not evt.is_failure


def test_multi_materialization():
    class DummyIOManager(IOManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_output_identifier())
            self.values[keys] = obj

            yield AssetMaterialization(asset_key="yield_one")
            yield AssetMaterialization(asset_key="yield_two")

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_output_identifier())
            return self.values[keys]

        def has_asset(self, context):
            keys = tuple(context.get_output_identifier())
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
    output_context = build_output_context(step_key="step_key", name="output_name")
    mem_io_manager_instance.handle_output(output_context, 1)
    input_context = build_input_context(upstream_output=output_context)
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


def test_get_output_context_with_resources():
    @solid
    def basic_solid():
        pass

    @pipeline
    def basic_pipeline():
        basic_solid()

    with pytest.raises(
        CheckError,
        match="Expected either resources or step context to be set, but "
        "received both. If step context is provided, resources for IO manager will be "
        "retrieved off of that.",
    ):
        get_output_context(
            execution_plan=create_execution_plan(basic_pipeline),
            pipeline_def=basic_pipeline,
            resolved_run_config=ResolvedRunConfig.build(basic_pipeline),
            step_output_handle=StepOutputHandle("basic_solid", "result"),
            run_id=None,
            log_manager=None,
            step_context=mock.MagicMock(),
            resources=mock.MagicMock(),
            version=None,
        )


def test_error_boundary_with_gen():
    class ErrorIOManager(IOManager):
        def load_input(self, context):
            pass

        def handle_output(self, context, obj):
            yield AssetMaterialization(asset_key="a")
            raise ValueError("handle output error")

    @io_manager
    def error_io_manager(_):
        return ErrorIOManager()

    @solid
    def basic_solid():
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": error_io_manager})])
    def single_solid_pipeline():
        basic_solid()

    result = execute_pipeline(single_solid_pipeline, raise_on_error=False)
    step_failure = [
        event for event in result.event_list if event.event_type_value == "STEP_FAILURE"
    ][0]
    assert step_failure.event_specific_data.error.cls_name == "DagsterExecutionHandleOutputError"


def test_handle_output_exception_raised():
    class ErrorIOManager(IOManager):
        def load_input(self, context):
            pass

        def handle_output(self, context, obj):
            raise ValueError("handle output error")

    @io_manager
    def error_io_manager(_):
        return ErrorIOManager()

    @op
    def basic_op():
        return 5

    @job(resource_defs={"io_manager": error_io_manager})
    def single_op_job():
        basic_op()

    result = single_op_job.execute_in_process(raise_on_error=False)
    step_failure = [
        event for event in result.all_node_events if event.event_type_value == "STEP_FAILURE"
    ][0]
    assert step_failure.event_specific_data.error.cls_name == "DagsterExecutionHandleOutputError"


def test_output_identifier_dynamic_memoization():
    context = build_output_context(version="foo", mapping_key="bar", step_key="baz", name="buzz")

    with pytest.raises(
        CheckError,
        match="Mapping key and version both provided for output 'buzz' of step 'baz'. Dynamic "
        "mapping is not supported when using versioning.",
    ):
        context.get_output_identifier()


def test_asset_key():
    in_asset_key = AssetKey(["a", "b"])
    out_asset_key = AssetKey(["c", "d"])

    @op(out=Out(asset_key=out_asset_key))
    def before():
        pass

    @op(ins={"a": In(asset_key=in_asset_key)}, out={})
    def after(a):
        assert a

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.asset_key == in_asset_key
            assert context.upstream_output.asset_key == out_asset_key
            return 1

        def handle_output(self, context, obj):
            assert context.asset_key == out_asset_key

    @graph
    def my_graph():
        after(before())

    result = my_graph.to_job(
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())}
    ).execute_in_process()
    assert result.success


def test_partition_key():
    @op
    def my_op():
        pass

    @op
    def my_op2(_input1):
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.has_partition_key
            assert context.partition_key == "2020-01-01"

        def handle_output(self, context, _obj):
            assert context.has_partition_key
            assert context.partition_key == "2020-01-01"

    @job(
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    def my_job():
        my_op2(my_op())

    assert my_job.execute_in_process(partition_key="2020-01-01").success
