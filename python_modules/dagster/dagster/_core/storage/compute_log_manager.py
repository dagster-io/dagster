from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from typing import Callable, Iterator, NamedTuple, Optional

from typing_extensions import Self

import dagster._check as check
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun

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
    """Representation of a chunk of compute execution log data."""

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


class ComputeLogManager(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract base class for storing unstructured compute logs (stdout/stderr) from the compute
    steps of pipeline solids.
    """

    @contextmanager
    def watch(self, dagster_run: DagsterRun, step_key: Optional[str] = None) -> Iterator[None]:
        """Watch the stdout/stderr for a given execution for a given run_id / step_key and persist it.

        Args:
            dagster_run (DagsterRun): The run config
            step_key (Optional[String]): The step_key for a compute step
        """
        check.inst_param(dagster_run, "dagster_run", DagsterRun)
        check.opt_str_param(step_key, "step_key")

        if not self.enabled(dagster_run, step_key):
            yield
            return

        self.on_watch_start(dagster_run, step_key)
        with self._watch_logs(dagster_run, step_key):
            yield
        self.on_watch_finish(dagster_run, step_key)

    @contextmanager
    @abstractmethod
    def _watch_logs(
        self, dagster_run: DagsterRun, step_key: Optional[str] = None
    ) -> Iterator[None]:
        """Method to watch the stdout/stderr logs for a given run_id / step_key.  Kept separate from
        blessed `watch` method, which triggers all the start/finish hooks that are necessary to
        implement the different remote implementations.

        Args:
            dagster_run (DagsterRun): The run config
            step_key (Optional[String]): The step_key for a compute step
        """

    @abstractmethod
    def get_local_path(self, run_id: str, key: str, io_type: ComputeIOType) -> str:
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
        ...

    @abstractmethod
    def is_watch_completed(self, run_id: str, key: str) -> bool:
        """Flag indicating when computation for a given execution step has completed.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)

        Returns:
            Boolean
        """

    @abstractmethod
    def on_watch_start(self, dagster_run: DagsterRun, step_key: Optional[str]) -> None:
        """Hook called when starting to watch compute logs.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """

    @abstractmethod
    def on_watch_finish(self, dagster_run: DagsterRun, step_key: Optional[str]) -> None:
        """Hook called when computation for a given execution step is finished.

        Args:
            pipeline_run (PipelineRun): The pipeline run config
            step_key (Optional[String]): The step_key for a compute step
        """

    @abstractmethod
    def download_url(self, run_id: str, key: str, io_type: ComputeIOType) -> str:
        """Get a URL where the logs can be downloaded.

        Args:
            run_id (str): The id of the pipeline run.
            key (str): The unique descriptor of the execution step (e.g. `solid_invocation.compute`)
            io_type (ComputeIOType): Flag indicating the I/O type, either stdout or stderr

        Returns:
            String
        """

    @abstractmethod
    def read_logs_file(
        self,
        run_id: str,
        key: str,
        io_type: ComputeIOType,
        cursor: int = 0,
        max_bytes: int = MAX_BYTES_FILE_READ,
    ) -> ComputeLogFileData:
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

    def enabled(self, _dagster_run: DagsterRun, _step_key: Optional[str]) -> bool:
        """Hook for disabling compute log capture.

        Args:
            _step_key (Optional[String]): The step_key for a compute step

        Returns:
            Boolean
        """
        return True

    @abstractmethod
    def on_subscribe(self, subscription: "ComputeLogSubscription") -> None:
        """Hook for managing streaming subscriptions for log data from `dagit`.

        Args:
            subscription (ComputeLogSubscription): subscription object which manages when to send
                back data to the subscriber
        """

    def on_unsubscribe(self, subscription: "ComputeLogSubscription") -> None:
        pass

    def observable(
        self, run_id: str, key: str, io_type: ComputeIOType, cursor: Optional[str] = None
    ) -> "ComputeLogSubscription":
        """Return a ComputeLogSubscription which streams back log data from the execution logs for a given
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
            cursor = int(cursor)  # type: ignore   # (var reassigned diff type)
        else:
            cursor = 0  # type: ignore  # (var reassigned diff type)

        subscription = ComputeLogSubscription(self, run_id, key, io_type, cursor)  # type: ignore  # (var reassigned diff type)
        self.on_subscribe(subscription)
        return subscription

    def dispose(self):
        pass


class ComputeLogSubscription:
    """Observable object that generates ComputeLogFileData objects as compute step execution logs
    are written.
    """

    def __init__(
        self,
        manager: ComputeLogManager,
        run_id: str,
        key: str,
        io_type: ComputeIOType,
        cursor: int,
    ):
        self.manager = manager
        self.run_id = run_id
        self.key = key
        self.io_type = io_type
        self.cursor = cursor
        self.observer: Optional[Callable[[ComputeLogFileData], None]] = None
        self.is_complete = False

    def __call__(self, observer: Callable[[ComputeLogFileData], None]) -> Self:
        self.observer = observer
        self.fetch()
        if self.manager.is_watch_completed(self.run_id, self.key):
            self.complete()
        return self

    def dispose(self) -> None:
        # called when the connection gets closed, allowing the observer to get GC'ed
        self.observer = None
        self.manager.on_unsubscribe(self)

    def fetch(self) -> None:
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
                self.observer(update)
                self.cursor = update.cursor
            should_fetch = update.data and len(update.data.encode("utf-8")) >= MAX_BYTES_CHUNK_READ

    def complete(self) -> None:
        self.is_complete = True
        if not self.observer:
            return
