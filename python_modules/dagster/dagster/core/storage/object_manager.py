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
    Base class for user-provided asset store.

    Extend this class to handle asset operations. Users should implement ``handle_object`` to store
    a data object that can be tracked by the Dagster machinery and ``load`` to retrieve a data
    object.
    """


def object_manager(
    config_schema=None,
    description=None,
    version=None,
    output_config_schema=None,
    input_config_schema=None,
):
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
