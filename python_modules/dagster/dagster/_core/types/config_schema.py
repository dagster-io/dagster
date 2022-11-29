from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Callable, Iterator, Optional, Union, cast

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._config import ConfigType
from dagster._core.decorator_utils import get_function_params, validate_expected_params
from dagster._core.definitions.events import AssetMaterialization, Materialization
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils import ensure_gen
from dagster._utils.backcompat import experimental_arg_warning

from ..definitions.resource_requirement import (
    ResourceRequirement,
    TypeLoaderResourceRequirement,
    TypeMaterializerResourceRequirement,
)

if TYPE_CHECKING:
    from dagster._core.definitions import JobDefinition, OpDefinition
    from dagster._core.execution.context.init import Resources
    from dagster._core.execution.context.system import (
        DagsterTypeLoaderContext,
        DagsterTypeMaterializerContext,
        StepExecutionContext,
    )


class DagsterTypeLoader(ABC):
    """
    Dagster type loaders are used to load unconnected inputs of the dagster type they are attached
    to.

    The recommended way to define a type loader is with the
    :py:func:`@dagster_type_loader <dagster_type_loader>` decorator.
    """

    @property
    @abstractmethod
    def schema_type(self) -> ConfigType:
        pass

    @property
    def loader_version(self) -> Optional[str]:
        return None

    def compute_loaded_input_version(self, _config_value: object) -> Optional[str]:
        return None

    def construct_from_config_value(
        self, _context: "DagsterTypeLoaderContext", config_value: object
    ) -> object:
        """
        How to create a runtime value from config data.
        """
        return config_value

    def required_resource_keys(self) -> AbstractSet[str]:
        return frozenset()

    def get_resource_requirements(
        self, outer_context: Optional[object] = None
    ) -> Iterator[ResourceRequirement]:
        type_display_name = cast(str, outer_context)
        for resource_key in sorted(list(self.required_resource_keys())):
            yield TypeLoaderResourceRequirement(
                key=resource_key, type_display_name=type_display_name
            )


class DagsterTypeMaterializer(ABC):
    """
    Dagster type materializers are used to materialize outputs of the dagster type they are attached
    to.

    The recommended way to define a type loader is with the
    :py:func:`@dagster_type_materializer <dagster_type_materializer>` decorator.
    """

    @property
    @abstractmethod
    def schema_type(self) -> ConfigType:
        pass

    @abstractmethod
    def materialize_runtime_values(
        self,
        _context: "DagsterTypeMaterializerContext",
        _config_value: object,
        _runtime_value: object,
    ) -> Iterator[Union[AssetMaterialization, Materialization]]:
        """
        How to materialize a runtime value given configuration.
        """

    def required_resource_keys(self) -> AbstractSet[str]:
        return frozenset()

    def get_resource_requirements(
        self, outer_context: Optional[object] = None
    ) -> Iterator[ResourceRequirement]:
        type_display_name = cast(str, outer_context)
        for resource_key in sorted(list(self.required_resource_keys())):
            yield TypeMaterializerResourceRequirement(
                key=resource_key, type_display_name=type_display_name
            )


class DagsterTypeLoaderFromDecorator(DagsterTypeLoader):
    def __init__(
        self,
        config_type,
        func,
        required_resource_keys,
        loader_version=None,
        external_version_fn=None,
    ):
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._func = check.callable_param(func, "func")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )
        self._loader_version = check.opt_str_param(loader_version, "loader_version")
        if self._loader_version:
            experimental_arg_warning("loader_version", "DagsterTypeLoaderFromDecorator.__init__")
        self._external_version_fn = check.opt_callable_param(
            external_version_fn, "external_version_fn"
        )
        if self._external_version_fn:
            experimental_arg_warning(
                "external_version_fn", "DagsterTypeLoaderFromDecorator.__init__"
            )

    @property
    def schema_type(self) -> ConfigType:
        return self._config_type

    @property
    def loader_version(self) -> Optional[str]:
        return self._loader_version

    def compute_loaded_input_version(self, config_value: object) -> Optional[str]:
        """Compute the type-loaded input from a given config_value.

        Args:
            config_value (object): Config value to be ingested by the external version
                loading function.
        Returns:
            Optional[str]: Hash of concatenated loader version and external input version if both
                are provided, else None.
        """
        version = ""
        if self.loader_version:
            version += str(self.loader_version)
        if self._external_version_fn:
            ext_version = self._external_version_fn(config_value)
            version += str(ext_version)

        if version == "":
            return None  # Sentinel value for no version provided.
        else:
            return hashlib.sha1(version.encode("utf-8")).hexdigest()

    def construct_from_config_value(
        self, context: "DagsterTypeLoaderContext", config_value: object
    ):
        return self._func(context, config_value)

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_type_loader_for_decorator(
    config_type: ConfigType,
    func,
    required_resource_keys: Optional[AbstractSet[str]],
    loader_version: Optional[str] = None,
    external_version_fn: Optional[Callable[[object], str]] = None,
):
    return DagsterTypeLoaderFromDecorator(
        config_type, func, required_resource_keys, loader_version, external_version_fn
    )


DagsterTypeLoaderFn: TypeAlias = Callable[["StepExecutionContext", object], object]


def dagster_type_loader(
    config_schema: object,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    loader_version: Optional[str] = None,
    external_version_fn: Optional[Callable[[object], str]] = None,
) -> Callable[[DagsterTypeLoaderFn], DagsterTypeLoaderFromDecorator]:
    """Create an dagster type loader that maps config data to a runtime value.

    The decorated function should take the execution context and parsed config value and return the
    appropriate runtime value.

    Args:
        config_schema (ConfigSchema): The schema for the config that's passed to the decorated
            function.
        loader_version (str): (Experimental) The version of the decorated compute function. Two
            loading functions should have the same version if and only if they deterministically
            produce the same outputs when provided the same inputs.
        external_version_fn (Callable): (Experimental) A function that takes in the same parameters as the loader
            function (config_value) and returns a representation of the version of the external
            asset (str). Two external assets with identical versions are treated as identical to one
            another.

    Examples:

    .. code-block:: python

        @dagster_type_loader(Permissive())
        def load_dict(_context, value):
            return value
    """
    from dagster._config import resolve_to_config_type

    config_type = resolve_to_config_type(config_schema)
    assert isinstance(
        config_type, ConfigType
    ), f"{config_schema} could not be resolved to config type"
    EXPECTED_POSITIONALS = ["context", "*"]

    def wrapper(func: DagsterTypeLoaderFn) -> DagsterTypeLoaderFromDecorator:
        params = get_function_params(func)
        missing_positional = validate_expected_params(params, EXPECTED_POSITIONALS)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@dagster_type_loader '{solid_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. @dagster_type_loader decorated functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=func.__name__, missing_param=missing_positional
                )
            )

        return _create_type_loader_for_decorator(
            config_type, func, required_resource_keys, loader_version, external_version_fn  # type: ignore  # mypy bug
        )

    return wrapper


class DagsterTypeMaterializerForDecorator(DagsterTypeMaterializer):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._func = check.callable_param(func, "func")
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )

    @property
    def schema_type(self) -> ConfigType:
        return self._config_type

    def materialize_runtime_values(
        self, context: "DagsterTypeMaterializerContext", config_value: object, runtime_value: object
    ) -> Iterator[Union[Materialization, AssetMaterialization]]:
        return ensure_gen(self._func(context, config_value, runtime_value))

    def required_resource_keys(self) -> AbstractSet[str]:
        return frozenset(self._required_resource_keys)


def _create_output_materializer_for_decorator(
    config_type: ConfigType,
    func: Callable[["DagsterTypeMaterializerContext", object, object], AssetMaterialization],
    required_resource_keys: Optional[AbstractSet[str]],
) -> DagsterTypeMaterializerForDecorator:
    return DagsterTypeMaterializerForDecorator(config_type, func, required_resource_keys)


def dagster_type_materializer(
    config_schema: object, required_resource_keys: Optional[AbstractSet[str]] = None
) -> Callable[
    [Callable[["DagsterTypeMaterializerContext", object, object], AssetMaterialization]],
    DagsterTypeMaterializerForDecorator,
]:
    """Create an output materialization hydration config that configurably materializes a runtime
    value.

    The decorated function should take a :py:class:'dagster.DagsterTypeMaterializerContext`, the parsed config value, and the
    runtime value. It should materialize the runtime value, and should
    return an appropriate :py:class:`AssetMaterialization`.

    Args:
        config_schema (object): The type of the config data expected by the decorated function.

    Examples:

    .. code-block:: python

        # Takes a list of dicts such as might be read in using csv.DictReader, as well as a config
        value, and writes
        @dagster_type_materializer(str)
        def materialize_df(_context, path, value):
            with open(path, 'w') as fd:
                writer = csv.DictWriter(fd, fieldnames=value[0].keys())
                writer.writeheader()
                writer.writerows(rowdicts=value)

            return AssetMaterialization.file(path)

    """
    from dagster._config import resolve_to_config_type

    config_type = resolve_to_config_type(config_schema)
    return lambda func: _create_output_materializer_for_decorator(
        config_type, func, required_resource_keys  # type: ignore
    )
