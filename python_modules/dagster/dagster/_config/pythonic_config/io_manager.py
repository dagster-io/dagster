from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Optional, Union, cast

from typing_extensions import TypeVar

from dagster._config.pythonic_config.attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)
from dagster._config.pythonic_config.config import Config
from dagster._config.pythonic_config.conversion_utils import TResValue
from dagster._config.pythonic_config.resource import (
    CoercibleToResource,
    ConfigurableResourceFactory,
    NestedResourcesResourceDefinition,
    PartialResource,
    T_Self,
)
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._core.definitions.definition_config_schema import CoercableToConfigSchema
from dagster._core.definitions.resource_definition import ResourceFunction
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition
from dagster._utils.cached_method import cached_method

TIOManagerValue = TypeVar("TIOManagerValue", bound=IOManager)


class ConfigurableIOManagerFactoryResourceDefinition(  # pyright: ignore[reportIncompatibleMethodOverride]
    NestedResourcesResourceDefinition,
    IOManagerDefinition,
):
    def __init__(
        self,
        configurable_resource_cls: type,
        resource_fn: ResourceFunction,
        config_schema: Any,
        description: Optional[str],
        nested_resources: Mapping[str, Any],
        nested_partial_resources: Mapping[str, Any],
        input_config_schema: Optional[Union[CoercableToConfigSchema, type[Config]]] = None,
        output_config_schema: Optional[Union[CoercableToConfigSchema, type[Config]]] = None,
        dagster_maintained: bool = False,
    ):
        input_config_schema_resolved: CoercableToConfigSchema = (
            cast(type[Config], input_config_schema).to_config_schema()
            if safe_is_subclass(input_config_schema, Config)
            else cast(CoercableToConfigSchema, input_config_schema)
        )
        output_config_schema_resolved: CoercableToConfigSchema = (
            cast(type[Config], output_config_schema).to_config_schema()
            if safe_is_subclass(output_config_schema, Config)
            else cast(CoercableToConfigSchema, output_config_schema)
        )
        super().__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            input_config_schema=input_config_schema_resolved,
            output_config_schema=output_config_schema_resolved,
        )
        self._nested_partial_resources = nested_partial_resources
        self._nested_resources = nested_resources
        self._configurable_resource_cls = configurable_resource_cls
        self._dagster_maintained = dagster_maintained

    @property
    def configurable_resource_cls(self) -> type:
        return self._configurable_resource_cls

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, Any]:
        return self._nested_resources

    @property
    def nested_partial_resources(
        self,
    ) -> Mapping[str, "CoercibleToResource"]:
        return self._nested_partial_resources


class ConfigurableIOManagerFactory(ConfigurableResourceFactory, Generic[TResValue]):
    """Base class for Dagster IO managers that utilize structured config. This base class
    is useful for cases in which the returned IO manager is not the same as the class itself
    (e.g. when it is a wrapper around the actual IO manager implementation).

    This class is a subclass of both :py:class:`IOManagerDefinition` and :py:class:`Config`.
    Implementers should provide an implementation of the :py:meth:`resource_function` method,
    which should return an instance of :py:class:`IOManager`.


    Example definition:

    .. code-block:: python

        class ExternalIOManager(IOManager):

            def __init__(self, connection):
                self._connection = connection

            def handle_output(self, context, obj):
                ...

            def load_input(self, context):
                ...

        class ConfigurableExternalIOManager(ConfigurableIOManagerFactory):
            username: str
            password: str

            def create_io_manager(self, context) -> IOManager:
                with database.connect(username, password) as connection:
                    return MyExternalIOManager(connection)

        defs = Definitions(
            ...,
            resources={
                "io_manager": ConfigurableExternalIOManager(
                    username="dagster",
                    password=EnvVar("DB_PASSWORD")
                )
            }
        )

    """

    def __init__(self, **data: Any):
        ConfigurableResourceFactory.__init__(self, **data)

    @abstractmethod
    def create_io_manager(self, context) -> TResValue:
        """Implement as one would implement a @io_manager decorator function."""
        raise NotImplementedError()

    def create_resource(self, context: InitResourceContext) -> TResValue:
        return self.create_io_manager(context)

    @classmethod
    def configure_at_launch(cls: "type[T_Self]", **kwargs) -> "PartialIOManager[T_Self]":
        """Returns a partially initialized copy of the IO manager, with remaining config fields
        set at runtime.
        """
        return PartialIOManager(resource_cls=cls, data=kwargs)

    @cached_method
    def get_resource_definition(self) -> ConfigurableIOManagerFactoryResourceDefinition:  # pyright: ignore[reportIncompatibleMethodOverride]
        return ConfigurableIOManagerFactoryResourceDefinition(
            self.__class__,
            resource_fn=self._get_initialize_and_run_fn(),
            config_schema=self._config_schema,
            description=self.__doc__,
            nested_partial_resources=self._nested_partial_resources,
            nested_resources=self.nested_resources,
            input_config_schema=self.__class__.input_config_schema(),
            output_config_schema=self.__class__.output_config_schema(),
            dagster_maintained=self._is_dagster_maintained(),
        )

    @classmethod
    def input_config_schema(
        cls,
    ) -> Optional[Union[CoercableToConfigSchema, type[Config]]]:
        return None

    @classmethod
    def output_config_schema(
        cls,
    ) -> Optional[Union[CoercableToConfigSchema, type[Config]]]:
        return None


class PartialIOManager(
    PartialResource[TResValue],
    Generic[TResValue],
):
    @cached_method
    def get_resource_definition(self) -> ConfigurableIOManagerFactoryResourceDefinition:  # pyright: ignore[reportIncompatibleMethodOverride]
        input_config_schema = None
        output_config_schema = None
        if safe_is_subclass(self.resource_cls, ConfigurableIOManagerFactory):
            factory_cls: type[ConfigurableIOManagerFactory] = cast(
                type[ConfigurableIOManagerFactory], self.resource_cls
            )
            input_config_schema = factory_cls.input_config_schema()
            output_config_schema = factory_cls.output_config_schema()

        return ConfigurableIOManagerFactoryResourceDefinition(
            self.resource_cls,
            resource_fn=self._state__internal__.resource_fn,
            config_schema=self._state__internal__.config_schema,
            description=self._state__internal__.description,
            nested_resources=self._state__internal__.nested_resources,
            nested_partial_resources=self._state__internal__.nested_partial_resources,
            input_config_schema=input_config_schema,
            output_config_schema=output_config_schema,
            dagster_maintained=self.resource_cls._is_dagster_maintained(),  # noqa: SLF001
        )


class ConfigurableIOManager(ConfigurableIOManagerFactory, IOManager):
    """Base class for Dagster IO managers that utilize structured config.

    This class is a subclass of both :py:class:`IOManagerDefinition`, :py:class:`Config`,
    and :py:class:`IOManager`. Implementers must provide an implementation of the
    :py:meth:`handle_output` and :py:meth:`load_input` methods.

    Example definition:

    .. code-block:: python

        class MyIOManager(ConfigurableIOManager):
            path_prefix: List[str]

            def _get_path(self, context) -> str:
                return "/".join(context.asset_key.path)

            def handle_output(self, context, obj):
                write_csv(self._get_path(context), obj)

            def load_input(self, context):
                return read_csv(self._get_path(context))

        defs = Definitions(
            ...,
            resources={
                "io_manager": MyIOManager(path_prefix=["my", "prefix"])
            }
        )

    """

    def create_io_manager(self, context) -> IOManager:
        return self


class ConfigurableLegacyIOManagerAdapter(ConfigurableIOManagerFactory):
    """Adapter base class for wrapping a decorated, function-style I/O manager
    with structured config.

    To use this class, subclass it, define config schema fields using Pydantic,
    and implement the ``wrapped_io_manager`` method.

    Example:
    .. code-block:: python

        class OldIOManager(IOManager):
            def __init__(self, base_path: str):
                ...

        @io_manager(config_schema={"base_path": str})
        def old_io_manager(context):
            base_path = context.resource_config["base_path"]

            return OldIOManager(base_path)

        class MyIOManager(ConfigurableLegacyIOManagerAdapter):
            base_path: str

            @property
            def wrapped_io_manager(self) -> IOManagerDefinition:
                return old_io_manager
    """

    @property
    @abstractmethod
    def wrapped_io_manager(self) -> IOManagerDefinition:
        raise NotImplementedError()

    def create_io_manager(self, context) -> IOManager:
        raise NotImplementedError(
            "Because we override resource_fn in the adapter, this is never called."
        )

    @cached_method
    def get_resource_definition(self) -> ConfigurableIOManagerFactoryResourceDefinition:
        return ConfigurableIOManagerFactoryResourceDefinition(
            self.__class__,
            resource_fn=self.wrapped_io_manager.resource_fn,
            config_schema=self._config_schema,
            description=self.__doc__,
            nested_partial_resources=self._nested_partial_resources,
            nested_resources=self.nested_resources,
            dagster_maintained=self._is_dagster_maintained(),
        )
