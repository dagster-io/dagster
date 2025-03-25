from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from dagster_shared.record import record

from dagster_components.core.defs_module.defs_builder import DefsBuilder

if TYPE_CHECKING:
    from dagster_components.core.context import ComponentLoadContext


class DefsLoader(ABC):
    def __call__(self, context: "ComponentLoadContext") -> DefsBuilder:
        return self.load(context)

    @abstractmethod
    def load(self, context: "ComponentLoadContext") -> DefsBuilder: ...


@record
class WrappedDefsLoader(DefsLoader):
    fn: Callable[["ComponentLoadContext"], DefsBuilder]

    def load(self, context: "ComponentLoadContext") -> DefsBuilder:
        return self.fn(context)
