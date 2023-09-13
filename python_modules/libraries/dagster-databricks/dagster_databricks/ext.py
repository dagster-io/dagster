import base64
import json
import os
import random
import string
import time
from contextlib import contextmanager
from typing import Iterator, Mapping, Optional

from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.ext.client import ExtClient, ExtContextInjector, ExtMessageReader
from dagster._core.ext.utils import (
    ExtBlobStoreMessageReader,
    ext_protocol,
)
from dagster_ext import (
    ExtContextData,
    ExtExtras,
    ExtParams,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files, jobs
from pydantic import Field


class _ExtDatabricks(ExtClient):
    """Ext client for databricks.

    Args:
        client (WorkspaceClient): A databricks workspace client.
        env (Optional[Mapping[str,str]]: An optional dict of environment variables to pass to the databricks job.
    """

    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )

    def __init__(self, client: WorkspaceClient, env: Optional[Mapping[str, str]] = None):
        self.client = client
        self.env = env

    def run(
        self,
        task: jobs.SubmitTask,
        *,
        context: OpExecutionContext,
        extras: Optional[ExtExtras] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
        submit_args: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Run a Databricks job with the EXT protocol.

        Args:
            task (databricks.sdk.service.jobs.SubmitTask): Specification of the databricks
                task to run. Environment variables used by dagster-ext will be set under the
                `spark_env_vars` key of the `new_cluster` field (if there is an existing dictionary
                here, the EXT environment variables will be merged in). Everything else will be
                passed unaltered under the `tasks` arg to `WorkspaceClient.jobs.submit`.
            submit_args (Optional[Mapping[str, str]]): Additional keyword arguments that will be
                forwarded as-is to `WorkspaceClient.jobs.submit`.
        """
        with ext_protocol(
            context=context,
            extras=extras,
            context_injector=context_injector or ExtDbfsContextInjector(client=self.client),
            message_reader=message_reader or ExtDbfsMessageReader(client=self.client),
        ) as ext_context:
            submit_task_dict = task.as_dict()
            submit_task_dict["new_cluster"]["spark_env_vars"] = {
                **submit_task_dict["new_cluster"].get("spark_env_vars", {}),
                **(self.env or {}),
                **ext_context.get_external_process_env_vars(),
            }
            task = jobs.SubmitTask.from_dict(submit_task_dict)
            run_id = self.client.jobs.submit(
                tasks=[task],
                **(submit_args or {}),
            ).bind()["run_id"]

            while True:
                run = self.client.jobs.get_run(run_id)
                if run.state.life_cycle_state in (
                    jobs.RunLifeCycleState.TERMINATED,
                    jobs.RunLifeCycleState.SKIPPED,
                ):
                    if run.state.result_state == jobs.RunResultState.SUCCESS:
                        return
                    else:
                        raise DagsterExternalExecutionError(
                            f"Error running Databricks job: {run.state.state_message}"
                        )
                elif run.state.life_cycle_state == jobs.RunLifeCycleState.INTERNAL_ERROR:
                    raise DagsterExternalExecutionError(
                        f"Error running Databricks job: {run.state.state_message}"
                    )
                time.sleep(5)


ExtDatabricks = ResourceParam[_ExtDatabricks]

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


class ExtDbfsContextInjector(ExtContextInjector):
    def __init__(self, *, client: WorkspaceClient):
        super().__init__()
        self.dbfs_client = files.DbfsAPI(client.api_client)

    @contextmanager
    def inject_context(self, context: "ExtContextData") -> Iterator[ExtParams]:
        with dbfs_tempdir(self.dbfs_client) as tempdir:
            path = os.path.join(tempdir, _CONTEXT_FILENAME)
            contents = base64.b64encode(json.dumps(context).encode("utf-8")).decode("utf-8")
            self.dbfs_client.put(path, contents=contents, overwrite=True)
            yield {"path": path}


class ExtDbfsMessageReader(ExtBlobStoreMessageReader):
    tempdir: Optional[str] = None

    def __init__(self, *, interval: int = 10, client: WorkspaceClient):
        super().__init__(interval=interval)
        self.dbfs_client = files.DbfsAPI(client.api_client)

    @contextmanager
    def setup(self) -> Iterator[None]:
        with dbfs_tempdir(self.dbfs_client) as tempdir:
            self.tempdir = tempdir
            yield

    def get_params(self) -> ExtParams:
        return {"path": self.tempdir}

    def download_messages_chunk(self, index: int) -> Optional[str]:
        assert self.tempdir
        message_path = os.path.join(self.tempdir, f"{index}.json")
        try:
            raw_message = self.dbfs_client.read(message_path)
            return raw_message.data
        except IOError:
            return None
