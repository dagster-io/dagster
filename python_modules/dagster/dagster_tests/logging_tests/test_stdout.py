import multiprocessing
import os
import random
import string
import sys
import tempfile
import time

import pytest
from dagster import DagsterEventType, fs_io_manager, reconstructable, resource
from dagster._core.definitions import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.input import In
from dagster._core.execution.api import execute_job
from dagster._core.execution.compute_logs import should_disable_io_stream_redirect
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._core.utils import make_new_run_id
from dagster._utils import ensure_dir, touch_file

HELLO_FROM_OP = "HELLO FROM OP"
HELLO_RESOURCE = "HELLO RESOURCE"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"


@resource
def resource_a(_):
    print(HELLO_RESOURCE)  # noqa: T201
    return "A"


@op
def spawn(_):
    return 1


@op(ins={"num": In(int)}, required_resource_keys={"a"})
def spew(_, num):
    print(HELLO_FROM_OP)  # noqa: T201
    return num


def define_job():
    @job(resource_defs={"a": resource_a, "io_manager": fs_io_manager})
    def spew_job():
        spew(spew(spawn()))

    return spew_job


def normalize_file_content(s):
    return "\n".join([line for line in s.replace(os.linesep, "\n").split("\n") if line])


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_to_disk():
    with instance_for_test() as instance:
        spew_job = define_job()
        manager = instance.compute_log_manager
        assert isinstance(manager, LocalComputeLogManager)
        result = spew_job.execute_in_process(instance=instance)
        assert result.success

        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 1
        event = capture_events[0]
        assert len(event.logs_captured_data.step_keys) == 3
        log_key = [result.run_id, "compute_logs", event.logs_captured_data.file_key]
        local_path = manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
        )
        assert os.path.exists(local_path)
        with open(local_path, encoding="utf8") as stdout_file:
            assert normalize_file_content(stdout_file.read()) == f"{HELLO_FROM_OP}\n{HELLO_FROM_OP}"


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_to_disk_multiprocess():
    spew_job = reconstructable(define_job)
    with instance_for_test() as instance:
        manager = instance.compute_log_manager
        assert isinstance(manager, LocalComputeLogManager)
        result = execute_job(
            spew_job,
            instance=instance,
        )
        assert result.success

        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 3  # one for each step
        last_spew_event = capture_events[-1]
        assert len(last_spew_event.logs_captured_data.step_keys) == 1
        log_key = [result.run_id, "compute_logs", last_spew_event.logs_captured_data.file_key]
        local_path = manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
        )
        assert os.path.exists(local_path)
        with open(local_path, encoding="utf8") as stdout_file:
            assert normalize_file_content(stdout_file.read()) == HELLO_FROM_OP


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_manager():
    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        spew_job = define_job()
        result = spew_job.execute_in_process(instance=instance)
        assert result.success

        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 1
        event = capture_events[0]
        log_key = manager.build_log_key_for_run(result.run_id, event.logs_captured_data.file_key)
        assert manager.is_capture_complete(log_key)
        log_data = manager.get_log_data(log_key)
        stdout = normalize_file_content(log_data.stdout.decode("utf-8"))
        assert stdout == f"{HELLO_FROM_OP}\n{HELLO_FROM_OP}"
        stderr = normalize_file_content(log_data.stderr.decode("utf-8"))
        cleaned_logs = stderr.replace("\x1b[34m", "").replace("\x1b[0m", "")
        assert "dagster - DEBUG - spew_job - " in cleaned_logs


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_manager_subscriptions():
    with instance_for_test() as instance:
        spew_job = define_job()
        result = spew_job.execute_in_process(instance=instance)
        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 1
        event = capture_events[0]
        log_key = [result.run_id, "compute_logs", event.logs_captured_data.file_key]
        subscription = instance.compute_log_manager.subscribe(log_key)
        log_data = []
        subscription(log_data.append)
        assert len(log_data) == 1
        assert log_data[0].stdout.decode("utf-8").startswith(HELLO_FROM_OP)


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_manager_subscription_updates():
    from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager

    with tempfile.TemporaryDirectory() as temp_dir:
        compute_log_manager = LocalComputeLogManager(temp_dir, polling_timeout=0.5)
        log_key = [make_new_run_id(), "compute_logs", "spew"]
        stdout_path = compute_log_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
        )
        # make sure the parent directory to be watched exists, file exists
        ensure_dir(os.path.dirname(stdout_path))
        touch_file(stdout_path)

        # set up the subscription
        messages = []
        subscription = compute_log_manager.subscribe(log_key)
        subscription(messages.append)

        # returns a single update, with 0 data
        assert len(messages) == 1
        last_chunk = messages[-1]
        assert not last_chunk.stdout

        with open(stdout_path, "a+", encoding="utf8") as f:
            print(HELLO_FROM_OP, file=f)

        # wait longer than the watchdog timeout
        time.sleep(1)
        assert len(messages) == 2
        last_chunk = messages[-1]
        assert last_chunk.stdout
        assert last_chunk.cursor


def gen_op_name(length):
    return "".join(random.choice(string.ascii_lowercase) for x in range(length))


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_long_op_names():
    op_name = gen_op_name(300)

    @job(resource_defs={"a": resource_a})
    def long_job():
        spew.alias(name=op_name)()

    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        result = long_job.execute_in_process(
            instance=instance,
            run_config={"ops": {op_name: {"inputs": {"num": 1}}}},
        )
        assert result.success

        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 1
        event = capture_events[0]
        log_key = [result.run_id, "compute_logs", event.logs_captured_data.file_key]
        assert manager.is_capture_complete(log_key)

        log_data = manager.get_log_data(log_key)
        assert normalize_file_content(log_data.stdout.decode("utf-8")) == HELLO_FROM_OP


def execute_inner(step_key: str, dagster_run: DagsterRun, instance_ref: InstanceRef) -> None:
    instance = DagsterInstance.from_ref(instance_ref)
    inner_step(instance, dagster_run, step_key)


def inner_step(instance: DagsterInstance, dagster_run: DagsterRun, step_key: str) -> None:
    log_key = [dagster_run.run_id, "compute_logs", step_key]
    with instance.compute_log_manager.capture_logs(log_key):
        time.sleep(0.1)
        print(step_key, "inner 1")  # noqa: T201
        print(step_key, "inner 2")  # noqa: T201
        print(step_key, "inner 3")  # noqa: T201
        time.sleep(0.1)


def expected_inner_output(step_key):
    return "\n".join([f"{step_key} inner {i + 1}" for i in range(3)])


def expected_outer_prefix():
    return "\n".join([f"outer {i + 1}" for i in range(3)])


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_single():
    with instance_for_test() as instance:
        job_name = "foo_job"
        dagster_run = create_run_for_test(instance, job_name=job_name)

        step_keys = ["A", "B", "C"]

        log_key = [dagster_run.run_id, "compute_logs", dagster_run.job_name]
        with instance.compute_log_manager.capture_logs(log_key):
            print("outer 1")  # noqa: T201
            print("outer 2")  # noqa: T201
            print("outer 3")  # noqa: T201

            for step_key in step_keys:
                inner_step(instance, dagster_run, step_key)

        for step_key in step_keys:
            log_key = [dagster_run.run_id, "compute_logs", step_key]
            log_data = instance.compute_log_manager.get_log_data(log_key)
            assert normalize_file_content(log_data.stdout.decode("utf-8")) == expected_inner_output(
                step_key
            )

        full_data = instance.compute_log_manager.get_log_data(
            [dagster_run.run_id, "compute_logs", job_name]
        )

        assert normalize_file_content(full_data.stdout.decode("utf-8")).startswith(
            expected_outer_prefix()
        )


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_base_with_spaces():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "compute_logs": {
                    "module": "dagster._core.storage.local_compute_log_manager",
                    "class": "LocalComputeLogManager",
                    "config": {"base_dir": os.path.join(temp_dir, "base with spaces")},
                }
            },
        ) as instance:
            job_name = "foo_job"
            dagster_run = create_run_for_test(instance, job_name=job_name)

            step_keys = ["A", "B", "C"]

            log_key = [dagster_run.run_id, "compute_logs", dagster_run.job_name]
            with instance.compute_log_manager.capture_logs(log_key):
                print("outer 1")  # noqa: T201
                print("outer 2")  # noqa: T201
                print("outer 3")  # noqa: T201

                for step_key in step_keys:
                    inner_step(instance, dagster_run, step_key)

            for step_key in step_keys:
                log_key = [dagster_run.run_id, "compute_logs", step_key]
                log_data = instance.compute_log_manager.get_log_data(log_key)
                assert normalize_file_content(
                    log_data.stdout.decode("utf-8")
                ) == expected_inner_output(step_key)

            full_data = instance.compute_log_manager.get_log_data(
                [dagster_run.run_id, "compute_logs", job_name]
            )

            assert normalize_file_content(full_data.stdout.decode("utf-8")).startswith(
                expected_outer_prefix()
            )


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_multi():
    ctx = multiprocessing.get_context("spawn")

    with instance_for_test() as instance:
        job_name = "foo_job"
        dagster_run = create_run_for_test(instance, job_name=job_name)

        step_keys = ["A", "B", "C"]

        log_key = [dagster_run.run_id, "compute_logs", dagster_run.job_name]
        with instance.compute_log_manager.capture_logs(log_key):
            print("outer 1")  # noqa: T201
            print("outer 2")  # noqa: T201
            print("outer 3")  # noqa: T201

            for step_key in step_keys:
                process = ctx.Process(
                    target=execute_inner,
                    args=(step_key, dagster_run, instance.get_ref()),
                )
                process.start()
                process.join()

        for step_key in step_keys:
            log_key = [dagster_run.run_id, "compute_logs", step_key]
            log_data = instance.compute_log_manager.get_log_data(log_key)
            assert normalize_file_content(log_data.stdout.decode("utf-8")) == expected_inner_output(
                step_key
            )

        full_data = instance.compute_log_manager.get_log_data(
            [dagster_run.run_id, "compute_logs", job_name]
        )

        # The way that the multiprocess compute-logging interacts with pytest (which stubs out the
        # sys.stdout fileno) makes this difficult to test.  The pytest-captured stdout only captures
        # the stdout from the outer process, not also the inner process
        assert normalize_file_content(full_data.stdout.decode("utf-8")).startswith(
            expected_outer_prefix()
        )
