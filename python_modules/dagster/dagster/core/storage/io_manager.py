from abc import abstractmethod
from functools import update_wrapper
from typing import Optional, Set

import dagster._check as check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.storage.input_manager import InputManager
from dagster.core.storage.output_manager import IOutputManagerDefinition, OutputManager
from dagster.core.storage.root_input_manager import IInputManagerDefinition


class IOManagerDefinition(ResourceDefinition, IInputManagerDefinition, IOutputManagerDefinition):
    """Definition of an IO manager resource.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    An IOManagerDefinition is a :py:class:`ResourceDefinition` whose `resource_fn` returns an
    :py:class:`IOManager`.

    The easiest way to create an IOManagerDefnition is with the :py:func:`@io_manager <io_manager>`
    decorator.
    """

    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
        input_config_schema=None,
        output_config_schema=None,
    ):
        self._input_config_schema = convert_user_facing_definition_config_schema(
            input_config_schema
        )
        # Unlike other configurable objects, whose config schemas default to Any, output_config_schema
        # defaults to None. This the because IOManager input / output config shares config
        # namespace with dagster type loaders and materializers. The absence of provided
        # output_config_schema means that we should fall back to using the materializer that
        # corresponds to the output dagster type.
        self._output_config_schema = (
            convert_user_facing_definition_config_schema(output_config_schema)
            if output_config_schema is not None
            else None
        )
        super(IOManagerDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
        )

    @property
    def input_config_schema(self):
        return self._input_config_schema

    @property
    def output_config_schema(self):
        return self._output_config_schema

    def copy_for_configured(self, description, config_schema, _):
        return IOManagerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            resource_fn=self.resource_fn,
            required_resource_keys=self.required_resource_keys,
            input_config_schema=self.input_config_schema,
            output_config_schema=self.output_config_schema,
        )

    @staticmethod
    def hardcoded_io_manager(value, description=None):
        """A helper function that creates an ``IOManagerDefinition`` with a hardcoded IOManager.

        Args:
            value (Any): A hardcoded IO Manager which helps mock the definition.
            description ([Optional[str]]): The description of the IO Manager. Defaults to None.

        Returns:
            [IOManagerDefinition]: A hardcoded resource.
        """
        check.inst_param(value, "value", IOManager)
        return IOManagerDefinition(resource_fn=lambda _init_context: value, description=description)


class IOManager(InputManager, OutputManager):
    """
    Base class for user-provided IO managers.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    Extend this class to handle how objects are loaded and stored. Users should implement
    ``handle_output`` to store an object and ``load_input`` to retrieve an object.
    """

    @abstractmethod
    def load_input(self, context):
        """User-defined method that loads an input to an op.

        Args:
            context (InputContext): The input context, which describes the input that's being loaded
                and the upstream output that's being loaded from.

        Returns:
            Any: The data object.
        """

    @abstractmethod
    def handle_output(self, context, obj):
        """User-defined method that stores an output of an op.

        Args:
            context (OutputContext): The context of the step output that produces this object.
            obj (Any): The object, returned by the op, to be stored.
        """

    def get_output_asset_key(self, _context) -> Optional[AssetKey]:
        """User-defined method that associates outputs handled by this IOManager with a particular
        AssetKey.

        Args:
            context (OutputContext): The context of the step output that produces this object.
        """
        return None

    def get_output_asset_partitions(self, _context) -> Set[str]:
        """User-defined method that associates outputs handled by this IOManager with a set of
        partitions of an AssetKey.

        Args:
            context (OutputContext): The context of the step output that produces this object.
        """
        return set()

    def get_input_asset_key(self, context) -> Optional[AssetKey]:
        """User-defined method that associates inputs loaded by this IOManager with a particular
        AssetKey.

        Args:
            context (InputContext): The input context, which describes the input that's being loaded
                and the upstream output that's being loaded from.
        """
        return self.get_output_asset_key(context.upstream_output)

    def get_input_asset_partitions(self, context) -> Set[str]:
        """User-defined method that associates inputs loaded by this IOManager with a set of
        partitions of an AssetKey.

        Args:
            context (InputContext): The input context, which describes the input that's being loaded
                and the upstream output that's being loaded from.
        """
        return self.get_output_asset_partitions(context.upstream_output)


def io_manager(
    config_schema=None,
    description=None,
    output_config_schema=None,
    input_config_schema=None,
    required_resource_keys=None,
    version=None,
):
    """
    Define an IO manager.

    IOManagers are used to store op outputs and load them as inputs to downstream ops.

    The decorated function should accept an :py:class:`InitResourceContext` and return an
    :py:class:`IOManager`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the resource config. Configuration
            data available in `init_context.resource_config`. If not set, Dagster will accept any
            config provided.
        description(Optional[str]): A human-readable description of the resource.
        output_config_schema (Optional[ConfigSchema]): The schema for per-output config. If not set,
            no per-output configuration will be allowed.
        input_config_schema (Optional[ConfigSchema]): The schema for per-input config. If not set,
            Dagster will accept any config provided.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the object
            manager.
        version (Optional[str]): (Experimental) The version of a resource function. Two wrapped
            resource functions should only have the same version if they produce the same resource
            definition when provided with the same inputs.

    **Examples:**

    .. code-block:: python

        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                write_csv("some/path")

            def load_input(self, context):
                return read_csv("some/path")

        @io_manager
        def my_io_manager(init_context):
            return MyIOManager()

        @op(out=Out(io_manager_key="my_io_manager_key"))
        def my_op(_):
            return do_stuff()

        @job(resource_defs={"my_io_manager_key": my_io_manager})
        def my_job():
            my_op()

    """
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return _IOManagerDecoratorCallable()(config_schema)

    def _wrap(resource_fn):
        return _IOManagerDecoratorCallable(
            config_schema=config_schema,
            description=description,
            required_resource_keys=required_resource_keys,
            version=version,
            output_config_schema=output_config_schema,
            input_config_schema=input_config_schema,
        )(resource_fn)

    return _wrap


class _IOManagerDecoratorCallable:
    def __init__(
        self,
        config_schema=None,
        description=None,
        required_resource_keys=None,
        version=None,
        output_config_schema=None,
        input_config_schema=None,
    ):
        # type validation happens in IOManagerDefinition
        self.config_schema = config_schema
        self.description = description
        self.required_resource_keys = required_resource_keys
        self.version = version
        self.output_config_schema = output_config_schema
        self.input_config_schema = input_config_schema

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        io_manager_def = IOManagerDefinition(
            resource_fn=fn,
            config_schema=self.config_schema,
            description=self.description,
            required_resource_keys=self.required_resource_keys,
            version=self.version,
            output_config_schema=self.output_config_schema,
            input_config_schema=self.input_config_schema,
        )

        update_wrapper(io_manager_def, wrapped=fn)

        return io_manager_def
