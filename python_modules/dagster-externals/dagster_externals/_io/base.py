from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
    ExternalExecutionParams,
)


class ExternalExecutionContextLoader(ABC):
    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        yield

    @abstractmethod
    def load_context(self) -> ExternalExecutionContextData:
        ...


class ExternalExecutionMessageWriter(ABC):
    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        yield

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
