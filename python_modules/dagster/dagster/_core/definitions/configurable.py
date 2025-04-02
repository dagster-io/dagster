from abc import ABC, abstractmethod
from typing import Any, Callable, NamedTuple, Optional, TypeVar, Union, cast

from typing_extensions import Self

import dagster._check as check
from dagster._config import EvaluateValueResult
from dagster._config.config_schema import UserConfigSchema
from dagster._config.field import Field
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.definition_config_schema import (
    CoercableToConfigSchema,
    ConfiguredDefinitionConfigSchema,
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)


class ConfigurableDefinition(ABC):
    @property
    @abstractmethod
    def config_schema(self) -> Optional[IDefinitionConfigSchema]:
        raise NotImplementedError()

    @property
    def has_config_field(self) -> bool:
        return self.config_schema is not None and bool(self.config_schema.as_field())

    @property
    def config_field(self) -> Optional[Field]:
        return None if not self.config_schema else self.config_schema.as_field()

    # getter for typed access
    def get_config_field(self) -> Field:
        field = self.config_field
        if field is None:
            check.failed("Must check has_config_Field before calling get_config_field")
        return field

    def apply_config_mapping(self, config: Any) -> EvaluateValueResult:
        """Applies user-provided config mapping functions to the given configuration and validates the
        results against the respective config schema.

        Expects incoming config to be validated and have fully-resolved values (StringSource values
        resolved, Enum types hydrated, etc.) via process_config() during ResolvedRunConfig
        construction and Graph config mapping.

        Args:
            config (Any): A validated and resolved configuration dictionary matching this object's
            config_schema

        Returns (EvaluateValueResult):
            If successful, the value is a validated and resolved configuration dictionary for the
            innermost wrapped object after applying the config mapping transformation function.
        """
        # If schema is on a mapped schema this is the innermost resource (base case),
        # so we aren't responsible for validating against anything farther down.
        # Returns an EVR for type consistency with config_mapping_fn.
        return (
            self.config_schema.resolve_config(config)
            if isinstance(self.config_schema, ConfiguredDefinitionConfigSchema)
            else EvaluateValueResult.for_value(config)
        )


class AnonymousConfigurableDefinition(ConfigurableDefinition):
    """An interface that makes the `configured` method not accept a name argument."""

    def configured(
        self,
        config_or_config_fn: Any,
        config_schema: CoercableToConfigSchema = None,
        description: Optional[str] = None,
    ) -> Self:
        """Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Using ``configured`` may result in config values being displayed in
        the Dagster UI, so it is not recommended to use this API with sensitive values,
        such as secrets.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            description (Optional[str]): Description of the new definition. If not specified,
                inherits the description of the definition being configured.

        Returns (ConfigurableDefinition): A configured version of this object.
        """
        new_config_schema = ConfiguredDefinitionConfigSchema(
            self, convert_user_facing_definition_config_schema(config_schema), config_or_config_fn
        )

        return self.copy_for_configured(description, new_config_schema)

    @abstractmethod
    def copy_for_configured(
        self,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
    ) -> Self:
        raise NotImplementedError()


class NamedConfigurableDefinition(ConfigurableDefinition):
    """An interface that makes the `configured` method require a positional `name` argument."""

    def configured(
        self,
        config_or_config_fn: Any,
        name: str,
        config_schema: Optional[UserConfigSchema] = None,
        description: Optional[str] = None,
    ) -> Self:
        """Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Using ``configured`` may result in config values being displayed in
        the Dagster UI, so it is not recommended to use this API with sensitive values,
        such as secrets.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            name (str): Name of the new definition. This is a required argument, as this definition
                type has a name uniqueness constraint.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            description (Optional[str]): Description of the new definition. If not specified,
                inherits the description of the definition being configured.

        Returns (ConfigurableDefinition): A configured version of this object.
        """
        name = check.str_param(name, "name")

        new_config_schema = ConfiguredDefinitionConfigSchema(
            self, convert_user_facing_definition_config_schema(config_schema), config_or_config_fn
        )

        return self.copy_for_configured(name, description, new_config_schema)

    @abstractmethod
    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
    ) -> Self: ...


def _check_configurable_param(configurable: ConfigurableDefinition) -> None:
    from dagster._core.definitions.composition import PendingNodeInvocation

    check.param_invariant(
        not isinstance(configurable, PendingNodeInvocation),
        "configurable",
        "You have invoked `configured` on a PendingNodeInvocation (an intermediate type), which"
        " is produced by aliasing or tagging a node definition. To configure a node, you must"
        " call `configured` on either an OpDefinition and GraphDefinition. To fix"
        " this error, make sure to call `configured` on the definition object *before* using"
        " the `tag` or `alias` methods. For usage examples, see"
        " https://legacy-docs.dagster.io/concepts/configuration/configured",
    )
    from dagster._config.pythonic_config import ConfigurableResourceFactory, safe_is_subclass

    if safe_is_subclass(configurable, ConfigurableResourceFactory):
        return
    else:
        check.inst_param(
            configurable,
            "configurable",
            ConfigurableDefinition,
            "Only the following types can be used with the `configured` method: ResourceDefinition,"
            " ExecutorDefinition, GraphDefinition, NodeDefinition, and LoggerDefinition."
            " For usage examples of `configured`, see"
            " https://legacy-docs.dagster.io/concepts/configuration/configured",
        )


T_Configurable = TypeVar(
    "T_Configurable", bound=Union["AnonymousConfigurableDefinition", "NamedConfigurableDefinition"]
)


class FunctionAndConfigSchema(NamedTuple):
    function: Callable[[Any], Any]
    config_schema: Optional[UserConfigSchema]


def _wrap_user_fn_if_pythonic_config(
    user_fn: Any, config_schema: Optional[UserConfigSchema]
) -> FunctionAndConfigSchema:
    """Helper function which allows users to provide a Pythonic config object to a @configurable
    function. Detects if the function has a single parameter annotated with a Config class.
    If so, wraps the function to convert the config dictionary into the appropriate Config object.
    """
    from dagster._config.pythonic_config import (
        Config,
        infer_schema_from_config_annotation,
        safe_is_subclass,
    )

    if not isinstance(user_fn, Callable):
        return FunctionAndConfigSchema(function=user_fn, config_schema=config_schema)

    config_fn_params = get_function_params(user_fn)
    check.invariant(
        len(config_fn_params) == 1, "@configured function should have exactly one parameter"
    )

    param = config_fn_params[0]

    # If the parameter is a subclass of Config, we can infer the config schema from the
    # type annotation. We'll also wrap the config mapping function to convert the config
    # dictionary into the appropriate Config object.
    if not safe_is_subclass(param.annotation, Config):
        return FunctionAndConfigSchema(function=user_fn, config_schema=config_schema)

    check.invariant(
        config_schema is None,
        "Cannot provide config_schema to @configured function with Config-annotated param",
    )

    config_schema_from_class = infer_schema_from_config_annotation(param.annotation, param.default)
    config_cls = cast(type[Config], param.annotation)

    param_name = param.name

    def wrapped_fn(config_as_dict) -> Any:
        config_input = config_cls(**config_as_dict)
        output = user_fn(**{param_name: config_input})

        if isinstance(output, Config):
            return output._convert_to_config_dictionary()  # noqa: SLF001
        else:
            return output

    return FunctionAndConfigSchema(function=wrapped_fn, config_schema=config_schema_from_class)


def configured(
    configurable: T_Configurable,
    config_schema: Optional[UserConfigSchema] = None,
    **kwargs: Any,
) -> Callable[[object], T_Configurable]:
    """A decorator that makes it easy to create a function-configured version of an object.

    The following definition types can be configured using this function:

    * :py:class:`GraphDefinition`
    * :py:class:`ExecutorDefinition`
    * :py:class:`LoggerDefinition`
    * :py:class:`ResourceDefinition`
    * :py:class:`OpDefinition`

    Using ``configured`` may result in config values being displayed in the Dagster UI,
    so it is not recommended to use this API with sensitive values, such as
    secrets.

    If the config that will be supplied to the object is constant, you may alternatively invoke this
    and call the result with a dict of config values to be curried. Examples of both strategies
    below.

    Args:
        configurable (ConfigurableDefinition): An object that can be configured.
        config_schema (ConfigSchema): The config schema that the inputs to the decorated function
            must satisfy. Alternatively, annotate the config parameter to the decorated function
            with a subclass of :py:class:`Config` and omit this argument.
        **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the returned
            object.

    Returns:
        (Callable[[Union[Any, Callable[[Any], Any]]], ConfigurableDefinition])

    **Examples:**

    .. code-block:: python

        class GreetingConfig(Config):
            message: str

        @op
        def greeting_op(config: GreetingConfig):
            print(config.message)

        class HelloConfig(Config):
            name: str

        @configured(greeting_op)
        def hello_op(config: HelloConfig):
            return GreetingConfig(message=f"Hello, {config.name}!")

    .. code-block:: python

        dev_s3 = configured(S3Resource, name="dev_s3")({'bucket': 'dev'})

        @configured(S3Resource)
        def dev_s3(_):
            return {'bucket': 'dev'}

        @configured(S3Resource, {'bucket_prefix', str})
        def dev_s3(config):
            return {'bucket': config['bucket_prefix'] + 'dev'}

    """
    _check_configurable_param(configurable)

    from dagster._config.pythonic_config import ConfigurableResourceFactory, safe_is_subclass
    from dagster._core.definitions.resource_definition import ResourceDefinition

    # we specially handle ConfigurableResources, treating it as @configured of the
    # underlying resource definition (which is indeed a ConfigurableDefinition)
    if safe_is_subclass(configurable, ConfigurableResourceFactory):
        configurable_inner = cast(
            ResourceDefinition,
            (
                cast(type[ConfigurableResourceFactory], configurable)
                .configure_at_launch()
                .get_resource_definition()
            ),
        )
        return configured(configurable_inner, config_schema=config_schema, **kwargs)  # type: ignore

    if isinstance(configurable, NamedConfigurableDefinition):

        def _configured(config_or_config_fn: object) -> T_Configurable:
            fn_name = (
                getattr(config_or_config_fn, "__name__", None)
                if callable(config_or_config_fn)
                else None
            )
            name: str = check.not_none(kwargs.get("name") or fn_name)

            updated_fn, new_config_schema = _wrap_user_fn_if_pythonic_config(
                config_or_config_fn, config_schema
            )
            return configurable.configured(
                config_or_config_fn=updated_fn,
                name=name,
                config_schema=new_config_schema,
                **{k: v for k, v in kwargs.items() if k != "name"},
            )

        return _configured
    elif isinstance(configurable, AnonymousConfigurableDefinition):

        def _configured(config_or_config_fn: object) -> T_Configurable:
            updated_fn, new_config_schema = _wrap_user_fn_if_pythonic_config(
                config_or_config_fn, config_schema
            )
            return configurable.configured(
                config_schema=new_config_schema, config_or_config_fn=updated_fn, **kwargs
            )

        return _configured
    else:
        check.failed(f"Invalid configurable definition type: {type(configurable)}")
