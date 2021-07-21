import warnings
from typing import Any, Dict, Optional, Set, Union, cast

from dagster import check

from ...definitions.composition import PendingNodeInvocation
from ...definitions.decorators.graph import graph
from ...definitions.dependency import Node
from ...definitions.hook import HookDefinition
from ...definitions.mode import ModeDefinition
from ...definitions.resource import IContainsGenerator, Resources
from ...definitions.solid import SolidDefinition
from ...errors import DagsterInvalidPropertyError, DagsterInvariantViolationError
from ...log_manager import DagsterLogManager
from ..plan.step import ExecutionStep
from .system import StepExecutionContext


def _property_msg(prop_name: str, method_name: str) -> str:
    return (
        f"The {prop_name} {method_name} is not set when a `HookContext` is constructed from "
        "`build_hook_context`."
    )


class HookContext:
    """The ``context`` object available to a hook function on an DagsterEvent.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        hook_def (HookDefinition): The hook that the context object belongs to.
        solid (Solid): The solid instance associated with the hook.
        step_key (str): The key for the step where this hook is being triggered.
        resources (Resources): Resources available in the hook context.
        solid_config (Any): The parsed config specific to this solid.
        pipeline_name (str): The name of the pipeline where this hook is being triggered.
        run_id (str): The id of the run where this hook is being triggered.
        mode_def (ModeDefinition): The mode with which the pipeline is being run.
    """

    def __init__(
        self,
        step_execution_context: StepExecutionContext,
        hook_def: HookDefinition,
    ):
        self._step_execution_context = step_execution_context
        self._hook_def = check.inst_param(hook_def, "hook_def", HookDefinition)
        self._required_resource_keys = hook_def.required_resource_keys
        self._resources = step_execution_context.scoped_resources_builder.build(
            self._required_resource_keys
        )

    @property
    def pipeline_name(self) -> str:
        return self._step_execution_context.pipeline_name

    @property
    def run_id(self) -> str:
        return self._step_execution_context.run_id

    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def solid(self) -> Node:
        return self._step_execution_context.solid

    @property
    def step(self) -> ExecutionStep:
        warnings.warn(
            "The step property of HookContext has been deprecated, and will be removed "
            "in a future release."
        )
        return self._step_execution_context.step

    @property
    def step_key(self) -> str:
        return self._step_execution_context.step.key

    @property
    def mode_def(self) -> Optional[ModeDefinition]:
        return self._step_execution_context.mode_def

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def solid_config(self) -> Any:
        solid_config = self._step_execution_context.resolved_run_config.solids.get(
            str(self._step_execution_context.step.solid_handle)
        )
        return solid_config.config if solid_config else None

    # Because of the fact that we directly use the log manager of the step, if a user calls
    # hook_context.log.with_tags, then they will end up mutating the step's logging tags as well.
    # This is not problematic because the hook only runs after the step has been completed.
    @property
    def log(self) -> DagsterLogManager:
        return self._step_execution_context.log

    @property
    def solid_exception(self) -> Optional[BaseException]:
        """The thrown exception in a failed solid.

        Returns:
            Optional[BaseException]: the exception object, None if the solid execution succeeds.
        """

        return self._step_execution_context.step_exception

    @property
    def solid_output_values(self) -> Dict[str, Union[Any, Dict[str, Any]]]:
        """The computed output values.

        Returns a dictionary where keys are output names and the values are:
            * the output values in the normal case
            * a dictionary from mapping key to corresponding value in the mapped case
        """
        results: Dict[str, Union[Any, Dict[str, Any]]] = {}

        # make the returned values more user-friendly
        for step_output_handle, value in self._step_execution_context.step_output_capture.items():
            if step_output_handle.mapping_key:
                if results.get(step_output_handle.output_name) is None:
                    results[step_output_handle.output_name] = {
                        step_output_handle.mapping_key: value
                    }
                else:
                    results[step_output_handle.output_name][step_output_handle.mapping_key] = value
            else:
                results[step_output_handle.output_name] = value

        return results


class UnboundHookContext(HookContext):
    def __init__(
        self,
        resources: Dict[str, Any],
        mode_def: Optional[ModeDefinition],
        solid: Optional[Union[SolidDefinition, PendingNodeInvocation]],
    ):  # pylint: disable=super-init-not-called
        from ..context_creation_pipeline import initialize_console_manager
        from ..build_resources import build_resources

        self._mode_def = mode_def

        self._solid = None
        if solid is not None:

            @graph(name="hook_context_container")
            def temp_graph():
                solid()

            self._solid = temp_graph.solids[0]

        # Open resource context manager
        self._resources_cm = build_resources(resources)
        self._resources = self._resources_cm.__enter__()  # pylint: disable=no-member
        self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)

        self._log = initialize_console_manager(None)

        self._cm_scope_entered = False

    def __enter__(self):
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        self._resources_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @property
    def pipeline_name(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("pipeline_name", "property"))

    @property
    def run_id(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("run_id", "property"))

    @property
    def hook_def(self) -> HookDefinition:
        raise DagsterInvalidPropertyError(_property_msg("hook_def", "property"))

    @property
    def solid(self) -> Node:
        check.invariant(
            self._solid is not None,
            "solid property was not provided when constructing the context.",
        )
        return cast(Node, self._solid)

    @property
    def step(self) -> ExecutionStep:
        raise DagsterInvalidPropertyError(_property_msg("step", "property"))

    @property
    def step_key(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("step_key", "property"))

    @property
    def mode_def(self) -> Optional[ModeDefinition]:
        return self._mode_def

    @property
    def required_resource_keys(self) -> Set[str]:
        raise DagsterInvalidPropertyError(_property_msg("hook_def", "property"))

    @property
    def resources(self) -> "Resources":
        if self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_hook_context(...) as context:`"
            )
        return self._resources

    @property
    def solid_config(self) -> Any:
        raise DagsterInvalidPropertyError(_property_msg("solid_config", "property"))

    @property
    def log(self) -> DagsterLogManager:
        return self._log

    @property
    def solid_exception(self) -> Optional[BaseException]:
        """The thrown exception in a failed solid.

        Returns:
            Optional[BaseException]: the exception object, None if the solid execution succeeds.
        """

        raise DagsterInvalidPropertyError(_property_msg("solid_exception", "property"))

    @property
    def solid_output_values(self) -> Dict[str, Union[Any, Dict[str, Any]]]:
        """The computed output values.

        Returns a dictionary where keys are output names and the values are:
            * the output values in the normal case
            * a dictionary from mapping key to corresponding value in the mapped case
        """
        raise DagsterInvalidPropertyError(_property_msg("solid_output_values", "method"))


class BoundHookContext(HookContext):
    def __init__(
        self,
        hook_def: HookDefinition,
        resources: Resources,
        solid: Optional[Node],
        mode_def: Optional[ModeDefinition],
        log_manager: DagsterLogManager,
    ):  # pylint: disable=super-init-not-called
        self._hook_def = hook_def
        self._resources = resources
        self._solid = solid
        self._mode_def = mode_def
        self._log_manager = log_manager

    @property
    def pipeline_name(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("pipeline_name", "property"))

    @property
    def run_id(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("run_id", "property"))

    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def solid(self) -> Node:
        check.invariant(
            self._solid is not None,
            "solid property was not provided when constructing the context.",
        )
        return cast(Node, self._solid)

    @property
    def step(self) -> ExecutionStep:
        raise DagsterInvalidPropertyError(_property_msg("step", "property"))

    @property
    def step_key(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("step_key", "property"))

    @property
    def mode_def(self) -> Optional[ModeDefinition]:
        return self._mode_def

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._hook_def.required_resource_keys

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def solid_config(self) -> Any:
        raise DagsterInvalidPropertyError(_property_msg("solid_config", "property"))

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    @property
    def solid_exception(self) -> Optional[BaseException]:
        """The thrown exception in a failed solid.

        Returns:
            Optional[BaseException]: the exception object, None if the solid execution succeeds.
        """

        raise DagsterInvalidPropertyError(_property_msg("solid_exception", "property"))

    @property
    def solid_output_values(self) -> Dict[str, Union[Any, Dict[str, Any]]]:
        """The computed output values.

        Returns a dictionary where keys are output names and the values are:
            * the output values in the normal case
            * a dictionary from mapping key to corresponding value in the mapped case
        """
        raise DagsterInvalidPropertyError(_property_msg("solid_output_values", "method"))


def build_hook_context(
    resources: Optional[Dict[str, Any]] = None,
    mode_def: Optional[ModeDefinition] = None,
    solid: Optional[Union[SolidDefinition, PendingNodeInvocation]] = None,
) -> UnboundHookContext:
    """Builds hook context from provided parameters.

    ``build_hook_context`` can be used as either a function or a context manager. If there is a
    provided resource to ``build_hook_context`` that is a context manager, then it must be used as a
    context manager. This function can be used to provide the context argument to the invocation of
    a hook definition.

    Args:
        resources (Optional[Dict[str, Any]]): The resources to provide to the context. These can
            either be values or resource definitions.
        mode_def (Optional[ModeDefinition]): The mode definition used with the context.
        solid (Optional[SolidDefinition, PendingNodeInvocation]): The solid definition which the
            hook may be associated with.

    Examples:
        .. code-block:: python

            context = build_hook_context()
            hook_to_invoke(context)

            with build_hook_context(resources={"foo": context_manager_resource}) as context:
                hook_to_invoke(context)
    """
    return UnboundHookContext(
        resources=check.opt_dict_param(resources, "resources", key_type=str),
        mode_def=check.opt_inst_param(mode_def, "mode_def", ModeDefinition),
        solid=check.opt_inst_param(solid, "solid", (SolidDefinition, PendingNodeInvocation)),
    )
