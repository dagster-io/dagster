import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from subprocess import Popen
from threading import Event
from typing import ContextManager, Iterator, Mapping, Optional, Sequence, Union

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionExtras,
)
from pydantic import Field

from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.external_execution.resource import ExternalExecutionResource
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
    ExternalTaskIOParams,
    ExternalTaskParams,
)


@dataclass
class SubprocessTaskParams(ExternalTaskParams):
    command: Sequence[str]
    cwd: Optional[str] = None
    socket_server_host: Optional[str] = None
    socket_server_port: Optional[int] = None
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass
class SubprocessTaskIOParams(ExternalTaskIOParams):
    stdio_fd: Optional[int] = None


class SubprocessExecutionTask(ExternalExecutionTask[SubprocessTaskParams, SubprocessTaskIOParams]):
    def _launch(
        self,
        base_env: Mapping[str, str],
        params: SubprocessTaskParams,
        input_params: SubprocessTaskIOParams,
        output_params: SubprocessTaskIOParams,
    ) -> None:
        process = Popen(
            params.command,
            cwd=params.cwd,
            stdin=input_params.stdio_fd,
            stdout=output_params.stdio_fd,
            env={
                **base_env,
                **params.env,
                **input_params.env,
                **output_params.env,
            },
        )
        process.wait()

        if process.returncode != 0:
            raise DagsterExternalExecutionError(
                f"External execution process failed with code {process.returncode}"
            )

    # ########################
    # ##### IO CONTEXT MANAGERS
    # ########################

    def _input_context_manager(
        self, tempdir: str, params: SubprocessTaskParams
    ) -> ContextManager[SubprocessTaskIOParams]:
        return self._file_input(tempdir)

    @contextmanager
    def _file_input(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._input_path, "input", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["input"]: path}
        try:
            self._write_input(path)
            yield SubprocessTaskIOParams(env=env)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def _output_context_manager(
        self, tempdir: str, params: SubprocessTaskParams
    ) -> ContextManager[SubprocessTaskIOParams]:
        return self._file_output(tempdir)

    @contextmanager
    def _file_output(self, tempdir: str) -> Iterator[SubprocessTaskIOParams]:
        path = self._prepare_io_path(self._output_path, "output", tempdir)
        env = {DAGSTER_EXTERNAL_ENV_KEYS["output"]: path}
        is_task_complete = Event()
        thread = None
        try:
            open(path, "w").close()  # create file
            thread = self._start_output_thread(path, is_task_complete)
            yield SubprocessTaskIOParams(env)
        finally:
            is_task_complete.set()
            if thread:
                thread.join()
            if os.path.exists(path):
                os.remove(path)


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
        params = SubprocessTaskParams(
            command=command,
            env={**(env or {}), **(self.env or {})},
            cwd=(cwd or self.cwd),
        )
        SubprocessExecutionTask(
            context=context,
            extras=extras,
            input_path=self.input_path,
            output_path=self.output_path,
        ).run(params)
