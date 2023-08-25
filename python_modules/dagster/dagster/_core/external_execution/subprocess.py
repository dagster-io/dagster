import os
import tempfile
from contextlib import contextmanager
from subprocess import Popen
from typing import Iterator, Mapping, Optional, Sequence, Union

from dagster_externals import (
    ExternalExecutionExtras,
)
from pydantic import Field

from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.external_execution.resource import ExternalExecutionResource
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
)
from dagster._core.external_execution.utils import (
    file_context_source,
    file_message_sink,
)

_CONTEXT_SOURCE_FILENAME = "context"
_MESSAGE_SINK_FILENAME = "messages"


class SubprocessExecutionTask(ExternalExecutionTask):
    def run(
        self,
        command: Sequence[str],
        cwd: Optional[str] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        with self._setup_io() as io_env:
            process = Popen(
                command,
                cwd=cwd,
                env={
                    **self.get_base_env(),
                    **(env or {}),
                    **io_env,
                },
            )
            process.wait()

            if process.returncode != 0:
                raise DagsterExternalExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )

    # ########################
    # ##### IO
    # ########################

    @contextmanager
    def _setup_io(self) -> Iterator[Mapping[str, str]]:
        with tempfile.TemporaryDirectory() as tempdir, file_context_source(
            self, os.path.join(tempdir, _CONTEXT_SOURCE_FILENAME)
        ) as context_env, file_message_sink(
            self, os.path.join(tempdir, _MESSAGE_SINK_FILENAME)
        ) as message_env:
            yield {**context_env, **message_env}


class SubprocessExecutionResource(ExternalExecutionResource):
    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to launch the subprocess command."
    )
    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )

    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        SubprocessExecutionTask(
            context=context,
            extras=extras,
        ).run(
            command=command,
            env={**(env or {}), **(self.env or {})},
            cwd=(cwd or self.cwd),
        )
