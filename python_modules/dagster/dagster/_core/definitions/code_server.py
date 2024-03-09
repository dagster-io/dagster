from abc import ABC, abstractmethod
from typing import Mapping

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)


class ICodeLocation(ABC):
    # User can override this method to perform any necessary setup when the code server starts
    def on_start(self) -> None: ...

    @abstractmethod
    def load_definitions_dict(self) -> Mapping[str, Definitions]: ...


class CodeLocation(ICodeLocation, ABC):
    def on_start(self) -> None: ...

    def load_definitions_dict(self) -> Mapping[str, Definitions]:
        return {SINGLETON_REPOSITORY_NAME: self.load_definitions()}

    @abstractmethod
    def load_definitions(self) -> Definitions: ...


class MultiDefinitionsCodeLocation(ICodeLocation):
    @abstractmethod
    def load_definitions_dict(self) -> Mapping[str, Definitions]: ...
