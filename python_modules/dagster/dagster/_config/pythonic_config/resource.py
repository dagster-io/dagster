import contextlib
import inspect
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterator, Mapping
from typing import (  # noqa: UP035
    AbstractSet,
    Any,
    Callable,
    Generic,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
)

from dagster_shared.dagster_model.pydantic_compat_layer import model_fields
from dagster_shared.error import DagsterError
from pydantic import BaseModel
from typing_extensions import TypeAlias, TypeGuard, get_args, get_origin

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._config.field import Field as DagsterField
from dagster._config.field_utils import config_dictionary_from_values
from dagster._config.pythonic_config.attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)
from dagster._config.pythonic_config.config import (
    Config,
    MakeConfigCacheable,
    infer_schema_from_config_class,
)
from dagster._config.pythonic_config.conversion_utils import TResValue, _curry_config_schema
from dagster._config.pythonic_config.typing_utils import (
    BaseResourceMeta,
    LateBoundTypesForResourceTypeChecking,
    TypecheckAllowPartialResourceInitParams,
)
from dagster._config.validate import validate_config
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.definition_config_schema import (
    ConfiguredDefinitionConfigSchema,
    DefinitionConfigSchema,
)
from dagster._core.definitions.resource_definition import (
    ResourceDefinition,
    ResourceFunction,
    ResourceFunctionWithContext,
    ResourceFunctionWithoutContext,
    has_at_least_one_parameter,
)
from dagster._core.definitions.resource_requirement import ResourceRequirement
from dagster._core.errors import DagsterInvalidConfigError, DagsterInvalidDefinitionError
from dagster._core.execution.context.init import InitResourceContext, build_init_resource_context
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.typing_api import is_closed_python_optional_type

T_Self = TypeVar("T_Self", bound="ConfigurableResourceFactory")
ResourceId: TypeAlias = int


class NestedResourcesResourceDefinition(ResourceDefinition, ABC):
    @property
    @abstractmethod
    def nested_partial_resources(self) -> Mapping[str, "CoercibleToResource"]: ...

    @property
    @abstractmethod
    def nested_resources(self) -> Mapping[str, Any]: ...

    @property
    @abstractmethod
    def configurable_resource_cls(self) -> type: ...

    def get_resource_requirements(self, source_key: str) -> Iterator["ResourceRequirement"]:  # pyright: ignore[reportIncompatibleMethodOverride]
        for attr_name, partial_resource in self.nested_partial_resources.items():
            yield PartialResourceDependencyRequirement(
                class_name=self.configurable_resource_cls.__name__,
                attr_name=attr_name,
                partial_resource=partial_resource,
            )

        for inner_key, resource in self.nested_resources.items():
            if is_coercible_to_resource(resource):
                yield from coerce_to_resource(resource).get_resource_requirements(inner_key)

        yield from super().get_resource_requirements(source_key)

    def get_required_resource_keys(
        self, resource_defs: Mapping[str, ResourceDefinition]
    ) -> AbstractSet[str]:
        resolved_keys = set(self.required_resource_keys)
        for attr_name, partial_resource in self.nested_partial_resources.items():
            if is_coercible_to_resource(partial_resource):
                resolved_keys.add(
                    _resolve_partial_resource_to_key(attr_name, partial_resource, resource_defs)
                )
            else:
                check.failed(
                    f"Unexpected nested partial resource of type {type(partial_resource)} is not coercible to resource"
                )

        for resource in self.nested_resources.values():
            if is_coercible_to_resource(resource):
                resolved_keys.update(
                    coerce_to_resource(resource).get_required_resource_keys(resource_defs)
                )

        return resolved_keys


class ConfigurableResourceFactoryResourceDefinition(NestedResourcesResourceDefinition):
    def __init__(
        self,
        configurable_resource_cls: type,
        resource_fn: ResourceFunction,
        config_schema: Any,
        description: Optional[str],
        nested_resources: Mapping[str, Any],
        nested_partial_resources: Mapping[str, Any],
        dagster_maintained: bool = False,
    ):
        super().__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
        )
        self._configurable_resource_cls = configurable_resource_cls
        self._nested_partial_resources = nested_partial_resources
        self._nested_resources = nested_resources
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

    def _is_dagster_maintained(self) -> bool:
        return self._dagster_maintained


class ConfigurableResourceFactoryState(NamedTuple):
    nested_partial_resources: Mapping[str, Any]
    resolved_config_dict: dict[str, Any]
    config_schema: DefinitionConfigSchema
    schema: DagsterField
    nested_resources: dict[str, Any]
    resource_context: Optional[InitResourceContext]


class ConfigurableResourceFactory(
    Config,
    TypecheckAllowPartialResourceInitParams,
    Generic[TResValue],
    ABC,
    metaclass=BaseResourceMeta,
):
    """Base class for creating and managing the lifecycle of Dagster resources that utilize structured config.

    Users should directly inherit from this class when they want the object passed to user-defined
    code (such as an asset or op) to be different than the object that defines the configuration
    schema and is passed to the :py:class:`Definitions` object. Cases where this is useful include is
    when the object passed to user code is:

    * An existing class from a third-party library that the user does not control.
    * A complex class that requires substantial internal state management or itself requires arguments beyond its config values.
    * A class with expensive initialization that should not be invoked on project load, but rather lazily on first use in an op or asset during a run.
    * A class that you desire to be a plain Python class, rather than a Pydantic class, for whatever reason.

    This class is a subclass of both :py:class:`ResourceDefinition` and :py:class:`Config`, and
    must implement ``create_resource``, which creates the resource to pass to user code.

    Example definition:

    .. code-block:: python

        class DatabaseResource(ConfigurableResourceFactory[Database]):
            connection_uri: str

            def create_resource(self, _init_context) -> Database:
                # For example Database could be from a third-party library or require expensive setup.
                # Or you could just prefer to separate the concerns of configuration and runtime representation
                return Database(self.connection_uri)

    To use a resource created by a factory in a job, you must use the Resource type annotation.

    Example usage:


    .. code-block:: python

        @asset
        def asset_that_uses_database(database: ResourceParam[Database]):
            # Database used directly in user code
            database.query("SELECT * FROM table")

        defs = Definitions(
            assets=[asset_that_uses_database],
            resources={"database": DatabaseResource(connection_uri="some_uri")},
        )

    """

    def __init__(self, **data: Any):
        resource_pointers, data_without_resources = separate_resource_params(self.__class__, data)

        schema = infer_schema_from_config_class(
            self.__class__, fields_to_omit=set(resource_pointers.keys())
        )

        # Populate config values
        super().__init__(**data_without_resources, **resource_pointers)

        # We pull the values from the Pydantic config object, which may cast values
        # to the correct type under the hood - useful in particular for enums
        casted_data_without_resources = {
            k: v
            for k, v in self._convert_to_config_dictionary().items()
            if k in data_without_resources
        }
        resolved_config_dict = config_dictionary_from_values(casted_data_without_resources, schema)

        self._state__internal__ = ConfigurableResourceFactoryState(
            # We keep track of any resources we depend on which are not fully configured
            # so that we can retrieve them at runtime
            nested_partial_resources={
                k: v for k, v in resource_pointers.items() if (not _is_fully_configured(v))
            },
            resolved_config_dict=resolved_config_dict,
            # These are unfortunately named very similarily
            config_schema=_curry_config_schema(schema, resolved_config_dict),
            schema=schema,
            nested_resources={k: v for k, v in resource_pointers.items()},
            resource_context=None,
        )

    @property
    def _schema(self):
        return self._state__internal__.schema

    @property
    def _config_schema(self):
        return self._state__internal__.config_schema

    @property
    def _nested_partial_resources(self):
        return self._state__internal__.nested_partial_resources

    @property
    def _nested_resources(self):
        return self._state__internal__.nested_resources

    @property
    def _resolved_config_dict(self):
        return self._state__internal__.resolved_config_dict

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        """This should be overridden to return True by all dagster maintained resources and IO managers."""
        return False

    @classmethod
    def _is_cm_resource_cls(cls: type["ConfigurableResourceFactory"]) -> bool:
        return (
            cls.yield_for_execution != ConfigurableResourceFactory.yield_for_execution
            or cls.teardown_after_execution != ConfigurableResourceFactory.teardown_after_execution
            # We assume that any resource which has nested resources needs to be treated as a
            # context manager resource, since its nested resources may be context managers
            # and need setup and teardown logic
            or len(_get_resource_param_fields(cls)) > 0
        )

    @property
    def _is_cm_resource(self) -> bool:
        return self.__class__._is_cm_resource_cls()  # noqa: SLF001

    def _get_initialize_and_run_fn(self) -> Callable:
        return self._initialize_and_run_cm if self._is_cm_resource else self._initialize_and_run

    @cached_method  # resource resolution depends on always resolving to the same ResourceDefinition instance
    def get_resource_definition(self) -> ConfigurableResourceFactoryResourceDefinition:
        return ConfigurableResourceFactoryResourceDefinition(
            self.__class__,
            resource_fn=self._get_initialize_and_run_fn(),
            config_schema=self._config_schema,
            description=self.__doc__,
            nested_resources=self.nested_resources,
            nested_partial_resources=self._nested_partial_resources,
            dagster_maintained=self._is_dagster_maintained(),
        )

    @abstractmethod
    def create_resource(self, context: InitResourceContext) -> TResValue:
        """Returns the object that this resource hands to user code, accessible by ops or assets
        through the context or resource parameters. This works like the function decorated
        with @resource when using function-based resources.
        """
        raise NotImplementedError()

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, Any]:
        return self._nested_resources

    @classmethod
    def configure_at_launch(cls: "type[T_Self]", **kwargs) -> "PartialResource[T_Self]":
        """Returns a partially initialized copy of the resource, with remaining config fields
        set at runtime.
        """
        return PartialResource(cls, data=kwargs)

    def _with_updated_values(
        self, values: Optional[Mapping[str, Any]]
    ) -> "ConfigurableResourceFactory[TResValue]":
        """Returns a new instance of the resource with the given values.
        Used when initializing a resource at runtime.
        """
        values = check.opt_mapping_param(values, "values", key_type=str)
        # Since Resource extends BaseModel and is a dataclass, we know that the
        # signature of any __init__ method will always consist of the fields
        # of this class. We can therefore safely pass in the values as kwargs.
        to_populate = self.__class__._get_non_default_public_field_values_cls(  # noqa: SLF001
            {**self._get_non_default_public_field_values(), **values}
        )
        out = self.__class__(**to_populate)
        out._state__internal__ = out._state__internal__._replace(  # noqa: SLF001
            resource_context=self._state__internal__.resource_context
        )
        return out

    @contextlib.contextmanager
    def _resolve_and_update_nested_resources(
        self, context: InitResourceContext
    ) -> Generator["ConfigurableResourceFactory[TResValue]", None, None]:
        """Updates any nested resources with the resource values from the context.
        In this case, populating partially configured resources or
        resources that return plain Python types.

        Returns a new instance of the resource.
        """
        from dagster._core.execution.build_resources import wrap_resource_for_execution

        partial_resources_to_update: dict[str, Any] = {}
        if self._nested_partial_resources:
            for attr_name, resource in self._nested_partial_resources.items():
                key = _resolve_partial_resource_to_key(
                    attr_name, resource, context.all_resource_defs
                )
                resolved_resource = getattr(context.resources, key)
                partial_resources_to_update[attr_name] = resolved_resource

        # Also evaluate any resources that are not partial
        with contextlib.ExitStack() as stack:
            resources_to_update, _ = separate_resource_params(self.__class__, self.__dict__)
            resources_to_update = {
                attr_name: _call_resource_fn_with_default(
                    stack, wrap_resource_for_execution(resource), context
                )
                for attr_name, resource in resources_to_update.items()
                if attr_name not in partial_resources_to_update
            }

            to_update = {**resources_to_update, **partial_resources_to_update}
            yield self._with_updated_values(to_update)

    @deprecated(
        breaking_version="2.0", additional_warn_text="Use `with_replaced_resource_context` instead"
    )
    def with_resource_context(
        self, resource_context: InitResourceContext
    ) -> "ConfigurableResourceFactory[TResValue]":
        return self.with_replaced_resource_context(resource_context)

    def with_replaced_resource_context(
        self, resource_context: InitResourceContext
    ) -> "ConfigurableResourceFactory[TResValue]":
        """Returns a new instance of the resource with the given resource init context bound."""
        # This utility is used to create a copy of this resource, without adjusting
        # any values in this case
        copy = self._with_updated_values({})
        copy._state__internal__ = copy._state__internal__._replace(  # noqa: SLF001
            resource_context=resource_context
        )
        return copy

    def _initialize_and_run(self, context: InitResourceContext) -> TResValue:
        with self._resolve_and_update_nested_resources(context) as has_nested_resource:
            updated_resource = has_nested_resource.with_replaced_resource_context(  # noqa: SLF001
                context
            )._with_updated_values(context.resource_config)

            updated_resource.setup_for_execution(context)
            return updated_resource.create_resource(context)

    @contextlib.contextmanager
    def _async_to_sync_cm(
        self,
        context: InitResourceContext,
        async_cm: contextlib.AbstractAsyncContextManager,
    ):
        aio_exit_stack = contextlib.AsyncExitStack()
        loop = context.event_loop
        if loop is None:
            raise DagsterError(
                "Unable to handle resource with async def yield_for_execution in the current context. "
                "If using direct execution utilities like build_context, pass an event loop in and use "
                "the same event loop to execute your asset/op."
            )

        try:
            value = loop.run_until_complete(aio_exit_stack.enter_async_context(async_cm))
            yield value
        finally:
            loop.run_until_complete(aio_exit_stack.aclose())

    @contextlib.contextmanager
    def _initialize_and_run_cm(
        self,
        context: InitResourceContext,
    ) -> Generator[TResValue, None, None]:
        with self._resolve_and_update_nested_resources(context) as has_nested_resource:
            updated_resource = has_nested_resource.with_replaced_resource_context(  # noqa: SLF001
                context
            )._with_updated_values(context.resource_config)

            resource_cm = updated_resource.yield_for_execution(context)
            if isinstance(resource_cm, contextlib.AbstractAsyncContextManager):
                resource_cm = self._async_to_sync_cm(context, resource_cm)

            with resource_cm as value:
                yield value

    def setup_for_execution(self, context: InitResourceContext) -> None:
        """Optionally override this method to perform any pre-execution steps
        needed before the resource is used in execution.
        """
        pass

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        """Optionally override this method to perform any post-execution steps
        needed after the resource is used in execution.

        teardown_after_execution will be called even if any part of the run fails.
        It will not be called if setup_for_execution fails.
        """
        pass

    @contextlib.contextmanager
    def yield_for_execution(self, context: InitResourceContext) -> Generator[TResValue, None, None]:
        """Optionally override this method to perform any lifecycle steps
        before or after the resource is used in execution. By default, calls
        setup_for_execution before yielding, and teardown_after_execution after yielding.

        Note that if you override this method and want setup_for_execution or
        teardown_after_execution to be called, you must invoke them yourself.
        """
        self.setup_for_execution(context)
        try:
            yield self.create_resource(context)
        finally:
            self.teardown_after_execution(context)

    def get_resource_context(self) -> InitResourceContext:
        """Returns the context that this resource was initialized with."""
        return check.not_none(
            self._state__internal__.resource_context,
            additional_message="Attempted to get context before resource was initialized.",
        )

    def process_config_and_initialize(self) -> TResValue:
        """Initializes this resource, fully processing its config and returning the prepared
        resource value.
        """
        from dagster._config.post_process import post_process_config

        post_processed_config = post_process_config(
            self._config_schema.config_type,  # pyright: ignore[reportArgumentType]
            self._convert_to_config_dictionary(),
        )

        if not post_processed_config.success:
            raise DagsterInvalidConfigError(
                "Errors while initializing resource",
                post_processed_config.errors,
                post_processed_config,
            )

        return self.from_resource_context(
            build_init_resource_context(config=post_processed_config.value),
            nested_resources=self.nested_resources,
        )

    @contextlib.contextmanager
    def process_config_and_initialize_cm(self) -> Generator[TResValue, None, None]:
        """Context which initializes this resource, fully processing its config and yielding the
        prepared resource value.
        """
        from dagster._config.post_process import post_process_config

        post_processed_config = post_process_config(
            self._config_schema.config_type,  # pyright: ignore[reportArgumentType]
            self._convert_to_config_dictionary(),
        )

        if not post_processed_config.success:
            raise DagsterInvalidConfigError(
                "Errors while initializing resource",
                post_processed_config.errors,
                post_processed_config,
            )

        with (
            build_init_resource_context(config=post_processed_config.value) as context,
            self.from_resource_context_cm(
                context,
                nested_resources=self.nested_resources,
            ) as out,
        ):
            yield out

    @classmethod
    def from_resource_context(
        cls, context: InitResourceContext, nested_resources: Optional[Mapping[str, Any]] = None
    ) -> TResValue:
        """Creates a new instance of this resource from a populated InitResourceContext.
        Useful when creating a resource from a function-based resource, for backwards
        compatibility purposes.

        For resources that have custom teardown behavior, use from_resource_context_cm instead.

        Example usage:

        .. code-block:: python

            class MyResource(ConfigurableResource):
                my_str: str

            @resource(config_schema=MyResource.to_config_schema())
            def my_resource(context: InitResourceContext) -> MyResource:
                return MyResource.from_resource_context(context)

        """
        check.invariant(
            not cls._is_cm_resource_cls(),
            "Use from_resource_context_cm for resources which have custom teardown behavior,"
            " e.g. overriding yield_for_execution or teardown_after_execution",
        )
        return cls(  # noqa: SLF001
            **{**(context.resource_config or {}), **(nested_resources or {})}
        )._initialize_and_run(context)

    @classmethod
    @contextlib.contextmanager
    def from_resource_context_cm(
        cls, context: InitResourceContext, nested_resources: Optional[Mapping[str, Any]] = None
    ) -> Generator[TResValue, None, None]:
        """Context which generates a new instance of this resource from a populated InitResourceContext.
        Useful when creating a resource from a function-based resource, for backwards
        compatibility purposes. Handles custom teardown behavior.

        Example usage:

        .. code-block:: python

            class MyResource(ConfigurableResource):
                my_str: str

            @resource(config_schema=MyResource.to_config_schema())
            def my_resource(context: InitResourceContext) -> Generator[MyResource, None, None]:
                with MyResource.from_resource_context_cm(context) as my_resource:
                    yield my_resource

        """
        with cls(  # noqa: SLF001
            **{**(context.resource_config or {}), **(nested_resources or {})}
        )._initialize_and_run_cm(context) as value:
            yield value


@public
class ConfigurableResource(ConfigurableResourceFactory[TResValue]):
    """Base class for Dagster resources that utilize structured config.

    This class is a subclass of both :py:class:`ResourceDefinition` and :py:class:`Config`.

    Example definition:

    .. code-block:: python

        class WriterResource(ConfigurableResource):
            prefix: str

            def output(self, text: str) -> None:
                print(f"{self.prefix}{text}")

    Example usage:

    .. code-block:: python

        @asset
        def asset_that_uses_writer(writer: WriterResource):
            writer.output("text")

        defs = Definitions(
            assets=[asset_that_uses_writer],
            resources={"writer": WriterResource(prefix="a_prefix")},
        )

    You can optionally use this class to model configuration only and vend an object
    of a different type for use at runtime. This is useful for those who wish to
    have a separate object that manages configuration and a separate object at runtime. Or
    where you want to directly use a third-party class that you do not control.

    To do this you override the `create_resource` methods to return a different object.

    .. code-block:: python

        class WriterResource(ConfigurableResource):
            prefix: str

            def create_resource(self, context: InitResourceContext) -> Writer:
                # Writer is pre-existing class defined else
                return Writer(self.prefix)

    Example usage:

    .. code-block:: python

        @asset
        def use_preexisting_writer_as_resource(writer: ResourceParam[Writer]):
            writer.output("text")

        defs = Definitions(
            assets=[use_preexisting_writer_as_resource],
            resources={"writer": WriterResource(prefix="a_prefix")},
        )
    """

    def create_resource(self, context: InitResourceContext) -> TResValue:
        """Returns the object that this resource hands to user code, accessible by ops or assets
        through the context or resource parameters. This works like the function decorated
        with @resource when using function-based resources.

        For ConfigurableResource, this function will return itself, passing
        the actual ConfigurableResource object to user code.
        """
        return cast("TResValue", self)


def _is_fully_configured(resource: "CoercibleToResource") -> bool:
    from dagster._core.execution.build_resources import wrap_resource_for_execution

    actual_resource = wrap_resource_for_execution(resource)
    res = (
        validate_config(
            actual_resource.config_schema.config_type,
            (
                actual_resource.config_schema.default_value
                if actual_resource.config_schema.default_provided
                else {}
            ),
        ).success
        is True
    )

    return res and not isinstance(resource, PartialResource)


class PartialResourceState(NamedTuple):
    nested_partial_resources: dict[str, Any]
    config_schema: DagsterField
    resource_fn: Callable[[InitResourceContext], Any]
    description: Optional[str]
    nested_resources: dict[str, Any]


class PartialResource(
    MakeConfigCacheable,
    Generic[TResValue],
):
    data: dict[str, Any]
    resource_cls: type[Any]

    def __init__(
        self,
        resource_cls: type[ConfigurableResourceFactory[TResValue]],
        data: dict[str, Any],
    ):
        resource_pointers, _data_without_resources = separate_resource_params(resource_cls, data)

        super().__init__(data=data, resource_cls=resource_cls)  # type: ignore  # extends BaseModel, takes kwargs

        def resource_fn(context: InitResourceContext):
            to_populate = resource_cls._get_non_default_public_field_values_cls(  # noqa: SLF001
                {**data, **context.resource_config}
            )
            instantiated = resource_cls(
                **to_populate
            )  # So that collisions are resolved in favor of the latest provided run config
            return instantiated._get_initialize_and_run_fn()(context)  # noqa: SLF001

        self._state__internal__ = PartialResourceState(
            # We keep track of any resources we depend on which are not fully configured
            # so that we can retrieve them at runtime
            nested_partial_resources={
                k: v for k, v in resource_pointers.items() if (not _is_fully_configured(v))
            },
            config_schema=infer_schema_from_config_class(
                resource_cls, fields_to_omit=set(resource_pointers.keys())
            ),
            resource_fn=resource_fn,
            description=resource_cls.__doc__,
            nested_resources={k: v for k, v in resource_pointers.items()},
        )

    # to make AllowDelayedDependencies work
    @property
    def _nested_partial_resources(
        self,
    ) -> Mapping[str, Any]:
        return self._state__internal__.nested_partial_resources

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, Any]:
        return self._state__internal__.nested_resources

    @cached_method  # resource resolution depends on always resolving to the same ResourceDefinition instance
    def get_resource_definition(self) -> ConfigurableResourceFactoryResourceDefinition:
        return ConfigurableResourceFactoryResourceDefinition(
            self.resource_cls,
            resource_fn=self._state__internal__.resource_fn,
            config_schema=self._state__internal__.config_schema,
            description=self._state__internal__.description,
            nested_resources=self.nested_resources,
            nested_partial_resources=self._nested_partial_resources,
            dagster_maintained=self.resource_cls._is_dagster_maintained(),  # noqa: SLF001
        )


ResourceOrPartial: TypeAlias = Union[
    ConfigurableResourceFactory[TResValue], PartialResource[TResValue]
]
ResourceOrPartialOrValue: TypeAlias = Union[
    ConfigurableResourceFactory[TResValue],
    PartialResource[TResValue],
    ResourceDefinition,
    TResValue,
]


V = TypeVar("V")


class ResourceDependency(Generic[V]):
    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, obj: "ConfigurableResourceFactory", owner: Any) -> V:
        return getattr(obj, self._name)

    def __set__(self, obj: Optional[object], value: ResourceOrPartialOrValue[V]) -> None:
        setattr(obj, self._name, value)


class ConfigurableLegacyResourceAdapter(ConfigurableResource, ABC):
    """Adapter base class for wrapping a decorated, function-style resource
    with structured config.

    To use this class, subclass it, define config schema fields using Pydantic,
    and implement the ``wrapped_resource`` method.

    Example:
    .. code-block:: python

        @resource(config_schema={"prefix": str})
        def writer_resource(context):
            prefix = context.resource_config["prefix"]

            def output(text: str) -> None:
                out_txt.append(f"{prefix}{text}")

            return output

        class WriterResource(ConfigurableLegacyResourceAdapter):
            prefix: str

            @property
            def wrapped_resource(self) -> ResourceDefinition:
                return writer_resource
    """

    @property
    @abstractmethod
    def wrapped_resource(self) -> ResourceDefinition:
        raise NotImplementedError()

    @cached_method
    def get_resource_definition(self) -> ConfigurableResourceFactoryResourceDefinition:
        return ConfigurableResourceFactoryResourceDefinition(
            self.__class__,
            resource_fn=self.wrapped_resource.resource_fn,
            config_schema=self._config_schema,
            description=self.__doc__,
            nested_resources=self.nested_resources,
            nested_partial_resources=self._nested_partial_resources,
            dagster_maintained=self._is_dagster_maintained(),
        )

    def __call__(self, *args, **kwargs):
        return self.wrapped_resource(*args, **kwargs)


class SeparatedResourceParams(NamedTuple):
    resources: dict[str, Any]
    non_resources: dict[str, Any]


def _is_annotated_as_resource_type(annotation: type, metadata: list[str]) -> bool:
    """Determines if a field in a structured config class is annotated as a resource type or not."""
    from dagster._config.pythonic_config.type_check_utils import safe_is_subclass

    if metadata and any(m == "resource_dependency" for m in metadata):
        return True

    if is_closed_python_optional_type(annotation):
        args = get_args(annotation)
        annotation_inner = next((arg for arg in args if arg is not None), None)
        if not annotation_inner:
            return False
        return _is_annotated_as_resource_type(annotation_inner, [])

    is_annotated_as_resource_dependency = get_origin(annotation) == ResourceDependency or getattr(
        annotation, "__metadata__", None
    ) == ("resource_dependency",)

    return is_annotated_as_resource_dependency or safe_is_subclass(
        annotation, (ResourceDefinition, ConfigurableResourceFactory)
    )


class ResourceDataWithAnnotation(NamedTuple):
    key: str
    value: Any
    annotation: type
    annotation_metadata: list[str]


def _get_resource_param_fields(cls: type[BaseModel]) -> set[str]:
    """Returns the set of field names in a structured config class which are annotated as resource types."""
    # We need to grab metadata from the annotation in order to tell if
    # this key was annotated with a typing.Annotated annotation (which we use for resource/resource deps),
    # since Pydantic 2.0 strips that info out and sticks any Annotated metadata in the
    # metadata field
    fields_by_resolved_field_name = {
        field.alias if field.alias else key: field for key, field in model_fields(cls).items()
    }

    return {
        field_name
        for field_name in fields_by_resolved_field_name
        if _is_annotated_as_resource_type(
            fields_by_resolved_field_name[field_name].annotation,
            fields_by_resolved_field_name[field_name].metadata,
        )
    }


def separate_resource_params(cls: type[BaseModel], data: dict[str, Any]) -> SeparatedResourceParams:
    """Separates out the key/value inputs of fields in a structured config Resource class which
    are marked as resources (ie, using ResourceDependency) from those which are not.
    """
    nested_resource_field_names = _get_resource_param_fields(cls)

    resources = {}
    non_resources = {}
    for field_name, field_value in data.items():
        if field_name in nested_resource_field_names:
            resources[field_name] = field_value
        else:
            non_resources[field_name] = field_value

    out = SeparatedResourceParams(
        resources=resources,
        non_resources=non_resources,
    )
    return out


def _call_resource_fn_with_default(
    stack: contextlib.ExitStack, obj: ResourceDefinition, context: InitResourceContext
) -> Any:
    from dagster._config.validate import process_config

    if isinstance(obj.config_schema, ConfiguredDefinitionConfigSchema):
        value = cast("dict[str, Any]", obj.config_schema.resolve_config({}).value)
        context = context.replace_config(value["config"])
    elif obj.config_schema.default_provided:
        # To explain why we need to process config here;
        # - The resource available on the init context (context.resource_config) has already been processed
        # - The nested resource's config has also already been processed, but is only available in the broader run config dictionary.
        # - The only information we have access to here is the unprocessed default value, so we need to process it a second time.
        unprocessed_config = obj.config_schema.default_value
        evr = process_config(
            {"config": obj.config_schema.config_type}, {"config": unprocessed_config}
        )
        if not evr.success:
            raise DagsterInvalidConfigError(
                "Error in config for nested resource ",
                evr.errors,
                unprocessed_config,
            )
        context = context.replace_config(cast("dict", evr.value)["config"])

    if has_at_least_one_parameter(obj.resource_fn):
        result = cast("ResourceFunctionWithContext", obj.resource_fn)(context)
    else:
        result = cast("ResourceFunctionWithoutContext", obj.resource_fn)()

    is_fn_generator = (
        inspect.isgenerator(obj.resource_fn)
        or isinstance(obj.resource_fn, contextlib.ContextDecorator)
        or isinstance(result, contextlib.AbstractContextManager)
    )
    if is_fn_generator:
        return stack.enter_context(cast("contextlib.AbstractContextManager", result))
    else:
        return result


LateBoundTypesForResourceTypeChecking.set_actual_types_for_type_checking(
    resource_dep_type=ResourceDependency,
    resource_type=ConfigurableResourceFactory,
    partial_resource_type=PartialResource,
)


def validate_resource_annotated_function(fn) -> None:
    """Validates any parameters on the decorated function that are annotated with
    :py:class:`dagster.ResourceDefinition`, raising a :py:class:`dagster.DagsterInvalidDefinitionError`
    if any are not also instances of :py:class:`dagster.ConfigurableResource` (these resources should
    instead be wrapped in the :py:func:`dagster.Resource` Annotation).
    """
    from dagster import DagsterInvalidDefinitionError
    from dagster._config.pythonic_config.resource import (
        ConfigurableResource,
        ConfigurableResourceFactory,
    )
    from dagster._config.pythonic_config.type_check_utils import safe_is_subclass

    malformed_params = [
        param
        for param in get_function_params(fn)
        if safe_is_subclass(param.annotation, (ResourceDefinition, ConfigurableResourceFactory))
        and not safe_is_subclass(param.annotation, ConfigurableResource)
    ]
    if len(malformed_params) > 0:
        malformed_param = malformed_params[0]
        output_type = None
        if safe_is_subclass(malformed_param.annotation, ConfigurableResourceFactory):
            orig_bases = getattr(malformed_param.annotation, "__orig_bases__", ())
            for base in orig_bases:
                if get_origin(base) is ConfigurableResourceFactory:
                    args = get_args(base)
                    output_type = args[0] if len(args) == 1 else None
                    if output_type == TResValue:
                        output_type = None

        output_type_name = getattr(output_type, "__name__", str(output_type))
        raise DagsterInvalidDefinitionError(
            """Resource param '{param_name}' is annotated as '{annotation_type}', but '{annotation_type}' outputs {value_message} value to user code such as @ops and @assets. This annotation should instead be {annotation_suggestion}""".format(
                param_name=malformed_param.name,
                annotation_type=malformed_param.annotation,
                value_message=f"a '{output_type}'" if output_type else "an unknown",
                annotation_suggestion=(
                    f"'ResourceParam[{output_type_name}]'"
                    if output_type
                    else "'ResourceParam[Any]' or 'ResourceParam[<output type>]'"
                ),
            )
        )


CoercibleToResource: TypeAlias = Union[
    ResourceDefinition, ConfigurableResourceFactory, PartialResource
]


def is_coercible_to_resource(val: Any) -> TypeGuard[CoercibleToResource]:
    return isinstance(val, (ResourceDefinition, ConfigurableResourceFactory, PartialResource))


def coerce_to_resource(val: CoercibleToResource):
    if isinstance(val, ResourceDefinition):
        return val
    else:
        return val.get_resource_definition()


def _resolve_partial_resource_to_key(
    attr_name: str,
    partial_resource: CoercibleToResource,
    resource_defs: Mapping[str, ResourceDefinition],
) -> str:
    partial_def = coerce_to_resource(partial_resource)
    matches = [key for key, resource_def in resource_defs.items() if resource_def is partial_def]
    check.invariant(
        len(matches) == 1,
        f"Failed to find resource for {attr_name}, expected this to be caught when resource requirements where evaluated.",
    )
    return matches[0]


@record
class PartialResourceDependencyRequirement(ResourceRequirement):
    class_name: str
    attr_name: str
    partial_resource: CoercibleToResource

    def is_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]):
        from dagster._config.pythonic_config.resource import coerce_to_resource

        return coerce_to_resource(self.partial_resource) in resource_defs.values()

    def ensure_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]):
        if not self.is_satisfied(resource_defs):
            raise DagsterInvalidDefinitionError(
                f"Failed to resolve resource nested at {self.class_name}.{self.attr_name}. "
                "Any partially configured, nested resources must be provided as a top level resource."
            )


def _get_class_name(cls: type) -> str:
    """Returns the fully qualified class name of the given class."""
    return str(cls)[8:-2]


def get_resource_type_name(resource: ResourceDefinition) -> str:
    """Returns a string that can be used to identify the type of a resource.
    For class-based resources, this is the fully qualified class name.
    For Pythonic resources, this is the module name and resource function name.
    """
    from dagster._config.pythonic_config.io_manager import (
        ConfigurableIOManagerFactoryResourceDefinition,
    )

    if type(resource) in (ResourceDefinition, IOManagerDefinition):
        original_resource_fn = (
            resource._hardcoded_resource_type  # noqa: SLF001
            if resource._hardcoded_resource_type  # noqa: SLF001
            else resource.resource_fn
        )
        module_name = check.not_none(inspect.getmodule(original_resource_fn)).__name__
        resource_type = f"{module_name}.{original_resource_fn.__name__}"
    # if it's a Pythonic resource, get the underlying Pythonic class name
    elif isinstance(
        resource,
        (
            ConfigurableResourceFactoryResourceDefinition,
            ConfigurableIOManagerFactoryResourceDefinition,
        ),
    ):
        resource_type = _get_class_name(resource.configurable_resource_cls)
    else:
        resource_type = _get_class_name(type(resource))
    return resource_type
