import io
import os
import subprocess
import sys
import tempfile
import time
import uuid
import warnings
from contextlib import contextmanager

from dagster.core.execution import poll_compute_logs, watch_orphans
from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster.seven import IS_WINDOWS, wait_for_process
from dagster.utils import ensure_file

WIN_PY36_COMPUTE_LOG_DISABLED_MSG = """\u001b[33mWARNING: Compute log capture is disabled for the current environment. Set the environment variable `PYTHONLEGACYWINDOWSSTDIO` to enable.\n\u001b[0m"""


@contextmanager
def redirect_to_file(stream, filepath):
    with open(filepath, "a+", buffering=1) as file_stream:
        with redirect_stream(file_stream, stream):
            yield


@contextmanager
def mirror_stream_to_file(stream, filepath):
    ensure_file(filepath)
    with tail_to_stream(filepath, stream) as pids:
        with redirect_to_file(stream, filepath):
            yield pids


def should_disable_io_stream_redirect():
    # See https://stackoverflow.com/a/52377087
    # https://www.python.org/dev/peps/pep-0528/
    return os.name == "nt" and not os.environ.get("PYTHONLEGACYWINDOWSSTDIO")


def warn_if_compute_logs_disabled():
    if should_disable_io_stream_redirect():
        warnings.warn(WIN_PY36_COMPUTE_LOG_DISABLED_MSG)


@contextmanager
def redirect_stream(to_stream=os.devnull, from_stream=sys.stdout):
    # swap the file descriptors to capture system-level output in the process
    # From https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262
    from_fd = _fileno(from_stream)
    to_fd = _fileno(to_stream)

    if not from_fd or not to_fd or should_disable_io_stream_redirect():
        yield
        return

    with os.fdopen(os.dup(from_fd), "wb") as copied:
        from_stream.flush()
        try:
            os.dup2(_fileno(to_stream), from_fd)
        except ValueError:
            with open(to_stream, "wb") as to_file:
                os.dup2(to_file.fileno(), from_fd)
        try:
            yield from_stream
        finally:
            from_stream.flush()
            to_stream.flush()
            os.dup2(copied.fileno(), from_fd)


@contextmanager
def tail_to_stream(path, stream):
    if IS_WINDOWS:
        with execute_windows_tail(path, stream) as pids:
            yield pids
    else:
        with execute_posix_tail(path, stream) as pids:
            yield pids


@contextmanager
def execute_windows_tail(path, stream):
    # Cannot use multiprocessing here because we already may be in a daemonized process
    # Instead, invoke a thin script to poll a file and dump output to stdout.  We pass the current
    # pid so that the poll process kills itself if it becomes orphaned
    poll_file = os.path.abspath(poll_compute_logs.__file__)
    stream = stream if _fileno(stream) else None

    with tempfile.TemporaryDirectory() as temp_dir:
        ipc_output_file = os.path.join(
            temp_dir, "execute-windows-tail-{uuid}".format(uuid=uuid.uuid4().hex)
        )

        try:
            tail_process = open_ipc_subprocess(
                [sys.executable, poll_file, path, str(os.getpid()), ipc_output_file], stdout=stream
            )
            yield (tail_process.pid, None)
        finally:
            if tail_process:
                start_time = time.time()
                while not os.path.isfile(ipc_output_file):
                    if time.time() - start_time > 15:
                        raise Exception("Timed out waiting for tail process to start")
                    time.sleep(1)

                # Now that we know the tail process has started, tell it to terminate once there is
                # nothing more to output
                interrupt_ipc_subprocess(tail_process)
                wait_for_process(tail_process)


@contextmanager
def execute_posix_tail(path, stream):
    # open a subprocess to tail the file and print to stdout
    tail_cmd = "tail -F -c +0 {}".format(path).split(" ")
    stream = stream if _fileno(stream) else None

    try:
        tail_process = None
        watcher_process = None
        tail_process = subprocess.Popen(tail_cmd, stdout=stream)

        # open a watcher process to check for the orphaning of the tail process (e.g. when the
        # current process is suddenly killed)
        watcher_file = os.path.abspath(watch_orphans.__file__)
        watcher_process = subprocess.Popen(
            [
                sys.executable,
                watcher_file,
                str(os.getpid()),
                str(tail_process.pid),
            ]
        )

        yield (tail_process.pid, watcher_process.pid)
    finally:
        if tail_process:
            _clean_up_subprocess(tail_process)

        if watcher_process:
            _clean_up_subprocess(watcher_process)


def _clean_up_subprocess(subprocess_obj):
    try:
        if subprocess_obj:
            subprocess_obj.terminate()
            wait_for_process(subprocess_obj)
    except OSError:
        pass


def _fileno(stream):
    try:
        fd = getattr(stream, "fileno", lambda: stream)()
    except io.UnsupportedOperation:
        # Test CLI runners will stub out stdout to a non-file stream, which will raise an
        # UnsupportedOperation if `fileno` is accessed.  We need to make sure we do not error out,
        # or tests will fail
        return None

    if isinstance(fd, int):
        return fd

    return None
