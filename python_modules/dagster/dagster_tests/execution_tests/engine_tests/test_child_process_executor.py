import os
import time
from multiprocessing import get_context
from multiprocessing.process import BaseProcess

import pytest
from dagster._core.executor.child_process_executor import (
    ChildProcessCommand,
    ChildProcessCrashException,
    ChildProcessDoneEvent,
    ChildProcessEvent,
    ChildProcessStartEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)
from dagster._utils import segfault

multiprocessing_ctx = get_context()


class DoubleAStringChildProcessCommand(ChildProcessCommand):
    def __init__(self, a_str):
        self.a_str = a_str

    def execute(self):
        yield self.a_str + self.a_str


class AnError(Exception):
    pass


class ThrowAnErrorCommand(ChildProcessCommand):
    def execute(self):
        raise AnError("Oh noes!")


class CrashyCommand(ChildProcessCommand):
    def execute(self):
        # access inner API to simulate hard crash
        os._exit(1)


class SegfaultCommand(ChildProcessCommand):
    def execute(self):
        # access inner API to simulate hard crash
        segfault()


class LongRunningCommand(ChildProcessCommand):
    def execute(self):
        time.sleep(0.5)
        yield 1


def test_basic_child_process_command():
    events = list(
        filter(
            lambda x: x and not isinstance(x, (ChildProcessEvent, BaseProcess)),
            execute_child_process_command(
                multiprocessing_ctx, DoubleAStringChildProcessCommand("aa")
            ),
        )
    )
    assert events == ["aaaa"]


def test_basic_child_process_command_with_process_events():
    events = list(
        filter(
            lambda x: x,
            execute_child_process_command(
                multiprocessing_ctx, DoubleAStringChildProcessCommand("aa")
            ),
        )
    )
    assert len(events) == 4

    assert isinstance(events[0], BaseProcess)

    assert isinstance(events[1], ChildProcessStartEvent)
    child_pid = events[1].pid
    assert child_pid != os.getpid()
    assert child_pid == events[0].pid
    assert events[2] == "aaaa"
    assert isinstance(events[3], ChildProcessDoneEvent)
    assert events[3].pid == child_pid


def test_child_process_uncaught_exception():
    results = list(
        filter(
            lambda x: x and isinstance(x, ChildProcessSystemErrorEvent),
            execute_child_process_command(multiprocessing_ctx, ThrowAnErrorCommand()),
        )
    )
    assert len(results) == 1

    assert "AnError" in str(results[0].error_info.message)  # type: ignore


def test_child_process_crashy_process():
    with pytest.raises(ChildProcessCrashException) as exc:
        list(execute_child_process_command(multiprocessing_ctx, CrashyCommand()))
    assert exc.value.exit_code == 1


@pytest.mark.skipif(os.name == "nt", reason="Segfault not being caught on Windows: See issue #2791")
def test_child_process_segfault():
    with pytest.raises(ChildProcessCrashException) as exc:
        list(execute_child_process_command(multiprocessing_ctx, SegfaultCommand()))
    assert exc.value.exit_code == -11


@pytest.mark.skip("too long")
def test_long_running_command():
    list(execute_child_process_command(multiprocessing_ctx, LongRunningCommand()))
