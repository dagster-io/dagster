from abc import ABC, abstractmethod

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
)


class ExternalExecutionContextSource(ABC):
    @abstractmethod
    def load_context(self) -> ExternalExecutionContextData:
        raise NotImplementedError()


class ExternalExecutionMessageSink(ABC):
    @abstractmethod
    def send_message(self, message: ExternalExecutionMessage) -> None:
        ...
