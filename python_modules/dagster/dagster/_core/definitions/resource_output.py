from inspect import Parameter
from typing import Sequence, TypeVar

from typing_extensions import Annotated

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.resource_definition import ResourceDefinition


def get_resource_args(fn) -> Sequence[Parameter]:
    return [param for param in get_function_params(fn) if _is_resource_annotated(param)]


def _is_resource_annotated(param: Parameter) -> bool:
    extends_resource_definition = False
    try:
        extends_resource_definition = isinstance(param.annotation, type) and issubclass(
            param.annotation, ResourceDefinition
        )
    except TypeError:
        # Using builtin Python types in python 3.9+ will raise a TypeError when using issubclass
        # even though the isinstance check will succeed (as will inspect.isclass), for example
        # list[dict[str, str]] will raise a TypeError
        pass

    return (extends_resource_definition) or (
        hasattr(param.annotation, "__metadata__")
        and getattr(param.annotation, "__metadata__") == ("resource_output",)
    )


T = TypeVar("T")
ResourceOutput = Annotated[T, "resource_output"]
