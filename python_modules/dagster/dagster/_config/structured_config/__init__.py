import inspect
from typing import (
    AbstractSet,
    Any,
    Dict,
    Generic,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import TypeAlias

from dagster._config.config_type import Array, ConfigFloatInstance, ConfigType
from dagster._config.field_utils import config_dictionary_from_values
from dagster._config.post_process import resolve_defaults
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.structured_config.typing_utils import TypecheckAllowPartialResourceInitParams
from dagster._config.validate import process_config, validate_config
from dagster._core.definitions.definition_config_schema import (
    ConfiguredDefinitionConfigSchema,
    DefinitionConfigSchema,
)
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.execution.context.init import InitResourceContext

try:
    from functools import cached_property  # type: ignore  # (py37 compat)
except ImportError:

    class cached_property:
        pass


from abc import ABC, abstractmethod

from pydantic import BaseModel, Extra
from pydantic.fields import SHAPE_DICT, SHAPE_LIST, SHAPE_MAPPING, SHAPE_SINGLETON, ModelField

import dagster._check as check
from dagster import Field, Selector, Shape
from dagster._config.field_utils import (
    FIELD_NO_DEFAULT_PROVIDED,
    Map,
    Permissive,
    convert_potential_field,
)
from dagster._core.definitions.resource_definition import (
    ResourceDefinition,
    ResourceFunction,
    ResourceFunctionWithContext,
    ResourceFunctionWithoutContext,
    has_at_least_one_parameter,
)
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition

from .typing_utils import BaseResourceMeta, LateBoundTypesForResourceTypeChecking
from .utils import safe_is_subclass

Self = TypeVar("Self", bound="ConfigurableResource")


class MakeConfigCacheable(BaseModel):
    """This class centralizes and implements all the chicanery we need in order
    to support caching decorators. If we decide this is a bad idea we can remove it
    all in one go.
    """

    # Pydantic config for this class
    # Cannot use kwargs for base class as this is not support for pydnatic<1.8
    class Config:
        # Various pydantic model config (https://docs.pydantic.dev/usage/model_config/)
        # Necessary to allow for caching decorators
        arbitrary_types_allowed = True
        # Avoid pydantic reading a cached property class as part of the schema
        keep_untouched = (cached_property,)
        # Ensure the class is serializable, for caching purposes
        frozen = True

    def __setattr__(self, name: str, value: Any):
        # This is a hack to allow us to set attributes on the class that are not part of the
        # config schema. Pydantic will normally raise an error if you try to set an attribute
        # that is not part of the schema.

        if name.startswith("_") or name.endswith("_cache"):
            object.__setattr__(self, name, value)
            return

        return super().__setattr__(name, value)


class Config(MakeConfigCacheable):
    """
    Base class for Dagster configuration models.
    """

    def __init__(self, **config_dict):
        """
        This constructor is overridden to handle any remapping of raw config dicts to
        the appropriate config classes. For example, discriminated unions are represented
        in Dagster config as dicts with a single key, which is the discriminator value.
        """
        modified_data = {}
        for key, value in config_dict.items():
            field = self.__fields__.get(key)
            if field and field.field_info.discriminator:
                nested_items = list(check.is_dict(value).items())
                check.invariant(
                    len(nested_items) == 1, "Discriminated union must have exactly one key"
                )
                discriminated_value, nested_values = nested_items[0]

                modified_data[key] = {
                    **nested_values,
                    field.discriminator_key: discriminated_value,
                }
            else:
                modified_data[key] = value
        super().__init__(**modified_data)

    def _as_config_dict(self) -> Mapping[str, Any]:
        """
        Returns a dictionary representation of this config object,
        ignoring any private fields.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class PermissiveConfig(Config):
    # Pydantic config for this class
    # Cannot use kwargs for base class as this is not support for pydantic<1.8
    class Config:
        extra = "allow"

    """
    Base class for Dagster configuration models that allow arbitrary extra fields.
    """


# This is from https://github.com/dagster-io/dagster/pull/11470
def _apply_defaults_to_schema_field(field: Field, additional_default_values: Any) -> Field:
    # This work by validating the top-level config and then
    # just setting it at that top-level field. Config fields
    # can actually take nested values so we only need to set it
    # at a single level

    evr = validate_config(field.config_type, additional_default_values)

    if not evr.success:
        raise DagsterInvalidConfigError(
            "Incorrect values passed to .configured",
            evr.errors,
            additional_default_values,
        )

    if field.default_provided:
        # In the case where there is already a default config value
        # we can apply "additional" defaults by actually invoking
        # the config machinery. Meaning we pass the new_additional_default_values
        # and then resolve the existing defaults over them. This preserves the default
        # values that are not specified in new_additional_default_values and then
        # applies the new value as the default value of the field in question.
        defaults_processed_evr = resolve_defaults(field.config_type, additional_default_values)
        check.invariant(
            defaults_processed_evr.success, "Since validation passed, this should always work."
        )
        default_to_pass = defaults_processed_evr.value
        return copy_with_default(field, default_to_pass)
    else:
        return copy_with_default(field, additional_default_values)


def copy_with_default(old_field: Field, new_config_value: Any) -> Field:
    return Field(
        config=old_field.config_type,
        default_value=new_config_value,
        is_required=False,
        description=old_field.description,
    )


def _process_config_values(
    schema_field: Field, data: Mapping[str, Any], config_obj_name: str
) -> Mapping[str, Any]:
    post_processed_config = process_config(
        schema_field.config_type, config_dictionary_from_values(data, schema_field)
    )

    if not post_processed_config.success:
        raise DagsterInvalidConfigError(
            "Error while processing {} config ".format(config_obj_name),
            post_processed_config.errors,
            data,
        )
    assert post_processed_config.value is not None

    return post_processed_config.value or {}


def _curry_config_schema(schema_field: Field, data: Any) -> DefinitionConfigSchema:
    """Return a new config schema configured with the passed in data"""
    return DefinitionConfigSchema(_apply_defaults_to_schema_field(schema_field, data))


TResValue = TypeVar("TResValue")
TIOManagerValue = TypeVar("TIOManagerValue", bound=IOManager)

ResourceId: TypeAlias = int


def _resolve_required_resource_keys_for_resource(
    resource: ResourceDefinition, resource_id_to_key_mapping: Mapping[ResourceId, str]
) -> AbstractSet[str]:
    """
    Gets the required resource keys for the provided resource, with the assistance of the passed
    resource-id-to-key mapping. For resources which may hold nested partial resources,
    this mapping is used to obtain the top-level resource keys to depend on.
    """
    if isinstance(resource, AllowDelayedDependencies):
        return resource._resolve_required_resource_keys(resource_id_to_key_mapping)
    return resource.required_resource_keys


class AllowDelayedDependencies:
    _nested_partial_resources: Mapping[str, ResourceDefinition] = {}

    def _resolve_required_resource_keys(
        self, resource_mapping: Mapping[int, str]
    ) -> AbstractSet[str]:
        # All dependent resources which are not fully configured
        # must be specified to the Definitions object so that the
        # resource can be configured at runtime by the user
        nested_partial_resource_keys = {
            attr_name: resource_mapping.get(id(resource_def))
            for attr_name, resource_def in self._nested_partial_resources.items()
        }
        check.invariant(
            all(pointer_key is not None for pointer_key in nested_partial_resource_keys.values()),
            (
                "Any partially configured, nested resources must be provided to Definitions"
                f" object: {nested_partial_resource_keys}"
            ),
        )

        # Recursively get all nested resource keys
        nested_resource_required_keys: Set[str] = set()
        for v in self._nested_partial_resources.values():
            nested_resource_required_keys.update(
                _resolve_required_resource_keys_for_resource(v, resource_mapping)
            )

        resources, _ = _separate_resource_params(self.__dict__)
        for v in resources.values():
            nested_resource_required_keys.update(
                _resolve_required_resource_keys_for_resource(v, resource_mapping)
            )

        out = set(cast(Set[str], nested_partial_resource_keys.values())).union(
            nested_resource_required_keys
        )
        return out


class InitResourceContextWithKeyMapping(InitResourceContext):
    """
    Passes along a mapping from ResourceDefinition id to resource key alongside the
    InitResourceContext. This is used to resolve the required resource keys for
    resources which may hold nested partial resources.
    """

    def __init__(
        self,
        context: InitResourceContext,
        resource_id_to_key_mapping: Mapping[ResourceId, str],
    ):
        super().__init__(
            resource_config=context.resource_config,
            resources=context.resources,
            instance=context.instance,
            resource_def=context.resource_def,
            dagster_run=context.dagster_run,
            log_manager=context.log,
        )
        self._resource_id_to_key_mapping = resource_id_to_key_mapping
        self._resources_by_id = {
            resource_id: getattr(context.resources, resource_key, None)
            for resource_id, resource_key in resource_id_to_key_mapping.items()
        }

    @property
    def resources_by_id(self) -> Mapping[ResourceId, Any]:
        return self._resources_by_id

    def replace_config(self, config: Any) -> "InitResourceContext":
        return InitResourceContextWithKeyMapping(
            super().replace_config(config), self._resource_id_to_key_mapping
        )


class ResourceWithKeyMapping(ResourceDefinition):
    """
    Wrapper around a ResourceDefinition which helps the inner resource resolve its required
    resource keys. This is useful for resources which may hold nested resources. At construction
    time, they are unaware of the resource keys of their nested resources - the resource id to
    key mapping is used to resolve this.
    """

    def __init__(
        self, resource: ResourceDefinition, resource_id_to_key_mapping: Dict[ResourceId, str]
    ):
        self._resource = resource
        self._resource_id_to_key_mapping = resource_id_to_key_mapping

        ResourceDefinition.__init__(
            self,
            resource_fn=self.setup_context_resources_and_call,
            config_schema=resource.config_schema,
            description=resource.description,
            version=resource.version,
        )

    def setup_context_resources_and_call(self, context: InitResourceContext):
        """
        Wrapper around the wrapped resource's resource_fn which attaches its
        resource id to key mapping to the context, and then calls the nested resource's resource_fn.
        """
        context_with_key_mapping = InitResourceContextWithKeyMapping(
            context, self._resource_id_to_key_mapping
        )

        if has_at_least_one_parameter(self._resource.resource_fn):
            return self._resource.resource_fn(context_with_key_mapping)
        else:
            return cast(ResourceFunctionWithoutContext, self._resource.resource_fn)()

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return _resolve_required_resource_keys_for_resource(
            self._resource, self._resource_id_to_key_mapping
        )


class IOManagerWithKeyMapping(ResourceWithKeyMapping, IOManagerDefinition):
    """
    Version of ResourceWithKeyMapping wrapper that also implements IOManagerDefinition.
    """

    def __init__(
        self, resource: ResourceDefinition, resource_id_to_key_mapping: Dict[ResourceId, str]
    ):
        ResourceWithKeyMapping.__init__(self, resource, resource_id_to_key_mapping)
        IOManagerDefinition.__init__(
            self, resource_fn=self.resource_fn, config_schema=resource.config_schema
        )


def attach_resource_id_to_key_mapping(
    resource_def: Any, resource_id_to_key_mapping: Dict[ResourceId, str]
) -> Any:
    if isinstance(resource_def, (ConfigurableResource, PartialResource)):
        return (
            IOManagerWithKeyMapping(resource_def, resource_id_to_key_mapping)
            if isinstance(resource_def, IOManagerDefinition)
            else ResourceWithKeyMapping(resource_def, resource_id_to_key_mapping)
        )
    return resource_def


class ConfigurableResource(
    Generic[TResValue],
    ResourceDefinition,
    Config,
    TypecheckAllowPartialResourceInitParams,
    AllowDelayedDependencies,
    metaclass=BaseResourceMeta,
):
    """
    Base class for Dagster resources that utilize structured config.

    This class is a subclass of both :py:class:`ResourceDefinition` and :py:class:`Config`, and
    provides a default implementation of the resource_fn that returns the resource itself.

    Example:
    .. code-block:: python

        class WriterResource(ConfigurableResource):
            prefix: str

            def output(self, text: str) -> None:
                print(f"{self.prefix}{text}")

    """

    def __init__(self, **data: Any):
        resource_pointers, data_without_resources = _separate_resource_params(data)

        schema = infer_schema_from_config_class(
            self.__class__, fields_to_omit=set(resource_pointers.keys())
        )

        # Resolve e.g. EnvVar values
        resolved_config_dict = config_dictionary_from_values(data_without_resources, schema)
        curried_schema = _curry_config_schema(schema, resolved_config_dict)

        Config.__init__(self, **{**data_without_resources, **resource_pointers})

        # We keep track of any resources we depend on which are not fully configured
        # so that we can retrieve them at runtime
        self._nested_partial_resources: Mapping[str, ResourceDefinition] = {
            k: v for k, v in resource_pointers.items() if (not _is_fully_configured(v))
        }

        ResourceDefinition.__init__(
            self,
            resource_fn=self.initialize_and_run,
            config_schema=curried_schema,
            description=self.__doc__,
        )
        self._resolved_config_dict = resolved_config_dict
        self._schema = schema

    @classmethod
    def configure_at_launch(cls: "Type[Self]", **kwargs) -> "PartialResource[Self]":
        """
        Returns a partially initialized copy of the resource, with remaining config fields
        set at runtime.
        """
        return PartialResource(cls, data=kwargs)

    def _with_updated_values(self, values: Mapping[str, Any]) -> "ConfigurableResource[TResValue]":
        """
        Returns a new instance of the resource with the given values.
        Used when initializing a resource at runtime.
        """
        # Since Resource extends BaseModel and is a dataclass, we know that the
        # signature of any __init__ method will always consist of the fields
        # of this class. We can therefore safely pass in the values as kwargs.
        return self.__class__(**{**self._as_config_dict(), **values})

    def _resolve_and_update_env_vars(self) -> "ConfigurableResource[TResValue]":
        """
        Processes the config dictionary to resolve any EnvVar values. This is called at runtime
        when the resource is initialized, so the user is only shown the error if they attempt to
        kick off a run relying on this resource.

        Returns a new instance of the resource.
        """
        post_processed_data = _process_config_values(
            self._schema, self._resolved_config_dict, self.__class__.__name__
        )
        return self._with_updated_values(post_processed_data)

    def _resolve_and_update_nested_resources(
        self, context: InitResourceContext
    ) -> "ConfigurableResource[TResValue]":
        """
        Updates any nested resources with the resource values from the context.
        In this case, populating partially configured resources or
        resources that return plain Python types.

        Returns a new instance of the resource.
        """
        partial_resources_to_update: Dict[str, Any] = {}
        if self._nested_partial_resources:
            context_with_mapping = cast(
                InitResourceContextWithKeyMapping,
                check.inst(
                    context,
                    InitResourceContextWithKeyMapping,
                    (
                        "This ConfiguredResource contains unresolved partially-specified nested"
                        " resources, and so can only be initialized using a"
                        " InitResourceContextWithKeyMapping"
                    ),
                ),
            )
            partial_resources_to_update = {
                attr_name: context_with_mapping.resources_by_id[id(resource_def)]
                for attr_name, resource_def in self._nested_partial_resources.items()
            }

        # Also evaluate any resources that are not partial
        resources_to_update, _ = _separate_resource_params(self.__dict__)
        resources_to_update = {
            attr_name: _call_resource_fn_with_default(resource_def, context)
            for attr_name, resource_def in resources_to_update.items()
            if attr_name not in partial_resources_to_update
        }

        to_update = {**resources_to_update, **partial_resources_to_update}
        return self._with_updated_values(to_update)

    def initialize_and_run(self, context: InitResourceContext) -> TResValue:
        with_nested_resources = self._resolve_and_update_nested_resources(context)
        with_env_vars = with_nested_resources._resolve_and_update_env_vars()

        return with_env_vars._create_object_fn(context)

    def _create_object_fn(self, context: InitResourceContext) -> TResValue:
        return self.create_resource(context)

    def create_resource(
        self, context: InitResourceContext
    ) -> TResValue:  # pylint: disable=unused-argument
        """
        Returns the object that this resource hands to user code, accessible by ops or assets
        through the context or resource parameters. This works like the function decorated
        with @resource when using function-based resources.

        Default behavior for new class-based resources is to return itself, passing
        the actual resource object to user code.
        """
        return cast(TResValue, self)


def _is_fully_configured(resource: ResourceDefinition) -> bool:
    res = (
        validate_config(
            resource.config_schema.config_type,
            resource.config_schema.default_value if resource.config_schema.default_provided else {},
        ).success
        is True
    )

    return res


class PartialResource(
    Generic[TResValue], ResourceDefinition, AllowDelayedDependencies, MakeConfigCacheable
):
    data: Dict[str, Any]
    resource_cls: Type[ConfigurableResource[TResValue]]

    def __init__(self, resource_cls: Type[ConfigurableResource[TResValue]], data: Dict[str, Any]):
        resource_pointers, data_without_resources = _separate_resource_params(data)

        MakeConfigCacheable.__init__(self, data=data, resource_cls=resource_cls)  # type: ignore  # extends BaseModel, takes kwargs

        # We keep track of any resources we depend on which are not fully configured
        # so that we can retrieve them at runtime
        self._nested_partial_resources: Dict[str, ResourceDefinition] = {
            k: v for k, v in resource_pointers.items() if (not _is_fully_configured(v))
        }

        schema = infer_schema_from_config_class(
            resource_cls, fields_to_omit=set(resource_pointers.keys())
        )

        def resource_fn(context: InitResourceContext):
            instantiated = resource_cls(**context.resource_config, **data)
            return instantiated.initialize_and_run(context)

        ResourceDefinition.__init__(
            self,
            resource_fn=resource_fn,
            config_schema=schema,
            description=resource_cls.__doc__,
        )


ResourceOrPartial: TypeAlias = Union[ConfigurableResource[TResValue], PartialResource[TResValue]]
ResourceOrPartialOrValue: TypeAlias = Union[
    ConfigurableResource[TResValue], PartialResource[TResValue], ResourceDefinition, TResValue
]


V = TypeVar("V")


class ResourceDependency(Generic[V]):
    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, obj: "ConfigurableResource", __owner: Any) -> V:
        return getattr(obj, self._name)

    def __set__(self, obj: Optional[object], value: ResourceOrPartialOrValue[V]) -> None:
        setattr(obj, self._name, value)


class ConfigurableLegacyResourceAdapter(ConfigurableResource, ABC):
    """
    Adapter base class for wrapping a decorated, function-style resource
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

    @property
    def resource_fn(self) -> ResourceFunction:
        return self.wrapped_resource.resource_fn

    def __call__(self, *args, **kwargs):
        return self.wrapped_resource(*args, **kwargs)


class ConfigurableIOManagerFactory(ConfigurableResource[TIOManagerValue], IOManagerDefinition):
    """
    Base class for Dagster IO managers that utilize structured config. This base class
    is useful for cases in which the returned IO manager is not the same as the class itself
    (e.g. when it is a wrapper around the actual IO manager implementation).

    This class is a subclass of both :py:class:`IOManagerDefinition` and :py:class:`Config`.
    Implementers should provide an implementation of the :py:meth:`resource_function` method,
    which should return an instance of :py:class:`IOManager`.
    """

    def __init__(self, **data: Any):
        ConfigurableResource.__init__(self, **data)
        IOManagerDefinition.__init__(
            self,
            resource_fn=self.initialize_and_run,
            config_schema=self._config_schema,
            description=self.__doc__,
        )

    def _create_object_fn(self, context: InitResourceContext) -> TIOManagerValue:
        return self.create_io_manager(context)

    @abstractmethod
    def create_io_manager(self, context) -> TIOManagerValue:
        """Implement as one would implement a @io_manager decorator function"""
        raise NotImplementedError()

    @classmethod
    def configure_at_launch(cls: "Type[Self]", **kwargs) -> "PartialIOManager[Self]":
        """
        Returns a partially initialized copy of the IO manager, with remaining config fields
        set at runtime.
        """
        return PartialIOManager(cls, data=kwargs)


class PartialIOManager(Generic[TResValue], PartialResource[TResValue], IOManagerDefinition):
    def __init__(self, resource_cls: Type[ConfigurableResource[TResValue]], data: Dict[str, Any]):
        PartialResource.__init__(self, resource_cls, data)
        IOManagerDefinition.__init__(
            self,
            resource_fn=self._resource_fn,
            config_schema=self._config_schema,
            description=resource_cls.__doc__,
        )


class ConfigurableIOManager(ConfigurableIOManagerFactory, IOManager):
    """
    Base class for Dagster IO managers that utilize structured config.

    This class is a subclass of both :py:class:`IOManagerDefinition`, :py:class:`Config`,
    and :py:class:`IOManager`. Implementers must provide an implementation of the
    :py:meth:`handle_output` and :py:meth:`load_input` methods.
    """

    def create_io_manager(self, context) -> IOManager:
        return self


PydanticShapeType: TypeAlias = int

MAPPING_TYPES = {SHAPE_MAPPING, SHAPE_DICT}
MAPPING_KEY_TYPE_TO_SCALAR = {
    StringSource: str,
    IntSource: int,
    BoolSource: bool,
    ConfigFloatInstance: float,
}


def _wrap_config_type(
    shape_type: PydanticShapeType, key_type: Optional[ConfigType], config_type: ConfigType
) -> ConfigType:
    """
    Based on a Pydantic shape type, wraps a config type in the appropriate Dagster config wrapper.
    For example, if the shape type is a Pydantic list, the config type will be wrapped in an Array.
    """
    if shape_type == SHAPE_SINGLETON:
        return config_type
    elif shape_type == SHAPE_LIST:
        return Array(config_type)
    elif shape_type in MAPPING_TYPES:
        if key_type not in MAPPING_KEY_TYPE_TO_SCALAR:
            raise NotImplementedError(
                f"Pydantic shape type is a mapping, but key type {key_type} is not a valid "
                "Map key type. Valid Map key types are: "
                f"{', '.join([str(t) for t in MAPPING_KEY_TYPE_TO_SCALAR.keys()])}."
            )
        return Map(MAPPING_KEY_TYPE_TO_SCALAR[key_type], config_type)
    else:
        raise NotImplementedError(f"Pydantic shape type {shape_type} not supported.")


def _convert_pydantic_field(pydantic_field: ModelField) -> Field:
    """
    Transforms a Pydantic field into a corresponding Dagster config field.
    """
    key_type = (
        _config_type_for_pydantic_field(pydantic_field.key_field)
        if pydantic_field.key_field
        else None
    )
    if pydantic_field.field_info.discriminator:
        return _convert_pydantic_descriminated_union_field(pydantic_field)

    if safe_is_subclass(pydantic_field.type_, Config):
        inferred_field = infer_schema_from_config_class(
            pydantic_field.type_,
            description=pydantic_field.field_info.description,
        )
        wrapped_config_type = _wrap_config_type(
            shape_type=pydantic_field.shape,
            config_type=inferred_field.config_type,
            key_type=key_type,
        )

        return Field(config=wrapped_config_type, description=inferred_field.description)
    else:
        config_type = _config_type_for_pydantic_field(pydantic_field)
        wrapped_config_type = _wrap_config_type(
            shape_type=pydantic_field.shape, config_type=config_type, key_type=key_type
        )
        return Field(
            config=wrapped_config_type,
            description=pydantic_field.field_info.description,
            is_required=_is_pydantic_field_required(pydantic_field),
            default_value=pydantic_field.default
            if pydantic_field.default
            else FIELD_NO_DEFAULT_PROVIDED,
        )


def _config_type_for_pydantic_field(pydantic_field: ModelField) -> ConfigType:
    return _config_type_for_type_on_pydantic_field(pydantic_field.type_)


def _config_type_for_type_on_pydantic_field(potential_dagster_type: Any) -> ConfigType:
    # special case raw python literals to their source equivalents
    if potential_dagster_type is str:
        return StringSource
    elif potential_dagster_type is int:
        return IntSource
    elif potential_dagster_type is bool:
        return BoolSource
    else:
        return convert_potential_field(potential_dagster_type).config_type


def _is_pydantic_field_required(pydantic_field: ModelField) -> bool:
    # required is of type BoolUndefined = Union[bool, UndefinedType] in Pydantic
    if isinstance(pydantic_field.required, bool):
        return pydantic_field.required

    raise Exception(
        "pydantic.field.required is their UndefinedType sentinel value which we "
        "do not fully understand the semantics of right now. For the time being going "
        "to throw an error to figure see when we actually encounter this state."
    )


class ConfigurableLegacyIOManagerAdapter(ConfigurableIOManagerFactory):
    """
    Adapter base class for wrapping a decorated, function-style I/O manager
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

    @property
    def resource_fn(self) -> ResourceFunction:
        return self.wrapped_io_manager.resource_fn


def _convert_pydantic_descriminated_union_field(pydantic_field: ModelField) -> Field:
    """
    Builds a Selector config field from a Pydantic field which is a descriminated union.

    For example:

    class Cat(Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(Config):
        pet_type: Literal["dog"]
        barks: float

    class OpConfigWithUnion(Config):
        pet: Union[Cat, Dog] = Field(..., discriminator="pet_type")

    Becomes:

    Shape({
      "pet": Selector({
          "cat": Shape({"meows": Int}),
          "dog": Shape({"barks": Float}),
      })
    })
    """
    sub_fields_mapping = pydantic_field.sub_fields_mapping
    if not sub_fields_mapping or not all(
        issubclass(pydantic_field.type_, Config) for pydantic_field in sub_fields_mapping.values()
    ):
        raise NotImplementedError("Descriminated unions with non-Config types are not supported.")

    # First, we generate a mapping between the various discriminator values and the
    # Dagster config fields that correspond to them. We strip the discriminator key
    # from the fields, since the user should not have to specify it.

    assert pydantic_field.sub_fields_mapping
    dagster_config_field_mapping = {
        discriminator_value: infer_schema_from_config_class(
            field.type_,
            fields_to_omit={pydantic_field.field_info.discriminator}
            if pydantic_field.field_info.discriminator
            else None,
        )
        for discriminator_value, field in sub_fields_mapping.items()
    }

    # We then nest the union fields under a Selector. The keys for the selector
    # are the various discriminator values
    return Field(config=Selector(fields=dagster_config_field_mapping))


def infer_schema_from_config_annotation(model_cls: Any, config_arg_default: Any) -> Field:
    """
    Parses a structured config class or primitive type and returns a corresponding Dagster config Field.
    """
    if safe_is_subclass(model_cls, Config):
        check.invariant(
            config_arg_default is inspect.Parameter.empty,
            "Cannot provide a default value when using a Config class",
        )
        return infer_schema_from_config_class(model_cls)

    # If were are here config is annotated with a primitive type
    # We do a conversion to a type as if it were a type on a pydantic field
    inner_config_type = _config_type_for_type_on_pydantic_field(model_cls)
    return Field(
        config=inner_config_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED
        if config_arg_default is inspect.Parameter.empty
        else config_arg_default,
    )


def infer_schema_from_config_class(
    model_cls: Type[Config],
    description: Optional[str] = None,
    fields_to_omit: Optional[Set[str]] = None,
) -> Field:
    """
    Parses a structured config class and returns a corresponding Dagster config Field.
    """
    fields_to_omit = fields_to_omit or set()

    check.param_invariant(
        safe_is_subclass(model_cls, Config),
        "Config type annotation must inherit from dagster._config.structured_config.Config",
    )

    fields = {}
    for pydantic_field in model_cls.__fields__.values():
        if pydantic_field.name not in fields_to_omit:
            fields[pydantic_field.alias] = _convert_pydantic_field(pydantic_field)

    shape_cls = Permissive if model_cls.__config__.extra == Extra.allow else Shape

    docstring = model_cls.__doc__.strip() if model_cls.__doc__ else None
    return Field(config=shape_cls(fields), description=description or docstring)


class SeparatedResourceParams(NamedTuple):
    resources: Dict[str, ResourceDefinition]
    non_resources: Dict[str, Any]


def _separate_resource_params(data: Dict[str, Any]) -> SeparatedResourceParams:
    """
    Separates out the key/value inputs of fields in a structured config Resource class which
    are themselves Resources and those which are not.
    """
    return SeparatedResourceParams(
        resources={k: v for k, v in data.items() if isinstance(v, ResourceDefinition)},
        non_resources={k: v for k, v in data.items() if not isinstance(v, ResourceDefinition)},
    )


def _call_resource_fn_with_default(obj: ResourceDefinition, context: InitResourceContext) -> Any:
    if isinstance(obj.config_schema, ConfiguredDefinitionConfigSchema):
        value = cast(Dict[str, Any], obj.config_schema.resolve_config({}).value)
        context = context.replace_config(value["config"])
    elif obj.config_schema.default_provided:
        context = context.replace_config(obj.config_schema.default_value)
    if has_at_least_one_parameter(obj.resource_fn):
        return cast(ResourceFunctionWithContext, obj.resource_fn)(context)
    else:
        return cast(ResourceFunctionWithoutContext, obj.resource_fn)()


LateBoundTypesForResourceTypeChecking.set_actual_types_for_type_checking(
    resource_dep_type=ResourceDependency,
    resource_type=ConfigurableResource,
    partial_resource_type=PartialResource,
)
