from inspect import Parameter
from typing import Any, Optional, Sequence, Type, TypeVar

from typing_extensions import Annotated

from dagster._core.decorator_utils import get_function_params, get_type_hints
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._seven import is_subclass


def get_resource_args(fn) -> Sequence[Parameter]:
    type_annotations = get_type_hints(fn)
    return [
        param
        for param in get_function_params(fn)
        if _is_resource_annotation(type_annotations.get(param.name))
    ]


RESOURCE_PARAM_METADATA = "resource_param"


def _is_resource_annotation(annotation: Optional[Type[Any]]) -> bool:
    from dagster._config.pythonic_config import ConfigurableResourceFactory

    if isinstance(annotation, type) and (
        is_subclass(annotation, ResourceDefinition)
        or is_subclass(annotation, ConfigurableResourceFactory)
    ):
        return True

    return hasattr(annotation, "__metadata__") and getattr(annotation, "__metadata__") == (
        RESOURCE_PARAM_METADATA,
    )


T = TypeVar("T")
ResourceParam = Annotated[T, RESOURCE_PARAM_METADATA]
