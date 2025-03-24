import os
import signal
import tempfile
import time
from threading import Thread

import pytest
from dagster import (
    DagsterEventType,
    Failure,
    Field,
    RetryPolicy,
    String,
    job,
    op,
    reconstructable,
    resource,
)
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.errors import DagsterExecutionInterruptedError, raise_execution_interrupts
from dagster._core.execution.api import execute_job, execute_run_iterator
from dagster._core.test_utils import instance_for_test
from dagster._utils import safe_tempfile_path, send_interrupt
from dagster._utils.interrupts import capture_interrupts, check_captured_interrupt
from dagster_shared import seven


def _send_kbd_int(temp_files):
    while not all([os.path.exists(temp_file) for temp_file in temp_files]):
        time.sleep(0.1)
    send_interrupt()


@op(config_schema={"tempfile": Field(String)})
def write_a_file(context):
    with open(context.op_config["tempfile"], "w", encoding="utf8") as ff:
        ff.write("yup")

    start_time = time.time()

    while (time.time() - start_time) < 30:
        time.sleep(0.1)
    raise Exception("Timed out")


@op
def should_not_start(_context):
    assert False


@job
def write_files_job():
    write_a_file.alias("write_1")()
    write_a_file.alias("write_2")()
    write_a_file.alias("write_3")()
    write_a_file.alias("write_4")()
    should_not_start.alias("x_should_not_start")()
    should_not_start.alias("y_should_not_start")()
    should_not_start.alias("z_should_not_start")()


def test_single_proc_interrupt():
    @job
    def write_a_file_job():
        write_a_file()

    with safe_tempfile_path() as success_tempfile:
        # launch a thread the waits until the file is written to launch an interrupt
        Thread(target=_send_kbd_int, args=([success_tempfile],)).start()

        result_types = []
        result_messages = []

        # next time the launched thread wakes up it will send a keyboard
        # interrupt
        for event in write_a_file_job.execute_in_process(
            run_config={"ops": {"write_a_file": {"config": {"tempfile": success_tempfile}}}},
            raise_on_error=False,
        ).all_events:
            result_types.append(event.event_type)
            result_messages.append(event.message)

        assert DagsterEventType.STEP_FAILURE in result_types
        assert DagsterEventType.PIPELINE_FAILURE in result_types

        assert any(
            [
                "Execution was interrupted unexpectedly. "
                "No user initiated termination request was found, treating as failure." in message
                for message in result_messages
            ]
        )


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_interrupt_multiproc():
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test(temp_dir=tempdir) as instance:
            file_1 = os.path.join(tempdir, "file_1")
            file_2 = os.path.join(tempdir, "file_2")
            file_3 = os.path.join(tempdir, "file_3")
            file_4 = os.path.join(tempdir, "file_4")

            # launch a thread that waits until the file is written to launch an interrupt
            Thread(target=_send_kbd_int, args=([file_1, file_2, file_3, file_4],)).start()

            # launch a job that writes a file and loops infinitely
            # next time the launched thread wakes up it will send a keyboard
            # interrupt
            with execute_job(
                reconstructable(write_files_job),
                run_config={
                    "ops": {
                        "write_1": {"config": {"tempfile": file_1}},
                        "write_2": {"config": {"tempfile": file_2}},
                        "write_3": {"config": {"tempfile": file_3}},
                        "write_4": {"config": {"tempfile": file_4}},
                    },
                    "execution": {"config": {"multiprocess": {"max_concurrent": 4}}},
                },
                instance=instance,
            ) as result:
                assert [event.event_type for event in result.all_events].count(
                    DagsterEventType.STEP_FAILURE
                ) == 4
                assert DagsterEventType.PIPELINE_FAILURE in [
                    event.event_type for event in result.all_events
                ]


def test_interrupt_resource_teardown():
    called = []
    cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append("A")
            yield "A"
        finally:
            cleaned.append("A")

    @op(config_schema={"tempfile": Field(String)}, required_resource_keys={"a"})
    def write_a_file_resource_op(context):
        with open(context.op_config["tempfile"], "w", encoding="utf8") as ff:
            ff.write("yup")

        while True:
            time.sleep(0.1)

    @job(resource_defs={"a": resource_a}, executor_def=in_process_executor)
    def write_a_file_job():
        write_a_file_resource_op()

    with instance_for_test() as instance:
        with safe_tempfile_path() as success_tempfile:
            # launch a thread the waits until the file is written to launch an interrupt
            Thread(target=_send_kbd_int, args=([success_tempfile],)).start()

            dagster_run = instance.create_run_for_job(
                write_a_file_job,
                run_config={
                    "ops": {"write_a_file_resource_op": {"config": {"tempfile": success_tempfile}}}
                },
            )

            results = []
            # launch a pipeline that writes a file and loops infinitely
            # next time the launched thread wakes up it will send an interrupt
            for event in execute_run_iterator(
                InMemoryJob(write_a_file_job),
                dagster_run,
                instance=instance,
            ):
                results.append(event.event_type)

            assert DagsterEventType.STEP_FAILURE in results
            assert DagsterEventType.PIPELINE_FAILURE in results
            assert "A" in cleaned


def _send_interrupt_to_self():
    os.kill(os.getpid(), signal.SIGINT)
    start_time = time.time()
    while not check_captured_interrupt():
        time.sleep(1)
        if time.time() - start_time > 15:
            raise Exception("Timed out waiting for interrupt to be received")


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_capture_interrupt():
    outer_interrupt = False
    inner_interrupt = False

    with capture_interrupts():
        try:
            _send_interrupt_to_self()
        except:
            inner_interrupt = True

    assert not inner_interrupt

    # Verify standard interrupt handler is restored
    standard_interrupt = False

    try:
        _send_interrupt_to_self()
    except KeyboardInterrupt:
        standard_interrupt = True

    assert standard_interrupt

    outer_interrupt = False
    inner_interrupt = False
    # No exception if no signal thrown
    try:
        with capture_interrupts():
            try:
                time.sleep(5)
            except:
                inner_interrupt = True
    except:
        outer_interrupt = True

    assert not outer_interrupt
    assert not inner_interrupt


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_raise_execution_interrupts():
    standard_interrupt = False
    with raise_execution_interrupts():
        try:
            _send_interrupt_to_self()
        except DagsterExecutionInterruptedError:
            standard_interrupt = True

    assert standard_interrupt


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_interrupt_inside_nested_delay_and_raise():
    interrupt_inside_nested_raise = False
    interrupt_after_delay = False

    try:
        with capture_interrupts():
            with raise_execution_interrupts():
                try:
                    _send_interrupt_to_self()
                except DagsterExecutionInterruptedError:
                    interrupt_inside_nested_raise = True

    except:
        interrupt_after_delay = True

    assert interrupt_inside_nested_raise
    assert not interrupt_after_delay


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_no_interrupt_after_nested_delay_and_raise():
    interrupt_inside_nested_raise = False
    interrupt_after_delay = False

    try:
        with capture_interrupts():
            with raise_execution_interrupts():
                try:
                    time.sleep(5)
                except:
                    interrupt_inside_nested_raise = True
            _send_interrupt_to_self()

    except:
        interrupt_after_delay = True

    assert not interrupt_inside_nested_raise
    assert not interrupt_after_delay


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_calling_raise_execution_interrupts_also_raises_any_captured_interrupts():
    interrupt_from_raise_execution_interrupts = False
    interrupt_after_delay = False
    try:
        with capture_interrupts():
            _send_interrupt_to_self()
            try:
                with raise_execution_interrupts():
                    pass
            except DagsterExecutionInterruptedError:
                interrupt_from_raise_execution_interrupts = True
    except:
        interrupt_after_delay = True

    assert interrupt_from_raise_execution_interrupts
    assert not interrupt_after_delay


@op(config_schema={"path": str})
def write_and_spin_if_missing(context):
    target = context.op_config["path"]
    if os.path.exists(target):
        return

    with open(target, "w", encoding="utf8") as ff:
        ff.write(str(os.getpid()))

    start_time = time.time()

    while (time.time() - start_time) < 3:
        time.sleep(0.1)

    os.remove(target)
    raise Failure("Timed out, file removed")


@job(op_retry_policy=RetryPolicy(max_retries=1), executor_def=in_process_executor)
def policy_job():
    write_and_spin_if_missing()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_retry_policy():
    """Start a thread which will interrupt the subprocess after it writes the file.
    On the retry the run will succeed since the op returns if the file already exists.
    """

    def _send_int(path):
        pid = None
        while True:
            if os.path.exists(path):
                with open(path, encoding="utf8") as f:
                    pid_str = f.read()
                    if pid_str:
                        pid = int(pid_str)
                        break

            time.sleep(0.05)

        os.kill(pid, signal.SIGINT)

    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "target.tmp")
        Thread(target=_send_int, args=(path,)).start()
        with instance_for_test(temp_dir=tempdir) as instance:
            result = policy_job.execute_in_process(
                run_config={"ops": {"write_and_spin_if_missing": {"config": {"path": path}}}},
                instance=instance,
            )
            assert result.success
