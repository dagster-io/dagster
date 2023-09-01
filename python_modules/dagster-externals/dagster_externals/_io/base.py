from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generic, Iterator, TypeVar

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
    ExternalExecutionParams,
)


class ExternalExecutionContextLoader(ABC):
    @abstractmethod
    @contextmanager
    def load_context(
        self, params: ExternalExecutionParams
    ) -> Iterator[ExternalExecutionContextData]:
        ...


T_MessageChannel = TypeVar("T_MessageChannel", bound="ExternalExecutionMessageWriterChannel")


class ExternalExecutionMessageWriter(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    @contextmanager
    def open(self, params: ExternalExecutionParams) -> Iterator[T_MessageChannel]:
        ...


class ExternalExecutionMessageWriterChannel(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    def write_message(self, message: ExternalExecutionMessage) -> None:
        ...


class ExternalExecutionParamLoader(ABC):
    @abstractmethod
    def load_context_params(self) -> ExternalExecutionParams:
        ...

    @abstractmethod
    def load_messages_params(self) -> ExternalExecutionParams:
        ...
