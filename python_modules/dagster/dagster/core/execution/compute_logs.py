import io
import os
import subprocess
import sys
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
        cmd = 'tail -F -n 1 {}'.format(path).split(' ')
        p = subprocess.Popen(cmd)
        try:
            yield
        finally:
            p.terminate()


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
