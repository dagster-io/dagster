from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

from dagster_pipes import (
    PipesContextData,
    PipesExtras,
    PipesParams,
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
        extras: Optional[PipesExtras] = None,
    ) -> Iterator["ExtResult"]: ...


class PipedProcessContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]: ...


class ExtMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, handler: "ExtMessageHandler") -> Iterator[PipesParams]: ...
