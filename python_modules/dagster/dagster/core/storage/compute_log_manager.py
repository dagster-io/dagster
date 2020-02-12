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


class ComputeLogFileData(namedtuple('ComputeLogFileData', 'path data cursor size download_url')):
    '''Representation of a chunk of compute execution log data'''

    def __new__(cls, path, data, cursor, size, download_url):
        return super(ComputeLogFileData, cls).__new__(
            cls,
            path=check.str_param(path, 'path'),
            data=check.opt_str_param(data, 'data'),
            cursor=check.int_param(cursor, 'cursor'),
            size=check.int_param(size, 'size'),
            download_url=check.opt_str_param(download_url, 'download_url'),
        )


class ComputeLogManager(six.with_metaclass(ABCMeta)):
    '''Abstract base class for storing unstructured compute logs (stdout/stderr) from the compute
    steps of pipeline solids.'''

    @abstractmethod
    def get_local_path(self, run_id, step_key, io_type):
        '''Get the local path of the logfile for a given execution step.  This determines the
        location on the local filesystem to which stdout/stderr will be rerouted.

        Args:
            run_id (str): The id of the pipeline run.
            step_key (str): The unique descriptor of the execution step
                            (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr

        Returns:
            Path
        '''

    @abstractmethod
    def is_compute_completed(self, run_id, step_key):
        '''Flag indicating when computation for a given execution step has completed.

        Args:
            run_id (str): The id of the pipeline run.
            step_key (str): The unique descriptor of the execution step
                            (e.g. `solid_invocation.compute`)

        Returns:
            Boolean
        '''

    @abstractmethod
    def on_compute_start(self, step_context):
        '''Hook called when computation for a given execution step is starting.

        Args:
            step_context (SystemStepExecutionContext): The execution context for the compute step
        '''

    @abstractmethod
    def on_compute_finish(self, step_context):
        '''Hook called when computation for a given execution step is finished.

        Args:
            step_context (SystemStepExecutionContext): The execution context for the compute step
        '''

    @abstractmethod
    def download_url(self, run_id, step_key, io_type):
        '''Get a URL where the logs can be downloaded.

        Args:
            run_id (str): The id of the pipeline run.
            step_key (str): The unique descriptor of the execution step
                            (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr

        Returns:
            String
        '''

    @abstractmethod
    def read_logs_file(self, run_id, step_key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        '''Get compute log data for a given compute step.

        Args:
            run_id (str): The id of the pipeline run.
            step_key (str): The unique descriptor of the execution step
                            (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr
            cursor (Optional[Int]): Starting cursor (byte) of log file
            max_bytes (Optional[Int]): Maximum number of bytes to be read and returned

        Returns:
            ComputeLogFileData
        '''

    def enabled(self, _step_context):
        '''Hook for disabling compute log capture.

        Args:
            _step_context (SystemStepExecutionContext): The execution context for the compute step

        Returns:
            Boolean
        '''
        return True

    @abstractmethod
    def on_subscribe(self, subscription):
        '''Hook for managing streaming subscriptions for log data from `dagit`

        Args:
            subscription (ComputeLogSubscription): subscription object which manages when to send
                back data to the subscriber
        '''

    def observable(self, run_id, step_key, io_type, cursor=None):
        '''Return an Observable which streams back log data from the execution logs for a given
        compute step.

        Args:
            run_id (str): The id of the pipeline run.
            step_key (str): The unique descriptor of the execution step
                            (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr
            cursor (Optional[Int]): Starting cursor (byte) of log file

        Returns:
            Observable
        '''
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
    '''Observable object that generates ComputeLogFileData objects as compute step execution logs
    are written
    '''

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
