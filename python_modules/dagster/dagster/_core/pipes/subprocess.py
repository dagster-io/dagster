import os
import signal
from collections.abc import Mapping, Sequence
from subprocess import PIPE, Popen
from typing import Optional, Union

from dagster_pipes import PipesExtras

from dagster import _check as check
from dagster._annotations import public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterPipesExecutionError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
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


@public
class PipesSubprocessClient(PipesClient, TreatAsResourceParam):
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
        forward_termination (bool): Whether to send a SIGINT signal to the subprocess
            if the orchestration process is interrupted or canceled. Defaults to True.
        forward_stdio (bool): Whether to forward stdout and stderr from the subprocess to the
            orchestration process. Defaults to True.
        termination_timeout_seconds (float): How long to wait after forwarding termination
            for the subprocess to exit. Defaults to 20.
    """

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
        forward_stdio: bool = True,
        termination_timeout_seconds: float = 20,
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
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.forward_stdio = check.bool_param(forward_stdio, "forward_stdio")
        self.termination_timeout_seconds = check.numeric_param(
            termination_timeout_seconds, "termination_timeout_seconds"
        )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        extras: Optional[PipesExtras] = None,
        command: Union[str, Sequence[str]],
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> PipesClientCompletedInvocation:
        """Synchronously execute a subprocess with in a pipes session.

        Args:
            command (Union[str, Sequence[str]]): The command to run. Will be passed to `subprocess.Popen()`.
            context (Union[OpExecutionContext, AssetExecutionContext]): The context from the executing op or asset.
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
                    **os.environ,
                    **self.env,
                    **(env or {}),
                    **pipes_session.get_bootstrap_env_vars(),
                },
                stdout=None if self.forward_stdio else PIPE,
                stderr=None if self.forward_stdio else PIPE,
            )
            try:
                process.wait()
                if process.returncode != 0:
                    raise DagsterPipesExecutionError(
                        f"External execution process failed with code {process.returncode}"
                    )
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.info("[pipes] execution interrupted, sending SIGINT to subprocess.")
                    # send sigint to give external process chance to exit gracefully
                    process.send_signal(signal.SIGINT)
                    process.wait(timeout=self.termination_timeout_seconds)
                raise

        return PipesClientCompletedInvocation(pipes_session)
