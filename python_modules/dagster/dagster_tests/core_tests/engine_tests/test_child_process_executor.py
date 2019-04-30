import os
import time
import pytest

from dagster.core.engine.child_process_executor import (
    ChildProcessCommand,
    execute_child_process_command,
    ChildProcessStartEvent,
    ChildProcessDoneEvent,
    ChildProcessException,
    ChildProcessCrashException,
)


class DoubleAStringChildProcessCommand(ChildProcessCommand):
    def __init__(self, a_str):
        self.a_str = a_str

    def execute(self):
        yield self.a_str + self.a_str


class AnError(Exception):
    pass


class ThrowAnErrorCommand(ChildProcessCommand):  # pylint: disable=no-init
    def execute(self):
        raise AnError('Oh noes!')


class CrashyCommand(ChildProcessCommand):  # pylint: disable=no-init
    def execute(self):
        # access inner API to simulate hard crash
        os._exit(1)  # pylint: disable=protected-access


class LongRunningCommand(ChildProcessCommand):  # pylint: disable=no-init
    def execute(self):
        time.sleep(1.0)
        yield 1


def test_basic_child_process_command():
    events = list(
        filter(lambda x: x, execute_child_process_command(DoubleAStringChildProcessCommand('aa')))
    )
    assert events == ['aaaa']


def test_basic_child_process_command_with_process_events():
    events = list(
        filter(
            lambda x: x,
            execute_child_process_command(
                DoubleAStringChildProcessCommand('aa'), return_process_events=True
            ),
        )
    )
    assert len(events) == 3

    assert isinstance(events[0], ChildProcessStartEvent)
    child_pid = events[0].pid
    assert child_pid != os.getpid()
    assert events[1] == 'aaaa'
    assert isinstance(events[2], ChildProcessDoneEvent)
    assert events[2].pid == child_pid


def test_child_process_uncaught_exception():
    with pytest.raises(ChildProcessException) as excinfo:
        list(execute_child_process_command(ThrowAnErrorCommand()))

    assert 'AnError' in str(excinfo.value)


def test_child_process_crashy_process():
    with pytest.raises(ChildProcessCrashException):
        list(execute_child_process_command(CrashyCommand()))


@pytest.mark.skip('too long')
def test_long_running_command():
    list(execute_child_process_command(LongRunningCommand()))
