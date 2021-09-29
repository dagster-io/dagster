from typing import Any, Dict, List, Optional, cast

from dagster import DagsterEvent, check
from dagster.core.definitions import NodeDefinition, NodeHandle
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle


class ExecuteInProcessResult:
    def __init__(
        self,
        node_def: NodeDefinition,
        all_events: List[DagsterEvent],
        run_id: str,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._node_def = node_def

        # If top-level result, no handle will be provided
        self._handle = NodeHandle(node_def.name, parent=None)
        self._event_list = all_events
        self._run_id = run_id

        self._output_capture = check.opt_dict_param(output_capture, "output_capture", key_type=str)

    @property
    def success(self) -> bool:
        """bool: Whether execution was successful."""
        return all([not event.is_failure for event in self._event_list])

    @property
    def all_node_events(self) -> List[DagsterEvent]:
        step_events = []

        for node_name in self._node_def.ensure_graph_def().node_dict.keys():
            handle = NodeHandle(node_name, None)
            step_events += _filter_events_by_handle(self._event_list, handle)

        return step_events

    def events_for_node(self, node_name: str) -> List[DagsterEvent]:
        check.str_param(node_name, "node_name")

        return _filter_events_by_handle(self._event_list, NodeHandle.from_string(node_name))

    def output_value(self, output_name: str = DEFAULT_OUTPUT) -> Any:

        check.str_param(output_name, "output_name")

        # Resolve the first layer of mapping
        graph_def = self._node_def.ensure_graph_def()
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

    def output_for_node(self, node_str: str, output_name: Optional[str] = DEFAULT_OUTPUT):

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


def _filter_events_by_handle(
    event_list: List[DagsterEvent], handle: NodeHandle
) -> List[DagsterEvent]:
    step_events = []
    for event in event_list:
        if event.is_step_event:
            handle = cast(
                NodeHandle, event.solid_handle
            )  # step events are guaranteed to have a node handle.
            if handle.is_or_descends_from(handle):
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
        if (
            step_key == step_output_handle.step_key
            and step_output_handle.output_name == output_name
        ):
            output_found = True
            if not step_output_handle.mapping_key:
                return output_dict[step_output_handle]
            mapped_outputs[step_output_handle.mapping_key] = value

    if not output_found:
        raise DagsterInvariantViolationError(f"No outputs found for node '{node_handle}'.")
    return mapped_outputs
