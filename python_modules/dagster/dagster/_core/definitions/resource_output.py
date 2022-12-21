from inspect import Parameter
from typing import Sequence, TypeVar

from typing_extensions import Annotated

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.resource_definition import ResourceDefinition


def get_resource_args(fn) -> Sequence[Parameter]:

    return [param for param in get_function_params(fn) if _is_resource_annotated(param)]


def _is_resource_annotated(param: Parameter) -> bool:
    return (
        isinstance(param.annotation, type) and issubclass(param.annotation, ResourceDefinition)
    ) or (
        hasattr(param.annotation, "__metadata__")
        and getattr(param.annotation, "__metadata__") == ("resource_output",)
    )


T = TypeVar("T")
ResourceOutput = Annotated[T, "resource_output"]
