from abc import ABC, abstractmethod, abstractproperty
from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.resource import ResourceDefinition


class IOutputManagerDefinition:
    @abstractproperty
    def output_config_schema(self):
        """The schema for per-output configuration for outputs that are managed by this
        manager"""


class OutputManagerDefinition(ResourceDefinition, IOutputManagerDefinition):
    """Definition of an output manager resource.

    An OutputManagerDefinition is a :py:class:`ResourceDefinition` whose resource_fn returns an
    :py:class:`OutputManager`.  OutputManagers are used to handle the outputs of solids.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        output_config_schema=None,
        required_resource_keys=None,
        version=None,
    ):
        self._output_config_schema = convert_user_facing_definition_config_schema(
            output_config_schema
        )
        super(OutputManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )

    @property
    def output_config_schema(self):
        return self._output_config_schema

    def copy_for_configured(self, name, description, config_schema, _):
        check.invariant(name is None, "ResourceDefintions do not have names")
        return OutputManagerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            output_config_schema=self.output_config_schema,
        )


class OutputManager(ABC):
    """Base class for user-provided output managers. OutputManagers are used to handle the outputs
    of solids.

    The easiest way to define an OutputManager is with the :py:function:`output_manager` decorator.
    """

    @abstractmethod
    def handle_output(self, context, obj):
        """Handles an output produced by a solid. Usually, this means materializing it to persistent
        storage.

        Args:
            context (OutputContext): The context of the step output that produces this object.
            obj (Any): The data object to be handled.
        """


def output_manager(
    config_schema=None,
    description=None,
    output_config_schema=None,
    required_resource_keys=None,
    version=None,
):
    """Define an output manager.

    The decorated function should accept a :py:class:`OutputContext` and resource config, and
    handle an object that is yielded as one of the outputs of a solid.

    The decorator produces an :py:class:`OutputManagerDefinition`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource-level config.
        description (Optional[str]): A human-readable description of the resource.
        output_config_schema (Optional[ConfigSchema]): A schema for the output-level config. Each
            output that uses this output manager can be configured separately using this config.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the output
            manager.
        version (Optional[str]): (Experimental) the version of the output manager definition.

    **Examples:**

    .. code-block:: python

        @output_manager
        def csv_materializer(_, _resource_config):
            write_csv("some/path")

        @solid(output_defs=[OutputDefinition(io_manager_key="csv_materializer_key")])
        def my_solid(_):
            return do_stuff()

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={"csv_materializer_key": csv_materializer})]
        )
        def my_pipeline():
            my_solid()

        execute_pipeline(my_pipeline)

    OutputManager with resource config:

    .. code-block:: python

        @output_manager(config_schema={"base_dir": str})
        def csv_materializer(context):
            write_csv(context.resource_config["base_dir"] + "/some/path")

        ...

        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"csv_materializer_key": {"config": {"base_dir"" "a/b/c"}}}},
        )

    OutputManager with per-output config:

    .. code-block:: python

        @output_manager(output_config_schema={"path": str})
        def csv_materializer(context):
            write_csv(context.config["path"])

        ...

        execute_pipeline(
            my_pipeline,
            run_config={"solids": {"my_solid": {"outputs": {"result": {"path"" "a/b/c/d"}}}}},
        )

    """
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _OutputManagerDecoratorCallable()(config_schema)

    def _wrap(load_fn):
        return _OutputManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            version=version,
            output_config_schema=output_config_schema,
            required_resource_keys=required_resource_keys,
        )(load_fn)

    return _wrap


class OutputManagerWrapper(OutputManager):
    def __init__(self, process_fn):
        self._process_fn = process_fn

    def handle_output(self, context, obj):
        return self._process_fn(context, obj)


class _OutputManagerDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        version=None,
        output_config_schema=None,
        required_resource_keys=None,
    ):
        #  type checks in definition
        self.config_schema = config_schema
        self.description = description
        self.version = version
        self.output_config_schema = output_config_schema
        self.required_resource_keys = required_resource_keys

    def __call__(self, load_fn):
        check.callable_param(load_fn, "load_fn")

        def _resource_fn(_):
            return OutputManagerWrapper(load_fn)

        output_manager_def = OutputManagerDefinition(
            resource_fn=_resource_fn,
            config_schema=self.config_schema,
            description=self.description,
            version=self.version,
            output_config_schema=self.output_config_schema,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(output_manager_def, wrapped=load_fn)

        return output_manager_def
