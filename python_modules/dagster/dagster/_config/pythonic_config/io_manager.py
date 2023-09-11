from abc import abstractmethod
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    Optional,
    Type,
    Union,
    cast,
)

from typing_extensions import TypeVar

from dagster._core.definitions.definition_config_schema import (
    CoercableToConfigSchema,
)
from dagster._core.definitions.resource_definition import (
    ResourceDefinition,
    ResourceFunction,
)
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition
from dagster._utils.cached_method import cached_method

from .attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)
from .config import Config
from .conversion_utils import TResValue
from .inheritance_utils import safe_is_subclass
from .resource import (
    AllowDelayedDependencies,
    ConfigurableResourceFactory,
    PartialResource,
    ResourceId,
    ResourceWithKeyMapping,
    Self,
)

try:
    from functools import cached_property  # type: ignore  # (py37 compat)
except ImportError:

    class cached_property:
        pass


TIOManagerValue = TypeVar("TIOManagerValue", bound=IOManager)


class ConfigurableIOManagerFactoryResourceDefinition(IOManagerDefinition, AllowDelayedDependencies):
    def __init__(
        self,
        configurable_resource_cls: Type,
        resource_fn: ResourceFunction,
        config_schema: Any,
        description: Optional[str],
        resolve_resource_keys: Callable[[Mapping[int, str]], AbstractSet[str]],
        nested_resources: Mapping[str, Any],
        input_config_schema: Optional[Union[CoercableToConfigSchema, Type[Config]]] = None,
        output_config_schema: Optional[Union[CoercableToConfigSchema, Type[Config]]] = None,
        dagster_maintained: bool = False,
    ):
        input_config_schema_resolved: CoercableToConfigSchema = (
            cast(Type[Config], input_config_schema).to_config_schema()
            if safe_is_subclass(input_config_schema, Config)
            else cast(CoercableToConfigSchema, input_config_schema)
        )
        output_config_schema_resolved: CoercableToConfigSchema = (
            cast(Type[Config], output_config_schema).to_config_schema()
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
        self._resolve_resource_keys = resolve_resource_keys
        self._nested_resources = nested_resources
        self._configurable_resource_cls = configurable_resource_cls
        self._dagster_maintained = dagster_maintained

    @property
    def configurable_resource_cls(self) -> Type:
        return self._configurable_resource_cls

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, Any]:
        return self._nested_resources

    def _resolve_required_resource_keys(
        self, resource_mapping: Mapping[int, str]
    ) -> AbstractSet[str]:
        return self._resolve_resource_keys(resource_mapping)


class IOManagerWithKeyMapping(ResourceWithKeyMapping, IOManagerDefinition):
    """Version of ResourceWithKeyMapping wrapper that also implements IOManagerDefinition."""

    def __init__(
        self,
        resource: ResourceDefinition,
        resource_id_to_key_mapping: Dict[ResourceId, str],
    ):
        ResourceWithKeyMapping.__init__(self, resource, resource_id_to_key_mapping)
        IOManagerDefinition.__init__(
            self, resource_fn=self.resource_fn, config_schema=resource.config_schema
        )


class ConfigurableIOManagerFactory(ConfigurableResourceFactory[TIOManagerValue]):
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
    def create_io_manager(self, context) -> TIOManagerValue:
        """Implement as one would implement a @io_manager decorator function."""
        raise NotImplementedError()

    def create_resource(self, context: InitResourceContext) -> TIOManagerValue:
        return self.create_io_manager(context)

    @classmethod
    def configure_at_launch(cls: "Type[Self]", **kwargs) -> "PartialIOManager[Self]":
        """Returns a partially initialized copy of the IO manager, with remaining config fields
        set at runtime.
        """
        return PartialIOManager(cls, data=kwargs)

    @cached_method
    def get_resource_definition(self) -> ConfigurableIOManagerFactoryResourceDefinition:
        return ConfigurableIOManagerFactoryResourceDefinition(
            self.__class__,
            resource_fn=self._get_initialize_and_run_fn(),
            config_schema=self._config_schema,
            description=self.__doc__,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
            input_config_schema=self.__class__.input_config_schema(),
            output_config_schema=self.__class__.output_config_schema(),
            dagster_maintained=self._is_dagster_maintained(),
        )

    @classmethod
    def input_config_schema(
        cls,
    ) -> Optional[Union[CoercableToConfigSchema, Type[Config]]]:
        return None

    @classmethod
    def output_config_schema(
        cls,
    ) -> Optional[Union[CoercableToConfigSchema, Type[Config]]]:
        return None


class PartialIOManager(Generic[TResValue], PartialResource[TResValue]):
    def __init__(
        self,
        resource_cls: Type[ConfigurableResourceFactory[TResValue]],
        data: Dict[str, Any],
    ):
        PartialResource.__init__(self, resource_cls, data)

    @cached_method
    def get_resource_definition(self) -> ConfigurableIOManagerFactoryResourceDefinition:
        input_config_schema = None
        output_config_schema = None
        if safe_is_subclass(self.resource_cls, ConfigurableIOManagerFactory):
            factory_cls: Type[ConfigurableIOManagerFactory] = cast(
                Type[ConfigurableIOManagerFactory], self.resource_cls
            )
            input_config_schema = factory_cls.input_config_schema()
            output_config_schema = factory_cls.output_config_schema()

        return ConfigurableIOManagerFactoryResourceDefinition(
            self.resource_cls,
            resource_fn=self._state__internal__.resource_fn,
            config_schema=self._state__internal__.config_schema,
            description=self._state__internal__.description,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self._state__internal__.nested_resources,
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
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
            dagster_maintained=self._is_dagster_maintained(),
        )
