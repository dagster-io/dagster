from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Iterator, Optional

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._config import ConfigType
from dagster._core.decorator_utils import get_function_params, validate_expected_params
from dagster._core.definitions.resource_requirement import (
    ResourceRequirement,
    TypeLoaderResourceRequirement,
)
from dagster._core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster._core.execution.context.system import DagsterTypeLoaderContext


@public
class DagsterTypeLoader(ABC):
    """Dagster type loaders are used to load unconnected inputs of the dagster type they are attached
    to.

    The recommended way to define a type loader is with the
    :py:func:`@dagster_type_loader <dagster_type_loader>` decorator.
    """

    @property
    @abstractmethod
    def schema_type(self) -> ConfigType:
        pass

    def construct_from_config_value(
        self, _context: "DagsterTypeLoaderContext", config_value: object
    ) -> object:
        """How to create a runtime value from config data."""
        return config_value

    def required_resource_keys(self) -> AbstractSet[str]:
        return frozenset()

    def get_resource_requirements(
        self, type_display_name: str
    ) -> Iterator[ResourceRequirement]:
        for resource_key in sorted(list(self.required_resource_keys())):
            yield TypeLoaderResourceRequirement(
                key=resource_key, type_display_name=type_display_name
            )


class DagsterTypeLoaderFromDecorator(DagsterTypeLoader):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._func = check.callable_param(func, "func")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )

    @property
    def schema_type(self) -> ConfigType:
        return self._config_type

    def construct_from_config_value(
        self, context: "DagsterTypeLoaderContext", config_value: object
    ):
        return self._func(context, config_value)

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_type_loader_for_decorator(
    config_type: ConfigType, func, required_resource_keys: Optional[AbstractSet[str]]
):
    return DagsterTypeLoaderFromDecorator(config_type, func, required_resource_keys)


DagsterTypeLoaderFn: TypeAlias = Callable[["DagsterTypeLoaderContext", Any], Any]


@public
def dagster_type_loader(
    config_schema: object, required_resource_keys: Optional[AbstractSet[str]] = None
) -> Callable[[DagsterTypeLoaderFn], DagsterTypeLoaderFromDecorator]:
    """Create an dagster type loader that maps config data to a runtime value.

    The decorated function should take the execution context and parsed config value and return the
    appropriate runtime value.

    Args:
        config_schema (ConfigSchema): The schema for the config that's passed to the decorated
            function.

    Examples:
        .. code-block:: python

            @dagster_type_loader(Permissive())
            def load_dict(_context, value):
                return value
    """
    from dagster._config import resolve_to_config_type

    config_type = resolve_to_config_type(config_schema)
    assert isinstance(config_type, ConfigType), (
        f"{config_schema} could not be resolved to config type"
    )
    EXPECTED_POSITIONALS = ["context", "*"]

    def wrapper(func: DagsterTypeLoaderFn) -> DagsterTypeLoaderFromDecorator:
        params = get_function_params(func)
        missing_positional = validate_expected_params(params, EXPECTED_POSITIONALS)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                f"@dagster_type_loader '{func.__name__}' decorated function does not have required"
                f" positional parameter '{missing_positional}'. @dagster_type_loader decorated"
                " functions should only have keyword arguments that match input names and a first"
                " positional parameter named 'context'."
            )

        return _create_type_loader_for_decorator(
            config_type, func, required_resource_keys
        )

    return wrapper
