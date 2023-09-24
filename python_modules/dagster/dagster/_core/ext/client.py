from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

from dagster_ext import (
    PipedProcessContextData,
    PipedProcessExtras,
    PipedProcessParams,
)

from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from .context import PipesMessageHandler, PipesResult


class PipedProcessClient(ABC):
    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[PipedProcessExtras] = None,
    ) -> Iterator["PipesResult"]: ...


class PipedContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(
        self, context_data: "PipedProcessContextData"
    ) -> Iterator[PipedProcessParams]: ...


class PipedMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, handler: "PipesMessageHandler") -> Iterator[PipedProcessParams]: ...
