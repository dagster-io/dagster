from subprocess import Popen
from typing import Iterator, Mapping, Optional, Sequence, Union

from dagster_pipes import PipesExtras

from dagster import _check as check
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    ExtMessageReader,
    PipesClient,
    PipesContextInjector,
)
from dagster._core.pipes.context import ExtResult
from dagster._core.pipes.utils import (
    ExtTempFileContextInjector,
    ExtTempFileMessageReader,
    pipes_protocol,
)


class _PipesSubprocess(PipesClient):
    """A pipes client that runs a subprocess with the given command and environment.

    By default parameters are injected via environment variables. And then context is passed via
    a temp file, and structured messages are read from from a temp file.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
        cwd (Optional[str]): Working directory in which to launch the subprocess command.
        context_injector (Optional[PipesContextInjector]): An context injector to use to inject context into the subprocess. Defaults to ExtTempFileContextInjector.
        message_reader (Optional[PipesContextInjector]): An context injector to use to read messages from  the subprocess. Defaults to ExtTempFileMessageReader.
    """

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
    ):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.cwd = check.opt_str_param(cwd, "cwd")
        self.context_injector = (
            check.opt_inst_param(
                context_injector,
                "context_injector",
                PipesContextInjector,
            )
            or ExtTempFileContextInjector()
        )
        self.message_reader = (
            check.opt_inst_param(
                message_reader,
                "message_reader",
                ExtMessageReader,
            )
            or ExtTempFileMessageReader()
        )

    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> Iterator[ExtResult]:
        with pipes_protocol(
            context=context,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
            extras=extras,
        ) as pipes_session:
            process = Popen(
                command,
                cwd=cwd or self.cwd,
                env={
                    **pipes_session.get_piped_process_env_vars(),
                    **self.env,
                    **(env or {}),
                },
            )
            while process.poll() is None:
                yield from pipes_session.get_results()

            if process.returncode != 0:
                raise DagsterExternalExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )
        yield from pipes_session.get_results()


PipesSubprocess = ResourceParam[_PipesSubprocess]
