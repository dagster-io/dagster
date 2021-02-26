from abc import abstractmethod, abstractproperty
from functools import update_wrapper

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.resource import ResourceDefinition
from dagster.core.storage.input_manager import InputManager
from dagster.utils.backcompat import experimental


class IInputManagerDefinition:
    @abstractproperty
    def input_config_schema(self):
        """The schema for per-input configuration for inputs that are managed by this
        input manager"""


class RootInputManagerDefinition(ResourceDefinition, IInputManagerDefinition):
    """Definition of a root input manager resource.

    Root input managers load solid inputs that aren't connected to upstream outputs.

    An RootInputManagerDefinition is a :py:class:`ResourceDefinition` whose resource_fn returns an
    :py:class:`RootInputManager`.

    The easiest way to create an RootInputManagerDefinition is with the
    :py:func:`@root_input_manager <root_input_manager>` decorator.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        input_config_schema=None,
        required_resource_keys=None,
        version=None,
    ):
        self._input_config_schema = convert_user_facing_definition_config_schema(
            input_config_schema
        )
        super(RootInputManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )

    @property
    def input_config_schema(self):
        return self._input_config_schema

    def copy_for_configured(self, description, config_schema, _):
        return RootInputManagerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            input_config_schema=self.input_config_schema,
        )


class RootInputManager(InputManager):
    """RootInputManagers are used to load inputs to solids at the root of a pipeline.

    The easiest way to define an RootInputManager is with the
    :py:func:`@root_input_manager <root_input_manager>` decorator.
    """

    @abstractmethod
    def load_input(self, context):
        """The user-defined read method that loads data given its metadata.

        Args:
            context (InputContext): The context of the step output that produces this asset.

        Returns:
            Any: The data object.
        """


@experimental
def root_input_manager(
    config_schema=None,
    description=None,
    input_config_schema=None,
    required_resource_keys=None,
    version=None,
):
    """Define a root input manager.

    Root input managers load solid inputs that aren't connected to upstream outputs.

    The decorated function should accept a :py:class:`InputContext` and resource config, and return
    a loaded object that will be passed into one of the inputs of a solid.

    The decorator produces an :py:class:`RootInputManagerDefinition`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource-level config.
        description (Optional[str]): A human-readable description of the resource.
        input_config_schema (Optional[ConfigSchema]): A schema for the input-level config. Each
            input that uses this input manager can be configured separately using this config.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the input
            manager.
        version (Optional[str]): (Experimental) the version of the input manager definition.

    **Examples:**

    .. code-block:: python

        @root_input_manager
        def csv_loader(_):
            return read_csv("some/path")

        @solid(input_defs=[InputDefinition("input1", root_manager_key="csv_loader_key")])
        def my_solid(_, input1):
            do_stuff(input1)

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"csv_loader_key": csv_loader})])
        def my_pipeline():
            my_solid()

        @root_input_manager(config_schema={"base_dir": str})
        def csv_loader(context):
            return read_csv(context.resource_config["base_dir"] + "/some/path")

        @root_input_manager(input_config_schema={"path": str})
        def csv_loader(context):
            return read_csv(context.config["path"])
    """

    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _InputManagerDecoratorCallable()(config_schema)

    def _wrap(load_fn):
        return _InputManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            version=version,
            input_config_schema=input_config_schema,
            required_resource_keys=required_resource_keys,
        )(load_fn)

    return _wrap


class RootInputManagerWrapper(RootInputManager):
    def __init__(self, load_fn):
        self._load_fn = load_fn

    def load_input(self, context):
        return self._load_fn(context)


class _InputManagerDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        version=None,
        input_config_schema=None,
        required_resource_keys=None,
    ):
        self.config_schema = config_schema
        self.description = check.opt_str_param(description, "description")
        self.version = check.opt_str_param(version, "version")
        self.input_config_schema = input_config_schema
        self.required_resource_keys = required_resource_keys

    def __call__(self, load_fn):
        check.callable_param(load_fn, "load_fn")

        def _resource_fn(_):
            return RootInputManagerWrapper(load_fn)

        root_input_manager_def = RootInputManagerDefinition(
            resource_fn=_resource_fn,
            config_schema=self.config_schema,
            description=self.description,
            version=self.version,
            input_config_schema=self.input_config_schema,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(root_input_manager_def, wrapped=load_fn)

        return root_input_manager_def
