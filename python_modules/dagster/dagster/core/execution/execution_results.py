from abc import abstractproperty
from typing import Any, Dict, List, Optional, cast

from dagster import DagsterEvent, check
from dagster.core.definitions import GraphDefinition, Node, NodeHandle, SolidDefinition
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import StepKind


def _filter_by_step_kind(event_list: List[DagsterEvent], kind: StepKind) -> List[DagsterEvent]:
    return [event for event in event_list if event.step_kind == kind]


def _filter_step_events_by_handle(
    event_list: List[DagsterEvent],
    ancestor_handle: Optional[NodeHandle],
    current_handle: NodeHandle,
) -> List[DagsterEvent]:
    events = []
    if ancestor_handle:
        handle_with_ancestor = cast(NodeHandle, current_handle.with_ancestor(ancestor_handle))
    else:
        handle_with_ancestor = current_handle

    for event in event_list:
        if event.is_step_event:
            solid_handle = cast(NodeHandle, event.solid_handle)
            if solid_handle.is_or_descends_from(handle_with_ancestor):
                events.append(event)

    return events


def _get_solid_handle_from_output(step_output_handle: StepOutputHandle) -> Optional[NodeHandle]:
    return NodeHandle.from_string(step_output_handle.step_key)


def _filter_outputs_by_handle(
    output_dict: Dict[StepOutputHandle, Any],
    ancestor_handle: Optional[NodeHandle],
    current_handle: NodeHandle,
):
    if ancestor_handle:
        handle_with_ancestor = current_handle.with_ancestor(ancestor_handle)
    else:
        handle_with_ancestor = current_handle

    outputs = {}
    for step_output_handle, value in output_dict.items():
        handle = _get_solid_handle_from_output(step_output_handle)
        if handle and handle_with_ancestor and handle.is_or_descends_from(handle_with_ancestor):
            outputs[step_output_handle] = value
    return outputs


class InProcessNodeResult:
    @property
    def success(self):
        """bool: Whether all steps in the execution were successful."""
        return all([not event.is_failure for event in self.event_list])

    @abstractproperty
    def output_values(self) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractproperty
    def event_list(self) -> List[DagsterEvent]:
        raise NotImplementedError()


class InProcessOpResult(InProcessNodeResult):
    def __init__(
        self,
        solid_def: SolidDefinition,
        handle: NodeHandle,
        all_events: List[DagsterEvent],
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._solid_def = solid_def
        self._handle = handle
        self._event_list = all_events
        self._output_capture = output_capture

    @property
    def output_values(self) -> Dict[str, Any]:
        """
        The output values for the associated op/solid, keyed by output name.
        """
        solid_handle_as_str = str(self.handle)
        results: Dict[str, Any] = {}
        if self._output_capture:
            for step_output_handle, value in self._output_capture.items():
                if step_output_handle.step_key == solid_handle_as_str:
                    if step_output_handle.mapping_key:
                        if results.get(step_output_handle.output_name) is None:
                            results[step_output_handle.output_name] = {
                                step_output_handle.mapping_key: value
                            }
                        else:
                            results[step_output_handle.output_name][
                                step_output_handle.mapping_key
                            ] = value
                    else:
                        results[step_output_handle.output_name] = value
        else:
            raise DagsterInvariantViolationError(
                "Trying to fetch output values, but output_capturing_enabled was False for the run"
            )

        return results

    def output_value(self, output_name=DEFAULT_OUTPUT):
        """Get a computed output value.

        Note that calling this method will reconstruct the pipeline context (including, e.g.,
        resources) to retrieve materialized output values.

        Args:
            output_name(str): The output name for which to retrieve the value. (default: 'result')

        Returns:
            Union[None, Any, Dict[str, Any]]: ``None`` if execution did not succeed, the output value
                in the normal case, and a dict of mapping keys to values in the mapped case.
        """
        check.str_param(output_name, "output_name")

        if not self._output_capture:
            raise DagsterInvariantViolationError(
                "Trying to fetch output values, but output_capturing_enabled was False for the run"
            )

        solid_handle_as_str = str(self.handle)

        # if the output isn't dynamic, we can do a fast version that's just a single lookup
        non_mapped_output_handle = StepOutputHandle(solid_handle_as_str, output_name)
        if non_mapped_output_handle in self._output_capture:
            return self._output_capture[non_mapped_output_handle]

        # otherwise, need to scan over all the outputs
        mapped_result: Dict[str, Any] = {}
        for step_output_handle, value in self._output_capture.items():
            if (
                step_output_handle.step_key == solid_handle_as_str
                and step_output_handle.output_name == output_name
            ):
                mapped_result[step_output_handle.mapping_key] = value

        return mapped_result

    @property
    def event_list(self) -> List[DagsterEvent]:
        return self._event_list

    @property
    def handle(self) -> NodeHandle:
        return self._handle


class InProcessGraphResult(InProcessNodeResult):
    def __init__(
        self,
        graph_def: GraphDefinition,
        handle: Optional[NodeHandle],
        all_events: List[DagsterEvent],
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._graph_def = graph_def
        self._handle = handle
        self._event_list = all_events
        self._output_capture = output_capture

    def _result_for_handle(self, solid: Node, handle: NodeHandle) -> InProcessNodeResult:
        node_def = solid.definition
        events_for_handle = _filter_step_events_by_handle(self.event_list, self.handle, handle)
        outputs_for_handle = (
            _filter_outputs_by_handle(self._output_capture, self.handle, handle)
            if self._output_capture
            else None
        )
        if self.handle:
            handle_with_ancestor = handle.with_ancestor(self.handle)
        else:
            handle_with_ancestor = handle

        if not handle_with_ancestor:
            raise DagsterInvariantViolationError(f"No handle provided for solid {solid.name}")

        if isinstance(node_def, SolidDefinition):
            return InProcessOpResult(
                solid_def=node_def,
                handle=handle_with_ancestor,
                all_events=events_for_handle,
                output_capture=outputs_for_handle,
            )
        elif isinstance(node_def, GraphDefinition):
            return InProcessGraphResult(
                graph_def=node_def,
                handle=handle_with_ancestor,
                all_events=events_for_handle,
                output_capture=outputs_for_handle,
            )

        check.failed("Unhandled node type {node_def}")

    @property
    def output_values(self) -> Dict[str, Any]:
        """
        The values for any outputs that this associated graph maps.
        """
        values = {}

        for output_name in self._graph_def.output_dict:
            output_mapping = self._graph_def.get_output_mapping(output_name)

            inner_solid_values = self._result_for_handle(
                self._graph_def.solid_named(output_mapping.maps_from.solid_name),
                NodeHandle(output_mapping.maps_from.solid_name, None),
            ).output_values

            if inner_solid_values is not None:  # may be None if inner solid was skipped
                if output_mapping.maps_from.output_name in inner_solid_values:
                    values[output_name] = inner_solid_values[output_mapping.maps_from.output_name]

        return values

    @property
    def event_list(self) -> List[DagsterEvent]:
        return self._event_list

    @property
    def handle(self) -> Optional[NodeHandle]:
        return self._handle

    def result_for_node(self, name: str) -> InProcessNodeResult:
        """
        The inner result for a node within the graph.
        """

        if not self._graph_def.has_solid_named(name):
            raise DagsterInvariantViolationError(
                "Tried to get result for node '{name}' in '{container}'. No such top level "
                "node.".format(name=name, container=self._graph_def.name)
            )
        handle = NodeHandle(name, None)
        solid = self._graph_def.get_solid(handle)
        return self._result_for_handle(solid, handle)

    def output_for_node(self, handle_str, output_name=DEFAULT_OUTPUT):
        """Get the output of a node by its node handle string and output name.

        Args:
            handle_str (str): The string handle for the node.
            output_name (str): Optional. The name of the output, default to DEFAULT_OUTPUT.

        Returns:
            The output value for the handle and output_name.
        """

        check.str_param(handle_str, "handle_str")
        check.str_param(output_name, "output_name")
        handle = NodeHandle.from_string(handle_str)
        node = self._graph_def.get_solid(handle)
        return self._result_for_handle(node, handle).output_value(output_name)
