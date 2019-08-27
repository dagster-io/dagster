import os
import sys
from contextlib import contextmanager

from dagster import check
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.utils import Features, dagster_compute_logs_dir, ensure_dir, is_dagster_home_set

IO_TYPE_STDOUT = 'out'
IO_TYPE_STDERR = 'err'


def fetch_run_step_logs(run_id, step_key):
    stdout = _fetch_run_step_lines(run_id, step_key, IO_TYPE_STDOUT)
    stderr = _fetch_run_step_lines(run_id, step_key, IO_TYPE_STDERR)
    return [stdout, stderr]


def should_capture_stdout():
    return Features.DAGIT_STDOUT.is_enabled


@contextmanager
def redirect_io_to_fs(step_context):
    # https://github.com/dagster-io/dagster/issues/1698
    if not should_capture_stdout():
        yield
        return

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    outpath = _filepath(step_context.run_id, step_context.step.key, IO_TYPE_STDOUT)
    errpath = _filepath(step_context.run_id, step_context.step.key, IO_TYPE_STDERR)
    ensure_dir(os.path.dirname(outpath))
    ensure_dir(os.path.dirname(errpath))

    with open(outpath, 'w') as out:
        with open(errpath, 'w') as err:
            with _redirect_stream(to_stream=out, from_stream=sys.stdout):
                with _redirect_stream(to_stream=err, from_stream=sys.stderr):
                    yield


def _fetch_run_step_lines(run_id, step_key, io_type):
    outfile = _filepath(run_id, step_key, io_type)
    lines = []
    if os.path.exists(outfile) and os.path.isfile(outfile):
        with open(outfile, 'r') as f:
            lines = f.readlines()
    return lines


def _filepath(run_id, step_key, io_type):
    assert is_dagster_home_set()
    extension = 'err' if io_type == IO_TYPE_STDERR else 'out'
    filename = "{}.{}".format(step_key, extension)
    return os.path.join(dagster_compute_logs_dir(), run_id, filename)


#
# From https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262
#
def _fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def _redirect_stream(to_stream=os.devnull, from_stream=sys.stdout):
    # https://github.com/dagster-io/dagster/issues/1699
    fd = _fileno(from_stream)
    with os.fdopen(os.dup(fd), 'wb') as copied:
        from_stream.flush()
        try:
            os.dup2(_fileno(to_stream), fd)
        except ValueError:
            with open(to_stream, 'wb') as to_file:
                os.dup2(to_file.fileno(), fd)
        try:
            yield from_stream
        finally:
            from_stream.flush()
            os.dup2(copied.fileno(), fd)
