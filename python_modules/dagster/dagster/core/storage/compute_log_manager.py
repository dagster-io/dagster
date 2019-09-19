import atexit
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from enum import Enum

import six
from rx import Observable

MAX_BYTES_FILE_READ = 33554432  # 32 MB
MAX_BYTES_CHUNK_READ = 4194304  # 4 MB


class ComputeIOType(Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'
    COMPLETE = 'complete'


ComputeLogData = namedtuple('ComputeLogData', 'stdout stderr cursor')
ComputeLogFileData = namedtuple('ComputeLogFileData', 'path data cursor size download_url')


class ComputeLogManager(six.with_metaclass(ABCMeta)):
    # API
    @abstractmethod
    def get_local_path(self, run_id, step_key, io_type):
        pass

    @abstractmethod
    def is_compute_completed(self, run_id, step_key):
        pass

    @abstractmethod
    def on_compute_start(self, step_context):
        pass

    @abstractmethod
    def on_compute_finish(self, step_context):
        pass

    @abstractmethod
    def download_url(self, run_id, step_key, io_type):
        pass

    @abstractmethod
    def read_logs(self, run_id, step_key, cursor=None, max_bytes=MAX_BYTES_FILE_READ):
        pass

    @abstractmethod
    def on_subscribe(self, subscription):
        pass

    def enabled(self, _step_context):
        return True

    def observable(self, run_id, step_key, cursor=None):
        subscription = ComputeLogSubscription(self, run_id, step_key, cursor)
        self.on_subscribe(subscription)
        return Observable.create(subscription)  # pylint: disable=E1101


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
        if not self.observer:
            return

        should_fetch = True
        while should_fetch:
            update = self.manager.read_logs(
                self.run_id, self.step_key, self.cursor, max_bytes=MAX_BYTES_CHUNK_READ
            )
            if update.cursor != self.cursor:
                self.observer.on_next(update)
                self.cursor = update.cursor
            should_fetch = (
                update.stdout and len(update.stdout.data.encode('utf-8')) >= MAX_BYTES_CHUNK_READ
            ) or (update.stderr and len(update.stderr.data.encode('utf-8')) >= MAX_BYTES_CHUNK_READ)

    def complete(self):
        if not self.observer:
            return
        self.observer.on_completed()

    def _clean(self):
        self.complete()
        self.observer = None
