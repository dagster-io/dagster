import os
import tempfile
from contextlib import contextmanager
from subprocess import Popen
from typing import Iterator, Mapping, Optional, Sequence, Union

from dagster_ext import ExtExtras
from pydantic import Field, PrivateAttr

import dagster._check as check
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.init import InitResourceContext
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
    def __init__(
        self,
        cwd: Optional[str] = None,
        env: Optional[Mapping[str, str]] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
    ) -> None:
        self._context_injector = check.opt_inst_param(context_injector, "context_injector", ExtContextInjector)
        self._message_reader = check.opt_inst_param(message_reader, "message_reader", ExtMessageReader)
        super().__init__(**dict(cwd=cwd,env=env))

    _context_injector = PrivateAttr(default=None)
    _message_reader = PrivateAttr(default=None)

    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to launch the subprocess command."
    )
    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )

    @contextmanager
    def yield_for_execution(self, context: InitResourceContext):
        if self._context_injector and self._message_reader:
            return

        with tempfile.TemporaryDirectory() as tempdir:
            self._context_injector = (
                ExtFileContextInjector(os.path.join(tempdir, _CONTEXT_INJECTOR_FILENAME))
                if not self._context_injector
                else self._context_injector
            )
            self._message_reader = (
                ExtFileMessageReader(os.path.join(tempdir, _MESSAGE_READER_FILENAME))
                if not self._message_reader
                else self._message_reader
            )
            yield self

    def run(
        self,
        command: Union[str, Sequence[str]],
        *,
        context: OpExecutionContext,
        extras: Optional[ExtExtras] = None,
        env: Optional[Mapping[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        external_context = ExtOrchestrationContext(context=context, extras=extras)
        with self._setup_io(external_context) as io_env:
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
    ) -> Iterator[Mapping[str, str]]:
        assert self._context_injector
        assert self._message_reader

        with self._context_injector.inject_context(
            external_context
        ) as context_injector_params, self._message_reader.read_messages(
            external_context
        ) as message_reader_params:
            yield io_params_as_env_vars(context_injector_params, message_reader_params)
