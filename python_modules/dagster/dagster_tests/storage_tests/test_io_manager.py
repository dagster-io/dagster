import os
import tempfile
import time
from collections.abc import Mapping
from unittest import mock

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    Definitions,
    DynamicOut,
    DynamicOutput,
    Field,
    In,
    IOManagerDefinition,
    Nothing,
    Out,
    ReexecutionOptions,
    asset,
    build_input_context,
    build_output_context,
    execute_job,
    graph,
    in_process_executor,
    job,
    materialize,
    op,
    reconstructable,
    resource,
)
from dagster._check import CheckError
from dagster._core.definitions.events import Output
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.errors import DagsterInvalidMetadata
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext, get_output_context
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster._core.storage.io_manager import IOManager, dagster_maintained_io_manager, io_manager
from dagster._core.storage.mem_io_manager import InMemoryIOManager, mem_io_manager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import instance_for_test
from dagster._core.utils import make_new_run_id


def test_io_manager_with_config():
    @op
    def my_op():
        pass

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.upstream_output.config["some_config"] == "some_value"  # pyright: ignore[reportOptionalMemberAccess]
            return 1

        def handle_output(self, context, obj):
            assert context.config["some_config"] == "some_value"

    @io_manager(output_config_schema={"some_config": str})
    def configurable_io_manager():
        return MyIOManager()

    @job(resource_defs={"io_manager": configurable_io_manager})
    def my_job():
        my_op()

    run_config = {"ops": {"my_op": {"outputs": {"result": {"some_config": "some_value"}}}}}
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


def define_job(
    manager: IOManagerDefinition, metadata_dict: Mapping[str, ArbitraryMetadataMapping]
) -> JobDefinition:
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
            assert loaded_input_events[0].event_specific_data.upstream_step_key == "op_a"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
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
    dagster_run = instance.create_run_for_job(
        job_def=recon_job.get_definition(),
        run_id=run_id,
        # the backfill flow can inject run group info
        parent_run_id=parent_run_id,
        root_run_id=root_run_id,
        run_config=run_config,
    )
    return execute_plan(plan, recon_job, instance, dagster_run, run_config=run_config)


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

        run_id = make_new_run_id()
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
        assert set([evt.step_key for evt in step_subset_events if evt.step_key]) == {"op_b"}

        # Asset Materialization events
        step_materialization_events = list(
            filter(lambda evt: evt.is_step_materialization, step_subset_events)
        )
        assert len(step_materialization_events) == 1
        assert os.path.join(tmpdir_path, test_metadata_dict["op_b"]["path"]) == (
            step_materialization_events[0].event_specific_data.materialization.metadata["path"].path  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
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
            keys = tuple(context.upstream_output.get_identifier())  # pyright: ignore[reportOptionalMemberAccess]
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


@io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
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
            yield

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
    @io_manager(  # pyright: ignore[reportArgumentType]
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
        ins={"_manager_input": In(input_manager_key="io_manager_reqs_resources")},
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


def test_mem_io_managers_result_for_op():
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
        match=(
            "Expected either resources or step context to be set, but "
            "received both. If step context is provided, resources for IO manager will be "
            "retrieved off of that."
        ),
    ):
        get_output_context(
            execution_plan=create_execution_plan(basic_job),
            job_def=basic_job,
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
    def single_op_job():
        basic_op()

    result = single_op_job.execute_in_process(raise_on_error=False)
    step_failure = next(
        event for event in result.all_events if event.event_type_value == "STEP_FAILURE"
    )
    assert step_failure.event_specific_data.error.cls_name == "DagsterExecutionHandleOutputError"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


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
    step_failure = next(
        event for event in result.all_node_events if event.event_type_value == "STEP_FAILURE"
    )
    assert step_failure.event_specific_data.error.cls_name == "DagsterExecutionHandleOutputError"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_output_identifier_dynamic_memoization():
    context = build_output_context(version="foo", mapping_key="bar", step_key="baz", name="buzz")

    with pytest.raises(
        CheckError,
        match=(
            "Mapping key and version both provided for output 'buzz' of step 'baz'. Dynamic "
            "mapping is not supported when using versioning."
        ),
    ):
        context.get_identifier()


def test_asset_key():
    @asset
    def before():
        pass

    @asset
    def after(before):
        assert before

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.asset_key == before.key
            assert context.upstream_output.asset_key == before.key  # pyright: ignore[reportOptionalMemberAccess]
            return 1

        def handle_output(self, context, obj):
            assert context.asset_key in {before.key, after.key}

    result = materialize([before, after], resources={"io_manager": MyIOManager()})
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
            keys = tuple(context.upstream_output.get_identifier())  # pyright: ignore[reportOptionalMemberAccess]
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
        assert first.dagster_event.event_specific_data.materialization.label == "first"  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]

        second = relevant_event_logs[1]
        assert second.dagster_event.event_specific_data.materialization.label == "second"  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]

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
                yield {"baz": "baz"}
                context.add_output_metadata({"bar": "bar"})
                yield materialization

            def load_input(self, context):
                keys = tuple(context.upstream_output.get_identifier())  # pyright: ignore[reportOptionalMemberAccess]
                return self.values[keys]

        @asset
        def key_on_out():
            return 5

        return materialize([key_on_out], resources={"io_manager": DummyIOManager()})

    result = build_for_materialization(AssetMaterialization("no_metadata"))
    assert result.success

    output_event = result.all_node_events[4]
    metadata = output_event.event_specific_data.metadata  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    # Ensure that ordering is preserved among yields and calls to log
    assert set(metadata.keys()) == {"foo", "baz", "bar"}

    materialization_event = result.all_node_events[2]
    metadata = materialization_event.event_specific_data.materialization.metadata  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    assert len(metadata) == 3
    assert set(metadata.keys()) == {"foo", "baz", "bar"}

    implicit_materialization_event = result.all_node_events[3]
    metadata = implicit_materialization_event.event_specific_data.materialization.metadata  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert len(metadata) == 3
    assert set(metadata.keys()) == {"foo", "baz", "bar"}

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "When handling output 'result' of op 'key_on_out', received a materialization with"
            " metadata, while context.add_output_metadata was used within the same call to"
            " handle_output. Due to potential conflicts, this is not allowed. Please specify"
            " metadata in one place within the `handle_output` function."
        ),
    ):
        build_for_materialization(AssetMaterialization("has_metadata", metadata={"bar": "baz"}))


def test_context_logging_metadata_add_output_metadata_called_twice():
    class DummyIOManager(IOManager):
        def handle_output(self, context, obj):
            del obj
            context.add_output_metadata({"foo": 1})
            context.add_output_metadata({"bar": 2})
            with pytest.raises(DagsterInvalidMetadata):
                context.add_output_metadata({"bar": 3})

        def load_input(self, context):
            del context

    @asset
    def asset1():
        return 5

    result = materialize([asset1], resources={"io_manager": DummyIOManager()})

    assert result.success
    materialization = result.asset_materializations_for_node("asset1")[0]
    assert set(materialization.metadata.keys()) == {"foo", "bar"}

    handled_output_event = next(
        event for event in result.all_node_events if event.event_type_value == "HANDLED_OUTPUT"
    )
    assert set(handled_output_event.event_specific_data.metadata.keys()) == {  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        "foo",
        "bar",
    }


def test_metadata_dynamic_outputs():
    class DummyIOManager(IOManager):
        def __init__(self):
            self.values = {}

        def handle_output(self, context, obj):
            keys = tuple(context.get_identifier())
            self.values[keys] = obj

            yield {"handle_output": "I come from handle_output"}

        def load_input(self, context):
            keys = tuple(context.upstream_output.get_identifier())  # pyright: ignore[reportOptionalMemberAccess]
            return self.values[keys]

    @op(out=DynamicOut())
    def the_op():
        yield DynamicOutput(1, mapping_key="one", metadata={"one": "blah"})
        yield DynamicOutput(2, mapping_key="two", metadata={"two": "blah"})

    @graph
    def the_graph():
        the_op()

    assert the_graph.execute_in_process(resources={"io_manager": DummyIOManager()}).success


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
    def op1(): ...

    @op(ins={"input1": In(Nothing)})
    def op2(): ...

    @job(resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(my_io_manager)})
    def job1():
        op2(op1())

    job1.execute_in_process()

    assert my_io_manager.handle_output_calls == 1  # Nothing return type for op1 skips I/O manager


def test_nothing_output_something_input():
    class MyIOManager(IOManager):
        def __init__(self):
            self.handle_output_calls = 0
            self.handle_input_calls = 0
            self.outs = {}

        def load_input(self, context):
            self.handle_input_calls += 1
            if tuple(context.get_identifier()) in self.outs.keys():
                return self.outs[tuple(context.get_identifier())]

            else:
                raise Exception("No corresponding output")

        def handle_output(self, context, obj):
            self.handle_output_calls += 1
            self.outs[tuple(context.get_identifier())] = obj

    my_io_manager = MyIOManager()

    @op(out=Out(Nothing))
    def op1(): ...

    @op
    def op2(_input1): ...

    @job(resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(my_io_manager)})
    def job1():
        op2(op1())

    with pytest.raises(Exception, match="No corresponding output"):
        job1.execute_in_process()

        assert (
            my_io_manager.handle_output_calls == 0
        )  # Nothing return type for op1 skips I/O manager
        assert my_io_manager.handle_input_calls == 1


def test_nothing_typing_type_non_none_return():
    @asset
    def returns_1() -> None:
        return 1  # type: ignore

    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([returns_1])


def test_instance_set_on_input_context():
    executed = {}

    class AssertingContextInputOnLoadInputIOManager(IOManager):
        def __init__(self):
            pass

        def load_input(self, context):
            assert context.instance
            executed["yes"] = True

        def handle_output(self, _context, _obj):
            pass

    @op
    def op1():
        pass

    @op
    def op2(_an_input):
        pass

    asserting_io_manager = AssertingContextInputOnLoadInputIOManager()

    @job(
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(asserting_io_manager)}
    )
    def job1():
        op2(op1())

    job1.execute_in_process()

    assert executed["yes"]


def test_instance_set_on_asset_loader():
    executed = {}

    class AssertingContextInputOnLoadInputIOManager(IOManager):
        def __init__(self):
            pass

        def load_input(self, context):
            assert context.instance
            executed["yes"] = True
            return 1

        def handle_output(self, _context, _obj):
            pass

    @asset
    def an_asset() -> int:
        return 1

    @asset
    def another_asset(an_asset: int) -> int:
        return an_asset + 1

    with DagsterInstance.ephemeral() as instance:
        defs = Definitions(
            assets=[an_asset, another_asset],
            resources={"io_manager": AssertingContextInputOnLoadInputIOManager()},
        )
        defs.get_implicit_global_asset_job_def().execute_in_process(
            asset_selection=[AssetKey("an_asset")], instance=instance
        )
        # load_input not called when asset does not have any inputs
        assert not executed.get("yes")

        defs.load_asset_value("another_asset", instance=instance)

        assert executed["yes"]


def test_telemetry_custom_io_manager():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            return {}

        def load_input(self, context):
            return 1

    @io_manager
    def my_io_manager():
        return MyIOManager()

    assert not my_io_manager._is_dagster_maintained()  # noqa: SLF001


def test_telemetry_dagster_io_manager():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            return {}

        def load_input(self, context):
            return 1

    @dagster_maintained_io_manager
    @io_manager
    def my_io_manager():
        return MyIOManager()

    assert my_io_manager._is_dagster_maintained()  # noqa: SLF001


def test_metadata_in_io_manager():
    expected_metadata = {"foo": "bar"}

    class MyDefinitionMetadataIOManager(IOManager):
        def handle_output(self, context: OutputContext, obj):
            assert context.definition_metadata == expected_metadata

        def load_input(self, context: InputContext):
            assert context.upstream_output
            assert context.upstream_output.definition_metadata == expected_metadata

    class MyOutputMetadataIOManager(IOManager):
        def handle_output(self, context: OutputContext, obj):
            normalized_metadata = (
                {
                    key: value if isinstance(value, str) else value.text
                    for key, value in context.output_metadata.items()
                }
                if context.output_metadata
                else None
            )
            assert normalized_metadata == expected_metadata

        def load_input(self, context: InputContext):
            assert context.upstream_output
            assert context.upstream_output.output_metadata == {}

    class MyAllMetadataIOManager(IOManager):
        def handle_output(self, context: OutputContext, obj):
            normalized_metadata = (
                {
                    key: value if isinstance(value, str) else value.text
                    for key, value in context.output_metadata.items()
                }
                if context.output_metadata
                else None
            )
            assert normalized_metadata == expected_metadata

            assert context.definition_metadata == expected_metadata

        def load_input(self, context: InputContext):
            assert context.upstream_output
            assert context.upstream_output.output_metadata == {}
            assert context.upstream_output.definition_metadata == expected_metadata

    @asset(metadata=expected_metadata)
    def metadata_on_def():
        return 1

    @asset
    def downstream_1(metadata_on_def) -> None:
        return None

    materialize(
        [metadata_on_def, downstream_1], resources={"io_manager": MyDefinitionMetadataIOManager()}
    )

    @asset
    def metadata_on_output():
        return Output(1, metadata=expected_metadata)

    @asset
    def downstream_2(metadata_on_output) -> None:
        return None

    materialize(
        [metadata_on_output, downstream_2], resources={"io_manager": MyOutputMetadataIOManager()}
    )

    @asset
    def metadata_added_to_context(context: AssetExecutionContext):
        context.add_output_metadata(expected_metadata)

    @asset
    def downstream_3(metadata_added_to_context) -> None:
        return None

    materialize(
        [metadata_added_to_context, downstream_3],
        resources={"io_manager": MyOutputMetadataIOManager()},
    )

    @asset(metadata=expected_metadata)
    def override_metadata(context: AssetExecutionContext):
        context.add_output_metadata(expected_metadata)

    @asset
    def downstream_4(override_metadata) -> None:
        return None

    materialize(
        [override_metadata, downstream_4], resources={"io_manager": MyAllMetadataIOManager()}
    )
