# pylint: disable=unused-argument
import os
import sys
import time

import pytest
from dagster import (
    Failure,
    Field,
    MetadataEntry,
    Nothing,
    Output,
    String,
    multiprocess_executor,
    reconstructable,
)
from dagster._core.definitions import op
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.errors import DagsterUnmetExecutorRequirementsError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.results import OpExecutionResult, PipelineExecutionResult
from dagster._core.instance import DagsterInstance
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.test_utils import default_mode_def_for_test, instance_for_test
from dagster._legacy import (
    PresetDefinition,
    execute_pipeline,
    pipeline,
)
from dagster._utils import safe_tempfile_path, segfault

from .retry_jobs import (
    assert_expected_failure_behavior,
    get_dynamic_job_op_failure,
    get_dynamic_job_resource_init_failure,
)


def test_diamond_simple_execution():
    result = execute_pipeline(define_diamond_pipeline())
    assert result.success
    assert result.result_for_node("adder").output_value() == 11


def compute_event(result: PipelineExecutionResult, solid_name: str) -> DagsterEvent:
    node_result = result.result_for_node(solid_name)
    assert isinstance(node_result, OpExecutionResult)
    return node_result.compute_step_events[0]


def test_diamond_multi_execution():
    with instance_for_test() as instance:
        pipe = reconstructable(define_diamond_pipeline)
        result = execute_pipeline(
            pipe,
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert result.success

        assert result.result_for_node("adder").output_value() == 11


def test_explicit_spawn():
    with instance_for_test() as instance:
        pipe = reconstructable(define_diamond_pipeline)
        result = execute_pipeline(
            pipe,
            run_config={
                "execution": {"multiprocess": {"config": {"start_method": {"spawn": {}}}}},
            },
            instance=instance,
        )
        assert result.success

        assert result.result_for_node("adder").output_value() == 11


@pytest.mark.skipif(os.name == "nt", reason="No forkserver on windows")
def test_forkserver_execution():
    with instance_for_test() as instance:
        pipe = reconstructable(define_diamond_pipeline)
        result = execute_pipeline(
            pipe,
            run_config={
                "execution": {"multiprocess": {"config": {"start_method": {"forkserver": {}}}}},
            },
            instance=instance,
        )
        assert result.success

        assert result.result_for_node("adder").output_value() == 11


@pytest.mark.skipif(os.name == "nt", reason="No forkserver on windows")
def test_forkserver_preload():
    with instance_for_test() as instance:
        pipe = reconstructable(define_diamond_pipeline)
        result = execute_pipeline(
            pipe,
            run_config={
                "execution": {
                    "multiprocess": {
                        "config": {"start_method": {"forkserver": {"preload_modules": []}}}
                    }
                },
            },
            instance=instance,
        )
        assert result.success

        assert result.result_for_node("adder").output_value() == 11


def define_diamond_pipeline():
    @op
    def return_two():
        return 2

    @op(ins={"num": In()})
    def add_three(num):
        return num + 3

    @op(ins={"num": In()})
    def mult_three(num):
        return num * 3

    @op(ins={"left": In(), "right": In()})
    def adder(left, right):
        return left + right

    @pipeline(
        preset_defs=[
            PresetDefinition(
                "just_adder",
                {
                    "execution": {"multiprocess": {}},
                    "solids": {"adder": {"inputs": {"left": {"value": 1}, "right": {"value": 1}}}},
                },
                solid_selection=["adder"],
            )
        ],
        mode_defs=[default_mode_def_for_test],
    )
    def diamond_pipeline():
        two = return_two()
        adder(left=add_three(two), right=mult_three(two))

    return diamond_pipeline


def define_in_mem_pipeline():
    @op
    def return_two():
        return 2

    @op(ins={"num": In()})
    def add_three(num):
        return num + 3

    @pipeline
    def in_mem_pipeline():
        add_three(return_two())

    return in_mem_pipeline


def define_error_pipeline():
    @op
    def should_never_execute(_x):
        assert False  # this should never execute

    @op
    def throw_error():
        raise Exception("bad programmer")

    @pipeline(mode_defs=[default_mode_def_for_test])
    def error_pipeline():
        should_never_execute(throw_error())

    return error_pipeline


def test_error_pipeline():
    pipe = define_error_pipeline()
    result = execute_pipeline(pipe, raise_on_error=False)
    assert not result.success


def test_error_pipeline_multiprocess():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_error_pipeline),
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert not result.success


def test_mem_storage_error_pipeline_multiprocess():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterUnmetExecutorRequirementsError,
            match=(
                "your pipeline includes solid outputs that will not be stored somewhere where other"
                " processes can retrieve them."
            ),
        ):
            execute_pipeline(
                reconstructable(define_in_mem_pipeline),
                run_config={"execution": {"multiprocess": {}}},
                instance=instance,
                raise_on_error=False,
            )


def test_invalid_instance():
    result = execute_pipeline(
        reconstructable(define_diamond_pipeline),
        run_config={"execution": {"multiprocess": {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_failure_data.error.cls_name
        == "DagsterUnmetExecutorRequirementsError"
    )
    assert "non-ephemeral instance" in result.event_list[0].pipeline_failure_data.error.message


def test_no_handle():
    result = execute_pipeline(
        define_diamond_pipeline(),
        run_config={"execution": {"multiprocess": {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_failure_data.error.cls_name
        == "DagsterUnmetExecutorRequirementsError"
    )
    assert "is not reconstructable" in result.event_list[0].pipeline_failure_data.error.message


def test_solid_selection():
    with instance_for_test() as instance:
        pipe = reconstructable(define_diamond_pipeline)

        result = execute_pipeline(pipe, preset="just_adder", instance=instance)

        assert result.success

        assert result.result_for_node("adder").output_value() == 2


def define_subdag_pipeline():
    @op(config_schema=Field(String))
    def waiter(context):
        done = False
        while not done:
            time.sleep(0.15)
            if os.path.isfile(context.op_config):
                return

    @op(
        ins={"after": In(Nothing)},
        config_schema=Field(String),
    )
    def writer(context):
        with open(context.op_config, "w", encoding="utf8") as fd:
            fd.write("1")
        return

    @op(
        ins={"after": In(Nothing)},
        out=Out(Nothing),
    )
    def noop():
        pass

    @pipeline(mode_defs=[default_mode_def_for_test])
    def separate():
        waiter()
        a = noop.alias("noop_1")()
        b = noop.alias("noop_2")(a)
        c = noop.alias("noop_3")(b)
        writer(c)

    return separate


def test_separate_sub_dags():
    with instance_for_test() as instance:
        pipe = reconstructable(define_subdag_pipeline)

        with safe_tempfile_path() as filename:
            result = execute_pipeline(
                pipe,
                run_config={
                    "execution": {"multiprocess": {"config": {"max_concurrent": 2}}},
                    "solids": {
                        "waiter": {"config": filename},
                        "writer": {"config": filename},
                    },
                },
                instance=instance,
            )

        assert result.success

        # this test is to ensure that the chain of noop -> noop -> noop -> writer is not blocked by waiter
        order = [
            str(event.solid_handle) for event in result.step_event_list if event.is_step_success
        ]

        # the writer and waiter my finish in different orders so just ensure the proceeding chain
        assert order[0:3] == ["noop_1", "noop_2", "noop_3"]


def test_ephemeral_event_log():
    with instance_for_test(
        overrides={
            "event_log_storage": {
                "module": "dagster._core.storage.event_log",
                "class": "InMemoryEventLogStorage",
            }
        }
    ) as instance:
        pipe = reconstructable(define_diamond_pipeline)
        # override event log to in memory

        result = execute_pipeline(
            pipe,
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert result.success

        assert result.result_for_node("adder").output_value() == 11


@op(
    out={
        "option_1": Out(is_required=False),
        "option_2": Out(is_required=False),
    }
)
def either_or(_context):
    yield Output(1, "option_1")


@op
def echo(x):
    return x


@pipeline(mode_defs=[default_mode_def_for_test])
def optional_stuff():
    option_1, option_2 = either_or()
    echo(echo(option_1))
    echo(echo(option_2))


def test_optional_outputs():
    with instance_for_test() as instance:
        single_result = execute_pipeline(optional_stuff)
        assert single_result.success
        assert not [event for event in single_result.step_event_list if event.is_step_failure]
        assert len([event for event in single_result.step_event_list if event.is_step_skipped]) == 2

        multi_result = execute_pipeline(
            reconstructable(optional_stuff),
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert multi_result.success
        assert not [event for event in multi_result.step_event_list if event.is_step_failure]
        assert len([event for event in multi_result.step_event_list if event.is_step_skipped]) == 2


@op
def throw():
    raise Failure(
        description="it Failure",
        metadata_entries=[MetadataEntry("label", value="text")],
    )


@pipeline(mode_defs=[default_mode_def_for_test])
def failure():
    throw()


def test_failure_multiprocessing():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(failure),
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
            raise_on_error=False,
        )
        assert not result.success
        failure_data = result.result_for_node("throw").failure_data
        assert failure_data
        assert failure_data.error.cls_name == "Failure"

        # hard coded
        assert failure_data.user_failure_data.label == "intentional-failure"
        # from Failure
        assert failure_data.user_failure_data.description == "it Failure"
        assert failure_data.user_failure_data.metadata_entries[0].label == "label"
        assert failure_data.user_failure_data.metadata_entries[0].value.text == "text"


@op
def sys_exit(context):
    context.log.info("Informational message")
    print("Crashy output to stdout")  # noqa: T201
    sys.stdout.flush()
    os._exit(1)  # pylint: disable=W0212


@pipeline(mode_defs=[default_mode_def_for_test])
def sys_exit_pipeline():
    sys_exit()


@pytest.mark.skipif(os.name == "nt", reason="Different crash output on Windows: See issue #2791")
def test_crash_multiprocessing():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(sys_exit_pipeline),
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
            raise_on_error=False,
        )
        assert not result.success
        failure_data = result.result_for_node("sys_exit").failure_data
        assert failure_data
        assert failure_data.error.cls_name == "ChildProcessCrashException"

        assert failure_data.user_failure_data is None

        capture_events = [
            event
            for event in result.event_list
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        event = capture_events[0]
        assert isinstance(instance.compute_log_manager, CapturedLogManager)
        log_key = instance.compute_log_manager.build_log_key_for_run(
            result.run_id, event.logs_captured_data.file_key
        )
        log_data = instance.compute_log_manager.get_log_data(log_key)

        assert "Crashy output to stdout" in log_data.stdout.decode("utf-8")

        # The argument to sys.exit won't (reliably) make it to the compute logs for stderr b/c the
        # LocalComputeLogManger is in-process -- documenting this behavior here though we may want to
        # change it

        # assert (
        #     'Crashy output to stderr' not in log_data.stdout.decode("utf-8")
        # )


# segfault test
@op
def segfault_solid(context):
    context.log.info("Informational message")
    print("Crashy output to stdout")  # noqa: T201
    segfault()


@pipeline(mode_defs=[default_mode_def_for_test])
def segfault_pipeline():
    segfault_solid()


@pytest.mark.skipif(os.name == "nt", reason="Different exception on Windows: See issue #2791")
def test_crash_hard_multiprocessing():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(segfault_pipeline),
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
            raise_on_error=False,
        )
        assert not result.success
        failure_data = result.result_for_node("segfault_solid").failure_data
        assert failure_data
        assert failure_data.error.cls_name == "ChildProcessCrashException"

        assert failure_data.user_failure_data is None

        # Neither the stderr not the stdout spew will (reliably) make it to the compute logs --
        # documenting this behavior here though we may want to change it

        # assert (
        #     'Crashy output to stdout'
        #     not in instance.compute_log_manager.read_logs_file(
        #         result.run_id, 'segfault_solid', ComputeIOType.STDOUT
        #     ).data
        # )

        # assert (
        #     instance.compute_log_manager.read_logs_file(
        #         result.run_id, 'sys_exit', ComputeIOType.STDERR
        #     ).data
        #     is None
        # )


def get_dynamic_resource_init_failure_job():
    return get_dynamic_job_resource_init_failure(multiprocess_executor)[0]


def get_dynamic_op_failure_job():
    return get_dynamic_job_op_failure(multiprocess_executor)[0]


# Tests identical retry behavior when a job fails because of resource
# initialization of a dynamic step, and failure during op runtime of a
# dynamic step.
@pytest.mark.parametrize(
    "job_fn,config_fn",
    [
        (
            get_dynamic_resource_init_failure_job,
            get_dynamic_job_resource_init_failure(multiprocess_executor)[1],
        ),
        (
            get_dynamic_op_failure_job,
            get_dynamic_job_op_failure(multiprocess_executor)[1],
        ),
    ],
)
def test_dynamic_failure_retry(job_fn, config_fn):
    assert_expected_failure_behavior(job_fn, config_fn)
