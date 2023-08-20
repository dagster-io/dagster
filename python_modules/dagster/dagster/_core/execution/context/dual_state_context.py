from contextlib import ExitStack
from typing import (
    Any,
    Mapping,
    Optional,
    Union,
)

import dagster._check as check
from dagster import DagsterInvariantViolationError
from dagster._core.definitions.resource_definition import Resources
from dagster._core.instance import DagsterInstance


class DualStateContextResourcesContainer:
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

    def ensure_context_managerful_resources_used_within_scope(
        self,
        fn_name_for_error_msg: str,
    ) -> Resources:
        if self.context_managerful_resources_used_outside_of_scope:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                f"open a context manager: `with {fn_name_for_error_msg}(...) as context:`"
            )
        return self._resources


class DualStateContextInstanceContainer:
    def __init__(self, instance: Optional[DagsterInstance]) -> None:
        from dagster._core.execution.api import ephemeral_instance_if_missing

        self._exit_stack = ExitStack()
        # Construct ephemeral instance if missing
        self._instance = self._exit_stack.enter_context(ephemeral_instance_if_missing(instance))

    def call_on_exit(self, *exc) -> None:
        self._exit_stack.close()

    def call_on_del(self) -> None:
        self._exit_stack.close()

    @property
    def instance(self) -> DagsterInstance:
        return self._instance
