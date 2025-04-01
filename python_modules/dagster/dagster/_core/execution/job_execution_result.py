from collections.abc import Sequence
from typing import Any, ContextManager, cast  # noqa: UP035

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions import JobDefinition, NodeHandle
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import PlanExecutionContext, StepExecutionContext
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.execution.plan.outputs import StepOutputData
from dagster._core.execution.plan.utils import build_resources_for_manager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.types.dagster_type import DagsterType


class JobExecutionResult(ExecutionResult):
    """Result object returned by :py:func:`dagster.execute_job`.

    Used for retrieving run success, events, and outputs from `execute_job`.
    Users should not directly instantiate this class.

    Events and run information can be retrieved off of the object directly. In
    order to access outputs, the `ExecuteJobResult` object needs to be opened
    as a context manager, which will re-initialize the resources from
    execution.
    """

    def __init__(
        self,
        job_def: JobDefinition,
        reconstruct_context: ContextManager[PlanExecutionContext],
        event_list: Sequence[DagsterEvent],
        dagster_run: DagsterRun,
    ):
        self._job_def = job_def
        self._reconstruct_context = reconstruct_context
        self._context = None
        self._event_list = event_list
        self._dagster_run = dagster_run

    def __enter__(self) -> "JobExecutionResult":
        context = self._reconstruct_context.__enter__()
        self._context = context
        return self

    def __exit__(self, *exc):
        exit_result = self._reconstruct_context.__exit__(*exc)
        self._context = None
        return exit_result

    @public
    @property
    def job_def(self) -> JobDefinition:
        """JobDefinition: The job definition that was executed."""
        return self._job_def

    @public
    @property
    def dagster_run(self) -> DagsterRun:
        """DagsterRun: The Dagster run that was executed."""
        return self._dagster_run

    @public
    @property
    def all_events(self) -> Sequence[DagsterEvent]:
        """Sequence[DagsterEvent]: List of all events yielded by the job execution."""
        return self._event_list

    @public
    @property
    def run_id(self) -> str:
        """str: The id of the Dagster run that was executed."""
        return self.dagster_run.run_id

    @public
    def output_value(self, output_name: str = DEFAULT_OUTPUT) -> Any:
        """Retrieves output of top-level job, if an output is returned.

        In order to use this method, the `ExecuteJobResult` object must be opened as a context manager. If this method is used without opening the context manager, it will result in a :py:class:`DagsterInvariantViolationError`. If the top-level job has no output, calling this method will also result in a :py:class:`DagsterInvariantViolationError`.

        Args:
            output_name (Optional[str]): The name of the output to retrieve. Defaults to `result`,
                the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """
        return super().output_value(output_name=output_name)

    @public
    def output_for_node(self, node_str: str, output_name: str = DEFAULT_OUTPUT) -> Any:
        """Retrieves output value with a particular name from the run of the job.

        In order to use this method, the `ExecuteJobResult` object must be opened as a context manager. If this method is used without opening the context manager, it will result in a :py:class:`DagsterInvariantViolationError`.

        Args:
            node_str (str): Name of the op/graph whose output should be retrieved. If the intended
                graph/op is nested within another graph, the syntax is `outer_graph.inner_node`.
            output_name (Optional[str]): Name of the output on the op/graph to retrieve. Defaults to
                `result`, the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """
        return super().output_for_node(node_str, output_name=output_name)

    def _get_output_for_handle(self, handle: NodeHandle, output_name: str) -> Any:
        if not self._context:
            raise DagsterInvariantViolationError(
                "In order to access output objects, the result of `execute_job` must be opened as a"
                " context manager: 'with execute_job(...) as result:"
            )
        found = False
        result = None
        for compute_step_event in self.compute_events_for_handle(handle):
            if (
                compute_step_event.is_successful_output
                and compute_step_event.step_output_data.output_name == output_name
            ):
                found = True
                output = compute_step_event.step_output_data
                step = self._context.execution_plan.get_executable_step_by_key(
                    check.not_none(compute_step_event.step_key)
                )
                dagster_type = (
                    self.job_def.get_node(handle).output_def_named(output_name).dagster_type
                )
                value = self._get_value(self._context.for_step(step), output, dagster_type)
                check.invariant(
                    not (output.mapping_key and step.get_mapping_key()),
                    "Not set up to handle mapped outputs downstream of mapped steps",
                )
                mapping_key = output.mapping_key or step.get_mapping_key()
                if mapping_key:
                    if result is None:
                        result = {mapping_key: value}
                    else:
                        cast(dict, result)[mapping_key] = value
                else:
                    result = value

        if found:
            return result

        node = self.job_def.get_node(handle)
        raise DagsterInvariantViolationError(
            f"Did not find result {output_name} in {node.describe_node()}"
        )

    def _get_value(
        self,
        context: StepExecutionContext,
        step_output_data: StepOutputData,
        dagster_type: DagsterType,
    ) -> object:
        step_output_handle = step_output_data.step_output_handle
        manager = context.get_io_manager(step_output_handle)
        manager_key = context.execution_plan.get_manager_key(step_output_handle, self.job_def)
        res = manager.load_input(
            context.for_input_manager(
                name="dummy_input_name",
                config=None,
                definition_metadata=None,
                dagster_type=dagster_type,
                source_handle=step_output_handle,
                resource_config=context.resolved_run_config.resources[manager_key].config,
                resources=build_resources_for_manager(manager_key, context),
            )
        )
        return res
