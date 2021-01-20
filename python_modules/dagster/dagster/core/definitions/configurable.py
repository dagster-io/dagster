from abc import ABC, abstractmethod, abstractproperty

from dagster import check
from dagster.config.evaluate_value_result import EvaluateValueResult
from dagster.core.errors import DagsterInvalidDefinitionError

from .definition_config_schema import (
    ConfiguredDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)


class ConfigurableDefinition(ABC):
    @abstractproperty
    def config_schema(self):
        raise NotImplementedError()

    @property
    def has_config_field(self):
        return self.config_schema and bool(self.config_schema.as_field())

    @property
    def config_field(self):
        return None if not self.config_schema else self.config_schema.as_field()

    @abstractmethod
    def copy_for_configured(self, name, description, config_schema, config_or_config_fn):
        raise NotImplementedError()

    def apply_config_mapping(self, config):
        """
        Applies user-provided config mapping functions to the given configuration and validates the
        results against the respective config schema.

        Expects incoming config to be validated and have fully-resolved values (StringSource values
        resolved, Enum types hydrated, etc.) via process_config() during EnvironmentConfig
        construction and CompositeSolid config mapping.

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

    def configured(self, config_or_config_fn, config_schema=None, name=None, description=None):
        """
        Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            name (Optional[str]): Name of the new definition. If not specified, inherits the name
                of the definition being configured. Note: some definitions (e.g. ResourceDefinition)
                are unnamed and this will error if a name is passed.
            description (Optional[str]): Name of the new definition. If not specified, inherits the name
                of the definition being configured.

        Returns (ConfigurableDefinition): A configured version of this object.
        """

        new_config_schema = ConfiguredDefinitionConfigSchema(
            self, convert_user_facing_definition_config_schema(config_schema), config_or_config_fn
        )

        return self.copy_for_configured(name, description, new_config_schema, config_or_config_fn)

    def _name_for_configured_node(self, old_name, new_name, original_config_or_config_fn):
        fn_name = (
            original_config_or_config_fn.__name__
            if callable(original_config_or_config_fn)
            else None
        )
        name = new_name or fn_name
        if not name:
            raise DagsterInvalidDefinitionError(
                'Missing string param "name" while attempting to configure the node '
                '"{node_name}". When configuring a node, you must specify a name for the '
                "resulting node definition as a keyword param or use `configured` in decorator "
                "form. For examples, visit https://docs.dagster.io/overview/configuration#configured.".format(
                    node_name=old_name,
                )
            )
        return name


def _check_configurable_param(configurable):
    from dagster.core.definitions.composition import CallableNode

    check.param_invariant(
        not isinstance(configurable, CallableNode),
        "configurable",
        (
            "You have invoked `configured` on a CallableNode (an intermediate type), which is "
            "produced by aliasing or tagging a solid definition. To configure a solid, you must "
            "call `configured` on either a SolidDefinition and CompositeSolidDefinition. To fix "
            "this error, make sure to call `configured` on the definition object *before* using "
            "the `tag` or `alias` methods. For usage examples, see "
            "https://docs.dagster.io/overview/configuration#configured"
        ),
    )
    check.inst_param(
        configurable,
        "configurable",
        ConfigurableDefinition,
        (
            "Only the following types can be used with the `configured` method: ResourceDefinition, "
            "ExecutorDefinition, CompositeSolidDefinition, SolidDefinition, LoggerDefinition, "
            "and IntermediateStorageDefinition. For usage examples of "
            "`configured`, see https://docs.dagster.io/overview/configuration#configured"
        ),
    )


def configured(configurable, config_schema=None, **kwargs):
    """
    A decorator that makes it easy to create a function-configured version of an object.
    The following definition types can be configured using this function:

    * :py:class:`CompositeSolidDefinition`
    * :py:class:`ExecutorDefinition`
    * :py:class:`IntermediateStorageDefinition`
    * :py:class:`LoggerDefinition`
    * :py:class:`ResourceDefinition`
    * :py:class:`SolidDefinition`

    If the config that will be supplied to the object is constant, you may alternatively invoke this
    and call the result with a dict of config values to be curried. Examples of both strategies
    below.

    Args:
        configurable (ConfigurableDefinition): An object that can be configured.
        config_schema (ConfigSchema): The config schema that the inputs to the decorated function
            must satisfy.
        **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the returned
            object.

    Returns:
        (Callable[[Union[Any, Callable[[Any], Any]]], ConfigurableDefinition])

    **Examples:**

    .. code-block:: python

        dev_s3 = configured(s3_resource, name="dev_s3")({'bucket': 'dev'})

        @configured(s3_resource):
        def dev_s3(_):
            return {'bucket': 'dev'}

        @configured(s3_resource, {'bucket_prefix', str}):
        def dev_s3(config):
            return {'bucket': config['bucket_prefix'] + 'dev'}
    """
    _check_configurable_param(configurable)

    def _configured(config_or_config_fn):
        return configurable.configured(
            config_schema=config_schema, config_or_config_fn=config_or_config_fn, **kwargs
        )

    return _configured
