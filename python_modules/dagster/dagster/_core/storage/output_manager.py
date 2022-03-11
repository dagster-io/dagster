from abc import ABC, abstractmethod

from dagster._core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)
from dagster._core.definitions.resource_definition import ResourceDefinition


class IOutputManagerDefinition:
    @property
    @abstractmethod
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

    def copy_for_configured(self, description, config_schema, _):
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
    """

    @abstractmethod
    def handle_output(self, context, obj):
        """Handles an output produced by a solid. Usually, this means materializing it to persistent
        storage.

        Args:
            context (OutputContext): The context of the step output that produces this object.
            obj (Any): The data object to be handled.
        """
