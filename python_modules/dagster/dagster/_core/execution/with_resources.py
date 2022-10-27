from typing import Any, Iterable, List, Mapping, Optional, Sequence, TypeVar, cast

from dagster import _check as check
from dagster._utils import merge_dicts

from ..._config import Shape
from ..definitions import ResourceDefinition
from ..definitions.resource_requirement import ResourceAddable
from ..definitions.utils import DEFAULT_IO_MANAGER_KEY
from ..errors import DagsterInvalidConfigError, DagsterInvalidInvocationError

T = TypeVar("T", bound=ResourceAddable)


def with_resources(
    definitions: Iterable[T],
    resource_defs: Mapping[str, ResourceDefinition],
    resource_config_by_key: Optional[Mapping[str, Any]] = None,
) -> Sequence[T]:
    """Adds dagster resources to copies of resource-requiring dagster definitions.

    An error will be thrown if any provided definitions have a conflicting
    resource definition provided for a key provided to resource_defs. Resource
    config can be provided, with keys in the config dictionary corresponding to
    the keys for each resource definition. If any definition has unsatisfied
    resource keys after applying with_resources, an error will be thrown.

    Args:
        definitions (Iterable[ResourceAddable]): Dagster definitions to provide resources to.
        resource_defs (Mapping[str, ResourceDefinition]):
            Mapping of resource keys to ResourceDefinition objects to satisfy
            resource requirements of provided dagster definitions.
        resource_config_by_key (Optional[Mapping[str, Any]]):
            Specifies config for provided resources. The key in this dictionary
            corresponds to configuring the same key in the resource_defs
            dictionary.

    Examples:

    .. code-block:: python

        from dagster import asset, resource, with_resources

        @resource(config_schema={"bar": str})
        def foo_resource():
            ...

        @asset(required_resource_keys={"foo"})
        def asset1(context):
            foo = context.resources.foo
            ...

        @asset(required_resource_keys={"foo"})
        def asset2(context):
            foo = context.resources.foo
            ...

        asset1_with_foo, asset2_with_foo = with_resources(
            [the_asset, other_asset],
            resource_config_by_key={
                "foo": {
                    "config": {"bar": ...}
                }
            }
        )


    """
    from dagster._config import validate_config
    from dagster._core.definitions.job_definition import (
        default_job_io_manager_with_fs_io_manager_schema,
    )

    check.mapping_param(resource_defs, "resource_defs")
    resource_config_by_key = check.opt_mapping_param(
        resource_config_by_key, "resource_config_by_key"
    )

    resource_defs = merge_dicts(
        {DEFAULT_IO_MANAGER_KEY: default_job_io_manager_with_fs_io_manager_schema}, resource_defs
    )

    for key, resource_def in resource_defs.items():
        if key in resource_config_by_key:
            resource_config = resource_config_by_key[key]
            if not isinstance(resource_config, dict) or "config" not in resource_config:
                raise DagsterInvalidInvocationError(
                    f"Error with config for resource key '{key}': Expected a "
                    "dictionary of the form {'config': ...}, but received "
                    f"{str(resource_config)}"
                )

            outer_config_shape = Shape({"config": resource_def.get_config_field()})
            config_evr = validate_config(outer_config_shape, resource_config)
            if not config_evr.success:
                raise DagsterInvalidConfigError(
                    f"Error when applying config for resource with key '{key}' ",
                    config_evr.errors,
                    resource_config,
                )
            resource_defs[key] = resource_defs[key].configured(resource_config["config"])

    transformed_defs: List[T] = []
    for definition in definitions:
        transformed_defs.append(cast(T, definition.with_resources(resource_defs)))

    return transformed_defs
