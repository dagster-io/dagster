from contextlib import contextmanager
from typing import Callable, Iterator, List, Optional

from dagster import (
    ResourceParam,
    _check as check,
)
from dagster._annotations import public
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import build_external_execution_context_data
from dagster._core.pipes.utils import PipesMessageHandler, open_pipes_session
from dagster_pipes import (
    PipesContext,
    PipesContextData,
    PipesContextLoader,
    PipesExtras,
    PipesMessage,
    PipesMessageWriter,
    PipesMessageWriterChannel,
    PipesParams,
    PipesParamsLoader,
    open_dagster_pipes_context,
)


class InProcessPipesContextLoader(PipesContextLoader):
    def __init__(self, pipes_context_data: PipesContextData):
        self.pipes_context_data = pipes_context_data

    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        yield self.pipes_context_data


class InProcessPipesMessageWriteChannel(PipesMessageWriterChannel):
    def __init__(self) -> None:
        self.messages: List[PipesMessage] = []

    def write_message(self, message: PipesMessage) -> None:
        self.messages.append(message)


class InProcessPipesMessageWriter(PipesMessageWriter):
    def __init__(self) -> None:
        self._write_channel = InProcessPipesMessageWriteChannel()
        check.inst(self._write_channel, InProcessPipesMessageWriteChannel)

    @property
    def write_channel(self) -> InProcessPipesMessageWriteChannel:
        return self._write_channel

    @contextmanager
    def open(self, params: PipesParams) -> Iterator[InProcessPipesMessageWriteChannel]:
        yield self._write_channel


class InProcessPipesParamLoader(PipesParamsLoader):
    def load_context_params(self) -> PipesParams:
        return {}

    def load_messages_params(self) -> PipesParams:
        return {}


class InProcessContextInjector(PipesContextInjector):
    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]:
        yield {}


class InProcessMessageReader(PipesMessageReader):
    def __init__(
        self,
        message_writer: InProcessPipesMessageWriter,
        fn: Callable[[PipesContext], None],
        pipes_context: PipesContext,
    ) -> None:
        self.message_writer = message_writer
        self.fn = fn
        self.pipes_context = pipes_context

    @contextmanager
    def read_messages(self, handler: "PipesMessageHandler") -> Iterator[PipesParams]:
        yield {}
        # instead of doing something like polling a thread, we just sychronously call the function and handle all messagse
        self.fn(self.pipes_context)
        for pipes_message in self.message_writer.write_channel.messages:
            handler.handle_message(pipes_message)


class _InProcessPipesClient(PipesClient):
    @public
    def run(
        self,
        *,
        context: OpExecutionContext,
        fn: Callable[[PipesContext], None],
        extras: Optional[PipesExtras] = None,
    ) -> PipesClientCompletedInvocation:
        pipes_context_data = build_external_execution_context_data(context=context, extras=extras)
        pipes_context_loader = InProcessPipesContextLoader(pipes_context_data)
        pipes_message_writer = InProcessPipesMessageWriter()
        with open_dagster_pipes_context(
            context_loader=pipes_context_loader,
            message_writer=pipes_message_writer,
            params_loader=InProcessPipesParamLoader(),
        ) as pipes_context:
            with open_pipes_session(
                context=context,
                context_injector=InProcessContextInjector(),
                message_reader=InProcessMessageReader(
                    pipes_message_writer, fn=fn, pipes_context=pipes_context
                ),
            ) as session:
                pass

        return PipesClientCompletedInvocation(list(session.get_results()))


InProcessPipesClient = ResourceParam[_InProcessPipesClient]
