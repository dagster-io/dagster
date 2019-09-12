import atexit
import io
import os
import subprocess
import sys
from collections import defaultdict
from contextlib import contextmanager
from enum import Enum

from rx import Observable
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from dagster import check
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.utils import ensure_dir, ensure_file, touch_file


class ComputeIOType(Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'
    COMPLETE = 'complete'


IO_TYPE_EXTENSION = {
    ComputeIOType.STDOUT: 'out',
    ComputeIOType.STDERR: 'err',
    ComputeIOType.COMPLETE: 'complete',
}

POLLING_TIMEOUT = 2.5
MAX_BYTES_FILE_READ = 33554432  # 32 MB
MAX_BYTES_CHUNK_READ = 4194304  # 4 MB


def build_local_download_url(run_id, step_key, io_type):
    # should match the app url rule in dagit, for the local case
    return "/download/{}/{}/{}".format(run_id, step_key, io_type.value)


class ComputeLogManager(object):
    def __init__(self, base_dir, logging_enabled=True):
        self._base_dir = base_dir
        self._logging_enabled = logging_enabled
        self._subscriptions = defaultdict(list)
        self._watchers = {}
        self._observer = PollingObserver(POLLING_TIMEOUT)
        self._observer.start()

    def enabled(self, _step_context):
        return self._logging_enabled

    def run_directory(self, run_id):
        return os.path.join(self._base_dir, run_id, 'compute_logs')

    def filepath(self, run_id, step_key, io_type):
        check.inst_param(io_type, 'io_type', ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        return os.path.join(self.run_directory(run_id), "{}.{}".format(step_key, extension))

    def compute_completed(self, run_id, step_key):
        return os.path.exists(self.filepath(run_id, step_key, ComputeIOType.COMPLETE))

    def fetch_log_data(self, run_id, step_key, cursor=None, max_bytes=MAX_BYTES_FILE_READ):
        out_offset, err_offset = _decode_cursor(cursor)
        stdout = self.fetch_file_data(run_id, step_key, ComputeIOType.STDOUT, out_offset, max_bytes)
        stderr = self.fetch_file_data(run_id, step_key, ComputeIOType.STDERR, err_offset, max_bytes)
        cursor = _encode_cursor(stdout.cursor if stdout else 0, stderr.cursor if stderr else 0)
        return ComputeLogData(stdout, stderr, cursor)

    def fetch_file_data(self, run_id, step_key, io_type, offset, max_bytes):
        path = self.filepath(run_id, step_key, io_type)
        if not os.path.exists(path) or not os.path.isfile(path):
            return None

        # See: https://docs.python.org/2/library/stdtypes.html#file.tell for Windows behavior
        with open(path, 'rb') as f:
            f.seek(offset, os.SEEK_SET)
            data = f.read(max_bytes)
            cursor = f.tell()
            stats = os.fstat(f.fileno())

        # local download path
        download_url = build_local_download_url(run_id, step_key, io_type)
        return ComputeLogFileData(path, data.decode('utf-8'), cursor, stats.st_size, download_url)

    def watch(self, run_id, step_key):
        key = _run_key(run_id, step_key)
        if key in self._watchers:
            return

        self._watchers[key] = self._observer.schedule(
            ComputeLogEventHandler(self, run_id, step_key), self.run_directory(run_id)
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
        subscription = ComputeLogSubscription(self, run_id, step_key, cursor)
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
        super(ComputeLogEventHandler, self).__init__(
            patterns=[
                manager.filepath(run_id, step_key, ComputeIOType.COMPLETE),
                manager.filepath(run_id, step_key, ComputeIOType.STDOUT),
                manager.filepath(run_id, step_key, ComputeIOType.STDERR),
            ]
        )

    def filepath(self, io_type):
        return self.manager.filepath(self.run_id, self.step_key, io_type)

    def on_created(self, event):
        if event.src_path == self.filepath(ComputeIOType.COMPLETE):
            self.manager.on_compute_end(self.run_id, self.step_key)
            self.manager.unwatch(self.run_id, self.step_key, self)

    def on_modified(self, event):
        if event.src_path in (
            self.filepath(ComputeIOType.STDOUT),
            self.filepath(ComputeIOType.STDERR),
        ):
            self.manager.on_update(self.run_id, self.step_key)


class ComputeLogSubscription(object):
    def __init__(self, manager, run_id, step_key, cursor):
        self.manager = manager
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
            should_fetch = True
            while should_fetch:
                update = self.manager.fetch_log_data(
                    self.run_id, self.step_key, self.cursor, max_bytes=MAX_BYTES_CHUNK_READ
                )
                if update.cursor != self.cursor:
                    self.observer.on_next(update)
                    self.cursor = update.cursor
                should_fetch = (
                    update.stdout
                    and len(update.stdout.data.encode('utf-8')) >= MAX_BYTES_CHUNK_READ
                ) or (
                    update.stderr
                    and len(update.stderr.data.encode('utf-8')) >= MAX_BYTES_CHUNK_READ
                )

    def on_compute_end(self):
        self.fetch()
        if self.observer:
            self.observer.on_completed()

    def _clean(self):
        if self.observer:
            self.observer.on_completed()
        self.observer = None


class ComputeLogData(object):
    def __init__(self, stdout, stderr, cursor):
        self.stdout = stdout
        self.stderr = stderr
        self.cursor = cursor


class ComputeLogFileData(object):
    def __init__(self, path, data, cursor, size, download_url):
        self.path = path
        self.data = data
        self.cursor = cursor
        self.size = size
        self.download_url = download_url


@contextmanager
def mirror_step_io(step_context):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    manager = step_context.instance.compute_log_manager
    outpath = manager.filepath(step_context.run_id, step_context.step.key, ComputeIOType.STDOUT)
    errpath = manager.filepath(step_context.run_id, step_context.step.key, ComputeIOType.STDERR)
    touchpath = manager.filepath(step_context.run_id, step_context.step.key, ComputeIOType.COMPLETE)

    ensure_dir(os.path.dirname(outpath))
    ensure_dir(os.path.dirname(errpath))

    if not manager.enabled(step_context):
        yield
        return

    with mirror_stream(sys.stderr, errpath):
        with mirror_stream(sys.stdout, outpath):
            yield

    # touch the file to signify that compute is complete
    touch_file(touchpath)


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
        yield
        p.terminate()


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
