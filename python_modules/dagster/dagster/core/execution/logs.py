import atexit
import os
import sys
from collections import defaultdict
from contextlib import contextmanager

from rx import Observable
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from dagster import check
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.utils import Features, dagster_compute_logs_dir, ensure_dir, is_dagster_home_set

IO_TYPE_STDOUT = 'out'
IO_TYPE_STDERR = 'err'
IO_TYPE_COMPLETE = 'complete'
POLLING_TIMEOUT = 2


class ComputeLogManager(object):
    def __init__(self):
        self._subscriptions = defaultdict(list)
        self._watchers = {}
        self._observer = PollingObserver(POLLING_TIMEOUT)
        self._observer.start()

    def watch(self, run_id, step_key):
        key = _run_key(run_id, step_key)
        if key in self._watchers:
            return

        self._watchers[key] = self._observer.schedule(
            ComputeLogEventHandler(self, run_id, step_key),
            os.path.dirname(_filepath(run_id, step_key, IO_TYPE_STDOUT)),
        )

    def unwatch(self, run_id, step_key, handler):
        key = _run_key(run_id, step_key)
        if key in self._watchers:
            self._observer.remove_handler_for_watch(handler, self._watchers[key])
        del self._watchers[key]

    def on_compute_end(self, run_id, step_key):
        run_key = _run_key(run_id, step_key)
        for subscription in self._subscriptions.pop(run_key, []):
            subscription.on_compute_end()

    def on_subscribe(self, subscription, run_id, step_key):
        key = _run_key(run_id, step_key)
        self._subscriptions[key].append(subscription)
        self.watch(run_id, step_key)

    def on_update(self, run_id, step_key):
        key = _run_key(run_id, step_key)
        for subscription in self._subscriptions[key]:
            subscription.fetch()

    def get_observable(self, run_id, step_key, cursor):
        subscription = ComputeLogSubscription(run_id, step_key, cursor)
        self.on_subscribe(subscription, run_id, step_key)
        return Observable.create(subscription)  # pylint: disable=E1101


def _run_key(run_id, step_key):
    return '{}:{}'.format(run_id, step_key)


def _from_run_key(key):
    return key.split(':')


class ComputeLogEventHandler(PatternMatchingEventHandler):
    def __init__(self, manager, run_id, step_key):
        self.manager = manager
        self.run_id = run_id
        self.step_key = step_key
        patterns = [
            _filepath(self.run_id, self.step_key, IO_TYPE_COMPLETE),
            _filepath(self.run_id, self.step_key, IO_TYPE_STDOUT),
            _filepath(self.run_id, self.step_key, IO_TYPE_STDERR),
        ]
        super(ComputeLogEventHandler, self).__init__(patterns=patterns)

    def on_created(self, event):
        if event.src_path == _filepath(self.run_id, self.step_key, IO_TYPE_COMPLETE):
            self.manager.on_compute_end(self.run_id, self.step_key)
            self.manager.unwatch(self.run_id, self.step_key, self)

    def on_modified(self, event):
        if event.src_path in (
            _filepath(self.run_id, self.step_key, IO_TYPE_STDOUT),
            _filepath(self.run_id, self.step_key, IO_TYPE_STDERR),
        ):
            self.manager.on_update(self.run_id, self.step_key)


class ComputeLogSubscription(object):
    def __init__(self, run_id, step_key, cursor):
        self.run_id = run_id
        self.step_key = step_key
        self.cursor = cursor
        self.observer = None
        atexit.register(self._clean)

    def __call__(self, observer):
        self.observer = observer
        self.fetch()

    def fetch(self):
        if self.observer:
            self.observer.on_next(fetch_compute_logs(self.run_id, self.step_key, self.cursor))

    def on_compute_end(self):
        self.fetch()
        if self.observer:
            self.observer.on_completed()

    def _clean(self):
        if self.observer:
            self.observer.on_completed()
        self.observer = None


class ComputeLogUpdate(object):
    def __init__(self, stdout, stderr, cursor):
        self.stdout = stdout
        self.stderr = stderr
        self.cursor = cursor


def fetch_compute_logs(run_id, step_key, cursor=None):
    out_offset, err_offset = _decode_cursor(cursor)
    stdout, _new_out_offset = _fetch_compute_data(run_id, step_key, IO_TYPE_STDOUT, out_offset)
    stderr, _new_err_offset = _fetch_compute_data(run_id, step_key, IO_TYPE_STDERR, err_offset)
    cursor = _encode_cursor(_new_out_offset, _new_err_offset)
    return ComputeLogUpdate(stdout, stderr, cursor)


def should_capture_stdout():
    # for ease of mocking
    return Features.DAGIT_STDOUT.is_enabled


def _fetch_compute_data(run_id, step_key, io_type, after=0):
    outfile = _filepath(run_id, step_key, io_type)
    data = ''
    cursor = 0
    if os.path.exists(outfile) and os.path.isfile(outfile):
        with open(outfile, 'r') as f:
            f.seek(after, os.SEEK_SET)
            data = f.read()
            cursor = f.tell()
    return data, cursor


@contextmanager
def redirect_io_to_fs(step_context):
    # https://github.com/dagster-io/dagster/issues/1698
    if not should_capture_stdout():
        yield
        return

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    outpath = _filepath(step_context.run_id, step_context.step.key, IO_TYPE_STDOUT)
    errpath = _filepath(step_context.run_id, step_context.step.key, IO_TYPE_STDERR)
    touchpath = _filepath(step_context.run_id, step_context.step.key, IO_TYPE_COMPLETE)

    ensure_dir(os.path.dirname(outpath))
    ensure_dir(os.path.dirname(errpath))

    with open(outpath, 'w') as out:
        with open(errpath, 'w') as err:
            with _redirect_stream(to_stream=out, from_stream=sys.stdout):
                with _redirect_stream(to_stream=err, from_stream=sys.stderr):
                    yield
    with open(touchpath, 'a'):
        # touch the file to signify that compute is complete
        os.utime(touchpath, None)


def _filebase(run_id, step_key):
    assert is_dagster_home_set()
    return os.path.join(dagster_compute_logs_dir(), run_id, step_key)


def _filepath(run_id, step_key, io_type):
    assert is_dagster_home_set()
    assert io_type in (IO_TYPE_COMPLETE, IO_TYPE_STDERR, IO_TYPE_STDOUT)
    if io_type == IO_TYPE_STDERR:
        extension = 'err'
    if io_type == IO_TYPE_STDOUT:
        extension = 'out'
    if io_type == IO_TYPE_COMPLETE:
        extension = 'complete'
    return "{}.{}".format(_filebase(run_id, step_key), extension)


def _decode_cursor(cursor):
    if not cursor:
        out_offset = 0
        err_offset = 0
    else:
        parts = cursor.split(':')
        out_offset = int(parts[0])
        err_offset = int(parts[1])
    return out_offset, err_offset


def _encode_cursor(out_offset, err_offset):
    check.int_param(out_offset, 'out_offset')
    check.int_param(err_offset, 'err_offset')
    return '{}:{}'.format(out_offset, err_offset)


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
