import _thread as thread
import os
import os.path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from subprocess import Popen
from types import TracebackType
from typing import Any, Callable, Optional, Union

from typing_extensions import TypeAlias

import dagster_shared.check as check
from dagster_shared.error import SerializableErrorInfo
from dagster_shared.record import record
from dagster_shared.serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster_shared.serdes.serdes import T_PackableValue
from dagster_shared.seven import IS_WINDOWS

# Windows subprocess termination utilities. See here for why we send on Windows:
# https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/


def open_ipc_subprocess(parts: Sequence[str], **kwargs: Any) -> "Popen[Any]":
    """Sets the correct flags to support graceful termination."""
    check.list_param(parts, "parts", str)

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        # pass_fds is not supported on Windows. Instead we set close_fds to False, which will allow
        # any inheritable file descriptors marked as inheritable to be inherited by the child
        # process.
        if kwargs.get("pass_fds"):
            del kwargs["pass_fds"]
            kwargs["close_fds"] = False

    return subprocess.Popen(
        parts,
        creationflags=creationflags,
        **kwargs,
    )


def interrupt_ipc_subprocess(proc: "Popen[Any]", sig: Optional[int] = None) -> None:
    """Send CTRL_BREAK on Windows, SIGINT on other platforms."""
    proc.send_signal(sig or get_default_interrupt_signal())


def interrupt_then_kill_ipc_subprocess(proc: "Popen[Any]", wait_time: int = 10) -> None:
    interrupt_ipc_subprocess(proc)
    try:
        proc.wait(timeout=wait_time)
    except subprocess.TimeoutExpired:
        proc.kill()


def interrupt_ipc_subprocess_pid(pid: int, sig: Optional[int] = None) -> None:
    """Send CTRL_BREAK_EVENT on Windows, SIGINT on other platforms."""
    os.kill(pid, sig or get_default_interrupt_signal())


def get_default_interrupt_signal() -> int:
    return signal.CTRL_BREAK_EVENT if sys.platform == "win32" else signal.SIGINT


def send_interrupt() -> None:
    if IS_WINDOWS:
        # This will raise a KeyboardInterrupt in python land - meaning this wont be able to
        # interrupt things like sleep()
        thread.interrupt_main()
    else:
        # If on unix send an os level signal to interrupt any situation we may be stuck in
        os.kill(os.getpid(), signal.SIGINT)


# ########################
# ##### SHUTDOWN PIPE
# ########################

_PIPE_SHUTDOWN_INDICATOR = "SHUTDOWN"


def get_ipc_shutdown_pipe() -> tuple[int, int]:
    r_fd, w_fd = os.pipe()

    # On windows, convert fd to a Windows handle so it can be reliably passed across processes.
    if sys.platform == "win32":
        import msvcrt

        os.set_inheritable(r_fd, True)
        r_fd = msvcrt.get_osfhandle(r_fd)
    return r_fd, w_fd


@contextmanager
def monitor_ipc_shutdown_pipe(pipe_fd: int, handler: Callable[[], None]) -> Iterator[None]:
    """Monitor the passed in pipe file descriptor for the shutdown indicator message.
    When received, trigger the handler.

    Args:
        pipe_fd: The file descriptor of the pipe to monitor. Must be readable.
            If on windows, this is assumed to be a Windows handle rather than a regular file
            descriptor.
        handler: The handler to call when the shutdown indicator is received.
    """
    # On windows, we expect to receive a raw Windows handle rather than a regular file descriptor.
    # Convert to a file descriptor before reading.
    if sys.platform == "win32":
        import msvcrt

        pipe_fd = msvcrt.open_osfhandle(pipe_fd, os.O_RDONLY)

    break_event = threading.Event()

    def _watch_pipe_for_shutdown():
        with open(pipe_fd) as pipe:
            while not break_event.is_set():
                line = pipe.readline()
                if not line:  # EOF or pipe closed
                    break_event.set()
                elif _PIPE_SHUTDOWN_INDICATOR in line.strip():
                    break_event.set()
                    handler()

    # Start a background thread that watches the pipe
    monitor_thread = threading.Thread(target=_watch_pipe_for_shutdown, daemon=True)
    monitor_thread.start()

    try:
        yield
    finally:
        # Signal the thread to exit and wait for it to stop
        break_event.set()
        monitor_thread.join()


@contextmanager
def interrupt_on_ipc_shutdown_message(pipe_fd: int) -> Iterator[None]:
    """Monitor the passed in pipe file descriptor for the shutdown indicator message. Interrupt the
    current process when the message is received.

    Args:
        pipe_fd: The file descriptor of the pipe to monitor. Must be readable.
            If on windows, this is assumed to be raw Windows handle rather than a regular file
            descriptor.
    """
    # Important to use `send_interrupt` here rather than unconditionally sending a signal. Sending a
    # signal, even to the process itself, often has strange behavior on windows.
    with monitor_ipc_shutdown_pipe(pipe_fd, handler=lambda: send_interrupt()):
        yield


def send_ipc_shutdown_message(w_fd: int) -> None:
    os.write(w_fd, f"{_PIPE_SHUTDOWN_INDICATOR}\n".encode())
    os.close(w_fd)


# ########################
# ##### TEMPFILE
# ########################


@contextmanager
def ipc_tempfile() -> Iterator[str]:
    """Yield a temporary file suitable for cross-platform IPC."""
    # Use delete=False and immediately close for windows compatibility, otherwise windows
    # file-locking will prevent writing to the file.
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    try:
        yield temp_file.name
    finally:
        os.remove(temp_file.name)


ExceptionInfo: TypeAlias = Union[
    tuple[type[BaseException], BaseException, TracebackType],
    tuple[None, None, None],
]


def _serializable_error_info_from_exc_info(
    exc_info: ExceptionInfo,
) -> SerializableErrorInfo:
    # `sys.exc_info() return Tuple[None, None, None] when there is no exception being processed. We accept this in
    # the type signature here since this function is meant to directly receive the return value of
    # `sys.exc_info`, but the function should never be called when there is no exception to process.
    exc_type, e, tb = exc_info
    tb_exc = traceback.TracebackException(
        check.not_none(exc_type), check.not_none(e), check.not_none(tb)
    )
    return SerializableErrorInfo.from_traceback(tb_exc)


class FileBasedWriteStream:
    def __init__(self, file_path):
        check.str_param("file_path", file_path)
        self._file_path = file_path

    def send(self, dagster_named_tuple):
        _send(self._file_path, dagster_named_tuple)

    def send_error(self, exc_info, message=None):
        _send_error(self._file_path, exc_info, message=message)


def _send(file_path, obj):
    with open(os.path.abspath(file_path), "a+") as fp:
        fp.write(serialize_value(obj) + "\n")


def _send_error(file_path, exc_info, message):
    return _send(
        file_path,
        IPCErrorMessage(
            serializable_error_info=_serializable_error_info_from_exc_info(exc_info),
            message=message,
        ),
    )


def _process_line(
    file_pointer, sleep_interval=0.1, as_type: Optional[type[T_PackableValue]] = None
):
    while True:
        line = file_pointer.readline()
        if line:
            return deserialize_value(
                line.rstrip(),
                as_type=(
                    Union[IPCStartMessage, IPCEndMessage, IPCErrorMessage, as_type]
                    if as_type
                    else Union[IPCStartMessage, IPCEndMessage, IPCErrorMessage]
                ),
            )
        time.sleep(sleep_interval)


def _poll_process(ipc_process):
    if not ipc_process:
        return
    if ipc_process.poll() is not None:
        raise DagsterIPCProtocolError(
            f"Process exited with return code {ipc_process.returncode} while waiting for events"
        )


def ipc_read_event_stream(
    file_path, timeout=30, ipc_process=None, as_type: Optional[type[T_PackableValue]] = None
):
    # Wait for file to be ready
    sleep_interval = 0.1
    elapsed_time = 0
    while (not timeout or elapsed_time < timeout) and not os.path.exists(file_path):
        _poll_process(ipc_process)
        elapsed_time += sleep_interval
        time.sleep(sleep_interval)

    if not os.path.exists(file_path):
        raise DagsterIPCProtocolError(
            f"Timeout: read stream has not received any data in {timeout} seconds"
        )

    with open(os.path.abspath(file_path)) as file_pointer:
        message = _process_line(file_pointer, as_type=as_type)
        while (not timeout or elapsed_time < timeout) and message is None:
            _poll_process(ipc_process)
            elapsed_time += sleep_interval
            time.sleep(sleep_interval)
            message = _process_line(file_pointer, as_type=as_type)

        # Process start message
        if not isinstance(message, IPCStartMessage):
            raise DagsterIPCProtocolError(
                f"Attempted to read stream at file {file_path}, but first message was not an "
                "IPCStartMessage"
            )

        message = _process_line(file_pointer, as_type=as_type)
        while not isinstance(message, IPCEndMessage):
            if message is None:
                _poll_process(ipc_process)
            yield message
            message = _process_line(file_pointer, as_type=as_type)


@contextmanager
def ipc_write_stream(file_path):
    check.str_param("file_path", file_path)
    _send(file_path, IPCStartMessage())
    try:
        yield FileBasedWriteStream(file_path)
    except Exception:  # pylint: disable=broad-except
        _send_error(file_path, sys.exc_info(), message=None)
    finally:
        _send(file_path, IPCEndMessage())


def write_unary_input(input_file, obj):
    check.str_param(input_file, "input_file")
    check.not_none_param(obj, "obj")
    with open(os.path.abspath(input_file), "w") as fp:
        fp.write(serialize_value(obj))


def read_unary_input(input_file, as_type: type[T_PackableValue]) -> T_PackableValue:
    check.str_param(input_file, "input_file")
    with open(os.path.abspath(input_file)) as fp:
        return deserialize_value(fp.read(), as_type=as_type)


def ipc_write_unary_response(output_file, obj):
    check.not_none_param(obj, "obj")
    with ipc_write_stream(output_file) as stream:
        stream.send(obj)


def read_unary_response(
    output_file, as_type: Optional[type[T_PackableValue]] = None, timeout=30, ipc_process=None
):
    messages = list(
        ipc_read_event_stream(
            output_file, timeout=timeout, ipc_process=ipc_process, as_type=as_type
        )
    )
    check.invariant(len(messages) == 1)
    return messages[0]


@whitelist_for_serdes
@record
class IPCStartMessage:
    pass


@whitelist_for_serdes
@record
class IPCErrorMessage:
    """This represents a user error encountered during the IPC call. This indicates a business
    logic error, rather than a protocol.
    """

    serializable_error_info: SerializableErrorInfo
    message: Optional[str]


@whitelist_for_serdes
@record
class IPCEndMessage:
    pass


class DagsterIPCProtocolError(Exception):
    """This indicates that something went wrong with the protocol. E.g. the
    process being called did not emit an IPCStartMessage first.
    """
