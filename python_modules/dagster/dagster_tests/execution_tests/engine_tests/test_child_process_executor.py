import logging
import os
import sys
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
from dagster_shared.seven import IS_PYTHON_3_14

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
    def execute(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        # access inner API to simulate hard crash
        segfault()


class LongRunningCommand(ChildProcessCommand):
    def execute(self):  # pyright: ignore[reportIncompatibleMethodOverride]
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


@pytest.mark.skipif(IS_PYTHON_3_14, reason="multiprocessing crash handling differs on 3.14")
def test_child_process_crashy_process():
    with pytest.raises(ChildProcessCrashException) as exc:
        list(execute_child_process_command(multiprocessing_ctx, CrashyCommand()))
    assert exc.value.exit_code == 1


@pytest.mark.skipif(os.name == "nt", reason="Segfault not being caught on Windows: See issue #2791")
@pytest.mark.skipif(IS_PYTHON_3_14, reason="multiprocessing crash handling differs on 3.14")
def test_child_process_segfault():
    with pytest.raises(ChildProcessCrashException) as exc:
        list(execute_child_process_command(multiprocessing_ctx, SegfaultCommand()))
    assert exc.value.exit_code == -11


@pytest.mark.skip("too long")
def test_long_running_command():
    list(execute_child_process_command(multiprocessing_ctx, LongRunningCommand()))


# --- preload_modules regression tests (issue #33535) ---


class ModuleImportedCheckCommand(ChildProcessCommand):
    """Yields True if the given module is already in sys.modules when execute() is called."""

    def __init__(self, module_name: str):
        self.module_name = module_name

    def execute(self):
        yield self.module_name in sys.modules


def _get_results(command, preload_modules=None):
    return list(
        filter(
            lambda x: x is not None and not isinstance(x, (ChildProcessEvent, BaseProcess)),
            execute_child_process_command(multiprocessing_ctx, command, preload_modules),
        )
    )


def test_preload_modules_imports_before_execute():
    # "colorsys" is not imported by the multiprocessing spawn bootstrap, so it will only
    # be in sys.modules if preload_modules explicitly causes it to be imported first.
    results = _get_results(
        ModuleImportedCheckCommand("colorsys"),
        preload_modules=["colorsys"],
    )
    assert results == [True]


def test_preload_modules_none_is_noop():
    # Without preload, "colorsys" won't be in sys.modules at execute() time in a fresh
    # spawn'd child process.
    results = _get_results(
        ModuleImportedCheckCommand("colorsys"),
        preload_modules=None,
    )
    assert results == [False]


def test_preload_modules_bad_module_does_not_crash():
    # caplog cannot capture logs from spawned child processes, so we only verify
    # that the command still completes successfully despite the bad preload entry.
    results = _get_results(
        DoubleAStringChildProcessCommand("ok"),
        preload_modules=["__nonexistent_module_xyz__"],
    )
    # The command still ran successfully despite the bad preload
    assert results == ["okok"]
