from abc import ABC, abstractmethod, abstractproperty
from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.resource import ResourceDefinition


class IInputManagerDefinition:
    @abstractproperty
    def input_config_schema(self):
        """The schema for per-input configuration for inputs that are managed by this
        input manager"""


class InputManagerDefinition(ResourceDefinition, IInputManagerDefinition):
    """Definition of an input manager resource.

    An InputManagerDefinition is a :py:class:`ResourceDefinition` whose resource_fn returns an
    :py:class:`InputManager`.  InputManagers are used to load the inputs to solids.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        version=None,
        input_config_schema=None,
    ):
        self._input_config_schema = convert_user_facing_definition_config_schema(
            input_config_schema
        )
        super(InputManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            version=version,
        )

    @property
    def input_config_schema(self):
        return self._input_config_schema


class InputManager(ABC):
    """InputManagers are used to load the inputs to solids.

    The easiest way to define an InputManager is with the :py:function:`input_manager` decorator.
    """

    @abstractmethod
    def load_input(self, context):
        """The user-defined read method that loads data given its metadata.

        Args:
            context (InputContext): The context of the step output that produces this asset.

        Returns:
            Any: The data object.
        """


def input_manager(config_schema=None, description=None, input_config_schema=None, version=None):
    """Define an input manager.

    The decorated function should accept a :py:class:`InputContext` and resource config, and return
    a loaded object that will be passed into one of the inputs of a solid.

    The decorator produces an :py:class:`InputManagerDefinition`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource-level config.
        description (Optional[str]): A human-readable description of the resource.
        input_config_schema (Optional[ConfigSchema]): A schema for the input-level config. Each
            input that uses this input manager can be configured separately using this config.
        version (Optional[str]): (Experimental) the version of the input manager definition.

    **Examples:**

    .. code-block:: python

        @input_manager
        def csv_loader(_, _resource_config):
            return read_csv("some/path")

        @solid(input_defs=[InputDefinition("input1", manager_key="csv_loader_key")])
        def my_solid(_, input1):
            do_stuff(input1)

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"csv_loader_key": csv_loader})])
        def my_pipeline():
            my_solid()

        @input_manager(config_schema={"base_dir": str})
        def csv_loader(_, resource_config):
            return read_csv(resource_config["base_dir"] + "/some/path")

        @input_manager(input_config_schema={"path": str})
        def csv_loader(context, _resource_config):
            return read_csv(context.input_config["path"])
    """

    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _InputManagerDecoratorCallable()(config_schema)

    def _wrap(load_fn):
        return _InputManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            version=version,
            input_config_schema=input_config_schema,
        )(load_fn)

    return _wrap


class ResourceConfigPassthroughInputManager(InputManager):
    def __init__(self, config, load_fn):
        self._config = config
        self._load_fn = load_fn

    def load_input(self, context):
        return self._load_fn(context, self._config)


class _InputManagerDecoratorCallable:
    def __init__(
        self, config_schema=None, description=None, version=None, input_config_schema=None,
    ):
        self.config_schema = config_schema
        self.description = check.opt_str_param(description, "description")
        self.version = check.opt_str_param(version, "version")
        self.input_config_schema = input_config_schema

    def __call__(self, load_fn):
        check.callable_param(load_fn, "load_fn")

        def _resource_fn(init_context):
            return ResourceConfigPassthroughInputManager(init_context.resource_config, load_fn)

        input_manager_def = InputManagerDefinition(
            resource_fn=_resource_fn,
            config_schema=self.config_schema,
            description=self.description,
            version=self.version,
            input_config_schema=self.input_config_schema,
        )

        update_wrapper(input_manager_def, wrapped=load_fn)

        return input_manager_def
