from abc import ABC, abstractmethod

from dagster._core.definitions.definitions_class import Definitions


class DefsFactory(ABC):
    @abstractmethod
    def build_defs(self) -> Definitions: ...
