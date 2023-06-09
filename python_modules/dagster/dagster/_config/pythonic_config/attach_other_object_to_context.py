from typing import (
    Any,
)


class IAttachDifferentObjectToOpContext:
    """Utility interface which adjusts the type of the bare object attached to the execution context
    by a resource. Useful when migrating function-style resources to class-style ConfigurableResources.

    For example, the following function-style resource is consumed by an asset:

    .. code-block:: python

        @resource(config_schema={"inner_string": str})
        def my_string_resource(context) -> str:
            return context.resource_config["inner_string"]

        @asset(required_resource_keys={"my_string"})
        def my_unconverted_asset(context: OpExecutionContext) -> str:
            return context.resources.my_string

    Adapted to a class-style resource, we can ensure our new ConfigurableResource is compatible
    with the asset by implementing this interface:

    .. code-block:: python

        class MyStringResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
            inner_string: str

            def get_object_to_set_on_execution_context(self) -> str:
                return self.inner_string

        @asset(required_resource_keys={"my_string"})
        def my_unconverted_asset(context: OpExecutionContext) -> str:
            return context.resources.my_string

        @asset
        def my_converted_asset(my_string: MyStringResource) -> str:
            return my_string.inner_string
    """

    def get_object_to_set_on_execution_context(self) -> Any:
        """Override to return the object to be attached to the execution context by this resource.
        """
        raise NotImplementedError()
