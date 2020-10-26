from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.config.evaluate_value_result import EvaluateValueResult
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.config.validate import process_config
from dagster.core.errors import DagsterConfigMappingFunctionError, user_code_error_boundary


class IConfigMappable(six.with_metaclass(ABCMeta)):
    @property
    def is_preconfigured(self):
        return self._configured_config_mapping_fn is not None

    @abstractproperty
    def _configured_config_mapping_fn(self):
        raise NotImplementedError()

    @abstractproperty
    def config_schema(self):
        raise NotImplementedError()

    @abstractmethod
    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
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
            **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the
                returned object.

        Returns (IConfigMappable): A configured version of this object.
        """
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
        # If there is no __configured_config_mapping_fn, this is the innermost resource (base case),
        # so we aren't responsible for validating against anything farther down. Returns an EVR for
        # type consistency with wrapped_config_mapping_fn.
        return (
            self._configured_config_mapping_fn(config)
            if self._configured_config_mapping_fn
            else EvaluateValueResult.for_value(config)
        )

    def _get_user_code_error_str_lambda(self):
        return lambda: (
            "The config mapping function on a `configured` {} has thrown an unexpected "
            "error during its execution."
        ).format(self.__class__.__name__)

    def _get_wrapped_config_mapping_fn(self, config_or_config_fn, config_schema):
        """
        Returns a config mapping helper function that will be stored on the child `IConfigMappable`
        under `_configured_config_mapping_fn`. Encapsulates the recursiveness of the `configurable`
        pattern by returning a closure that invokes `self.apply_config_mapping` (belonging to this
        parent object) on the mapping function or static config passed into this method.
        """
        # Provide either a config mapping function with noneable schema...
        if callable(config_or_config_fn):
            config_fn = config_or_config_fn
        else:  # or a static config object (and no schema).
            check.invariant(
                config_schema is None,
                "When non-callable config is given, config_schema must be None",
            )

            def config_fn(_):  # Stub a config mapping function from the static config object.
                return config_or_config_fn

        def wrapped_config_mapping_fn(validated_and_resolved_config):
            """
            Given validated and resolved configuration for this IConfigMappable, applies the
            provided config mapping function, validates its output against the inner resource's
            config_schema, and recursively invoked the `apply_config_mapping` method on the resource
            """
            check.dict_param(validated_and_resolved_config, "validated_and_resolved_config")
            with user_code_error_boundary(
                DagsterConfigMappingFunctionError, self._get_user_code_error_str_lambda()
            ):
                mapped_config = {
                    "config": config_fn(validated_and_resolved_config.get("config", {}))
                }
            # Validate mapped_config against the inner resource's config_schema (on self).
            config_evr = process_config({"config": self.config_schema or {}}, mapped_config)
            if config_evr.success:
                return self.apply_config_mapping(config_evr.value)  # Recursive step
            else:
                return config_evr  # Bubble up the errors

        return wrapped_config_mapping_fn


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
        IConfigMappable,
        (
            "Only the following types can be used with the `configured` method: ResourceDefinition, "
            "ExecutorDefinition, CompositeSolidDefinition, SolidDefinition, LoggerDefinition, "
            "IntermediateStorageDefinition, and SystemStorageDefinition. For usage examples of "
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
    * :py:class:`SystemStorageDefinition`

    If the config that will be supplied to the object is constant, you may alternatively invoke this
    and call the result with a dict of config values to be curried. Examples of both strategies
    below.

    Args:
        configurable (IConfigMappable): An object that can be configured.
        config_schema (ConfigSchema): The config schema that the inputs to the decorated function
            must satisfy.
        **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the returned
            object.

    Returns:
        (Callable[[Union[Any, Callable[[Any], Any]]], IConfigMappable])

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
    config_schema = check_user_facing_opt_config_param(config_schema, "config_schema")

    def _configured(config_or_config_fn):
        return configurable.configured(
            config_schema=config_schema, config_or_config_fn=config_or_config_fn, **kwargs
        )

    return _configured
