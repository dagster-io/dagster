from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generic, TypeVar

TTypeMetadata = TypeVar("TTypeMetadata")


class BaseCompiler(Generic[TTypeMetadata], ABC):
    @abstractmethod
    def visit(self, message: TTypeMetadata) -> AsyncGenerator[str, None]:
        pass
