from abc import ABC, abstractmethod

from dagster._core.definitions.definitions_class import Definitions

from dagster_components.core.context import DefinitionsLoadContext


class DefsLoader(ABC):
    """Base class for a class capable of loading definitions."""

    @abstractmethod
    def build_defs(self, context: DefinitionsLoadContext) -> Definitions: ...
