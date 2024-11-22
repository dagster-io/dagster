from contextlib import contextmanager
from typing import Callable, Iterator, List, Optional, Union

from dagster._annotations import public
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
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
)


class InProcessPipesContextLoader(PipesContextLoader):
    def __init__(self, pipes_context_data: PipesContextData):
        self.pipes_context_data = pipes_context_data

    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        yield self.pipes_context_data


class InProcessPipesMessageWriteChannel(PipesMessageWriterChannel):
    def __init__(self) -> None:
        self.messages: list[PipesMessage] = []

    def write_message(self, message: PipesMessage) -> None:
        self.messages.append(message)


class InProcessPipesMessageWriter(PipesMessageWriter):
    def __init__(self) -> None:
        self.write_channel = InProcessPipesMessageWriteChannel()

    @contextmanager
    def open(self, params: PipesParams) -> Iterator[InProcessPipesMessageWriteChannel]:
        yield self.write_channel


class InProcessPipesParamLoader(PipesParamsLoader):
    def load_context_params(self) -> PipesParams:
        return {}

    def load_messages_params(self) -> PipesParams:
        return {}

    def is_dagster_pipes_process(self) -> bool:
        return True


class InProcessContextInjector(PipesContextInjector):
    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]:
        yield {}

    def no_messages_debug_text(self) -> str:
        return "In-process context injection."


class InProcessMessageReader(PipesMessageReader):
    def __init__(
        self,
        message_writer: InProcessPipesMessageWriter,
        pipes_context: PipesContext,
    ) -> None:
        self.message_writer = message_writer
        self.pipes_context = pipes_context

    @contextmanager
    def read_messages(self, handler: "PipesMessageHandler") -> Iterator[PipesParams]:
        yield {}
        for pipes_message in self.message_writer.write_channel.messages:
            handler.handle_message(pipes_message)

    def no_messages_debug_text(self) -> str:
        return "In-process message reader."


class InProcessPipesClient(PipesClient, TreatAsResourceParam):
    """An in-process pipes clients unusable in test cases. A function inside the orchestration
    process actually serves as the "external" execution. This allows us to test the inner machinery
    of pipes without actually launching subprocesses, which makes the tests much more lightweight
    and repeatable.
    """

    @public
    def run(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        fn: Callable[[PipesContext], None],
        extras: Optional[PipesExtras] = None,
        metadata: Optional[RawMetadataMapping] = None,  # metadata to attach to all materializations
    ) -> PipesClientCompletedInvocation:
        pipes_context_data = build_external_execution_context_data(context=context, extras=extras)
        pipes_context_loader = InProcessPipesContextLoader(pipes_context_data)
        pipes_message_writer = InProcessPipesMessageWriter()
        with (
            PipesContext(  # construct PipesContext directly to avoid env var check in open_dagster_pipes
                context_loader=pipes_context_loader,
                message_writer=pipes_message_writer,
                params_loader=InProcessPipesParamLoader(),
            ) as pipes_context
        ):
            with open_pipes_session(
                context=context,
                context_injector=InProcessContextInjector(),
                message_reader=InProcessMessageReader(
                    pipes_message_writer,
                    pipes_context=pipes_context,
                ),
            ) as session:
                fn(pipes_context)

        return PipesClientCompletedInvocation(session, metadata=metadata)
