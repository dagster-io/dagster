from __future__ import print_function

import io
import os
import subprocess
import sys
import time
from contextlib import contextmanager

from dagster import check
from dagster.core.execution import watch_orphans
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.seven import IS_WINDOWS
from dagster.utils import ensure_file

WIN_PY36_COMPUTE_LOG_DISABLED_MSG = '''\u001b[33mWARNING: Compute log capture is disabled for the current environment. Set the environment variable `PYTHONLEGACYWINDOWSSTDIO` to enable.\n\u001b[0m'''


@contextmanager
def mirror_step_io(step_context):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    manager = step_context.instance.compute_log_manager
    if not manager.enabled(step_context):
        yield
        return

    outpath = manager.get_local_path(
        step_context.run_id, step_context.step.key, ComputeIOType.STDOUT
    )
    errpath = manager.get_local_path(
        step_context.run_id, step_context.step.key, ComputeIOType.STDERR
    )

    manager.on_compute_start(step_context)
    with mirror_io(outpath, errpath):
        # compute function executed here
        yield
    manager.on_compute_finish(step_context)


def should_disable_io_stream_redirect():
    # See https://stackoverflow.com/a/52377087
    return (
        os.name == 'nt'
        and sys.version_info.major == 3
        and sys.version_info.minor >= 6
        and not os.environ.get('PYTHONLEGACYWINDOWSSTDIO')
    )


def warn_if_compute_logs_disabled():
    if should_disable_io_stream_redirect():
        print(WIN_PY36_COMPUTE_LOG_DISABLED_MSG)


@contextmanager
def mirror_io(outpath, errpath, buffering=1):
    with mirror_stream(outpath, ComputeIOType.STDOUT, buffering):
        with mirror_stream(errpath, ComputeIOType.STDERR, buffering):
            yield


@contextmanager
def mirror_stream(path, io_type, buffering=1):
    ensure_file(path)
    from_stream = sys.stderr if io_type == ComputeIOType.STDERR else sys.stdout
    with tailf(path, io_type):
        with open(path, 'a+', buffering=buffering) as to_stream:
            with redirect_stream(to_stream=to_stream, from_stream=from_stream):
                yield


@contextmanager
def redirect_stream(to_stream=os.devnull, from_stream=sys.stdout):
    # swap the file descriptors to capture system-level output in the process
    # From https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262
    from_fd = _fileno(from_stream)
    to_fd = _fileno(to_stream)

    if not from_fd or not to_fd or should_disable_io_stream_redirect():
        yield
        return

    with os.fdopen(os.dup(from_fd), 'wb') as copied:
        from_stream.flush()
        try:
            os.dup2(_fileno(to_stream), from_fd)
        except ValueError:
            with open(to_stream, 'wb') as to_file:
                os.dup2(to_file.fileno(), from_fd)
        try:
            yield from_stream
        finally:
            from_stream.flush()
            to_stream.flush()
            os.dup2(copied.fileno(), from_fd)


POLLING_INTERVAL = 0.1


@contextmanager
def tailf(path, io_type=ComputeIOType.STDOUT):
    if IS_WINDOWS:
        with execute_windows_tail(path, io_type):
            yield
    else:
        with execute_posix_tail(path, io_type):
            yield


@contextmanager
def execute_windows_tail(path, io_type):
    # Cannot use multiprocessing here because we already may be in a daemonized process
    # Instead, invoke a thin wrapper around tail_polling using the dagster cli
    cmd = '{} -m dagster utils tail {} --parent-pid {} --io-type {}'.format(
        sys.executable, path, os.getpid(), io_type
    ).split(' ')
    tail_process = subprocess.Popen(cmd)

    try:
        yield
    finally:
        if tail_process:
            time.sleep(2 * POLLING_INTERVAL)
            tail_process.terminate()


@contextmanager
def execute_posix_tail(path, io_type):
    # open a subprocess to tail the file and print to stdout
    tail_cmd = 'tail -F -c +0 {}'.format(path).split(' ')
    stream = sys.stdout if io_type == ComputeIOType.STDOUT else sys.stderr
    stream = stream if _fileno(stream) else None
    tail_process = subprocess.Popen(tail_cmd, stdout=stream)

    # open a watcher process to check for the orphaning of the tail process (e.g. when the
    # current process is suddenly killed)
    watcher_file = os.path.abspath(watch_orphans.__file__)
    watcher_process = subprocess.Popen(
        [sys.executable, watcher_file, str(os.getpid()), str(tail_process.pid),]
    )

    try:
        yield
    finally:
        _clean_up_subprocess(tail_process)
        _clean_up_subprocess(watcher_process)


def _clean_up_subprocess(subprocess_obj):
    try:
        if subprocess_obj:
            subprocess_obj.terminate()
    except OSError:
        pass


def tail_polling(filepath, stream=sys.stdout, parent_pid=None):
    '''
    Tails a file and outputs the content to the specified stream via polling.
    The pid of the parent process (if provided) is checked to see if the tail process should be
    terminated, in case the parent is hard-killed / segfaults
    '''
    with open(filepath, 'r') as file:
        for block in iter(lambda: file.read(1024), None):
            if block:
                print(block, end='', file=stream)
            else:
                if parent_pid and current_process_is_orphaned(parent_pid):
                    sys.exit()
                time.sleep(POLLING_INTERVAL)


def current_process_is_orphaned(parent_pid):
    parent_pid = int(parent_pid)
    if sys.platform == 'win32':
        import psutil

        try:
            parent = psutil.Process(parent_pid)
            return parent.status() != psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return True

    else:
        return os.getppid() != parent_pid


def _fileno(stream):
    try:
        fd = getattr(stream, 'fileno', lambda: stream)()
    except io.UnsupportedOperation:
        # Test CLI runners will stub out stdout to a non-file stream, which will raise an
        # UnsupportedOperation if `fileno` is accessed.  We need to make sure we do not error out,
        # or tests will fail
        return None

    if isinstance(fd, int):
        return fd

    return None
