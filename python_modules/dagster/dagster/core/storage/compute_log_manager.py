from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from typing import NamedTuple, Optional

from rx import Observable

import dagster._check as check
from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.storage.pipeline_run import PipelineRun

MAX_BYTES_FILE_READ = 33554432  # 32 MB
MAX_BYTES_CHUNK_READ = 4194304  # 4 MB


class ComputeIOType(Enum):
    STDOUT = "stdout"
    STDERR = "stderr"


class ComputeLogFileData(
    NamedTuple(
        "ComputeLogFileData",
        [
            ("path", str),
            ("data", Optional[str]),
            ("cursor", int),
            ("size", int),
            ("download_url", Optional[str]),
        ],
    )
):
    """Representation of a chunk of compute execution log data"""

    def __new__(
        cls, path: str, data: Optional[str], cursor: int, size: int, download_url: Optional[str]
    ):
        return super(ComputeLogFileData, cls).__new__(
            cls,
            path=check.str_param(path, "path"),
            data=check.opt_str_param(data, "data"),
            cursor=check.int_param(cursor, "cursor"),
            size=check.int_param(size, "size"),
            download_url=check.opt_str_param(download_url, "download_url"),
        )


class ComputeLogManager(ABC, MayHaveInstanceWeakref):
    """Abstract base class for storing unstructured compute logs (stdout/stderr) from the compute
    steps of pipeline solids."""

    @contextmanager
    def watch(self, pipeline_run, step_key=None):
        """
        Watch the stdout/stderr for a given execution for a given run_id / step_key and persist it.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        check.opt_str_param(step_key, "step_key")

        if not self.enabled(pipeline_run, step_key):
            yield
            return

        self.on_watch_start(pipeline_run, step_key)
        with self._watch_logs(pipeline_run, step_key):
            yield
        self.on_watch_finish(pipeline_run, step_key)

    @contextmanager
    @abstractmethod
    def _watch_logs(self, pipeline_run, step_key=None):
        """
        Method to watch the stdout/stderr logs for a given run_id / step_key.  Kept separate from
        blessed `watch` method, which triggers all the start/finish hooks that are necessary to
        implement the different remote implementations.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """

    def get_local_path(self, run_id, key, io_type):
        """Get the local path of the logfile for a given execution step.  This determines the
        location on the local filesystem to which stdout/stderr will be rerouted.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either ComputeIOType.STDOUT or
                ComputeIOType.STDERR

        Returns:
            str
        """

    @abstractmethod
    def is_watch_completed(self, run_id, key):
        """Flag indicating when computation for a given execution step has completed.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)

        Returns:
            Boolean
        """

    @abstractmethod
    def on_watch_start(self, pipeline_run, step_key):
        """Hook called when starting to watch compute logs.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """

    @abstractmethod
    def on_watch_finish(self, pipeline_run, step_key):
        """Hook called when computation for a given execution step is finished.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """

    @abstractmethod
    def download_url(self, run_id, key, io_type):
        """Get a URL where the logs can be downloaded.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr

        Returns:
            String
        """

    @abstractmethod
    def read_logs_file(self, run_id, key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        """Get compute log data for a given compute step.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr
            cursor (Optional[Int]): Starting cursor (byte) of log file
            max_bytes (Optional[Int]): Maximum number of bytes to be read and returned

        Returns:
            ComputeLogFileData
        """

    def enabled(self, _pipeline_run, _step_key):
        """Hook for disabling compute log capture.

        Args:
            _step_key (Optional[String]): The step_key for a compute step

        Returns:
            Boolean
        """
        return True

    @abstractmethod
    def on_subscribe(self, subscription):
        """Hook for managing streaming subscriptions for log data from `dagit`

        Args:
            subscription (ComputeLogSubscription): subscription object which manages when to send
                back data to the subscriber
        """

    def on_unsubscribe(self, subscription):
        pass

    def observable(self, run_id, key, io_type, cursor=None):
        """Return an Observable which streams back log data from the execution logs for a given
        compute step.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr
            cursor (Optional[Int]): Starting cursor (byte) of log file

        Returns:
            Observable
        """
        check.str_param(run_id, "run_id")
        check.str_param(key, "key")
        check.inst_param(io_type, "io_type", ComputeIOType)
        check.opt_str_param(cursor, "cursor")

        if cursor:
            cursor = int(cursor)
        else:
            cursor = 0

        subscription = ComputeLogSubscription(self, run_id, key, io_type, cursor)
        self.on_subscribe(subscription)
        return Observable.create(subscription)  # pylint: disable=E1101

    def dispose(self):
        pass


class ComputeLogSubscription:
    """Observable object that generates ComputeLogFileData objects as compute step execution logs
    are written
    """

    def __init__(self, manager, run_id, key, io_type, cursor):
        self.manager = manager
        self.run_id = run_id
        self.key = key
        self.io_type = io_type
        self.cursor = cursor
        self.observer = None

    def __call__(self, observer):
        self.observer = observer
        self.fetch()
        if self.manager.is_watch_completed(self.run_id, self.key):
            self.complete()
        return self

    def dispose(self):
        # called when the connection gets closed, allowing the observer to get GC'ed
        if self.observer and callable(getattr(self.observer, "dispose", None)):
            self.observer.dispose()
        self.observer = None
        self.manager.on_unsubscribe(self)

    def fetch(self):
        if not self.observer:
            return

        should_fetch = True
        while should_fetch:
            update = self.manager.read_logs_file(
                self.run_id,
                self.key,
                self.io_type,
                self.cursor,
                max_bytes=MAX_BYTES_CHUNK_READ,
            )
            if not self.cursor or update.cursor != self.cursor:
                self.observer.on_next(update)
                self.cursor = update.cursor
            should_fetch = update.data and len(update.data.encode("utf-8")) >= MAX_BYTES_CHUNK_READ

    def complete(self):
        if not self.observer:
            return
        self.observer.on_completed()
