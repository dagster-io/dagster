from typing import Any, Mapping, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.resource_definition import (
    IContainsGenerator,
    ResourceDefinition,
    Resources,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance


class UsesResourcesContext:
    def __init__(
        self,
        *,
        context_str: str,
        resources: Optional[Union[Resources, Mapping[str, Any]]] = None,
        resources_config: Optional[Mapping[str, Any]] = None,
        instance: Optional[DagsterInstance] = None,
    ):
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        self._resources_cm = None
        self._instance_cm = None
        self._instance = instance
        self._context_str = context_str

        # If resources object has already been provided, no need to construct resources
        if isinstance(resources, Resources):
            self._resources = resources
            self._resource_defs = None
            check.invariant(
                resources_config is None,
                "resources_config should not be set when resource instances are directly provided.",
            )
            self._resources_config = None
        else:
            self._resources = None
            self._resource_defs = wrap_resources_for_execution(
                check.opt_mapping_param(resources, "resources", key_type=str)
            )
            self._resources_config = check.opt_mapping_param(resources_config, "resources_config")

    def get_resources(self) -> Resources:
        from dagster._core.execution.build_resources import build_resources

        if self._resources is None:
            with build_resources(
                resources=self._resource_defs,
                instance=self._instance,
                resource_config=self._resources_config,
            ) as resources:
                # We only find out that there is a generator resource after
                # initialization, but ideally, we should be able to find out
                # before resource initialization occurs.
                if isinstance(resources, IContainsGenerator):
                    raise DagsterInvariantViolationError(
                        "At least one provided resource is a generator, but attempting to access "
                        "resources outside of context manager scope. You can use the following syntax to "
                        f"open a context manager: `with build_{self._context_str}_context(...) as context:`"
                    )
                self._resources = resources
        return self._resources

    def get_resource_defs(self) -> Mapping[str, ResourceDefinition]:
        if self._resource_defs is None:
            raise DagsterInvariantViolationError(
                "Resource defs were not directly provided to this context."
            )
        return cast(Mapping[str, ResourceDefinition], self._resource_defs)

    def get_resources_config(self) -> Mapping[str, Any]:
        if self._resources_config is None:
            raise DagsterInvariantViolationError(
                "Resources config was not directly provided to this context."
            )
        return cast(Mapping[str, Any], self._resources_config)

    def __enter__(self):
        from dagster._core.execution.api import ephemeral_instance_if_missing
        from dagster._core.execution.build_resources import build_resources

        if not self._instance:
            self._instance_cm = ephemeral_instance_if_missing(None)
            self._instance = self._instance_cm.__enter__()

        self._resources_cm = build_resources(
            resources=self._resource_defs,
            instance=self._instance,
            resource_config=self._resources_config,
        )
        self._resources = self._resources_cm.__enter__()
        return self

    def __exit__(self, *exc):
        if self._instance_cm:
            self._instance = None
            self._instance_cm.__exit__(*exc)
        if self._resources_cm:
            self._resources = None
            self._resources_cm.__exit__(*exc)

    def get_instance(self) -> DagsterInstance:
        if not self._instance:
            raise DagsterInvariantViolationError(
                "No instance was provided, and context object is outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_op_context(...) as context:"
            )
        return self._instance
