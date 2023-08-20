from typing import (
    Any,
    Mapping,
    Optional,
    Union,
)

import dagster._check as check
from dagster._core.definitions.resource_definition import Resources


class ResourcesBagOfHolding:
    def __init__(self, resources: Optional[Union["Resources", Mapping[str, Any]]] = None):
        from dagster._core.definitions.resource_definition import IContainsGenerator, Resources
        from dagster._core.execution.build_resources import build_resources

        if isinstance(resources, Resources):
            self._resources_cm = None
            self._resources = resources
        else:
            self._resources_cm = build_resources(
                check.opt_mapping_param(resources, "resources", key_type=str)
            )
            self._resources = self._resources_cm.__enter__()
            self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)
            self._cm_scope_entered = False

    def call_on_enter(self) -> None:
        if self._resources_cm:
            self._cm_scope_entered = True

    def call_on_exit(self, *exc) -> None:
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)

    def call_on_del(self) -> None:
        if self._resources_cm and self._resources_contain_cm and self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)

    @property
    def resources(self) -> Optional[Resources]:
        return self._resources

    @property
    def context_managerful_resources_used_outside_of_scope(self) -> bool:
        return bool(
            self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered
        )
