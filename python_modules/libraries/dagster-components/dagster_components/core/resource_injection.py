from collections.abc import Mapping
from typing import Any, Callable

from dagster_components.core.component import ComponentLoadContext

INJECTED_RESOURCES_FN_ATTR = "__dagster_resource_injector"


def is_resource_injector(obj: Any) -> bool:
    return getattr(obj, INJECTED_RESOURCES_FN_ATTR, False) is True


def resource_injector(
    fn: Callable[[ComponentLoadContext], Mapping[str, object]],
) -> Callable[[ComponentLoadContext], Mapping[str, object]]:
    setattr(fn, INJECTED_RESOURCES_FN_ATTR, True)
    return fn
