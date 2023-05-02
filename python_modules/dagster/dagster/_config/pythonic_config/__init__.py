import contextlib
import inspect
import re
from enum import Enum
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from pydantic import ConstrainedFloat, ConstrainedInt, ConstrainedStr
from typing_extensions import TypeAlias, TypeGuard, get_args

from dagster import (
    Enum as DagsterEnum,
    Field as DagsterField,
)
from dagster._config.config_type import (
    Array,
    ConfigFloatInstance,
    ConfigType,
    EnumValue,
    Noneable,
)
from dagster._config.field_utils import config_dictionary_from_values
from dagster._config.post_process import resolve_defaults
from dagster._config.pythonic_config.typing_utils import (
    TypecheckAllowPartialResourceInitParams,
)
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.validate import process_config, validate_config
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.definition_config_schema import (
    CoercableToConfigSchema,
    ConfiguredDefinitionConfigSchema,
    DefinitionConfigSchema,
)
from dagster._core.errors import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidPythonicConfigDefinitionError,
)
from dagster._core.execution.context.init import InitResourceContext
from dagster._utils.cached_method import CACHED_METHOD_FIELD_SUFFIX, cached_method

from .attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)

try:
    from functools import cached_property  # type: ignore  # (py37 compat)
except ImportError:

    class cached_property:
        pass


from abc import ABC, abstractmethod

from pydantic import BaseModel, Extra
from pydantic.fields import (
    SHAPE_DICT,
    SHAPE_LIST,
    SHAPE_MAPPING,
    SHAPE_SINGLETON,
    ModelField,
)

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

Self = TypeVar("Self", bound="ConfigurableResourceFactory")

INTERNAL_MARKER = "__internal__"

# ensure that this ends with the internal marker so we can do a single check
assert CACHED_METHOD_FIELD_SUFFIX.endswith(INTERNAL_MARKER)


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

        if self._is_field_internal(name):
            object.__setattr__(self, name, value)
            return

        try:
            return super().__setattr__(name, value)
        except (TypeError, ValueError) as e:
            clsname = self.__class__.__name__
            if "is immutable and does not support item assignment" in str(e):
                if isinstance(self, ConfigurableResourceFactory):
                    raise DagsterInvalidInvocationError(
                        f"'{clsname}' is a Pythonic resource and does not support item assignment,"
                        " as it inherits from 'pydantic.BaseModel' with frozen=True. If trying to"
                        " maintain state on this resource, consider building a separate, stateful"
                        " client class, and provide a method on the resource to construct and"
                        " return the stateful client."
                    ) from e
                else:
                    raise DagsterInvalidInvocationError(
                        f"'{clsname}' is a Pythonic config class and does not support item"
                        " assignment, as it inherits from 'pydantic.BaseModel' with frozen=True."
                    ) from e
            elif "object has no field" in str(e):
                field_name = check.not_none(
                    re.search(r"object has no field \"(.*)\"", str(e))
                ).group(1)
                if isinstance(self, ConfigurableResourceFactory):
                    raise DagsterInvalidInvocationError(
                        f"'{clsname}' is a Pythonic resource and does not support manipulating"
                        f" undeclared attribute '{field_name}' as it inherits from"
                        " 'pydantic.BaseModel' without extra=\"allow\". If trying to maintain"
                        " state on this resource, consider building a separate, stateful client"
                        " class, and provide a method on the resource to construct and return the"
                        " stateful client."
                    ) from e
                else:
                    raise DagsterInvalidInvocationError(
                        f"'{clsname}' is a Pythonic config class and does not support manipulating"
                        f" undeclared attribute '{field_name}' as it inherits from"
                        " 'pydantic.BaseModel' without extra=\"allow\"."
                    ) from e
            else:
                raise

    def _is_field_internal(self, name: str) -> bool:
        return name.endswith(INTERNAL_MARKER)


class Config(MakeConfigCacheable):
    """Base class for Dagster configuration models, used to specify config schema for
    ops and assets. Subclasses :py:class:`pydantic.BaseModel`.

    Example definition:

    .. code-block:: python

        from pydantic import Field

        class MyAssetConfig(Config):
            my_str: str = "my_default_string"
            my_int_list: List[int]
            my_bool_with_metadata: bool = Field(default=False, description="A bool field")


    Example usage:

    .. code-block:: python

        @asset
        def asset_with_config(config: MyAssetConfig):
            assert config.my_str == "my_default_string"
            assert config.my_int_list == [1, 2, 3]
            assert config.my_bool_with_metadata == False

        asset_with_config(MyAssetConfig(my_int_list=[1, 2, 3], my_bool_with_metadata=True))

    """

    def __init__(self, **config_dict) -> None:
        """This constructor is overridden to handle any remapping of raw config dicts to
        the appropriate config classes. For example, discriminated unions are represented
        in Dagster config as dicts with a single key, which is the discriminator value.
        """
        modified_data = {}
        for key, value in config_dict.items():
            field = self.__fields__.get(key)
            if field and field.field_info.discriminator:
                nested_dict = value

                discriminator_key = check.not_none(field.discriminator_key)
                if isinstance(value, Config):
                    nested_dict = _discriminated_union_config_dict_to_selector_config_dict(
                        discriminator_key,
                        value._get_non_none_public_field_values(),  # noqa: SLF001
                    )

                nested_items = list(check.is_dict(nested_dict).items())
                check.invariant(
                    len(nested_items) == 1,
                    "Discriminated union must have exactly one key",
                )
                discriminated_value, nested_values = nested_items[0]

                modified_data[key] = {
                    **nested_values,
                    discriminator_key: discriminated_value,
                }
            else:
                modified_data[key] = value
        super().__init__(**modified_data)

    def _convert_to_config_dictionary(self) -> Mapping[str, Any]:
        """Converts this Config object to a Dagster config dictionary, in the same format as the dictionary
        accepted as run config or as YAML in the launchpad.

        Inner fields are recursively converted to dictionaries, meaning nested config objects
        or EnvVars will be converted to the appropriate dictionary representation.
        """
        public_fields = self._get_non_none_public_field_values()
        return {
            k: _config_value_to_dict_representation(self.__fields__.get(k), v)
            for k, v in public_fields.items()
        }

    def _get_non_none_public_field_values(self) -> Mapping[str, Any]:
        """Returns a dictionary representation of this config object,
        ignoring any private fields, and any optional fields that are None.

        Inner fields are returned as-is in the dictionary,
        meaning any nested config objects will be returned as config objects, not dictionaries.
        """
        output = {}
        for key, value in self.__dict__.items():
            if self._is_field_internal(key):
                continue
            field = self.__fields__.get(key)
            if field and value is None and not _is_pydantic_field_required(field):
                continue

            if field:
                output[field.alias] = value
            else:
                output[key] = value
        return output

    @classmethod
    def to_config_schema(cls) -> DefinitionConfigSchema:
        """Converts the config structure represented by this class into a DefinitionConfigSchema."""
        return DefinitionConfigSchema(infer_schema_from_config_class(cls))

    @classmethod
    def to_fields_dict(cls) -> Dict[str, DagsterField]:
        """Converts the config structure represented by this class into a dictionary of dagster.Fields.
        This is useful when interacting with legacy code that expects a dictionary of fields but you
        want the source of truth to be a config class.
        """
        return cast(Shape, cls.to_config_schema().as_field().config_type).fields


def _discriminated_union_config_dict_to_selector_config_dict(
    discriminator_key: str, config_dict: Mapping[str, Any]
):
    """Remaps a config dictionary which is a member of a discriminated union to
    the appropriate structure for a Dagster config selector.

    A discriminated union with key "my_key" and value "my_value" will be represented
    as {"my_key": "my_value", "my_field": "my_field_value"}. When converted to a selector,
    this should be represented as {"my_value": {"my_field": "my_field_value"}}.
    """
    updated_dict = dict(config_dict)
    discriminator_value = updated_dict.pop(discriminator_key)
    wrapped_dict = {discriminator_value: updated_dict}
    return wrapped_dict


def _config_value_to_dict_representation(field: Optional[ModelField], value: Any):
    """Converts a config value to a dictionary representation. If a field is provided, it will be used
    to determine the appropriate dictionary representation in the case of discriminated unions.
    """
    from dagster._config.field_utils import EnvVar, IntEnvVar

    if isinstance(value, dict):
        return {k: _config_value_to_dict_representation(None, v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_config_value_to_dict_representation(None, v) for v in value]
    elif isinstance(value, EnvVar):
        return {"env": str(value)}
    elif isinstance(value, IntEnvVar):
        return {"env": value.name}
    if isinstance(value, Config):
        if field and field.discriminator_key:
            return {
                k: v
                for k, v in _discriminated_union_config_dict_to_selector_config_dict(
                    field.discriminator_key,
                    value._convert_to_config_dictionary(),  # noqa: SLF001
                ).items()
            }
        else:
            return {k: v for k, v in value._convert_to_config_dictionary().items()}  # noqa: SLF001
    elif isinstance(value, Enum):
        return value.name

    return value


class PermissiveConfig(Config):
    """Subclass of :py:class:`Config` that allows arbitrary extra fields. This is useful for
    config classes which may have open-ended inputs.

    Example definition:

    .. code-block:: python

        class MyPermissiveOpConfig(PermissiveConfig):
            my_explicit_parameter: bool
            my_other_explicit_parameter: str


    Example usage:

    .. code-block:: python

        @op
        def op_with_config(config: MyPermissiveOpConfig):
            assert config.my_explicit_parameter == True
            assert config.my_other_explicit_parameter == "foo"
            assert config.dict().get("my_implicit_parameter") == "bar"

        op_with_config(
            MyPermissiveOpConfig(
                my_explicit_parameter=True,
                my_other_explicit_parameter="foo",
                my_implicit_parameter="bar"
            )
        )

    """

    # Pydantic config for this class
    # Cannot use kwargs for base class as this is not support for pydantic<1.8
    class Config:
        extra = "allow"


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
            defaults_processed_evr.success,
            "Since validation passed, this should always work.",
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
            f"Error while processing {config_obj_name} config ",
            post_processed_config.errors,
            data,
        )
    assert post_processed_config.value is not None

    return post_processed_config.value or {}


def _curry_config_schema(schema_field: Field, data: Any) -> DefinitionConfigSchema:
    """Return a new config schema configured with the passed in data."""
    return DefinitionConfigSchema(_apply_defaults_to_schema_field(schema_field, data))


TResValue = TypeVar("TResValue")
TIOManagerValue = TypeVar("TIOManagerValue", bound=IOManager)

ResourceId: TypeAlias = int


def _resolve_required_resource_keys_for_resource(
    resource: ResourceDefinition, resource_id_to_key_mapping: Mapping[ResourceId, str]
) -> AbstractSet[str]:
    """Gets the required resource keys for the provided resource, with the assistance of the passed
    resource-id-to-key mapping. For resources which may hold nested partial resources,
    this mapping is used to obtain the top-level resource keys to depend on.
    """
    if isinstance(resource, AllowDelayedDependencies):
        return resource._resolve_required_resource_keys(resource_id_to_key_mapping)  # noqa: SLF001
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

        resources, _ = separate_resource_params(self.__dict__)
        for v in resources.values():
            nested_resource_required_keys.update(
                _resolve_required_resource_keys_for_resource(
                    coerce_to_resource(v), resource_mapping
                )
            )

        out = set(cast(Set[str], nested_partial_resource_keys.values())).union(
            nested_resource_required_keys
        )
        return out


class InitResourceContextWithKeyMapping(InitResourceContext):
    """Passes along a mapping from ResourceDefinition id to resource key alongside the
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
    """Wrapper around a ResourceDefinition which helps the inner resource resolve its required
    resource keys. This is useful for resources which may hold nested resources. At construction
    time, they are unaware of the resource keys of their nested resources - the resource id to
    key mapping is used to resolve this.
    """

    def __init__(
        self,
        resource: ResourceDefinition,
        resource_id_to_key_mapping: Dict[ResourceId, str],
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
        """Wrapper around the wrapped resource's resource_fn which attaches its
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

    @property
    def wrapped_resource(self) -> ResourceDefinition:
        return self._resource

    @property
    def inner_resource(self):
        return self._resource


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


def attach_resource_id_to_key_mapping(
    resource_def: Any, resource_id_to_key_mapping: Dict[ResourceId, str]
) -> Any:
    if isinstance(resource_def, (ConfigurableResourceFactory, PartialResource)):
        defn = resource_def.get_resource_definition()
        return (
            IOManagerWithKeyMapping(defn, resource_id_to_key_mapping)
            if isinstance(defn, IOManagerDefinition)
            else ResourceWithKeyMapping(defn, resource_id_to_key_mapping)
        )
    return resource_def


CoercibleToResource: TypeAlias = Union[
    ResourceDefinition, "ConfigurableResourceFactory", "PartialResource"
]


def is_coercible_to_resource(val: Any) -> TypeGuard[CoercibleToResource]:
    return isinstance(val, (ResourceDefinition, ConfigurableResourceFactory, PartialResource))


def coerce_to_resource(
    coercible_to_resource: CoercibleToResource,
) -> ResourceDefinition:
    if isinstance(coercible_to_resource, (ConfigurableResourceFactory, PartialResource)):
        return coercible_to_resource.get_resource_definition()
    return coercible_to_resource


class ConfigurableResourceFactoryResourceDefinition(ResourceDefinition, AllowDelayedDependencies):
    def __init__(
        self,
        resource_fn: ResourceFunction,
        config_schema: Any,
        description: Optional[str],
        resolve_resource_keys: Callable[[Mapping[int, str]], AbstractSet[str]],
        nested_resources: Mapping[str, CoercibleToResource],
    ):
        super().__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
        )
        self._resolve_resource_keys = resolve_resource_keys
        self._nested_resources = nested_resources

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, CoercibleToResource]:
        return self._nested_resources

    def _resolve_required_resource_keys(
        self, resource_mapping: Mapping[int, str]
    ) -> AbstractSet[str]:
        return self._resolve_resource_keys(resource_mapping)


class ConfigurableIOManagerFactoryResourceDefinition(IOManagerDefinition, AllowDelayedDependencies):
    def __init__(
        self,
        resource_fn: ResourceFunction,
        config_schema: Any,
        description: Optional[str],
        resolve_resource_keys: Callable[[Mapping[int, str]], AbstractSet[str]],
        nested_resources: Mapping[str, CoercibleToResource],
        input_config_schema: Optional[Union[CoercableToConfigSchema, Type[Config]]] = None,
        output_config_schema: Optional[Union[CoercableToConfigSchema, Type[Config]]] = None,
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

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, CoercibleToResource]:
        return self._nested_resources

    def _resolve_required_resource_keys(
        self, resource_mapping: Mapping[int, str]
    ) -> AbstractSet[str]:
        return self._resolve_resource_keys(resource_mapping)


class ConfigurableResourceFactoryState(NamedTuple):
    nested_partial_resources: Mapping[str, CoercibleToResource]
    resolved_config_dict: Dict[str, Any]
    config_schema: DefinitionConfigSchema
    schema: DagsterField
    nested_resources: Dict[str, CoercibleToResource]
    resource_context: Optional[InitResourceContext]


class ConfigurableResourceFactory(
    Generic[TResValue],
    Config,
    TypecheckAllowPartialResourceInitParams,
    AllowDelayedDependencies,
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
    * A class with expensive initialization that should not be invoked on code location load, but rather lazily on first use in an op or asset during a run.
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
        resource_pointers, data_without_resources = separate_resource_params(data)

        schema = infer_schema_from_config_class(
            self.__class__, fields_to_omit=set(resource_pointers.keys())
        )

        # Populate config values
        Config.__init__(self, **{**data_without_resources, **resource_pointers})

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
    def _is_cm_resource_cls(cls: Type["ConfigurableResourceFactory"]) -> bool:
        return (
            cls.yield_for_execution != ConfigurableResourceFactory.yield_for_execution
            or cls.teardown_after_execution != ConfigurableResourceFactory.teardown_after_execution
        )

    @property
    def _is_cm_resource(self) -> bool:
        return self.__class__._is_cm_resource_cls()  # noqa: SLF001

    def _get_initialize_and_run_fn(self) -> Callable:
        return self._initialize_and_run_cm if self._is_cm_resource else self._initialize_and_run

    @cached_method
    def get_resource_definition(self) -> ConfigurableResourceFactoryResourceDefinition:
        return ConfigurableResourceFactoryResourceDefinition(
            resource_fn=self._get_initialize_and_run_fn(),
            config_schema=self._config_schema,
            description=self.__doc__,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
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
    ) -> Mapping[str, CoercibleToResource]:
        return self._nested_resources

    @classmethod
    def configure_at_launch(cls: "Type[Self]", **kwargs) -> "PartialResource[Self]":
        """Returns a partially initialized copy of the resource, with remaining config fields
        set at runtime.
        """
        return PartialResource(cls, data=kwargs)

    def _with_updated_values(
        self, values: Mapping[str, Any]
    ) -> "ConfigurableResourceFactory[TResValue]":
        """Returns a new instance of the resource with the given values.
        Used when initializing a resource at runtime.
        """
        # Since Resource extends BaseModel and is a dataclass, we know that the
        # signature of any __init__ method will always consist of the fields
        # of this class. We can therefore safely pass in the values as kwargs.
        out = self.__class__(**{**self._get_non_none_public_field_values(), **values})
        out._state__internal__ = out._state__internal__._replace(  # noqa: SLF001
            resource_context=self._state__internal__.resource_context
        )
        return out

    def _resolve_and_update_env_vars(self) -> "ConfigurableResourceFactory[TResValue]":
        """Processes the config dictionary to resolve any EnvVar values. This is called at runtime
        when the resource is initialized, so the user is only shown the error if they attempt to
        kick off a run relying on this resource.

        Returns a new instance of the resource.
        """
        post_processed_data = _process_config_values(
            self._schema, self._resolved_config_dict, self.__class__.__name__
        )
        return self._with_updated_values(post_processed_data)

    @contextlib.contextmanager
    def _resolve_and_update_nested_resources(
        self, context: InitResourceContext
    ) -> Generator["ConfigurableResourceFactory[TResValue]", None, None]:
        """Updates any nested resources with the resource values from the context.
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
                attr_name: context_with_mapping.resources_by_id[id(resource)]
                for attr_name, resource in self._nested_partial_resources.items()
            }

        # Also evaluate any resources that are not partial
        with contextlib.ExitStack() as stack:
            resources_to_update, _ = separate_resource_params(self.__dict__)
            resources_to_update = {
                attr_name: _call_resource_fn_with_default(
                    stack, coerce_to_resource(resource), context
                )
                for attr_name, resource in resources_to_update.items()
                if attr_name not in partial_resources_to_update
            }

            to_update = {**resources_to_update, **partial_resources_to_update}
            yield self._with_updated_values(to_update)

    def with_resource_context(
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
            updated_resource = has_nested_resource.with_resource_context(  # noqa: SLF001
                context
            )._resolve_and_update_env_vars()

            updated_resource.setup_for_execution(context)
            return updated_resource.create_resource(context)

    @contextlib.contextmanager
    def _initialize_and_run_cm(
        self, context: InitResourceContext
    ) -> Generator[TResValue, None, None]:
        with self._resolve_and_update_nested_resources(context) as has_nested_resource:
            updated_resource = has_nested_resource.with_resource_context(  # noqa: SLF001
                context
            )._resolve_and_update_env_vars()

            with updated_resource.yield_for_execution(context) as value:
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

    @classmethod
    def from_resource_context(cls, context: InitResourceContext) -> TResValue:
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
            (
                "Use from_resource_context_cm for resources which have custom teardown behavior,"
                " e.g. overriding yield_for_execution or teardown_after_execution"
            ),
        )
        return cls(**context.resource_config or {})._initialize_and_run(context)  # noqa: SLF001

    @classmethod
    @contextlib.contextmanager
    def from_resource_context_cm(
        cls, context: InitResourceContext
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
        with cls(**context.resource_config or {})._initialize_and_run_cm(  # noqa: SLF001
            context
        ) as value:
            yield value


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

    """

    def create_resource(self, context: InitResourceContext) -> TResValue:
        """Returns the object that this resource hands to user code, accessible by ops or assets
        through the context or resource parameters. This works like the function decorated
        with @resource when using function-based resources.

        For ConfigurableResource, this function will return itself, passing
        the actual ConfigurableResource object to user code.
        """
        return cast(TResValue, self)


def _is_fully_configured(resource: CoercibleToResource) -> bool:
    actual_resource = coerce_to_resource(resource)
    res = (
        validate_config(
            actual_resource.config_schema.config_type,
            actual_resource.config_schema.default_value
            if actual_resource.config_schema.default_provided
            else {},
        ).success
        is True
    )

    return res


class PartialResourceState(NamedTuple):
    nested_partial_resources: Dict[str, CoercibleToResource]
    config_schema: DagsterField
    resource_fn: Callable[[InitResourceContext], Any]
    description: Optional[str]
    nested_resources: Dict[str, CoercibleToResource]


class PartialResource(Generic[TResValue], AllowDelayedDependencies, MakeConfigCacheable):
    data: Dict[str, Any]
    resource_cls: Type[ConfigurableResourceFactory[TResValue]]

    def __init__(
        self,
        resource_cls: Type[ConfigurableResourceFactory[TResValue]],
        data: Dict[str, Any],
    ):
        resource_pointers, _data_without_resources = separate_resource_params(data)

        MakeConfigCacheable.__init__(self, data=data, resource_cls=resource_cls)  # type: ignore  # extends BaseModel, takes kwargs

        def resource_fn(context: InitResourceContext):
            instantiated = resource_cls(**context.resource_config, **data)
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
    ) -> Mapping[str, CoercibleToResource]:
        return self._state__internal__.nested_partial_resources

    @property
    def nested_resources(
        self,
    ) -> Mapping[str, CoercibleToResource]:
        return self._state__internal__.nested_resources

    @cached_method
    def get_resource_definition(self) -> ConfigurableResourceFactoryResourceDefinition:
        return ConfigurableResourceFactoryResourceDefinition(
            resource_fn=self._state__internal__.resource_fn,
            config_schema=self._state__internal__.config_schema,
            description=self._state__internal__.description,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
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

    def __get__(self, obj: "ConfigurableResourceFactory", __owner: Any) -> V:
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
            resource_fn=self.wrapped_resource.resource_fn,
            config_schema=self._config_schema,
            description=self.__doc__,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
        )

    def __call__(self, *args, **kwargs):
        return self.wrapped_resource(*args, **kwargs)


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
            resource_fn=self._get_initialize_and_run_fn(),
            config_schema=self._config_schema,
            description=self.__doc__,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
            input_config_schema=self.__class__.input_config_schema(),
            output_config_schema=self.__class__.output_config_schema(),
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
            resource_fn=self._state__internal__.resource_fn,
            config_schema=self._state__internal__.config_schema,
            description=self._state__internal__.description,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self._state__internal__.nested_resources,
            input_config_schema=input_config_schema,
            output_config_schema=output_config_schema,
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


PydanticShapeType: TypeAlias = int

MAPPING_TYPES = {SHAPE_MAPPING, SHAPE_DICT}
MAPPING_KEY_TYPE_TO_SCALAR = {
    StringSource: str,
    IntSource: int,
    BoolSource: bool,
    ConfigFloatInstance: float,
}


def _wrap_config_type(
    shape_type: PydanticShapeType,
    key_type: Optional[ConfigType],
    config_type: ConfigType,
) -> ConfigType:
    """Based on a Pydantic shape type, wraps a config type in the appropriate Dagster config wrapper.
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


def _get_inner_field_if_exists(
    shape_type: PydanticShapeType, field: ModelField
) -> Optional[ModelField]:
    """Grabs the inner Pydantic field type for a data structure such as a list or dictionary.

    Returns None for types which have no inner field.
    """
    # See https://github.com/pydantic/pydantic/blob/v1.10.3/pydantic/fields.py#L758 for
    # where sub_fields is set.
    if shape_type == SHAPE_SINGLETON:
        return None
    elif shape_type == SHAPE_LIST:
        # List has a single subfield, which is the type of the list elements.
        return check.not_none(field.sub_fields)[0]
    elif shape_type in MAPPING_TYPES:
        # Mapping has a single subfield, which is the type of the mapping values.
        return check.not_none(field.sub_fields)[0]
    else:
        raise NotImplementedError(f"Pydantic shape type {shape_type} not supported.")


def _convert_pydantic_field(pydantic_field: ModelField, model_cls: Optional[Type] = None) -> Field:
    """Transforms a Pydantic field into a corresponding Dagster config field.


    Args:
        pydantic_field (ModelField): The Pydantic field to convert.
        model_cls (Optional[Type]): The Pydantic model class that the field belongs to. This is
            used for error messages.
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
        return Field(
            config=Noneable(wrapped_config_type)
            if pydantic_field.allow_none
            else wrapped_config_type,
            description=inferred_field.description,
            is_required=_is_pydantic_field_required(pydantic_field),
        )
    else:
        # For certain data structure types, we need to grab the inner Pydantic field (e.g. List type)
        inner_field = _get_inner_field_if_exists(pydantic_field.shape, pydantic_field)
        if inner_field:
            config_type = _convert_pydantic_field(inner_field, model_cls=model_cls).config_type
        else:
            config_type = _config_type_for_pydantic_field(pydantic_field)

        wrapped_config_type = _wrap_config_type(
            shape_type=pydantic_field.shape, config_type=config_type, key_type=key_type
        )

        return Field(
            config=Noneable(wrapped_config_type)
            if pydantic_field.allow_none
            else wrapped_config_type,
            description=pydantic_field.field_info.description,
            is_required=_is_pydantic_field_required(pydantic_field),
            default_value=pydantic_field.default
            if pydantic_field.default is not None
            else FIELD_NO_DEFAULT_PROVIDED,
        )


def _config_type_for_pydantic_field(pydantic_field: ModelField) -> ConfigType:
    """Generates a Dagster ConfigType from a Pydantic field.

    Args:
        pydantic_field (ModelField): The Pydantic field to convert.
    """
    return _config_type_for_type_on_pydantic_field(
        pydantic_field.type_,
    )


def _config_type_for_type_on_pydantic_field(
    potential_dagster_type: Any,
) -> ConfigType:
    """Generates a Dagster ConfigType from a Pydantic field's Python type.

    Args:
        potential_dagster_type (Any): The Python type of the Pydantic field.
    """
    # special case pydantic constrained types to their source equivalents
    if safe_is_subclass(potential_dagster_type, ConstrainedStr):
        return StringSource
    # no FloatSource, so we just return float
    elif safe_is_subclass(potential_dagster_type, ConstrainedFloat):
        potential_dagster_type = float
    elif safe_is_subclass(potential_dagster_type, ConstrainedInt):
        return IntSource

    if safe_is_subclass(potential_dagster_type, Enum):
        return DagsterEnum(
            potential_dagster_type.__name__,
            [
                EnumValue(v.name, python_value=v.value)
                for v in cast(Iterable[Enum], potential_dagster_type)
            ],
        )

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
            resource_fn=self.wrapped_io_manager.resource_fn,
            config_schema=self._config_schema,
            description=self.__doc__,
            resolve_resource_keys=self._resolve_required_resource_keys,
            nested_resources=self.nested_resources,
        )


def _convert_pydantic_descriminated_union_field(pydantic_field: ModelField) -> Field:
    """Builds a Selector config field from a Pydantic field which is a descriminated union.

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
    """Parses a structured config class or primitive type and returns a corresponding Dagster config Field.
    """
    if safe_is_subclass(model_cls, Config):
        check.invariant(
            config_arg_default is inspect.Parameter.empty,
            "Cannot provide a default value when using a Config class",
        )
        return infer_schema_from_config_class(model_cls)

    # If were are here config is annotated with a primitive type
    # We do a conversion to a type as if it were a type on a pydantic field
    try:
        inner_config_type = _config_type_for_type_on_pydantic_field(model_cls)
    except (DagsterInvalidDefinitionError, DagsterInvalidConfigDefinitionError):
        raise DagsterInvalidPythonicConfigDefinitionError(
            invalid_type=model_cls, config_class=None, field_name=None
        )
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
    """Parses a structured config class and returns a corresponding Dagster config Field."""
    fields_to_omit = fields_to_omit or set()

    check.param_invariant(
        safe_is_subclass(model_cls, Config),
        "Config type annotation must inherit from dagster.Config",
    )

    fields = {}
    for pydantic_field in model_cls.__fields__.values():
        if pydantic_field.name not in fields_to_omit:
            if isinstance(pydantic_field.default, Field):
                raise DagsterInvalidDefinitionError(
                    "Using 'dagster.Field' is not supported within a Pythonic config or resource"
                    " definition. 'dagster.Field' should only be used in legacy Dagster config"
                    " schemas. Did you mean to use 'pydantic.Field' instead?"
                )

            try:
                fields[pydantic_field.alias] = _convert_pydantic_field(
                    pydantic_field,
                )
            except DagsterInvalidConfigDefinitionError as e:
                raise DagsterInvalidPythonicConfigDefinitionError(
                    config_class=model_cls,
                    field_name=pydantic_field.name,
                    invalid_type=e.current_value,
                    is_resource=model_cls is not None
                    and safe_is_subclass(model_cls, ConfigurableResourceFactory),
                )

    shape_cls = Permissive if model_cls.__config__.extra == Extra.allow else Shape

    docstring = model_cls.__doc__.strip() if model_cls.__doc__ else None
    return Field(config=shape_cls(fields), description=description or docstring)


class SeparatedResourceParams(NamedTuple):
    resources: Dict[str, CoercibleToResource]
    non_resources: Dict[str, Any]


def separate_resource_params(data: Dict[str, Any]) -> SeparatedResourceParams:
    """Separates out the key/value inputs of fields in a structured config Resource class which
    are themselves Resources and those which are not.
    """
    return SeparatedResourceParams(
        resources={k: v for k, v in data.items() if is_coercible_to_resource(v)},
        non_resources={k: v for k, v in data.items() if not is_coercible_to_resource(v)},
    )


def _call_resource_fn_with_default(
    stack: contextlib.ExitStack, obj: ResourceDefinition, context: InitResourceContext
) -> Any:
    if isinstance(obj.config_schema, ConfiguredDefinitionConfigSchema):
        value = cast(Dict[str, Any], obj.config_schema.resolve_config({}).value)
        context = context.replace_config(value["config"])
    elif obj.config_schema.default_provided:
        context = context.replace_config(obj.config_schema.default_value)

    is_fn_generator = inspect.isgenerator(obj.resource_fn) or isinstance(
        obj.resource_fn, contextlib.ContextDecorator
    )
    if has_at_least_one_parameter(obj.resource_fn):  # type: ignore[unreachable]
        result = cast(ResourceFunctionWithContext, obj.resource_fn)(context)
    else:
        result = cast(ResourceFunctionWithoutContext, obj.resource_fn)()

    if is_fn_generator:
        return stack.enter_context(cast(contextlib.AbstractContextManager, result))
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
    from dagster._config.pythonic_config import (
        ConfigurableResource,
        ConfigurableResourceFactory,
        TResValue,
    )
    from dagster._config.pythonic_config.utils import safe_is_subclass

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
            orig_bases = getattr(malformed_param.annotation, "__orig_bases__", None)
            output_type = get_args(orig_bases[0])[0] if orig_bases and len(orig_bases) > 0 else None
            if output_type == TResValue:
                output_type = None

        output_type_name = getattr(output_type, "__name__", str(output_type))
        raise DagsterInvalidDefinitionError(
            """Resource param '{param_name}' is annotated as '{annotation_type}', but '{annotation_type}' outputs {value_message} value to user code such as @ops and @assets. This annotation should instead be {annotation_suggestion}""".format(
                param_name=malformed_param.name,
                annotation_type=malformed_param.annotation,
                value_message=f"a '{output_type}'" if output_type else "an unknown",
                annotation_suggestion=f"'ResourceParam[{output_type_name}]'"
                if output_type
                else "'ResourceParam[Any]' or 'ResourceParam[<output type>]'",
            )
        )
