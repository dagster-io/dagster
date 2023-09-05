import os
import tempfile
from contextlib import ExitStack, contextmanager
from subprocess import Popen
from typing import Iterator, Mapping, Optional, Sequence, Union

from dagster_ext import ExtExtras
from pydantic import Field

from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.ext.context import (
    ExtOrchestrationContext,
)
from dagster._core.ext.resource import (
    ExtContextInjector,
    ExtMessageReader,
    ExtResource,
)
from dagster._core.ext.utils import (
    ExtFileContextInjector,
    ExtFileMessageReader,
    io_params_as_env_vars,
)

_CONTEXT_INJECTOR_FILENAME = "context"
_MESSAGE_READER_FILENAME = "messages"


class ExtSubprocess(ExtResource):
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
        extras: Optional[ExtExtras] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        external_context = ExtOrchestrationContext(context=context, extras=extras)
        with self._setup_io(external_context, context_injector, message_reader) as io_env:
            process = Popen(
                command,
                cwd=cwd or self.cwd,
                env={
                    **self.get_base_env(),
                    **{**(env or {}), **(self.env or {})},
                    **io_env,
                },
            )
            process.wait()

            if process.returncode != 0:
                raise DagsterExternalExecutionError(
                    f"External execution process failed with code {process.returncode}"
                )

    @contextmanager
    def _setup_io(
        self,
        external_context: ExtOrchestrationContext,
        context_injector: Optional[ExtContextInjector],
        message_reader: Optional[ExtMessageReader],
    ) -> Iterator[Mapping[str, str]]:
        with ExitStack() as stack:
            if context_injector is None or message_reader is None:
                tempdir = stack.enter_context(tempfile.TemporaryDirectory())
                context_injector = context_injector or ExtFileContextInjector(
                    os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME)
                )
                message_reader = message_reader or ExtFileMessageReader(
                    os.path.join(tempdir, _MESSAGE_READER_FILENAME)
                )
            context_injector_params = stack.enter_context(
                context_injector.inject_context(external_context)
            )
            message_reader_params = stack.enter_context(
                message_reader.read_messages(external_context)
            )
            yield io_params_as_env_vars(context_injector_params, message_reader_params)
