import warnings
from typing import AbstractSet, Any, Dict, Mapping, Optional, Set, Union

import dagster._check as check
from dagster._annotations import public

from ...definitions.composition import PendingNodeInvocation
from ...definitions.decorators.graph_decorator import graph
from ...definitions.dependency import Node
from ...definitions.hook_definition import HookDefinition
from ...definitions.op_definition import OpDefinition
from ...definitions.resource_definition import IContainsGenerator, Resources
from ...errors import DagsterInvalidPropertyError, DagsterInvariantViolationError
from ...log_manager import DagsterLogManager
from ..plan.step import ExecutionStep
from .system import StepExecutionContext


def _property_msg(prop_name: str, method_name: str) -> str:
    return (
        f"The {prop_name} {method_name} is not set when a `HookContext` is constructed from "
        "`build_hook_context`."
    )


def _check_property_on_test_context(
    context: "HookContext", attr_str: str, user_facing_name: str, param_on_builder: str
):
    """Check if attribute is not None on context. If none, error, and point user in direction of
    how to specify the parameter on the context object."""

    value = getattr(context, attr_str)
    if value is None:
        raise DagsterInvalidPropertyError(
            f"Attribute '{user_facing_name}' was not provided when "
            f"constructing context. Provide a value for the '{param_on_builder}' parameter on "
            "'build_hook_context'. To learn more, check out the testing hooks section of Dagster's "
            "concepts docs: https://docs.dagster.io/concepts/ops-jobs-graphs/op-hooks#testing-hooks"
        )
    else:
        return value


class HookContext:
    """The ``context`` object available to a hook function on an DagsterEvent.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        hook_def (HookDefinition): The hook that the context object belongs to.
        op (Op): The op instance associated with the hook.
        step_key (str): The key for the step where this hook is being triggered.
        required_resource_keys (Set[str]): Resources required by this hook.
        resources (Resources): Resources available in the hook context.
        op_config (Any): The parsed config specific to this op.
        job_name (str): The name of the job where this hook is being triggered.
        run_id (str): The id of the run where this hook is being triggered.
        op_exception (Optional[BaseException]): The thrown exception in a failed op.
        op_output_values (Dict): Computed output values in an op.
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
        return self.job_name

    @public  # type: ignore
    @property
    def job_name(self) -> str:
        return self._step_execution_context.job_name

    @public  # type: ignore
    @property
    def run_id(self) -> str:
        return self._step_execution_context.run_id

    @public  # type: ignore
    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def op(self) -> Node:
        return self._step_execution_context.solid

    @property
    def step(self) -> ExecutionStep:
        warnings.warn(
            "The step property of HookContext has been deprecated, and will be removed "
            "in a future release."
        )
        return self._step_execution_context.step

    @public  # type: ignore
    @property
    def step_key(self) -> str:
        return self._step_execution_context.step.key

    @public  # type: ignore
    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return self._required_resource_keys

    @public  # type: ignore
    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def solid_config(self) -> Any:
        solid_config = self._step_execution_context.resolved_run_config.solids.get(
            str(self._step_execution_context.step.solid_handle)
        )
        return solid_config.config if solid_config else None

    @public  # type: ignore
    @property
    def op_config(self) -> Any:
        return self.solid_config

    # Because of the fact that we directly use the log manager of the step, if a user calls
    # hook_context.log.with_tags, then they will end up mutating the step's logging tags as well.
    # This is not problematic because the hook only runs after the step has been completed.
    @public  # type: ignore
    @property
    def log(self) -> DagsterLogManager:
        return self._step_execution_context.log

    @property
    def solid_exception(self) -> Optional[BaseException]:
        """The thrown exception in a failed solid.

        Returns:
            Optional[BaseException]: the exception object, None if the solid execution succeeds.
        """
        return self.op_exception

    @public  # type: ignore
    @property
    def op_exception(self):
        return self._step_execution_context.step_exception

    @property
    def solid_output_values(self) -> Mapping[str, Union[Any, Mapping[str, Any]]]:
        """The computed output values.

        Returns a dictionary where keys are output names and the values are:
            * the output values in the normal case
            * a dictionary from mapping key to corresponding value in the mapped case
        """
        results: Dict[str, Union[Any, Dict[str, Any]]] = {}
        captured = self._step_execution_context.step_output_capture

        if captured is None:
            check.failed("Outputs were unexpectedly not captured for hook")

        # make the returned values more user-friendly
        for step_output_handle, value in captured.items():
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

    @public  # type: ignore
    @property
    def op_output_values(self):
        return self.solid_output_values


class UnboundHookContext(HookContext):
    def __init__(
        self,
        resources: Mapping[str, Any],
        op: Optional[Union[OpDefinition, PendingNodeInvocation]],
        run_id: Optional[str],
        job_name: Optional[str],
        op_exception: Optional[Exception],
    ):  # pylint: disable=super-init-not-called
        from ..build_resources import build_resources, wrap_resources_for_execution
        from ..context_creation_pipeline import initialize_console_manager

        self._op = None
        if op is not None:

            @graph(name="hook_context_container")
            def temp_graph():
                op()

            self._op = temp_graph.solids[0]

        # Open resource context manager
        self._resource_defs = wrap_resources_for_execution(resources)
        self._resources_cm = build_resources(self._resource_defs)
        self._resources = self._resources_cm.__enter__()  # pylint: disable=no-member
        self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)

        self._run_id = run_id
        self._job_name = job_name
        self._op_exception = op_exception

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
    def job_name(self) -> str:
        return self.pipeline_name

    @property
    def run_id(self) -> str:
        return _check_property_on_test_context(
            self, attr_str="_run_id", user_facing_name="run_id", param_on_builder="run_id"
        )

    @property
    def hook_def(self) -> HookDefinition:
        raise DagsterInvalidPropertyError(_property_msg("hook_def", "property"))

    @property
    def op(self) -> Node:
        return _check_property_on_test_context(
            self, attr_str="_op", user_facing_name="op", param_on_builder="op"
        )

    @property
    def step(self) -> ExecutionStep:
        raise DagsterInvalidPropertyError(_property_msg("step", "property"))

    @property
    def step_key(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("step_key", "property"))

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
    def op_exception(self) -> Optional[BaseException]:
        return self._op_exception

    @property
    def solid_output_values(self) -> Mapping[str, Union[Any, Mapping[str, Any]]]:
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
        op: Optional[Node],
        log_manager: DagsterLogManager,
        run_id: Optional[str],
        job_name: Optional[str],
        op_exception: Optional[Exception],
    ):  # pylint: disable=super-init-not-called
        self._hook_def = hook_def
        self._resources = resources
        self._op = op
        self._log_manager = log_manager
        self._run_id = run_id
        self._job_name = job_name
        self._op_exception = op_exception

    @property
    def job_name(self) -> str:
        return _check_property_on_test_context(
            self, attr_str="_job_name", user_facing_name="job_name", param_on_builder="job_name"
        )

    @property
    def run_id(self) -> str:
        return _check_property_on_test_context(
            self, attr_str="_run_id", user_facing_name="run_id", param_on_builder="run_id"
        )

    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def op(self) -> Node:
        return _check_property_on_test_context(
            self, attr_str="_op", user_facing_name="op", param_on_builder="op"
        )

    @property
    def step(self) -> ExecutionStep:
        raise DagsterInvalidPropertyError(_property_msg("step", "property"))

    @property
    def step_key(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("step_key", "property"))

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
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
    def op_exception(self):
        return self._op_exception

    @property
    def solid_output_values(self) -> Mapping[str, Union[Any, Mapping[str, Any]]]:
        """The computed output values.

        Returns a dictionary where keys are output names and the values are:
            * the output values in the normal case
            * a dictionary from mapping key to corresponding value in the mapped case
        """
        raise DagsterInvalidPropertyError(_property_msg("solid_output_values", "method"))


def build_hook_context(
    resources: Optional[Mapping[str, Any]] = None,
    op: Optional[Union[OpDefinition, PendingNodeInvocation]] = None,
    run_id: Optional[str] = None,
    job_name: Optional[str] = None,
    op_exception: Optional[Exception] = None,
) -> UnboundHookContext:
    """Builds hook context from provided parameters.

    ``build_hook_context`` can be used as either a function or a context manager. If there is a
    provided resource to ``build_hook_context`` that is a context manager, then it must be used as a
    context manager. This function can be used to provide the context argument to the invocation of
    a hook definition.

    Args:
        resources (Optional[Dict[str, Any]]): The resources to provide to the context. These can
            either be values or resource definitions.
        op (Optional[OpDefinition, PendingNodeInvocation]): The op definition which the
            hook may be associated with.
        run_id (Optional[str]): The id of the run in which the hook is invoked (provided for mocking purposes).
        job_name (Optional[str]): The name of the job in which the hook is used (provided for mocking purposes).
        op_exception (Optional[Exception]): The exception that caused the hook to be triggered.

    Examples:
        .. code-block:: python

            context = build_hook_context()
            hook_to_invoke(context)

            with build_hook_context(resources={"foo": context_manager_resource}) as context:
                hook_to_invoke(context)
    """

    op = check.opt_inst_param(op, "op", (OpDefinition, PendingNodeInvocation))

    return UnboundHookContext(
        resources=check.opt_mapping_param(resources, "resources", key_type=str),
        op=op,  # type: ignore[arg-type] # (mypy bug)
        run_id=check.opt_str_param(run_id, "run_id"),
        job_name=check.opt_str_param(job_name, "job_name"),
        op_exception=check.opt_inst_param(op_exception, "op_exception", Exception),
    )
