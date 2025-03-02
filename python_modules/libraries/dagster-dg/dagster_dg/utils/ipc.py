import _thread as thread
import os
import signal
import subprocess
import sys
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, Callable

# NOTE: This is copied over from dagster core. It primarily supports testing of dagster dev in
# varied CI environments, where use of signals is dicey cross-platform.


def open_ipc_subprocess(parts: Sequence[str], **kwargs: Any) -> "subprocess.Popen[Any]":
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


def send_interrupt() -> None:
    if sys.platform == "win32":
        thread.interrupt_main()
    else:
        # If on unix send an os level signal to interrupt any situation we may be stuck in
        os.kill(os.getpid(), signal.SIGINT)
