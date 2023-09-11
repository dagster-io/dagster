from subprocess import Popen
from typing import Mapping, Optional, Sequence, Union

from dagster_ext import ExtExtras

from dagster import _check as check
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.ext.client import (
    ExtClient,
    ExtContextInjector,
    ExtMessageReader,
)
from dagster._core.ext.utils import (
    ExtTempFileContextInjector,
    ExtTempFileMessageReader,
    ext_protocol,
)


class _ExtSubprocess(ExtClient):
    """An ext client that runs a subprocess with the given command and environment.

    By default parameters are injected via environment variables. And then context is passed via
    a temp file, and structured messages are read from from a temp file.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
        cwd (Optional[str]): Working directory in which to launch the subprocess command.
    """

    def __init__(self, env: Optional[Mapping[str, str]] = None, cwd: Optional[str] = None):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.cwd = check.opt_str_param(cwd, "cwd")

    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[ExtExtras] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        with ext_protocol(
            context=context,
            context_injector=context_injector or ExtTempFileContextInjector(),
            message_reader=message_reader or ExtTempFileMessageReader(),
            extras=extras,
        ) as ext_context:
            process = Popen(
                command,
                cwd=cwd or self.cwd,
                env={
                    **ext_context.get_external_process_env_vars(),
                    **(self.env or {}),  # type: ignore  # (pyright bug)
                    **(env or {}),  # type: ignore  # (pyright bug)
                },
            )
            process.wait()

            if process.returncode != 0:
                raise DagsterExternalExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )


ExtSubprocess = ResourceParam[_ExtSubprocess]
