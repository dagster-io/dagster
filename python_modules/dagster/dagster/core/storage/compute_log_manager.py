import atexit
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from enum import Enum

import six
from rx import Observable

from dagster import check

MAX_BYTES_FILE_READ = 33554432  # 32 MB
MAX_BYTES_CHUNK_READ = 4194304  # 4 MB


class ComputeIOType(Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'


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
    def read_logs_file(self, run_id, step_key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        pass

    @abstractmethod
    def on_subscribe(self, subscription):
        pass

    def enabled(self, _step_context):
        return True

    def observable(self, run_id, step_key, io_type, cursor=None):
        check.str_param(run_id, 'run_id')
        check.str_param(step_key, 'step_key')
        check.inst_param(io_type, 'io_type', ComputeIOType)
        check.opt_str_param(cursor, 'cursor')

        if cursor:
            cursor = int(cursor)
        else:
            cursor = 0

        subscription = ComputeLogSubscription(self, run_id, step_key, io_type, cursor)
        self.on_subscribe(subscription)
        return Observable.create(subscription)  # pylint: disable=E1101


class ComputeLogSubscription(object):
    def __init__(self, manager, run_id, step_key, io_type, cursor):
        self.manager = manager
        self.run_id = run_id
        self.step_key = step_key
        self.io_type = io_type
        self.cursor = cursor
        self.observer = None
        atexit.register(self._clean)

    def __call__(self, observer):
        self.observer = observer
        self.fetch()
        if self.manager.is_compute_completed(self.run_id, self.step_key):
            self.complete()

    def fetch(self):
        if not self.observer:
            return

        should_fetch = True
        while should_fetch:
            update = self.manager.read_logs_file(
                self.run_id,
                self.step_key,
                self.io_type,
                self.cursor,
                max_bytes=MAX_BYTES_CHUNK_READ,
            )
            if not self.cursor or update.cursor != self.cursor:
                self.observer.on_next(update)
                self.cursor = update.cursor
            should_fetch = update.data and len(update.data.encode('utf-8')) >= MAX_BYTES_CHUNK_READ

    def complete(self):
        if not self.observer:
            return
        self.observer.on_completed()

    def _clean(self):
        self.complete()
        self.observer = None
