"""Facilities for running arbitrary commands in child processes."""

import os
import queue
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from multiprocessing.context import BaseContext as MultiprocessingBaseContext
from multiprocessing.process import BaseProcess
from typing import TYPE_CHECKING, Literal, NamedTuple, Protocol, Union

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
        "ChildProcessSystemErrorEvent", [("pid", int), ("error_info", SerializableErrorInfo)]
    ),
    ChildProcessEvent,
):
    pass


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

    def __init__(self, pid, exit_code=None):
        self.pid = pid
        self.exit_code = exit_code
        super().__init__()


class _EventWriter(Protocol):
    def put(self, value: object, /) -> None: ...


def _execute_command_in_child_process(event_queue: _EventWriter, command: ChildProcessCommand):
    """Wraps the execution of a ChildProcessCommand.

    Handles errors and communicates across a queue with the parent process.
    """
    check.inst_param(command, "command", ChildProcessCommand)

    with capture_interrupts():
        pid = os.getpid()
        event_queue.put(ChildProcessStartEvent(pid=pid))
        try:
            for step_event in command.execute():
                event_queue.put(step_event)
            event_queue.put(ChildProcessDoneEvent(pid=pid))

        except (
            Exception,
            KeyboardInterrupt,
            DagsterExecutionInterruptedError,
        ):
            event_queue.put(
                ChildProcessSystemErrorEvent(
                    pid=pid, error_info=serializable_error_info_from_exc_info(sys.exc_info())
                )
            )


TICK = 20.0 * 1.0 / 1000.0
"""The minimum interval at which to check for child process liveness -- default 20ms."""

PROCESS_DEAD_AND_QUEUE_EMPTY = "PROCESS_DEAD_AND_QUEUE_EMPTY"
"""Sentinel value."""


def _poll_for_event(
    process, event_queue
) -> Union["DagsterEvent", Literal["PROCESS_DEAD_AND_QUEUE_EMPTY"]] | None:
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
) -> Iterator[Union["DagsterEvent", ChildProcessEvent, BaseProcess] | None]:
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
    try:
        process = multiprocessing_ctx.Process(  # type: ignore
            target=_execute_command_in_child_process, args=(event_queue, command)
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
            # TODO Figure out what to do about stderr/stdout
            raise ChildProcessCrashException(pid=process.pid, exit_code=process.exitcode)

        process.join()
    finally:
        event_queue.close()


class ChildProcessDeadlineExceeded(ChildProcessCrashException):
    """Worker exceeded its configured lifetime and was killed and joined."""

    def __init__(self, pid, exit_code, timeout_seconds: float):
        super().__init__(pid, exit_code)
        self.timeout_seconds = timeout_seconds
        self.args = (
            f"Step worker lifetime exceeded {timeout_seconds:g} seconds; worker terminated.",
        )


def execute_child_process_with_deadline(
    multiprocessing_ctx, command, seconds, spool_root, cancelled, max_event_bytes
):
    """Run a worker with a parent-clock lifetime limit and finite event frames."""
    import tempfile
    import time

    from dagster._core.executor._deadline_spool import (
        TRANSPORT_ERROR_EXIT_CODE,
        AtomicEventSpool,
        EventTransportError,
    )

    with tempfile.TemporaryDirectory(prefix="attempt-", dir=spool_root) as directory:
        events = AtomicEventSpool(directory, max_event_bytes)
        process = multiprocessing_ctx.Process(
            target=_execute_deadline_command_in_child_process, args=(events, command)
        )
        began = time.monotonic()
        process.start()
        killed_at = None
        deadline_expired = False
        completed = False
        try:
            yield process
            while True:
                # Consume a complete published event before considering expiry on this tick.
                try:
                    event = events.get_nowait()
                except queue.Empty:
                    event = None
                if event is not None:
                    if isinstance(event, (ChildProcessDoneEvent, ChildProcessSystemErrorEvent)):
                        completed = True
                    yield event
                now = time.monotonic()
                cancellation = cancelled()
                if (
                    killed_at is None
                    and process.is_alive()
                    and (cancellation or now - began >= seconds)
                ):
                    deadline_expired = not cancellation
                    process.kill()
                    killed_at = now
                if not process.is_alive():
                    process.join(timeout=0)
                    # Only finish after draining complete ordered frames. Partials are discarded
                    # by TemporaryDirectory after actual child exit; no pipe recv can block.
                    if event is not None:
                        continue
                    import json
                    from pathlib import Path

                    reason = None
                    marker = Path(directory) / "transport-error.json"
                    try:
                        if (
                            marker.is_file()
                            and not marker.is_symlink()
                            and marker.stat().st_size <= 128
                        ):
                            decoded = json.loads(marker.read_text())
                            if decoded == {"reason": "event_size_limit"}:
                                reason = f"event exceeds step_worker_timeout_max_event_bytes={max_event_bytes}"
                            elif decoded == {"reason": "event_transport_failure"}:
                                reason = "event_transport_failure"
                    except (OSError, ValueError):
                        pass
                    if reason is not None or process.exitcode == TRANSPORT_ERROR_EXIT_CODE:
                        raise EventTransportError(reason or "event_transport_failure")
                    if deadline_expired:
                        raise ChildProcessDeadlineExceeded(process.pid, process.exitcode, seconds)
                    if not completed:
                        raise ChildProcessCrashException(process.pid, process.exitcode)
                    break
                if killed_at is not None and now - killed_at > 5:
                    raise RuntimeError("Worker deadline could not reap killed worker")
                yield None
                if event is None:
                    time.sleep(TICK)
        finally:
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
                if process.is_alive():
                    raise RuntimeError("Worker deadline cleanup could not reap worker")
            else:
                process.join(timeout=0)


def _execute_deadline_command_in_child_process(events, command):
    from dagster._core.executor._deadline_spool import (
        TRANSPORT_ERROR_EXIT_CODE,
        EventTransportError,
    )

    class ChildEventWriter:
        def put(self, value):
            try:
                events.put(value)
            except EventTransportError:
                # Exit at the put boundary, before user generator/resource unwinding.
                # That cleanup can itself hang, even when the diagnostic disk is full.
                os._exit(TRANSPORT_ERROR_EXIT_CODE)

    try:
        _execute_command_in_child_process(ChildEventWriter(), command)
    except EventTransportError:
        # The normal command wrapper also sends its errors through the event channel.
        # This reserved enabled-path status survives failure of that same channel.
        os._exit(TRANSPORT_ERROR_EXIT_CODE)
