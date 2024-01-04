import base64
import json
import os
import random
import string
import sys
import time
from contextlib import ExitStack, contextmanager
from typing import Iterator, Literal, Mapping, Optional, Sequence, TextIO

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterPipesExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesChunkedLogReader,
    PipesLogReader,
    open_pipes_session,
)
from dagster_pipes import (
    PipesContextData,
    PipesExtras,
    PipesParams,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files, jobs
from pydantic import Field


@experimental
class _PipesDatabricksClient(PipesClient):
    """Pipes client for databricks.

    Args:
        client (WorkspaceClient): A databricks `WorkspaceClient` object.
        env (Optional[Mapping[str,str]]: An optional dict of environment variables to pass to the
            databricks job.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the k8s container process. Defaults to :py:class:`PipesDbfsContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the databricks job. Defaults to :py:class:`PipesDbfsMessageReader`.
        poll_interval_seconds (float): How long to sleep between checking the status of the job run.
            Defaults to 5.
        forward_termination (bool): Whether to cancel the Databricks job if the orchestration process
            is interrupted or canceled. Defaults to True.
    """

    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )

    def __init__(
        self,
        client: WorkspaceClient,
        env: Optional[Mapping[str, str]] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        poll_interval_seconds: float = 5,
        forward_termination: bool = True,
    ):
        self.client = client
        self.env = env
        self.context_injector = check.opt_inst_param(
            context_injector,
            "context_injector",
            PipesContextInjector,
        ) or PipesDbfsContextInjector(client=self.client)
        self.message_reader = check.opt_inst_param(
            message_reader,
            "message_reader",
            PipesMessageReader,
        )
        self.poll_interval_seconds = check.numeric_param(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_default_message_reader(self, task: jobs.SubmitTask) -> "PipesDbfsMessageReader":
        # include log readers if the user is writing their logs to DBFS
        if task.as_dict().get("new_cluster", {}).get("cluster_log_conf", {}).get("dbfs", None):
            log_readers = [
                PipesDbfsLogReader(
                    client=self.client, remote_log_name="stdout", target_stream=sys.stdout
                ),
                PipesDbfsLogReader(
                    client=self.client, remote_log_name="stderr", target_stream=sys.stderr
                ),
            ]
        else:
            log_readers = None
        return PipesDbfsMessageReader(
            client=self.client,
            log_readers=log_readers,
        )

    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        task: jobs.SubmitTask,
        submit_args: Optional[Mapping[str, str]] = None,
    ) -> PipesClientCompletedInvocation:
        """Synchronously execute a Databricks job with the pipes protocol.

        Args:
            task (databricks.sdk.service.jobs.SubmitTask): Specification of the databricks
                task to run. Environment variables used by dagster-pipes will be set under the
                `spark_env_vars` key of the `new_cluster` field (if there is an existing dictionary
                here, the EXT environment variables will be merged in). Everything else will be
                passed unaltered under the `tasks` arg to `WorkspaceClient.jobs.submit`.
            context (OpExecutionContext): The context from the executing op or asset.
            extras (Optional[PipesExtras]): An optional dict of extra parameters to pass to the
                subprocess.
            submit_args (Optional[Mapping[str, str]]): Additional keyword arguments that will be
                forwarded as-is to `WorkspaceClient.jobs.submit`.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
                process.
        """
        message_reader = self.message_reader or self.get_default_message_reader(task)
        with open_pipes_session(
            context=context,
            extras=extras,
            context_injector=self.context_injector,
            message_reader=message_reader,
        ) as pipes_session:
            submit_task_dict = task.as_dict()
            submit_task_dict["new_cluster"]["spark_env_vars"] = {
                **submit_task_dict["new_cluster"].get("spark_env_vars", {}),
                **(self.env or {}),
                **pipes_session.get_bootstrap_env_vars(),
            }

            task = jobs.SubmitTask.from_dict(submit_task_dict)
            run_id = self.client.jobs.submit(
                tasks=[task],
                **(submit_args or {}),
            ).bind()["run_id"]

            try:
                self._poll_til_success(context, run_id)
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.info("[pipes] execution interrupted, canceling Databricks job.")
                    self.client.jobs.cancel_run(run_id)
                    self._poll_til_terminating(run_id)

        return PipesClientCompletedInvocation(pipes_session)

    def _poll_til_success(self, context: OpExecutionContext, run_id: str) -> None:
        # poll the Databricks run until it reaches RunResultState.SUCCESS, raising otherwise

        last_observed_state = None
        while True:
            run = self.client.jobs.get_run(run_id)
            if run.state.life_cycle_state != last_observed_state:
                context.log.info(
                    f"[pipes] Databricks run {run_id} observed state transition to {run.state.life_cycle_state}"
                )
            last_observed_state = run.state.life_cycle_state

            if run.state.life_cycle_state in (
                jobs.RunLifeCycleState.TERMINATED,
                jobs.RunLifeCycleState.SKIPPED,
            ):
                if run.state.result_state == jobs.RunResultState.SUCCESS:
                    break
                else:
                    raise DagsterPipesExecutionError(
                        f"Error running Databricks job: {run.state.state_message}"
                    )
            elif run.state.life_cycle_state == jobs.RunLifeCycleState.INTERNAL_ERROR:
                raise DagsterPipesExecutionError(
                    f"Error running Databricks job: {run.state.state_message}"
                )

            time.sleep(self.poll_interval_seconds)

    def _poll_til_terminating(self, run_id: str) -> None:
        # Wait to see the job enters a state that indicates the underlying task is no longer executing
        # TERMINATING: "The task of this run has completed, and the cluster and execution context are being cleaned up."
        while True:
            run = self.client.jobs.get_run(run_id)
            if run.state.life_cycle_state in (
                jobs.RunLifeCycleState.TERMINATING,
                jobs.RunLifeCycleState.TERMINATED,
                jobs.RunLifeCycleState.SKIPPED,
                jobs.RunLifeCycleState.INTERNAL_ERROR,
            ):
                return

            time.sleep(self.poll_interval_seconds)


PipesDatabricksClient = ResourceParam[_PipesDatabricksClient]

_CONTEXT_FILENAME = "context.json"


@contextmanager
def dbfs_tempdir(dbfs_client: files.DbfsAPI) -> Iterator[str]:
    dirname = "".join(random.choices(string.ascii_letters, k=30))
    tempdir = f"/tmp/{dirname}"
    dbfs_client.mkdirs(tempdir)
    try:
        yield tempdir
    finally:
        dbfs_client.delete(tempdir, recursive=True)


@experimental
class PipesDbfsContextInjector(PipesContextInjector):
    """A context injector that injects context into a Databricks job by writing a JSON file to DBFS.

    Args:
        client (WorkspaceClient): A databricks `WorkspaceClient` object.
    """

    def __init__(self, *, client: WorkspaceClient):
        super().__init__()
        self.dbfs_client = files.DbfsAPI(client.api_client)

    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:
        """Inject context to external environment by writing it to an automatically-generated
        DBFS temporary file as JSON and exposing the path to the file.

        Args:
            context_data (PipesContextData): The context data to inject.

        Yields:
            PipesParams: A dict of parameters that can be used by the external process to locate and
                load the injected context data.
        """
        with dbfs_tempdir(self.dbfs_client) as tempdir:
            path = os.path.join(tempdir, _CONTEXT_FILENAME)
            contents = base64.b64encode(json.dumps(context).encode("utf-8")).decode("utf-8")
            self.dbfs_client.put(path, contents=contents, overwrite=True)
            yield {"path": path}

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to inject context via a temporary file in dbfs. Expected"
            " PipesDbfsContextLoader to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )


@experimental
class PipesDbfsMessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from an
    automatically-generated temporary directory on DBFS.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        client (WorkspaceClient): A databricks `WorkspaceClient` object.
        cluster_log_root (Optional[str]): The root path on DBFS where the cluster logs are written.
            If set, this will be used to read stderr/stdout logs.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of readers for logs on DBFS.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        client: WorkspaceClient,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )
        self.dbfs_client = files.DbfsAPI(client.api_client)

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        with ExitStack() as stack:
            params: PipesParams = {}
            params["path"] = stack.enter_context(dbfs_tempdir(self.dbfs_client))
            yield params

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        message_path = os.path.join(params["path"], f"{index}.json")
        try:
            raw_message = self.dbfs_client.read(message_path)
            # Files written to dbfs using the Python IO interface used in PipesDbfsMessageWriter are
            # base64-encoded.
            return base64.b64decode(raw_message.data).decode("utf-8")
        # An error here is an expected result, since an IOError will be thrown if the next message
        # chunk doesn't yet exist. Swallowing the error here is equivalent to doing a no-op on a
        # status check showing a non-existent file.
        except IOError:
            return None

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to read messages from a temporary file in dbfs. Expected"
            " PipesDbfsMessageWriter to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )


@experimental
class PipesDbfsLogReader(PipesChunkedLogReader):
    """Reader that reads a log file from DBFS.

    Args:
        interval (float): interval in seconds between attempts to download a log chunk
        remote_log_name (Literal["stdout", "stderr"]): The name of the log file to read.
        target_stream (TextIO): The stream to which to forward log chunk that have been read.
        client (WorkspaceClient): A databricks `WorkspaceClient` object.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        remote_log_name: Literal["stdout", "stderr"],
        target_stream: TextIO,
        client: WorkspaceClient,
    ):
        super().__init__(interval=interval, target_stream=target_stream)
        self.dbfs_client = files.DbfsAPI(client.api_client)
        self.remote_log_name = remote_log_name
        self.log_position = 0
        self.log_modification_time = None
        self.log_path = None

    def download_log_chunk(self, params: PipesParams) -> Optional[str]:
        log_path = self._get_log_path(params)
        if log_path is None:
            return None
        else:
            try:
                status = self.dbfs_client.get_status(log_path)
                # No need to download again if it hasn't changed
                if status.modification_time == self.log_modification_time:
                    return None
                read_response = self.dbfs_client.read(log_path)
                assert read_response.data
                content = base64.b64decode(read_response.data).decode("utf-8")
                chunk = content[self.log_position :]
                self.log_position = len(content)
                return chunk
            except IOError:
                return None

    def target_is_readable(self, params: PipesParams) -> bool:
        return self._get_log_path(params) is not None

    @property
    def name(self) -> str:
        return f"PipesDbfsLogReader({self.remote_log_name})"

    # The directory containing logs will not exist until either 5 minutes have elapsed or the
    # job has finished.
    def _get_log_path(self, params: PipesParams) -> Optional[str]:
        if self.log_path is None:
            cluster_driver_log_root = params["extras"].get("cluster_driver_log_root")
            if cluster_driver_log_root is None:
                return None
            try:
                child_dirs = list(self.dbfs_client.list(cluster_driver_log_root))
            except IOError:
                child_dirs = []  # log root doesn't exist yet
            match = next(
                (
                    child_dir
                    for child_dir in child_dirs
                    if child_dir.path and child_dir.path.endswith(self.remote_log_name)
                ),
                None,
            )
            if match:
                self.log_path = f"dbfs:{match.path}"

        return self.log_path
