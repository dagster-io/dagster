from contextlib import ExitStack
from typing import Any, Mapping, Optional

from dagster._core.definitions.scoped_resources_builder import IContainsGenerator, Resources
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.build_resources import build_resources, wrap_resources_for_execution


class DualStateContextResourcesContainer:
    """We have generalized pattern where we allow users to either directly construct
    bare contexts or to use them in the context managers. We require that they
    use context managers when they themselves contain resources that are context
    managers. Thie results in a complicated, stateful, difficult-to-reason-about
    message in all of our context objects subject to this pattern where `__enter__`
    is optionally called, and we must track whether it has been called, and error
    appropriately when resources are accessed.

    This class exists to comparmentalize this grosteque, stateful pattern to a single
    point of pain, rather than blithely spreading it throughout the codebase.
    """

    def __init__(
        self,
        resources_dict: Mapping[str, Any],
        resources_config: Optional[Mapping[str, Any]] = None,
    ):
        self._cm_scope_entered = False
        self._exit_stack = ExitStack()
        self.resource_defs = wrap_resources_for_execution(resources_dict)
        self._resources = self._exit_stack.enter_context(
            build_resources(resources=self.resource_defs, resource_config=resources_config)
        )
        self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)

    def call_on_enter(self) -> None:
        self._cm_scope_entered = True
        pass

    def call_on_exit(self) -> None:
        self._exit_stack.close()

    def call_on_del(self) -> None:
        self._exit_stack.close()

    def get_resources(self, fn_name_for_err_msg: str) -> Resources:
        if self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                f"open a context manager: `with {fn_name_for_err_msg}(...) as context:`"
            )
        return self._resources
