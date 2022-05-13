from typing import Any, Dict, List, Optional, Union, cast

import dagster._check as check
from dagster.core.definitions import NodeDefinition, NodeHandle
from dagster.core.definitions.events import AssetMaterialization, AssetObservation, Materialization
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterError, DagsterInvariantViolationError
from dagster.core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.storage.pipeline_run import DagsterRun


class ExecuteInProcessResult:
    def __init__(
        self,
        node_def: NodeDefinition,
        all_events: List[DagsterEvent],
        dagster_run: DagsterRun,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._node_def = node_def

        # If top-level result, no handle will be provided
        self._handle = NodeHandle(node_def.name, parent=None)
        self._event_list = all_events
        self._dagster_run = dagster_run

        self._output_capture = check.opt_dict_param(
            output_capture, "output_capture", key_type=StepOutputHandle
        )

    @property
    def success(self) -> bool:
        """bool: Whether execution was successful."""
        return self._dagster_run.is_success

    @property
    def all_node_events(self) -> List[DagsterEvent]:
        """List[DagsterEvent]: All dagster events from the in-process execution."""

        step_events = []

        for node_name in self._node_def.ensure_graph_def().node_dict.keys():
            handle = NodeHandle(node_name, None)
            step_events += _filter_events_by_handle(self._event_list, handle)

        return step_events

    @property
    def all_events(self) -> List[DagsterEvent]:
        """List[DagsterEvent]: All dagster events emitted during in-process execution."""

        return self._event_list

    @property
    def run_id(self) -> str:
        """str: The run id for the executed run"""
        return self._dagster_run.run_id

    @property
    def dagster_run(self) -> DagsterRun:
        """DagsterRun: the DagsterRun object for the completed execution."""
        return self._dagster_run

    def events_for_node(self, node_name: str) -> List[DagsterEvent]:
        """Retrieves all dagster events for a specific node.

        Args:
            node_name (str): The name of the node for which outputs should be retrieved.

        Returns:
            List[DagsterEvent]: A list of all dagster events associated with provided node name.
        """
        check.str_param(node_name, "node_name")

        return _filter_events_by_handle(self._event_list, NodeHandle.from_string(node_name))

    def asset_materializations_for_node(
        self, node_name
    ) -> List[Union[Materialization, AssetMaterialization]]:
        return [
            cast(StepMaterializationData, event.event_specific_data).materialization
            for event in self.events_for_node(node_name)
            if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION.value
        ]

    def asset_observations_for_node(self, node_name) -> List[AssetObservation]:
        return [
            cast(AssetObservationData, event.event_specific_data).asset_observation
            for event in self.events_for_node(node_name)
            if event.event_type_value == DagsterEventType.ASSET_OBSERVATION.value
        ]

    def output_value(self, output_name: str = DEFAULT_OUTPUT) -> Any:
        """Retrieves output of top-level job, if an output is returned.

        If the top-level job has no output, calling this method will result in a
        DagsterInvariantViolationError.

        Args:
            output_name (Optional[str]): The name of the output to retrieve. Defaults to `result`,
                the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """

        check.str_param(output_name, "output_name")

        graph_def = self._node_def.ensure_graph_def()
        if not graph_def.has_output(output_name) and len(graph_def.output_mappings) == 0:
            raise DagsterInvariantViolationError(
                f"Attempted to retrieve top-level outputs for '{graph_def.name}', which has no outputs."
            )
        elif not graph_def.has_output(output_name):
            raise DagsterInvariantViolationError(
                f"Could not find top-level output '{output_name}' in '{graph_def.name}'."
            )
        # Resolve the first layer of mapping
        output_mapping = graph_def.get_output_mapping(output_name)
        mapped_node = graph_def.solid_named(output_mapping.maps_from.solid_name)
        origin_output_def, origin_handle = mapped_node.definition.resolve_output_to_origin(
            output_mapping.maps_from.output_name,
            NodeHandle(mapped_node.name, None),
        )

        # Get output from origin node
        return _filter_outputs_by_handle(
            self._output_capture, origin_handle, origin_output_def.name
        )

    def output_for_node(self, node_str: str, output_name: Optional[str] = DEFAULT_OUTPUT) -> Any:
        """Retrieves output value with a particular name from the in-process run of the job.

        Args:
            node_str (str): Name of the op/graph whose output should be retrieved. If the intended
                graph/op is nested within another graph, the syntax is `outer_graph.inner_node`.
            output_name (Optional[str]): Name of the output on the op/graph to retrieve. Defaults to
                `result`, the default output name in dagster.

        Returns:
            Any: The value of the retrieved output.
        """

        # resolve handle of node that node_str is referring to
        target_handle = NodeHandle.from_string(node_str)
        target_node_def = self._node_def.ensure_graph_def().get_solid(target_handle).definition
        origin_output_def, origin_handle = target_node_def.resolve_output_to_origin(
            output_name, NodeHandle.from_string(node_str)
        )

        # retrieve output value from resolved handle
        return _filter_outputs_by_handle(
            self._output_capture, origin_handle, origin_output_def.name
        )

    def get_job_success_event(self):
        """Returns a DagsterEvent with type DagsterEventType.PIPELINE_SUCCESS if it ocurred during
        execution
        """
        events = list(
            filter(
                lambda event: event.event_type == DagsterEventType.PIPELINE_SUCCESS, self.all_events
            )
        )

        if len(events) == 0:
            raise DagsterError("No event of type DagsterEventType.PIPELINE_SUCCESS found.")

        return events[0]

    def get_job_failure_event(self):
        """Returns a DagsterEvent with type DagsterEventType.PIPELINE_FAILURE if it ocurred during
        execution
        """
        events = list(
            filter(
                lambda event: event.event_type == DagsterEventType.PIPELINE_FAILURE, self.all_events
            )
        )

        if len(events) == 0:
            raise DagsterError("No event of type DagsterEventType.PIPELINE_FAILURE found.")

        return events[0]


def _filter_events_by_handle(
    event_list: List[DagsterEvent], handle: NodeHandle
) -> List[DagsterEvent]:
    step_events = []
    for event in event_list:
        if event.is_step_event:
            event_handle = cast(
                NodeHandle, event.solid_handle
            )  # step events are guaranteed to have a node handle.
            if event_handle.is_or_descends_from(handle):
                step_events.append(event)

    return step_events


def _filter_outputs_by_handle(
    output_dict: Dict[StepOutputHandle, Any],
    node_handle: NodeHandle,
    output_name: str,
) -> Any:
    mapped_outputs = {}
    step_key = str(node_handle)
    output_found = False
    for step_output_handle, value in output_dict.items():

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
                return output_dict[step_output_handle]
            mapped_outputs[step_output_handle.mapping_key] = value

    if not output_found:
        raise DagsterInvariantViolationError(
            f"No outputs found for output '{output_name}' from node '{node_handle}'."
        )
    return mapped_outputs
