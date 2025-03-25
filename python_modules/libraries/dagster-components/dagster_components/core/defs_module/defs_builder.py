from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from dagster._core.definitions.definitions_class import Definitions
from dagster_shared.record import record

if TYPE_CHECKING:
    from dagster_components.core.context import ComponentLoadContext


class DefsBuilder(ABC):
    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    def post_process(self, fn: Callable[[Definitions], Definitions]) -> "PostProcessDefsBuilder":
        return PostProcessDefsBuilder(inner=self, fn=fn)


@record
class PostProcessDefsBuilder(DefsBuilder):
    inner: DefsBuilder
    fn: Callable[[Definitions], Definitions]

    def build_defs(self, context: "ComponentLoadContext") -> Definitions:
        return self.fn(self.inner.build_defs(context))
