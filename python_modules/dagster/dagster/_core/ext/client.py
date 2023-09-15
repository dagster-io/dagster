from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

from dagster_ext import (
    ExtContextData,
    ExtExtras,
    ExtParams,
)

from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from .context import ExtMessageHandler


class ExtClient(ABC):
    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExtExtras] = None,
    ) -> None:
        ...


class ExtContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(self, context_data: "ExtContextData") -> Iterator[ExtParams]:
        ...


class ExtMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, handler: "ExtMessageHandler") -> Iterator[ExtParams]:
        ...
