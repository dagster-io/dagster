from inspect import Parameter
from typing import Any, Optional, Sequence, Type, TypeVar

from typing_extensions import Annotated

from dagster._core.decorator_utils import get_function_params, get_type_hints
from dagster._core.definitions.resource_definition import ResourceDefinition


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

    extends_resource_definition = False
    try:
        extends_resource_definition = isinstance(annotation, type) and issubclass(
            annotation, (ResourceDefinition, ConfigurableResourceFactory)
        )
    except TypeError:
        # Using builtin Python types in python 3.9+ will raise a TypeError when using issubclass
        # even though the isinstance check will succeed (as will inspect.isclass), for example
        # list[dict[str, str]] will raise a TypeError
        pass

    return (extends_resource_definition) or (
        hasattr(annotation, "__metadata__")
        and getattr(annotation, "__metadata__") == (RESOURCE_PARAM_METADATA,)
    )


T = TypeVar("T")
ResourceParam = Annotated[T, RESOURCE_PARAM_METADATA]
