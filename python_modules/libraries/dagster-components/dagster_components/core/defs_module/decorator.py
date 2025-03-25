from typing import Callable, TypeVar

from typing_extensions import TypeAlias

from dagster_components.core.context import ComponentLoadContext
from dagster_components.core.defs_module.defs_builder import DefsBuilder
from dagster_components.core.defs_module.defs_loader import DefsLoader, WrappedDefsLoader

T_DefsBuilder = TypeVar("T_DefsBuilder", bound=DefsBuilder)
UserLoaderFn: TypeAlias = Callable[["ComponentLoadContext"], T_DefsBuilder]


def defs_loader(fn: Callable[[ComponentLoadContext], DefsBuilder]) -> DefsLoader:
    return WrappedDefsLoader(fn=fn)
