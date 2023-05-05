import os
import sys
import time

import pytest
from dagster import (
    Failure,
    Field,
    In,
    JobDefinition,
    Nothing,
    Out,
    Output,
    String,
    job,
    multiprocess_executor,
    op,
    reconstructable,
)
from dagster._check import CheckError
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.errors import DagsterUnmetExecutorRequirementsError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution import execution_result
from dagster._core.execution.api import execute_job
from dagster._core.instance import DagsterInstance
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.storage.mem_io_manager import mem_io_manager
from dagster._core.test_utils import (
    instance_for_test,
)
from dagster._utils import safe_tempfile_path, segfault

from .retry_jobs import (
    assert_expected_failure_behavior,
    get_dynamic_job_op_failure,
    get_dynamic_job_resource_init_failure,
)


def test_diamond_simple_execution():
    result = define_diamond_job().execute_in_process()
    assert result.success
    assert result.output_for_node("adder") == 11


def compute_event(result: execution_result.ExecutionResult, op_name: str) -> DagsterEvent:
    for event in result.events_for_node(op_name):
        if event.step_kind_value == "COMPUTE":
            return event
    raise Exception(f"Could not find compute event for op {op_name}")


def test_diamond_multi_execution():
    with instance_for_test() as instance:
        recon_job = reconstructable(define_diamond_job)
        with execute_job(
            recon_job,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 11


def test_explicit_spawn():
    with instance_for_test() as instance:
        recon_job = reconstructable(define_diamond_job)
        with execute_job(
            recon_job,
            run_config={
                "execution": {"config": {"multiprocess": {"start_method": {"spawn": {}}}}},
            },
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 11


@pytest.mark.skipif(os.name == "nt", reason="No forkserver on windows")
def test_forkserver_execution():
    with instance_for_test() as instance:
        recon_job = reconstructable(define_diamond_job)
        with execute_job(
            recon_job,
            run_config={
                "execution": {"config": {"multiprocess": {"start_method": {"forkserver": {}}}}},
            },
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 11


@pytest.mark.skipif(os.name == "nt", reason="No forkserver on windows")
def test_forkserver_preload():
    with instance_for_test() as instance:
        recon_job = reconstructable(define_diamond_job)
        with execute_job(
            recon_job,
            run_config={
                "execution": {
                    "config": {
                        "multiprocess": {"start_method": {"forkserver": {"preload_modules": []}}}
                    }
                },
            },
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 11


JUST_ADDER_CONFIG = {
    "ops": {"adder": {"inputs": {"left": {"value": 1}, "right": {"value": 1}}}},
}


def define_diamond_job() -> JobDefinition:
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

    @job
    def diamond_job():
        two = return_two()
        adder(left=add_three(two), right=mult_three(two))

    return diamond_job


def define_in_mem_job():
    @op
    def return_two():
        return 2

    @op(ins={"num": In()})
    def add_three(num):
        return num + 3

    @job(resource_defs={"io_manager": mem_io_manager})
    def in_mem_job():
        add_three(return_two())

    return in_mem_job


def define_error_job():
    @op
    def should_never_execute(_x):
        assert False  # this should never execute

    @op
    def throw_error():
        raise Exception("bad programmer")

    @job
    def error_job():
        should_never_execute(throw_error())

    return error_job


def test_error_job():
    job_def = define_error_job()
    result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success


def test_error_job_multiprocess():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(define_error_job),
            instance=instance,
        ) as result:
            assert not result.success


def test_mem_storage_error_job_multiprocess():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterUnmetExecutorRequirementsError,
            match=(
                "your job includes op outputs that will not be stored somewhere where other"
                " processes can retrieve them."
            ),
        ):
            execute_job(
                reconstructable(define_in_mem_job),
                instance=instance,
                raise_on_error=False,
            )


def test_invalid_instance():
    with execute_job(
        reconstructable(define_diamond_job),
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    ) as result:
        assert not result.success
        assert len(result.all_events) == 1
        assert result.all_events[0].is_failure
        assert (
            result.all_events[0].job_failure_data.error.cls_name
            == "DagsterUnmetExecutorRequirementsError"
        )
        assert "non-ephemeral instance" in result.all_events[0].job_failure_data.error.message


def test_no_handle():
    with pytest.raises(CheckError, match='Param "job" is not a ReconstructableJob.'):
        execute_job(
            define_diamond_job(),
            instance=DagsterInstance.ephemeral(),
            raise_on_error=False,
        )


def test_op_selection():
    with instance_for_test() as instance:
        recon_job = reconstructable(define_diamond_job)

        with execute_job(
            recon_job, instance=instance, run_config=JUST_ADDER_CONFIG, op_selection=["adder"]
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 2


def define_subdag_job():
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

    @job
    def separate():
        waiter()
        a = noop.alias("noop_1")()
        b = noop.alias("noop_2")(a)
        c = noop.alias("noop_3")(b)
        writer(c)

    return separate


def test_separate_sub_dags():
    with instance_for_test() as instance:
        pipe = reconstructable(define_subdag_job)

        with safe_tempfile_path() as filename:
            with execute_job(
                pipe,
                run_config={
                    "execution": {"config": {"multiprocess": {"max_concurrent": 2}}},
                    "ops": {
                        "waiter": {"config": filename},
                        "writer": {"config": filename},
                    },
                },
                instance=instance,
            ) as result:
                assert result.success

                # this test is to ensure that the chain of noop -> noop -> noop -> writer is not blocked by waiter
                order = [
                    str(event.node_handle) for event in result.all_events if event.is_step_success
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
        pipe = reconstructable(define_diamond_job)
        # override event log to in memory

        with execute_job(
            pipe,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("adder") == 11


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


@job
def optional_stuff():
    option_1, option_2 = either_or()
    echo(echo(option_1))
    echo(echo(option_2))


def test_optional_outputs():
    with instance_for_test() as instance:
        single_result = optional_stuff.execute_in_process()
        assert single_result.success
        assert not [event for event in single_result.all_events if event.is_step_failure]
        assert len([event for event in single_result.all_events if event.is_step_skipped]) == 2

        with execute_job(
            reconstructable(optional_stuff),
            instance=instance,
        ) as multi_result:
            assert multi_result.success
            assert not [event for event in multi_result.all_events if event.is_step_failure]
            assert len([event for event in multi_result.all_events if event.is_step_skipped]) == 2


@op
def throw():
    raise Failure(
        description="it Failure",
        metadata={"label": "text"},
    )


@job
def failure():
    throw()


def test_failure_multiprocessing():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(failure),
            instance=instance,
            raise_on_error=False,
        ) as result:
            assert not result.success
            failure_data = result.failure_data_for_node("throw")
            assert failure_data
            assert failure_data.error.cls_name == "Failure"

            # hard coded
            assert failure_data.user_failure_data.label == "intentional-failure"
            # from Failure
            assert failure_data.user_failure_data.description == "it Failure"
            assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")


@op
def sys_exit(context):
    context.log.info("Informational message")
    print("Crashy output to stdout")  # noqa: T201
    sys.stdout.flush()
    os._exit(1)  # noqa: SLF001


@job
def sys_exit_job():
    sys_exit()


@pytest.mark.skipif(os.name == "nt", reason="Different crash output on Windows: See issue #2791")
def test_crash_multiprocessing():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(sys_exit_job),
            instance=instance,
            raise_on_error=False,
        ) as result:
            assert not result.success
            failure_data = result.failure_data_for_node("sys_exit")
            assert failure_data
            assert failure_data.error.cls_name == "ChildProcessCrashException"

            assert failure_data.user_failure_data is None

            capture_events = [
                event
                for event in result.all_events
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
def segfault_op(context):
    context.log.info("Informational message")
    print("Crashy output to stdout")  # noqa: T201
    segfault()


@job
def segfault_job():
    segfault_op()


@pytest.mark.skipif(os.name == "nt", reason="Different exception on Windows: See issue #2791")
def test_crash_hard_multiprocessing():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(segfault_job),
            instance=instance,
            raise_on_error=False,
        ) as result:
            assert not result.success
            failure_data = result.failure_data_for_node("segfault_op")
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
