import base64
import json
import os
import random
import string
import sys
import time
from contextlib import ExitStack, contextmanager
from typing import Iterator, Literal, Mapping, Optional, TextIO

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterPipesExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesBlobStoreStdioReader,
    PipesChunkedStdioReader,
    open_pipes_session,
)
from dagster_pipes import (
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PipesContextData,
    PipesExtras,
    PipesParams,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files, jobs
from pydantic import Field

# Number of seconds between status checks on Databricks jobs launched by the
# `PipesDatabricksClient`.
_RUN_POLL_INTERVAL = 5


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
        ) or PipesDbfsMessageReader(
            client=self.client,
            stdout_reader=PipesDbfsStdioReader(
                client=self.client, remote_log_name="stdout", target_stream=sys.stdout
            ),
            stderr_reader=PipesDbfsStdioReader(
                client=self.client, remote_log_name="stderr", target_stream=sys.stderr
            ),
        )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

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
        with open_pipes_session(
            context=context,
            extras=extras,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
        ) as pipes_session:
            submit_task_dict = task.as_dict()
            submit_task_dict["new_cluster"]["spark_env_vars"] = {
                **submit_task_dict["new_cluster"].get("spark_env_vars", {}),
                **(self.env or {}),
                **pipes_session.get_bootstrap_env_vars(),
            }
            cluster_log_root = pipes_session.get_bootstrap_params()[
                DAGSTER_PIPES_MESSAGES_ENV_VAR
            ].get("cluster_log_root")
            if cluster_log_root is not None:
                submit_task_dict["new_cluster"]["cluster_log_conf"] = {
                    "dbfs": {"destination": f"dbfs:{cluster_log_root}"}
                }
            task = jobs.SubmitTask.from_dict(submit_task_dict)
            run_id = self.client.jobs.submit(
                tasks=[task],
                **(submit_args or {}),
            ).bind()["run_id"]

            while True:
                run = self.client.jobs.get_run(run_id)
                context.log.info(
                    f"Databricks run {run_id} current state: {run.state.life_cycle_state}"
                )
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
                time.sleep(_RUN_POLL_INTERVAL)
        return PipesClientCompletedInvocation(tuple(pipes_session.get_results()))


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

    If `stdout_reader` or `stderr_reader` are passed, this reader will also start them when
    `read_messages` is called. If they are not passed, then the reader performs no stdout/stderr
    forwarding.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        client (WorkspaceClient): A databricks `WorkspaceClient` object.
        cluster_log_root (Optional[str]): The root path on DBFS where the cluster logs are written.
            If set, this will be used to read stderr/stdout logs.
        stdout_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stdout logs.
        stderr_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stderr logs.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        client: WorkspaceClient,
        stdout_reader: Optional[PipesBlobStoreStdioReader] = None,
        stderr_reader: Optional[PipesBlobStoreStdioReader] = None,
    ):
        super().__init__(
            interval=interval, stdout_reader=stdout_reader, stderr_reader=stderr_reader
        )
        self.dbfs_client = files.DbfsAPI(client.api_client)

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        with ExitStack() as stack:
            params: PipesParams = {}
            params["path"] = stack.enter_context(dbfs_tempdir(self.dbfs_client))
            if self.stdout_reader or self.stderr_reader:
                params["cluster_log_root"] = stack.enter_context(dbfs_tempdir(self.dbfs_client))
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
class PipesDbfsStdioReader(PipesChunkedStdioReader):
    """Reader that reads stdout/stderr logs from DBFS.

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
        self.log_path = None

    def download_log_chunk(self, params: PipesParams) -> Optional[str]:
        log_path = self._get_log_path(params)
        if log_path is None:
            return None
        else:
            try:
                read_response = self.dbfs_client.read(log_path)
                assert read_response.data
                content = base64.b64decode(read_response.data).decode("utf-8")
                chunk = content[self.log_position :]
                self.log_position = len(content)
                return chunk
            except IOError:
                return None

    def is_ready(self, params: PipesParams) -> bool:
        return self._get_log_path(params) is not None

    # The directory containing logs will not exist until either 5 minutes have elapsed or the
    # job has finished.
    def _get_log_path(self, params: PipesParams) -> Optional[str]:
        if self.log_path is None:
            log_root_path = os.path.join(params["cluster_log_root"])
            child_dirs = list(self.dbfs_client.list(log_root_path))
            if len(child_dirs) > 0:
                self.log_path = f"dbfs:{child_dirs[0].path}/driver/{self.remote_log_name}"
        return self.log_path
