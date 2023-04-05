from inspect import Parameter
from typing import Sequence, TypeVar

from typing_extensions import Annotated, get_args

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.resource_definition import ResourceDefinition


def get_resource_args(fn, err_aggressively: bool = False) -> Sequence[Parameter]:
    from dagster import DagsterInvalidDefinitionError
    from dagster._config.structured_config import (
        ConfigurableResource,
        ConfigurableResourceFactory,
        TResValue,
    )
    from dagster._config.structured_config.utils import safe_is_subclass

    if err_aggressively:
        malformed_params = [
            param
            for param in get_function_params(fn)
            if safe_is_subclass(param.annotation, ResourceDefinition)
            and not safe_is_subclass(param.annotation, ConfigurableResource)
        ]
        if len(malformed_params) > 0:
            malformed_param = malformed_params[0]
            if safe_is_subclass(malformed_param.annotation, ConfigurableResourceFactory):
                orig_bases = getattr(malformed_param.annotation, "__orig_bases__", None)
                output_type = (
                    get_args(orig_bases[0])[0] if orig_bases and len(orig_bases) > 0 else None
                )
                if output_type == TResValue:
                    output_type = None
                raise DagsterInvalidDefinitionError(
                    """Resource param '{param_name}' is annotated as '{annotation_type}', but '{annotation_type}' outputs {value_message} value to user code such as @ops and @assets. This annotation should instead be 'Resource[{output_type}]'""".format(
                        param_name=malformed_param.name,
                        annotation_type=malformed_param.annotation,
                        value_message=f"a '{output_type}'" if output_type else "an unknown",
                        output_type=output_type.__name__ if output_type else "Any",
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    """Resource param '{param_name}' is annotated as '{annotation_type}', but '{param_name}' produces a `Foo` value. This annotation should instead be `Resource[Foo]`"""
                )

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
Resource = Annotated[T, "resource_output"]
