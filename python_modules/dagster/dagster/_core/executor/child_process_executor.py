"""Facilities for running arbitrary commands in child processes."""

import io
import os
import queue
import sys
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from multiprocessing import Queue
from multiprocessing.context import BaseContext as MultiprocessingBaseContext
from multiprocessing.process import BaseProcess
from typing import TYPE_CHECKING, Literal, NamedTuple, Optional, Union

import dagster._check as check
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.interrupts import capture_interrupts

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent


class ChildProcessEvent:
    pass


class ChildProcessStartEvent(
    NamedTuple("ChildProcessStartEvent", [("pid", int)]), ChildProcessEvent
):
    pass


class ChildProcessDoneEvent(NamedTuple("ChildProcessDoneEvent", [("pid", int)]), ChildProcessEvent):
    pass


class ChildProcessSystemErrorEvent(
    NamedTuple(
        "ChildProcessSystemErrorEvent",
        [
            ("pid", int),
            ("error_info", SerializableErrorInfo),
            ("stdout", Optional[str]),
            ("stderr", Optional[str]),
        ],
    ),
    ChildProcessEvent,
):
    def __new__(
        cls,
        pid: int,
        error_info: SerializableErrorInfo,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        return super().__new__(cls, pid, error_info, stdout, stderr)


class ChildProcessCommand(ABC):
    """Inherit from this class in order to use this library.

    The object must be picklable; instantiate it and pass it to _execute_command_in_child_process.
    """

    @abstractmethod
    def execute(self) -> Iterator[Union[ChildProcessEvent, "DagsterEvent"]]:
        """This method is invoked in the child process.

        Yields a sequence of events to be handled by _execute_command_in_child_process.
        """


class ChildProcessCrashException(Exception):
    """Thrown when the child process crashes."""

    def __init__(
        self,
        pid: int,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        self.pid = pid
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        base_message = f"Child process {self.pid} crashed with exit code {self.exit_code}."
        output = _format_captured_output(self.stdout, self.stderr)
        if output:
            return f"{base_message}\n\n{output}"
        return base_message

    def __str__(self) -> str:
        return self._build_message()


CAPTURED_CHILD_PROCESS_LOG_BYTES = int(
    os.getenv("DAGSTER_CHILD_PROCESS_LOG_CAPTURE_BYTES", "65536")
)


class _TeeStream(io.TextIOBase):
    def __init__(self, *streams: io.TextIOBase):
        self._streams = streams

    def write(self, s: str) -> int:
        for stream in self._streams:
            stream.write(s)
            stream.flush()
        return len(s)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def _format_captured_output(stdout: Optional[str], stderr: Optional[str]) -> str:
    sections = []
    if stdout:
        sections.append(f"Captured stdout:\n{stdout}")
    if stderr:
        sections.append(f"Captured stderr:\n{stderr}")
    return "\n\n".join(sections)


def _read_log_tail(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        with open(path, "rb") as log_file:
            log_file.seek(0, os.SEEK_END)
            size = log_file.tell()
            if size > CAPTURED_CHILD_PROCESS_LOG_BYTES:
                log_file.seek(-CAPTURED_CHILD_PROCESS_LOG_BYTES, os.SEEK_END)
            else:
                log_file.seek(0)
            data = log_file.read()
        return data.decode("utf-8", errors="replace")
    except OSError:
        return None


def _with_output_snippet(
    error_info: SerializableErrorInfo, stdout: Optional[str], stderr: Optional[str]
) -> SerializableErrorInfo:
    output = _format_captured_output(stdout, stderr)
    if not output:
        return error_info
    return SerializableErrorInfo(
        message=f"{error_info.message.rstrip()}\n\n{output}",
        stack=error_info.stack,
        cls_name=error_info.cls_name,
        cause=error_info.cause,
        context=error_info.context,
    )


def _make_temp_log_file(prefix: str) -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".log")
    os.close(fd)
    return path


@contextmanager
def _redirect_output(stdout_path: Optional[str], stderr_path: Optional[str]):
    if not stdout_path and not stderr_path:
        yield
        return

    stdout_file = open(stdout_path, "w", encoding="utf-8") if stdout_path else None
    stderr_file = open(stderr_path, "w", encoding="utf-8") if stderr_path else None
    try:
        stdout_stream = _TeeStream(sys.stdout, stdout_file) if stdout_file else sys.stdout
        stderr_stream = _TeeStream(sys.stderr, stderr_file) if stderr_file else sys.stderr
        with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
            yield
    finally:
        if stdout_file:
            stdout_file.flush()
            stdout_file.close()
        if stderr_file:
            stderr_file.flush()
            stderr_file.close()


def _execute_command_in_child_process(
    event_queue: Queue,
    command: ChildProcessCommand,
    stdout_path: Optional[str],
    stderr_path: Optional[str],
):
    """Wraps the execution of a ChildProcessCommand.

    Handles errors and communicates across a queue with the parent process.
    """
    check.inst_param(command, "command", ChildProcessCommand)

    with capture_interrupts():
        pid = os.getpid()
        event_queue.put(ChildProcessStartEvent(pid=pid))
        try:
            with _redirect_output(stdout_path, stderr_path):
                for step_event in command.execute():
                    event_queue.put(step_event)
                event_queue.put(ChildProcessDoneEvent(pid=pid))

        except (
            Exception,
            KeyboardInterrupt,
            DagsterExecutionInterruptedError,
        ):
            stdout = _read_log_tail(stdout_path)
            stderr = _read_log_tail(stderr_path)
            error_info = _with_output_snippet(
                serializable_error_info_from_exc_info(sys.exc_info()), stdout, stderr
            )
            event_queue.put(
                ChildProcessSystemErrorEvent(
                    pid=pid, error_info=error_info, stdout=stdout, stderr=stderr
                )
            )


TICK = 20.0 * 1.0 / 1000.0
"""The minimum interval at which to check for child process liveness -- default 20ms."""

PROCESS_DEAD_AND_QUEUE_EMPTY = "PROCESS_DEAD_AND_QUEUE_EMPTY"
"""Sentinel value."""


def _poll_for_event(
    process, event_queue
) -> Optional[Union["DagsterEvent", Literal["PROCESS_DEAD_AND_QUEUE_EMPTY"]]]:
    try:
        return event_queue.get(block=True, timeout=TICK)
    except queue.Empty:
        if not process.is_alive():
            # There is a possibility that after the last queue.get the
            # process created another event and then died. In that case
            # we want to continue draining the queue.
            try:
                return event_queue.get(block=False)
            except queue.Empty:
                # If the queue empty we know that there are no more events
                # and that the process has died.
                return PROCESS_DEAD_AND_QUEUE_EMPTY
    return None


def execute_child_process_command(
    multiprocessing_ctx: MultiprocessingBaseContext, command: ChildProcessCommand
) -> Iterator[Optional[Union["DagsterEvent", ChildProcessEvent, BaseProcess]]]:
    """Execute a ChildProcessCommand in a new process.

    This function starts a new process whose execution target is a ChildProcessCommand wrapped by
    _execute_command_in_child_process; polls the queue for events yielded by the child process
    until the process dies and the queue is empty.

    This function yields a complex set of objects to enable having multiple child process
    executions in flight:
        * None - nothing has happened, yielded to enable cooperative multitasking other iterators

        * multiprocessing.BaseProcess - the child process object.

        * ChildProcessEvent - Family of objects that communicates state changes in the child process

        * The actual values yielded by the child process command

    Args:
        multiprocessing_ctx: The multiprocessing context to execute in (spawn, forkserver, fork)
        command (ChildProcessCommand): The command to execute in the child process.

    Warning: if the child process is in an infinite loop, this will
    also infinitely loop.
    """
    check.inst_param(command, "command", ChildProcessCommand)

    event_queue = multiprocessing_ctx.Queue()
    stdout_path = _make_temp_log_file("dagster-child-stdout-")
    stderr_path = _make_temp_log_file("dagster-child-stderr-")
    try:
        process = multiprocessing_ctx.Process(  # type: ignore
            target=_execute_command_in_child_process,
            args=(event_queue, command, stdout_path, stderr_path),
        )
        process.start()
        yield process

        completed_properly = False

        while not completed_properly:
            event = _poll_for_event(process, event_queue)

            if event == PROCESS_DEAD_AND_QUEUE_EMPTY:
                break

            yield event

            if isinstance(event, (ChildProcessDoneEvent, ChildProcessSystemErrorEvent)):
                completed_properly = True

        if not completed_properly:
            process.join()
            stdout = _read_log_tail(stdout_path)
            stderr = _read_log_tail(stderr_path)
            raise ChildProcessCrashException(
                pid=process.pid, exit_code=process.exitcode, stdout=stdout, stderr=stderr
            )

        process.join()
    finally:
        event_queue.close()
        for path in (stdout_path, stderr_path):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass
