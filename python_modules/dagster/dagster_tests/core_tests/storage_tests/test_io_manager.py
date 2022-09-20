import os
import tempfile
import time

import mock
import pytest

from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    DagsterInvariantViolationError,
    DynamicOut,
    DynamicOutput,
    Field,
    IOManagerDefinition,
    In,
    MetadataEntry,
    Nothing,
    Out,
    ReexecutionOptions,
    build_input_context,
    build_output_context,
    execute_job,
    graph,
    in_process_executor,
    job,
    op,
    reconstructable,
    resource,
)
from dagster._check import CheckError
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.context.output import get_output_context
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster._core.storage.io_manager import IOManager, io_manager
from dagster._core.storage.mem_io_manager import InMemoryIOManager, mem_io_manager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import instance_for_test


def test_io_manager_with_config():
    @op
    def my_op():
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.upstream_output.config["some_config"] == "some_value"
            return 1

        def handle_output(self, context, obj):
            assert context.config["some_config"] == "some_value"

    @io_manager(output_config_schema={"some_config": str})
    def configurable_io_manager():
        return MyIOManager()

    @job(resource_defs={"io_manager": configurable_io_manager})
    def my_job():
        my_op()

    run_config = {"solids": {"my_op": {"outputs": {"result": {"some_config": "some_value"}}}}}
    result = my_job.execute_in_process(run_config=run_config)
    assert result.success


def test_io_manager_with_optional_config():
    @op
    def my_op():
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            pass

        def handle_output(self, context, obj):
            pass

    @io_manager(output_config_schema={"some_config": Field(str, is_required=False)})
    def configurable_io_manager():
        return MyIOManager()

    @job(resource_defs={"io_manager": configurable_io_manager})
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.success


def test_io_manager_with_required_resource_keys():
    @op
    def my_op():
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
    def foo_resource():
        return "foo"

    @job(
        resource_defs={
            "io_manager": io_manager_requires_resource,
            "foo_resource": foo_resource,
        }
    )
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.success


def define_job(manager, metadata_dict):
    @op(out=Out(metadata=metadata_dict.get("op_a")))
    def op_a(_context):
        return [1, 2, 3]

    @op(out=Out(metadata=metadata_dict.get("op_b")))
    def op_b(_context, _df):
        return 1

    @job(resource_defs={"io_manager": manager}, executor_def=in_process_executor)
    def my_job():
        op_b(op_a())

    return my_job


def define_fs_io_manager_job():
    return define_job(fs_io_manager, {})


def test_result_output():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})
        job_def = define_job(default_io_manager, {})

        result = job_def.execute_in_process()
        assert result.success

        # test output_value
        assert result.output_for_node("op_a") == [1, 2, 3]
        assert result.output_for_node("op_b") == 1


def test_fs_io_manager_reexecution():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test() as instance:
            result = execute_job(
                reconstructable(define_fs_io_manager_job),
                instance,
                run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
            )
            assert result.success
            re_result = execute_job(
                reconstructable(define_fs_io_manager_job),
                instance,
                run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
                reexecution_options=ReexecutionOptions(
                    parent_run_id=result.run_id, step_selection=["op_b"]
                ),
            )
            assert re_result.success
            loaded_input_events = re_result.filter_events(lambda evt: evt.is_loaded_input)
            assert len(loaded_input_events) == 1
            assert loaded_input_events[0].event_specific_data.upstream_step_key == "op_a"
            assert [
                evt.step_key for evt in re_result.filter_events(lambda evt: evt.is_step_success)
            ] == ["op_b"]


def test_can_reexecute():
    job_def = define_job(fs_io_manager, {})
    plan = create_execution_plan(job_def)
    assert plan.artifacts_persisted


def define_can_fail_job():
    @op
    def one():
        return 1

    @op(config_schema={"should_fail": bool})
    def plus_two(context, i):
        if context.op_config["should_fail"] is True:
            raise Exception()
        return i + 2

    @op
    def plus_three(i):
        return i + 3

    @job(executor_def=in_process_executor)
    def my_job():
        plus_three(plus_two(one()))

    return my_job


def test_reexecute_subset_of_subset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test() as instance:
            result = execute_job(
                reconstructable(define_can_fail_job),
                instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": True}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
            )
            assert not result.success
            reexecution_options = ReexecutionOptions.from_failure(result.run_id, instance)
            with execute_job(
                reconstructable(define_can_fail_job),
                instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": False}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                reexecution_options=reexecution_options,
            ) as first_re_result:
                assert first_re_result.success
                assert first_re_result.output_for_node("plus_two") == 3
            with execute_job(
                reconstructable(define_can_fail_job),
                instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": False}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                reexecution_options=ReexecutionOptions(
                    first_re_result.run_id, step_selection=["plus_two*"]
                ),
            ) as second_re_result:
                assert second_re_result.success
                assert second_re_result.output_for_node("plus_two") == 3

            with execute_job(
                reconstructable(define_can_fail_job),
                instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": False}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                reexecution_options=ReexecutionOptions(
                    second_re_result.run_id, step_selection=["plus_two*"]
                ),
            ) as third_re_result:
                assert third_re_result.success
                assert third_re_result.output_for_node("plus_two") == 3


def define_composite_job():
    @op
    def one():
        return 1

    @op
    def plus_two(i):
        return i + 2

    @graph
    def one_plus_two():
        return plus_two(one())

    @op
    def plus_three(i):
        return i + 3

    @job(executor_def=in_process_executor)
    def my_job():
        plus_three(one_plus_two())

    return my_job


def test_reexecute_subset_of_subset_with_composite():

    with instance_for_test() as instance:
        result = execute_job(reconstructable(define_composite_job), instance)
        assert result.success

        first_re_result = execute_job(
            reconstructable(define_composite_job),
            instance,
            reexecution_options=ReexecutionOptions(result.run_id, step_selection=["plus_three"]),
        )
        assert first_re_result.success

        second_re_result = execute_job(
            reconstructable(define_composite_job),
            instance,
            reexecution_options=ReexecutionOptions(result.run_id, step_selection=["plus_three"]),
        )
        assert second_re_result.success

        third_re_result = execute_job(
            reconstructable(define_composite_job),
            instance,
            reexecution_options=ReexecutionOptions(result.run_id, step_selection=["plus_three"]),
        )
        assert third_re_result.success


def execute_job_with_steps(
    instance,
    job_fn,
    step_keys_to_execute=None,
    run_id=None,
    parent_run_id=None,
    root_run_id=None,
    run_config=None,
):
    recon_job = reconstructable(job_fn)
    plan = create_execution_plan(
        recon_job, step_keys_to_execute=step_keys_to_execute, run_config=run_config
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=recon_job.get_definition(),
        run_id=run_id,
        # the backfill flow can inject run group info
        parent_run_id=parent_run_id,
        root_run_id=root_run_id,
        run_config=run_config,
    )
    return execute_plan(plan, recon_job, instance, pipeline_run, run_config=run_config)


def define_metadata_job():
    test_metadata_dict = {
        "op_a": {"path": "a"},
        "op_b": {"path": "b"},
    }
    return define_job(custom_path_fs_io_manager, test_metadata_dict)


def test_step_subset_with_custom_paths():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral()
        # pass hardcoded file path via metadata
        test_metadata_dict = {
            "op_a": {"path": "a"},
            "op_b": {"path": "b"},
        }

        events = execute_job_with_steps(
            instance,
            define_metadata_job,
            run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
        )
        for evt in events:
            assert not evt.is_failure

        run_id = "my_run_id"
        # when a path is provided via io manager, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations
        step_subset_events = execute_job_with_steps(
            instance,
            define_metadata_job,
            step_keys_to_execute=["op_b"],
            run_id=run_id,
            run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
        )
        for evt in step_subset_events:
            assert not evt.is_failure
        # only the selected step subset was executed
        assert set([evt.step_key for evt in step_subset_events]) == {"op_b"}

        # Asset Materialization events
        step_materialization_events = list(
            filter(lambda evt: evt.is_step_materialization, step_subset_events)
        )
        assert len(step_materialization_events) == 1
        assert os.path.join(tmpdir_path, test_metadata_dict["op_b"]["path"]) == (
            step_materialization_events[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )

        # test reexecution via backfills (not via re-execution apis)
        another_step_subset_events = execute_job_with_steps(
            instance,
            define_metadata_job,
            step_keys_to_execute=["op_b"],
            parent_run_id=run_id,
            root_run_id=run_id,
            run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
        )
        for evt in another_step_subset_events:
            assert not evt.is_failure


def test_multi_materialization():
    class DummyIOManager(IOManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_identifier())
            self.values[keys] = obj

            yield AssetMaterialization(asset_key="yield_one")
            yield AssetMaterialization(asset_key="yield_two")

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_identifier())
            return self.values[keys]

        def has_asset(self, context):
            keys = tuple(context.get_identifier())
            return keys in self.values

    @io_manager
    def dummy_io_manager():
        return DummyIOManager()

    @op(out=Out(io_manager_key="my_io_manager"))
    def op_a(_context):
        return 1

    @op()
    def op_b(_context, a):
        assert a == 1

    @job(resource_defs={"my_io_manager": dummy_io_manager})
    def my_job():
        op_b(op_a())

    result = my_job.execute_in_process()
    assert result.success
    # Asset Materialization events
    step_materialization_events = result.filter_events(lambda evt: evt.is_step_materialization)

    assert len(step_materialization_events) == 2


def test_different_io_managers():
    @op(
        out=Out(io_manager_key="my_io_manager"),
    )
    def op_a(_context):
        return 1

    @op()
    def op_b(_context, a):
        assert a == 1

    @job(resource_defs={"my_io_manager": mem_io_manager})
    def my_job():
        op_b(op_a())

    assert my_job.execute_in_process().success


@io_manager
def my_io_manager():
    pass


def test_fan_in():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        @op
        def input_op1():
            return 1

        @op
        def input_op2():
            return 2

        @op
        def op1(input1):
            assert input1 == [1, 2]

        @job(resource_defs={"io_manager": default_io_manager})
        def my_job():
            op1(input1=[input_op1(), input_op2()])

        my_job.execute_in_process()


def test_fan_in_skip():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        default_io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})

        @op(out={"skip": Out(is_required=False)})
        def skip():
            return
            yield  # pylint: disable=unreachable

        @op
        def one():
            return 1

        @op
        def receiver(input1):
            assert input1 == [1]

        @job(resource_defs={"io_manager": default_io_manager})
        def my_job():
            receiver(input1=[one(), skip()])

        assert my_job.execute_in_process().success


def test_configured():
    @io_manager(
        config_schema={"base_dir": str},
        description="abc",
        output_config_schema={"path": str},
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def an_io_manager():
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
    def foo_resource():
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

    @op(
        ins={"_manager_input": In(root_manager_key="io_manager_reqs_resources")},
        out=Out(dagster_type=str, io_manager_key="io_manager_reqs_resources"),
    )
    def big_op(_manager_input):
        return "manager_input"

    @job(
        resource_defs={
            "io_manager_reqs_resources": io_manager_reqs_resources,
            "foo_resource": foo_resource,
        }
    )
    def basic_job():
        big_op()

    result = basic_job.execute_in_process()

    assert result.success


def test_mem_io_managers_result_for_solid():
    @op
    def one():
        return 1

    @op
    def add_one(x):
        return x + 1

    @job(resource_defs={"io_manager": mem_io_manager})
    def my_job():
        add_one(one())

    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("one") == 1
    assert result.output_for_node("add_one") == 2


def test_hardcoded_io_manager():
    @op
    def basic_op():
        return 5

    @job(
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(InMemoryIOManager())}
    )
    def basic_job():
        basic_op()

    result = basic_job.execute_in_process()
    assert result.success
    assert result.output_for_node("basic_op") == 5


def test_get_output_context_with_resources():
    @op
    def basic_op():
        pass

    @job
    def basic_job():
        basic_op()

    with pytest.raises(
        CheckError,
        match="Expected either resources or step context to be set, but "
        "received both. If step context is provided, resources for IO manager will be "
        "retrieved off of that.",
    ):
        get_output_context(
            execution_plan=create_execution_plan(basic_job),
            pipeline_def=basic_job,
            resolved_run_config=ResolvedRunConfig.build(basic_job),
            step_output_handle=StepOutputHandle("basic_op", "result"),
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
    def error_io_manager():
        return ErrorIOManager()

    @op
    def basic_op():
        return 5

    @job(resource_defs={"io_manager": error_io_manager})
    def single_solid_job():
        basic_op()

    result = single_solid_job.execute_in_process(raise_on_error=False)
    step_failure = [
        event for event in result.all_events if event.event_type_value == "STEP_FAILURE"
    ][0]
    assert step_failure.event_specific_data.error.cls_name == "DagsterExecutionHandleOutputError"


def test_handle_output_exception_raised():
    class ErrorIOManager(IOManager):
        def load_input(self, context):
            pass

        def handle_output(self, context, obj):
            raise ValueError("handle output error")

    @io_manager
    def error_io_manager():
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
        context.get_identifier()


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


def test_context_logging_user_events():
    class DummyIOManager(IOManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_identifier())
            self.values[keys] = obj

            context.log_event(AssetMaterialization(asset_key="first"))
            time.sleep(1)
            context.log.debug("foo bar")
            context.log_event(AssetMaterialization(asset_key="second"))

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_identifier())
            return self.values[keys]

    @op
    def the_op():
        return 5

    @graph
    def the_graph():
        the_op()

    with instance_for_test() as instance:
        result = the_graph.execute_in_process(
            resources={"io_manager": DummyIOManager()}, instance=instance
        )

        assert result.success

        relevant_event_logs = [
            event_log
            for event_log in instance.all_logs(result.run_id)
            if event_log.dagster_event is not None
            and event_log.dagster_event.is_step_materialization
        ]

        log_entries = [
            event_log
            for event_log in instance.all_logs(result.run_id)
            if event_log.dagster_event is None
        ]

        log = log_entries[0]
        assert log.user_message == "foo bar"

        first = relevant_event_logs[0]
        assert first.dagster_event.event_specific_data.materialization.label == "first"

        second = relevant_event_logs[1]
        assert second.dagster_event.event_specific_data.materialization.label == "second"

        assert second.timestamp - first.timestamp >= 1
        assert log.timestamp - first.timestamp >= 1


def test_context_logging_metadata():
    def build_for_materialization(materialization):
        class DummyIOManager(IOManager):
            def __init__(self):
                self.values = {}

            def handle_output(self, context, obj):
                keys = tuple(context.get_identifier())
                self.values[keys] = obj

                context.add_output_metadata({"foo": "bar"})
                yield MetadataEntry("baz", value="baz")
                context.add_output_metadata({"bar": "bar"})
                yield materialization

            def load_input(self, context):
                keys = tuple(context.upstream_output.get_identifier())
                return self.values[keys]

        @op(out=Out(asset_key=AssetKey("key_on_out")))
        def the_op():
            return 5

        @graph
        def the_graph():
            the_op()

        return the_graph.execute_in_process(resources={"io_manager": DummyIOManager()})

    result = build_for_materialization(AssetMaterialization("no_metadata"))
    assert result.success

    output_event = result.all_node_events[4]
    entry_labels = [entry.label for entry in output_event.event_specific_data.metadata_entries]
    # Ensure that ordering is preserved among yields and calls to log
    assert entry_labels == ["foo", "baz", "bar"]

    materialization_event = result.all_node_events[2]
    metadata_entries = materialization_event.event_specific_data.materialization.metadata_entries

    assert len(metadata_entries) == 3
    entry_labels = [entry.label for entry in metadata_entries]
    assert entry_labels == ["foo", "baz", "bar"]

    implicit_materialization_event = result.all_node_events[3]
    metadata_entries = (
        implicit_materialization_event.event_specific_data.materialization.metadata_entries
    )
    assert len(metadata_entries) == 3
    entry_labels = [entry.label for entry in metadata_entries]
    assert entry_labels == ["foo", "baz", "bar"]

    with pytest.raises(
        DagsterInvariantViolationError,
        match="When handling output 'result' of op 'the_op', received a materialization with metadata, while context.add_output_metadata was used within the same call to handle_output. Due to potential conflicts, this is not allowed. Please specify metadata in one place within the `handle_output` function.",
    ):
        build_for_materialization(AssetMaterialization("has_metadata", metadata={"bar": "baz"}))


def test_metadata_dynamic_outputs():
    class DummyIOManager(IOManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_identifier())
            self.values[keys] = obj

            yield MetadataEntry("handle_output", value="I come from handle_output")

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_identifier())
            return self.values[keys]

    @op(out=DynamicOut(asset_key=AssetKey(["foo"])))
    def the_op():
        yield DynamicOutput(1, mapping_key="one", metadata={"one": "blah"})
        yield DynamicOutput(2, mapping_key="two", metadata={"two": "blah"})

    @graph
    def the_graph():
        the_op()

    result = the_graph.execute_in_process(resources={"io_manager": DummyIOManager()})
    materializations = result.asset_materializations_for_node("the_op")
    assert len(materializations) == 2
    for materialization in materializations:
        assert materialization.metadata_entries[1].label == "handle_output"
        assert materialization.metadata_entries[1].entry_data.text == "I come from handle_output"

    assert materializations[0].metadata_entries[0].label == "one"
    assert materializations[1].metadata_entries[0].label == "two"


def test_nothing_output_nothing_input():
    class MyIOManager(IOManager):
        def __init__(self):
            self.handle_output_calls = 0

        def load_input(self, context):
            assert False

        def handle_output(self, context, obj):
            self.handle_output_calls += 1

    my_io_manager = MyIOManager()

    @op(out=Out(Nothing))
    def op1():
        ...

    @op(ins={"input1": In(Nothing)})
    def op2():
        ...

    @job(resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(my_io_manager)})
    def job1():
        op2(op1())

    job1.execute_in_process()

    assert my_io_manager.handle_output_calls == 2


def test_nothing_output_something_input():
    class MyIOManager(IOManager):
        def __init__(self):
            self.handle_output_calls = 0
            self.handle_input_calls = 0

        def load_input(self, context):
            self.handle_input_calls += 1

        def handle_output(self, context, obj):
            self.handle_output_calls += 1

    my_io_manager = MyIOManager()

    @op(out=Out(Nothing))
    def op1():
        ...

    @op
    def op2(_input1):
        ...

    @job(resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(my_io_manager)})
    def job1():
        op2(op1())

    job1.execute_in_process()

    assert my_io_manager.handle_output_calls == 2
    assert my_io_manager.handle_input_calls == 1
