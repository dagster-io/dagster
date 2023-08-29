from abc import ABC, abstractmethod

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
)


class ExternalExecutionContextLoader(ABC):
    @abstractmethod
    def load_context(self) -> ExternalExecutionContextData:
        raise NotImplementedError()


class ExternalExecutionMessageWriter(ABC):
    @abstractmethod
    def write_message(self, message: ExternalExecutionMessage) -> None:
        ...
