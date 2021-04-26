import os
import signal
import tempfile
import time
from threading import Thread

import pytest
from dagster import (
    DagsterEventType,
    Field,
    ModeDefinition,
    String,
    execute_pipeline_iterator,
    pipeline,
    reconstructable,
    resource,
    seven,
    solid,
)
from dagster.core.errors import DagsterExecutionInterruptedError, raise_execution_interrupts
from dagster.core.test_utils import instance_for_test_tempdir
from dagster.utils import safe_tempfile_path, send_interrupt
from dagster.utils.interrupts import capture_interrupts, check_captured_interrupt


def _send_kbd_int(temp_files):
    while not all([os.path.exists(temp_file) for temp_file in temp_files]):
        time.sleep(0.1)
    send_interrupt()


@solid(config_schema={"tempfile": Field(String)})
def write_a_file(context):
    with open(context.solid_config["tempfile"], "w") as ff:
        ff.write("yup")

    start_time = time.time()

    while (time.time() - start_time) < 30:
        time.sleep(0.1)
    raise Exception("Timed out")


@solid
def should_not_start(_context):
    assert False


@pipeline
def write_files_pipeline():
    write_a_file.alias("write_1")()
    write_a_file.alias("write_2")()
    write_a_file.alias("write_3")()
    write_a_file.alias("write_4")()
    should_not_start.alias("x_should_not_start")()
    should_not_start.alias("y_should_not_start")()
    should_not_start.alias("z_should_not_start")()


def test_single_proc_interrupt():
    @pipeline
    def write_a_file_pipeline():
        write_a_file()

    with safe_tempfile_path() as success_tempfile:

        # launch a thread the waits until the file is written to launch an interrupt
        Thread(target=_send_kbd_int, args=([success_tempfile],)).start()

        result_types = []
        result_messages = []

        # next time the launched thread wakes up it will send a keyboard
        # interrupt
        for result in execute_pipeline_iterator(
            write_a_file_pipeline,
            run_config={"solids": {"write_a_file": {"config": {"tempfile": success_tempfile}}}},
        ):
            result_types.append(result.event_type)
            result_messages.append(result.message)

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
        with instance_for_test_tempdir(tempdir) as instance:

            file_1 = os.path.join(tempdir, "file_1")
            file_2 = os.path.join(tempdir, "file_2")
            file_3 = os.path.join(tempdir, "file_3")
            file_4 = os.path.join(tempdir, "file_4")

            # launch a thread that waits until the file is written to launch an interrupt
            Thread(target=_send_kbd_int, args=([file_1, file_2, file_3, file_4],)).start()

            results = []

            # launch a pipeline that writes a file and loops infinitely
            # next time the launched thread wakes up it will send a keyboard
            # interrupt
            for result in execute_pipeline_iterator(
                reconstructable(write_files_pipeline),
                run_config={
                    "solids": {
                        "write_1": {"config": {"tempfile": file_1}},
                        "write_2": {"config": {"tempfile": file_2}},
                        "write_3": {"config": {"tempfile": file_3}},
                        "write_4": {"config": {"tempfile": file_4}},
                    },
                    "execution": {"multiprocess": {"config": {"max_concurrent": 4}}},
                    "intermediate_storage": {"filesystem": {}},
                },
                instance=instance,
            ):
                results.append(result)

            assert [result.event_type for result in results].count(
                DagsterEventType.STEP_FAILURE
            ) == 4
            assert DagsterEventType.PIPELINE_FAILURE in [result.event_type for result in results]


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

    @solid(config_schema={"tempfile": Field(String)}, required_resource_keys={"a"})
    def write_a_file_resource_solid(context):
        with open(context.solid_config["tempfile"], "w") as ff:
            ff.write("yup")

        while True:
            time.sleep(0.1)

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
    def write_a_file_pipeline():
        write_a_file_resource_solid()

    with safe_tempfile_path() as success_tempfile:

        # launch a thread the waits until the file is written to launch an interrupt
        Thread(target=_send_kbd_int, args=([success_tempfile],)).start()

        results = []
        # launch a pipeline that writes a file and loops infinitely
        # next time the launched thread wakes up it will send an interrupt
        for result in execute_pipeline_iterator(
            write_a_file_pipeline,
            run_config={
                "solids": {
                    "write_a_file_resource_solid": {"config": {"tempfile": success_tempfile}}
                }
            },
        ):
            results.append(result.event_type)

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
        except:  # pylint: disable=bare-except
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
            except:  # pylint: disable=bare-except
                inner_interrupt = True
    except:  # pylint: disable=bare-except
        outer_interrupt = True

    assert not outer_interrupt
    assert not inner_interrupt


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Interrupts handled differently on windows")
def test_raise_execution_interrupts():
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

    except:  # pylint: disable=bare-except
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
                except:  # pylint: disable=bare-except
                    interrupt_inside_nested_raise = True
            _send_interrupt_to_self()

    except:  # pylint: disable=bare-except
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
    except:  # pylint: disable=bare-except
        interrupt_after_delay = True

    assert interrupt_from_raise_execution_interrupts
    assert not interrupt_after_delay
