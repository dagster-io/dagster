# pyright: strict

from abc import ABC, abstractmethod
from typing import AbstractSet, Callable, List, Sequence, Set, Union, cast

import dagster._check as check
from dagster._core.definitions import JobDefinition, NodeHandle
from dagster._core.definitions.events import AssetMaterialization, AssetObservation, Materialization
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.errors import DagsterError, DagsterInvariantViolationError
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    ExpectationResult,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster._core.execution.plan.step import StepKind
from dagster._core.storage.pipeline_run import DagsterRun


class ExecutionResult(ABC):
    @property
    @abstractmethod
    def job_def(self) -> JobDefinition:
        ...

    @property
    @abstractmethod
    def dagster_run(self) -> DagsterRun:
        ...

    @property
    @abstractmethod
    def all_events(self) -> Sequence[DagsterEvent]:
        ...

    @property
    @abstractmethod
    def run_id(self) -> str:
        """The unique identifier of the executed run."""
        ...

    @property
    def success(self) -> bool:
        """bool: Whether execution was successful."""
        return self.dagster_run.is_success

    @property
    def all_node_events(self) -> Sequence[DagsterEvent]:
        """List[DagsterEvent]: All dagster events from the execution."""
        step_events: List[DagsterEvent] = []

        for node_name in self.job_def.graph.node_dict.keys():
            handle = NodeHandle.from_string(node_name)
            step_events += self._filter_events_by_handle(handle)

        return step_events

    @abstractmethod
    def _get_output_for_handle(self, handle: NodeHandle, output_name: str) -> object:
        raise NotImplementedError()

    def _filter_events_by_handle(self, handle: NodeHandle) -> Sequence[DagsterEvent]:
        def _is_event_from_node(event: DagsterEvent) -> bool:
            if not event.is_step_event:
                return False
            node_handle = cast(NodeHandle, event.solid_handle)
            return node_handle.is_or_descends_from(handle)

        return self.filter_events(_is_event_from_node)

    def output_value(self, output_name: str = DEFAULT_OUTPUT) -> object:
        check.str_param(output_name, "output_name")

        graph_def = self.job_def.graph
        if not graph_def.has_output(output_name) and len(graph_def.output_mappings) == 0:
            raise DagsterInvariantViolationError(
                f"Attempted to retrieve top-level outputs for '{graph_def.name}', which has no"
                " outputs."
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
        return self._get_output_for_handle(check.not_none(origin_handle), origin_output_def.name)

    def output_for_node(self, node_str: str, output_name: str = DEFAULT_OUTPUT) -> object:
        # resolve handle of node that node_str is referring to
        target_handle = NodeHandle.from_string(node_str)
        target_node_def = self.job_def.graph.get_solid(target_handle).definition
        origin_output_def, origin_handle = target_node_def.resolve_output_to_origin(
            output_name, NodeHandle.from_string(node_str)
        )

        # retrieve output value from resolved handle
        return self._get_output_for_handle(check.not_none(origin_handle), origin_output_def.name)

    def filter_events(self, event_filter: Callable[[DagsterEvent], bool]) -> Sequence[DagsterEvent]:
        return [event for event in self.all_events if event_filter(event)]

    def events_for_node(self, node_name: str) -> Sequence[DagsterEvent]:
        """Retrieves all dagster events for a specific node.

        Args:
            node_name (str): The name of the node for which outputs should be retrieved.

        Returns:
            List[DagsterEvent]: A list of all dagster events associated with provided node name.
        """
        check.str_param(node_name, "node_name")

        return self._filter_events_by_handle(NodeHandle.from_string(node_name))

    def get_job_failure_event(self) -> DagsterEvent:
        """Returns a DagsterEvent with type DagsterEventType.PIPELINE_FAILURE if it ocurred during
        execution.
        """
        events = self.filter_events(
            lambda event: event.event_type == DagsterEventType.PIPELINE_FAILURE
        )

        if len(events) == 0:
            raise DagsterError("No event of type DagsterEventType.PIPELINE_FAILURE found.")

        return events[0]

    def get_job_success_event(self) -> DagsterEvent:
        """Returns a DagsterEvent with type DagsterEventType.PIPELINE_SUCCESS if it ocurred during
        execution.
        """
        events = self.filter_events(
            lambda event: event.event_type == DagsterEventType.PIPELINE_SUCCESS
        )

        if len(events) == 0:
            raise DagsterError("No event of type DagsterEventType.PIPELINE_SUCCESS found.")

        return events[0]

    def asset_materializations_for_node(
        self, node_name: str
    ) -> Sequence[Union[Materialization, AssetMaterialization]]:
        return [
            cast(StepMaterializationData, event.event_specific_data).materialization
            for event in self.events_for_node(node_name)
            if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION.value
        ]

    def asset_observations_for_node(self, node_name: str) -> Sequence[AssetObservation]:
        return [
            cast(AssetObservationData, event.event_specific_data).asset_observation
            for event in self.events_for_node(node_name)
            if event.event_type_value == DagsterEventType.ASSET_OBSERVATION.value
        ]

    def get_step_success_events(self) -> Sequence[DagsterEvent]:
        return [event for event in self.all_events if event.is_step_success]

    def get_step_skipped_events(self) -> Sequence[DagsterEvent]:
        return [event for event in self.all_events if event.is_step_skipped]

    def get_failed_step_keys(self) -> AbstractSet[str]:
        failure_events = self.filter_events(
            lambda event: event.is_step_failure or event.is_resource_init_failure
        )
        keys: Set[str] = set()
        for event in failure_events:
            if event.step_key:
                keys.add(event.step_key)
        return keys

    def compute_events_for_handle(self, handle: NodeHandle) -> Sequence[DagsterEvent]:
        return [
            event
            for event in self._filter_events_by_handle(handle)
            if event.step_kind == StepKind.COMPUTE
        ]

    def expectation_results_for_node(self, node_str: str) -> Sequence[ExpectationResult]:
        handle = NodeHandle.from_string(node_str)
        compute_events = self.compute_events_for_handle(handle)
        expectation_result_events = list(
            filter(
                lambda event: event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT,
                compute_events,
            )
        )
        return [
            cast(StepExpectationResultData, event.event_specific_data).expectation_result
            for event in expectation_result_events
        ]
