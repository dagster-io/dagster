from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
)


class ExternalExecutionContextLoader(ABC):
    @contextmanager
    def scoped_context(self) -> Iterator["ExternalExecutionContextData"]:
        yield self.load_context()

    @abstractmethod
    def load_context(self) -> ExternalExecutionContextData:
        raise NotImplementedError()


class ExternalExecutionMessageWriter(ABC):
    @abstractmethod
    def write_message(self, message: ExternalExecutionMessage) -> None:
        ...
