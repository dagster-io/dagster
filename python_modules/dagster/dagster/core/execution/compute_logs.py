import io
import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager

from dagster import check
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.utils import ensure_file


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
    with mirror_stream(sys.stderr, errpath):
        with mirror_stream(sys.stdout, outpath):
            # compute function executed here
            yield
    manager.on_compute_finish(step_context)


@contextmanager
def mirror_stream(stream, path, buffering=1):
    ensure_file(path)
    with tailf(path):
        with open(path, 'a+', buffering=buffering) as to_stream:
            with redirect_stream(to_stream=to_stream, from_stream=stream):
                yield


@contextmanager
def redirect_stream(to_stream=os.devnull, from_stream=sys.stdout):
    # swap the file descriptors to capture system-level output in the process
    # From https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262
    from_fd = _fileno(from_stream)
    to_fd = _fileno(to_stream)

    if not from_fd or not to_fd:
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


@contextmanager
def tailf(path):
    if sys.platform == 'win32':
        # no tail, bail
        yield
    else:
        # unix only
        cmd = 'tail -F -n 1 {}'.format(path).split(' ')

        # open a subprocess to tail the file and print to stdout
        tail_process = subprocess.Popen(cmd)

        # fork a child watcher process to sleep/wait for the parent process (which yields to the
        # compute function) to either A) complete and clean-up OR B) segfault / die silently.  In
        # the case of B, the spawned tail process will not automatically get terminated, so we need
        # to make sure that we terminate it explicitly and then exit.
        watcher_pid = os.fork()

        if watcher_pid == 0:
            # this is the child watcher process, sleep until orphaned, then kill the tail process
            # and exit
            while True:
                if os.getppid() == 1:  # orphaned process
                    time.sleep(1)
                    tail_process.terminate()
                    sys.exit()
                else:
                    time.sleep(1)
        else:
            # this is the parent process, yield to the compute function and then terminate both the
            # tail and watcher processes.
            try:
                yield
            finally:
                tail_process.terminate()
                os.kill(watcher_pid, signal.SIGTERM)


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
