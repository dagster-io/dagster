from abc import abstractproperty
from typing import Any, Dict, List, Optional

from dagster import DagsterEvent
from dagster.core.definitions import GraphDefinition, Solid, SolidDefinition, SolidHandle
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import StepKind


def _filter_by_step_kind(event_list: List[DagsterEvent], kind: StepKind) -> List[DagsterEvent]:
    return [event for event in event_list if event.step_kind == kind]


def _filter_step_events_by_handle(
    event_list: List[DagsterEvent], ancestor_handle: SolidHandle, current_handle: SolidHandle
) -> List[DagsterEvent]:
    events = []
    handle_with_ancestor = current_handle.with_ancestor(ancestor_handle)
    for event in event_list:
        if event.is_step_event:
            if event.solid_handle.is_or_descends_from(handle_with_ancestor):
                events.append(event)

    return events


def _get_solid_handle_from_output(step_output_handle: StepOutputHandle) -> Optional[SolidHandle]:
    return SolidHandle.from_string(step_output_handle.step_key)


def _filter_outputs_by_handle(
    output_dict: Dict[StepOutputHandle, Any],
    ancestor_handle: SolidHandle,
    current_handle: SolidHandle,
):
    handle_with_ancestor = current_handle.with_ancestor(ancestor_handle)
    outputs = {}
    for step_output_handle, value in output_dict.items():
        handle = _get_solid_handle_from_output(step_output_handle)
        if handle and handle_with_ancestor and handle.is_or_descends_from(handle_with_ancestor):
            outputs[step_output_handle] = value
    return outputs


class NodeExecutionResult:
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

    @property
    def handle(self) -> SolidHandle:
        raise NotImplementedError()


class InProcessSolidResult(NodeExecutionResult):
    def __init__(
        self,
        solid_def: SolidDefinition,
        handle: SolidHandle,
        all_events: List[DagsterEvent],
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._solid_def = solid_def
        self._handle = handle
        self._event_list = all_events
        self._output_capture = output_capture

    @property
    def output_values(self) -> Dict[str, Any]:
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

        return results

    @property
    def event_list(self) -> List[DagsterEvent]:
        return self._event_list

    @property
    def handle(self) -> SolidHandle:
        return self._handle


class InProcessGraphResult(NodeExecutionResult):
    def __init__(
        self,
        graph_def: GraphDefinition,
        handle: SolidHandle,
        all_events: List[DagsterEvent],
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._graph_def = graph_def
        self._handle = handle
        self._event_list = all_events
        self._output_capture = output_capture

    def _result_for_handle(self, solid: Solid, handle: SolidHandle) -> NodeExecutionResult:
        node_def = solid.definition
        events_for_handle = _filter_step_events_by_handle(self.event_list, self.handle, handle)
        outputs_for_handle = (
            _filter_outputs_by_handle(self._output_capture, self.handle, handle)
            if self._output_capture
            else None
        )
        handle_with_ancestor = handle.with_ancestor(self.handle)
        if not handle_with_ancestor:
            raise DagsterInvariantViolationError(f"No handle provided for solid {solid.name}")
        if isinstance(node_def, SolidDefinition):
            return InProcessSolidResult(
                solid_def=node_def,
                handle=handle_with_ancestor,
                all_events=events_for_handle,
                output_capture=outputs_for_handle,
            )
        else:
            return InProcessGraphResult(
                graph_def=node_def,
                handle=handle_with_ancestor,
                all_events=events_for_handle,
                output_capture=outputs_for_handle,
            )

    @property
    def output_values(self) -> Dict[str, Any]:
        values = {}

        for output_name in self._graph_def.output_dict:
            output_mapping = self._graph_def.get_output_mapping(output_name)

            inner_solid_values = self._result_for_handle(
                self._graph_def.solid_named(output_mapping.maps_from.solid_name),
                SolidHandle(output_mapping.maps_from.solid_name, None),
            ).output_values

            if inner_solid_values is not None:  # may be None if inner solid was skipped
                if output_mapping.maps_from.output_name in inner_solid_values:
                    values[output_name] = inner_solid_values[output_mapping.maps_from.output_name]

        return values

    @property
    def event_list(self) -> List[DagsterEvent]:
        return self._event_list

    @property
    def handle(self) -> SolidHandle:
        return self._handle

    def result_for_node(self, name: str) -> NodeExecutionResult:
        if not self._graph_def.has_solid_named(name):
            raise DagsterInvariantViolationError(
                "Tried to get result for node '{name}' in '{container}'. No such top level "
                "node.".format(name=name, container=self._graph_def.name)
            )
        handle = SolidHandle(name, None)
        solid = self._graph_def.get_solid(handle)
        return self._result_for_handle(solid, handle)
