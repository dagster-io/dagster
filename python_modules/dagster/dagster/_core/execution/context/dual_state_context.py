from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from dagster._core.definitions.scoped_resources_builder import (
    IContainsGenerator,
    Resources,
    ScopedResourcesBuilder,
)
from dagster._core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


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
        resources_dict_or_resources_obj: Optional[Union[Mapping[str, Any], Resources]],
        resources_config: Optional[Mapping[str, Any]] = None,
    ):
        self._cm_scope_entered = False
        self._exit_stack = ExitStack()
        self._resources_config = resources_config

        if isinstance(resources_dict_or_resources_obj, Resources):
            self.resource_defs = {}
            self._resources = resources_dict_or_resources_obj
        else:
            from dagster._core.execution.build_resources import (
                wrap_resources_for_execution,
            )

            self._resources = None
            self.resource_defs = wrap_resources_for_execution(resources_dict_or_resources_obj)

    def call_on_enter(self) -> None:
        self._cm_scope_entered = True

    def call_on_exit(self) -> None:
        self._exit_stack.close()

    def call_on_del(self) -> None:
        self._exit_stack.close()

    def has_been_accessed(self) -> bool:
        return self._resources is not None

    def get_resources(self, fn_name_for_err_msg: str) -> Resources:
        if self._resources:
            return self._resources

        # Early exit if no resources are defined. This skips unnecessary initialization
        # entirely. This allows users to run user code servers in cases where they
        # do not have access to the instance if they use a subset of features do
        # that do not require instance access. In this case, if they do not use
        # resources on schedules they do not require the instance, so we do not
        # instantiate it
        #
        # Tracking at https://github.com/dagster-io/dagster/issues/14345
        if not self.resource_defs:
            self._resources = ScopedResourcesBuilder.build_empty()
            return self._resources

        from dagster._core.execution.build_resources import build_resources

        self._resources = self._exit_stack.enter_context(
            build_resources(self.resource_defs, resource_config=self._resources_config)
        )
        resources_contain_cm = isinstance(self._resources, IContainsGenerator)

        if resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                f"open a context manager: `with {fn_name_for_err_msg}(...) as context:`"
            )
        return self._resources


class DualStateInstanceContainer:
    def __init__(self, instance: Optional["DagsterInstance"]):
        from dagster._core.execution.api import ephemeral_instance_if_missing

        self._exit_stack = ExitStack()
        self.instance = self._exit_stack.enter_context(ephemeral_instance_if_missing(instance))

    def call_on_exit(self) -> None:
        self._exit_stack.close()

    def call_on_del(self) -> None:
        self._exit_stack.close()
