from subprocess import Popen
from typing import Mapping, Optional, Sequence, Union

from dagster_pipes import PipesExtras

from dagster import _check as check
from dagster._annotations import experimental, public
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
    PipesTempFileContextInjector,
    PipesTempFileMessageReader,
    open_pipes_session,
)


@experimental
class _PipesSubprocess(PipesClient):
    """A pipes client that runs a subprocess with the given command and environment.

    By default parameters are injected via environment variables. Context is passed via
    a temp file, and structured messages are read from from a temp file.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the
            subprocess.
        cwd (Optional[str]): Working directory in which to launch the subprocess command.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the subprocess. Defaults to :py:class:`PipesTempFileContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages from
            the subprocess. Defaults to :py:class:`PipesTempFileMessageReader`.
    """

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
    ):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.cwd = check.opt_str_param(cwd, "cwd")
        self.context_injector = (
            check.opt_inst_param(
                context_injector,
                "context_injector",
                PipesContextInjector,
            )
            or PipesTempFileContextInjector()
        )
        self.message_reader = (
            check.opt_inst_param(
                message_reader,
                "message_reader",
                PipesMessageReader,
            )
            or PipesTempFileMessageReader()
        )

    @public
    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> PipesClientCompletedInvocation:
        """Synchronously execute a subprocess with in a pipes session.

        Args:
            command (Union[str, Sequence[str]]): The command to run. Will be passed to `subprocess.Popen()`.
            context (OpExecutionContext): The context from the executing op or asset.
            extras (Optional[PipesExtras]): An optional dict of extra parameters to pass to the subprocess.
            env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
            cwd (Optional[str]): Working directory in which to launch the subprocess command.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
            extras=extras,
        ) as pipes_session:
            process = Popen(
                command,
                cwd=cwd or self.cwd,
                env={
                    **pipes_session.get_bootstrap_env_vars(),
                    **self.env,
                    **(env or {}),
                },
            )
            process.wait()
            if process.returncode != 0:
                raise DagsterPipesExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )
        return PipesClientCompletedInvocation(tuple(pipes_session.get_results()))


PipesSubprocessClient = ResourceParam[_PipesSubprocess]
