from abc import ABC, abstractmethod

from dagster._core.definitions.definitions_class import Definitions


class DefsFactory(ABC):
    @abstractmethod
    def build_defs(self) -> Definitions: ...


def defs_from_factories(*factories: DefsFactory) -> Definitions:
    return Definitions.merge(*[factory.build_defs() for factory in factories])
