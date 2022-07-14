from abc import ABC, abstractmethod
from typing import Any, List, Mapping, Optional, Sequence, Union, cast

import dagster._check as check
from dagster.core.definitions import JobDefinition, NodeDefinition, NodeHandle
from dagster.core.definitions.events import AssetMaterialization, AssetObservation, Materialization
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterError, DagsterInvariantViolationError
from dagster.core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)
from dagster.core.execution.context.system import PlanExecutionContext
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import StepKind
from dagster.core.execution.plan.utils import build_resources_for_manager
from dagster.core.storage.pipeline_run import DagsterRun

from .execution_result import ExecutionResult


class ExecuteJobResultContext:
    def __init__(self, job_def, reconstruct_context, event_list, dagster_run):
        self._job_def = job_def
        self._reconstruct_context = reconstruct_context
        self._event_list = event_list
        self._dagster_run = dagster_run


class ExecuteJobResult(ExecutionResult):
    def __init__(self, job_def, reconstruct_context, event_list, dagster_run):
        self._job_def = job_def
        self._reconstruct_context = reconstruct_context
        self._context = None
        self._event_list = event_list
        self._dagster_run = dagster_run

    def __enter__(self) -> "ExecuteJobResult":
        context = self._reconstruct_context.__enter__()
        self._context = context
        return self

    def __exit__(self, *exc):
        return self._reconstruct_context.__exit__(*exc)

    @property
    def job_def(self) -> JobDefinition:
        return self._job_def

    @property
    def dagster_run(self) -> DagsterRun:
        return self._dagster_run

    @property
    def all_events(self) -> Sequence[DagsterEvent]:
        return self._event_list

    @property
    def run_id(self) -> str:
        return self.dagster_run.run_id

    def compute_events_for_handle(self, handle: NodeHandle) -> Sequence[DagsterEvent]:
        return [
            event
            for event in self._filter_events_by_handle(handle)
            if event.step_kind == StepKind.COMPUTE
        ]

    def _get_output_for_handle(self, handle: NodeHandle, output_name: str) -> Any:
        if not self._context:
            raise DagsterInvariantViolationError(
                "In order to access output objects, the result of `execute_job` must be opened as a context manager: 'with execute_job(...) as result:"
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
                step = self._context.execution_plan.get_step_by_key(compute_step_event.step_key)
                dagster_type = (
                    self.job_def.get_solid(handle).output_def_named(output_name).dagster_type
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
                        result[
                            mapping_key
                        ] = value  # pylint:disable=unsupported-assignment-operation
                else:
                    result = value

        if found:
            return result

        node = self.job_def.get_solid(handle)
        raise DagsterInvariantViolationError(
            f"Did not find result {output_name} in {node.describe_node()} " "execution result"
        )

    def _get_value(self, context, step_output_data, dagster_type):
        step_output_handle = step_output_data.step_output_handle
        manager = context.get_io_manager(step_output_handle)
        manager_key = context.execution_plan.get_manager_key(step_output_handle, self.job_def)
        res = manager.load_input(
            context.for_input_manager(
                name=None,
                config=None,
                metadata=None,
                dagster_type=dagster_type,
                source_handle=step_output_handle,
                resource_config=context.resolved_run_config.resources[manager_key].config,
                resources=build_resources_for_manager(manager_key, context),
            )
        )
        return res
