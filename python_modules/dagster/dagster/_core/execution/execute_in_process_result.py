from typing import Any, Mapping, Optional, Sequence

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions import JobDefinition, NodeHandle
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.storage.pipeline_run import DagsterRun

from .execution_result import ExecutionResult


class ExecuteInProcessResult(ExecutionResult):
    """Result object returned by in-process testing APIs.

    Users should not instantiate this object directly. Used for retrieving run success, events, and outputs from execution methods that return this object.

    This object is returned by:
    - :py:meth:`dagster.GraphDefinition.execute_in_process`
    - :py:meth:`dagster.JobDefinition.execute_in_process`
    - :py:meth:`dagster.materialize_to_memory`
    - :py:meth:`dagster.materialize`
    """

    _handle: NodeHandle
    _event_list: Sequence[DagsterEvent]
    _dagster_run: DagsterRun
    _output_capture: Mapping[StepOutputHandle, Any]
    _job_def: JobDefinition

    def __init__(
        self,
        event_list: Sequence[DagsterEvent],
        dagster_run: DagsterRun,
        output_capture: Optional[Mapping[StepOutputHandle, Any]],
        job_def: JobDefinition,
    ):
        self._job_def = job_def

        self._event_list = event_list
        self._dagster_run = dagster_run

        self._output_capture = check.opt_mapping_param(
            output_capture, "output_capture", key_type=StepOutputHandle
        )

    @public  # type: ignore
    @property
    def job_def(self) -> JobDefinition:
        return self._job_def

    @public  # type: ignore
    @property
    def dagster_run(self) -> DagsterRun:
        return self._dagster_run

    @public  # type: ignore
    @property
    def all_events(self) -> Sequence[DagsterEvent]:
        """List[DagsterEvent]: All dagster events emitted during execution."""
        return self._event_list

    @public  # type: ignore
    @property
    def run_id(self) -> str:
        return self.dagster_run.run_id

    def _get_output_for_handle(self, handle: NodeHandle, output_name: str) -> Any:
        mapped_outputs = {}
        step_key = str(handle)
        output_found = False
        for step_output_handle, value in self._output_capture.items():
            # For the mapped output case, where step keys are in the format
            # "step_key[upstream_mapped_output_name]" within the step output handle.
            if (
                step_output_handle.step_key.startswith(f"{step_key}[")
                and step_output_handle.output_name == output_name
            ):
                output_found = True
                key_start = step_output_handle.step_key.find("[")
                key_end = step_output_handle.step_key.find("]")
                upstream_mapped_output_name = step_output_handle.step_key[key_start + 1 : key_end]
                mapped_outputs[upstream_mapped_output_name] = value

            # For all other cases, search for exact match.
            elif (
                step_key == step_output_handle.step_key
                and step_output_handle.output_name == output_name
            ):
                output_found = True
                if not step_output_handle.mapping_key:
                    return self._output_capture[step_output_handle]
                mapped_outputs[step_output_handle.mapping_key] = value

        if not output_found:
            raise DagsterInvariantViolationError(
                f"No outputs found for output '{output_name}' from node '{handle}'."
            )
        return mapped_outputs

    @public
    def output_for_node(self, node_str: str, output_name: str = DEFAULT_OUTPUT) -> Any:
        """Retrieves output value with a particular name from the in-process run of the job.

        Args:
            node_str (str): Name of the op/graph whose output should be retrieved. If the intended
                graph/op is nested within another graph, the syntax is `outer_graph.inner_node`.
            output_name (Optional[str]): Name of the output on the op/graph to retrieve. Defaults to
                `result`, the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """
        return super(ExecuteInProcessResult, self).output_for_node(
            node_str, output_name=output_name
        )

    @public
    def asset_value(self, asset_key: CoercibleToAssetKey) -> Any:
        node_output_handle = self._job_def.asset_layer.node_output_handle_for_asset(
            AssetKey.from_coerceable(asset_key)
        )
        return self.output_for_node(
            node_str=str(node_output_handle.node_handle), output_name=node_output_handle.output_name
        )

    @public
    def output_value(self, output_name: str = DEFAULT_OUTPUT) -> Any:
        """Retrieves output of top-level job, if an output is returned.

        Args:
            output_name (Optional[str]): The name of the output to retrieve. Defaults to `result`,
                the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """
        return super(ExecuteInProcessResult, self).output_value(output_name=output_name)
