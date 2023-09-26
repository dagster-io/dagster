from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

from dagster_pipes import (
    PipeableExtras,
    PipeableParams,
    PipedProcessContextData,
)

from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from .context import ExtMessageHandler, ExtResult


class PipedProcessClient(ABC):
    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[PipeableExtras] = None,
    ) -> Iterator["ExtResult"]: ...


class PipedProcessContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(
        self, context_data: "PipedProcessContextData"
    ) -> Iterator[PipeableParams]: ...


class ExtMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, handler: "ExtMessageHandler") -> Iterator[PipeableParams]: ...
