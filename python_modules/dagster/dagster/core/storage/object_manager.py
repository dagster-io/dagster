from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.resource import ResourceDefinition
from dagster.core.storage.input_manager import IInputManagerDefinition, InputManager
from dagster.core.storage.output_manager import IOutputManagerDefinition, OutputManager


class ObjectManagerDefinition(
    ResourceDefinition, IInputManagerDefinition, IOutputManagerDefinition
):
    """Definition of an output manager resource.

    An OutputManagerDefinition is a :py:class:`ResourceDefinition` whose resource_fn returns an
    :py:class:`ObjectManager`.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        _configured_config_mapping_fn=None,
        version=None,
        input_config_schema=None,
        output_config_schema=None,
    ):
        self._input_config_schema = input_config_schema
        self._output_config_schema = output_config_schema
        super(ObjectManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            version=version,
        )

    @property
    def input_config_schema(self):
        return self._input_config_schema

    @property
    def output_config_schema(self):
        return self._output_config_schema


class ObjectManager(InputManager, OutputManager):
    """
    Base class for user-provided object managers.

    Extend this class to handle how objects are loaded and stored. Users should implement
    ``handle_object`` to store an object and ``load_input`` to retrieve an object.
    """


def object_manager(
    config_schema=None,
    description=None,
    output_config_schema=None,
    input_config_schema=None,
    version=None,
):
    """
    Define an object manager.

    The decorated function should accept an :py:class:`InitResourceContext and return an
    py:class:`ObjectManager`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource config. Configuration
            data available in `init_context.resource_config`.
        description(Optional[str]): A human-readable description of the resource.
        output_config_schema (Optional[ConfigSchema]): The schema for per-output config.
        input_config_schema (Optional[ConfigSchema]): The schema for per-input config.
        version (Optional[str]): (Experimental) The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.

    **Examples:**

    .. code-block:: python

        class MyObjectManager(ObjectManager):
            def handle_output(self, context, obj):
                write_csv("some/path")

            def load_input(self, context):
                return read_csv("some/path")

        @object_manager
        def my_object_manager(init_context):
            return MyObjectManager()

        @solid(output_defs=[OutputDefinition(manager_key="my_object_manager_key")])
        def my_solid(_):
            return do_stuff()

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={"my_object_manager_key": my_object_manager})]
        )
        def my_pipeline():
            my_solid()

        execute_pipeline(my_pipeline)
    """
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _ObjectManagerDecoratorCallable()(config_schema)

    def _wrap(resource_fn):
        return _ObjectManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            version=version,
            output_config_schema=output_config_schema,
            input_config_schema=input_config_schema,
        )(resource_fn)

    return _wrap


class _ObjectManagerDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        version=None,
        output_config_schema=None,
        input_config_schema=None,
    ):
        self.config_schema = convert_user_facing_definition_config_schema(config_schema)
        self.description = check.opt_str_param(description, "description")
        self.version = check.opt_str_param(version, "version")
        self.output_config_schema = convert_user_facing_definition_config_schema(
            output_config_schema
        )
        self.input_config_schema = convert_user_facing_definition_config_schema(input_config_schema)

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        asset_store_def = ObjectManagerDefinition(
            resource_fn=fn,
            config_schema=self.config_schema,
            description=self.description,
            version=self.version,
            output_config_schema=self.output_config_schema,
            input_config_schema=self.input_config_schema,
        )

        update_wrapper(asset_store_def, wrapped=fn)

        return asset_store_def
