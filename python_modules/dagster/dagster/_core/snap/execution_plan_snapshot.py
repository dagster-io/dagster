from typing import Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.definitions import NodeHandle
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._core.execution.plan.inputs import (
    StepInput,
    StepInputSourceUnion,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from dagster._core.execution.plan.outputs import StepOutput, StepOutputHandle, StepOutputProperties
from dagster._core.execution.plan.plan import ExecutionPlan, StepHandleTypes, StepHandleUnion
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import (
    ExecutionStep,
    IExecutionStep,
    StepKind,
    UnresolvedCollectExecutionStep,
    UnresolvedMappedExecutionStep,
)
from dagster._serdes import create_snapshot_id, whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo

# Can be incremented on breaking changes to the snapshot (since it is used to reconstruct
# the ExecutionPlan during execution). Every time you need to bump this, consider
# adding a new snapshot folder to test in est_execution_plan_snapshot_backcompat.
CURRENT_SNAPSHOT_VERSION = 1


def create_execution_plan_snapshot_id(execution_plan_snapshot: "ExecutionPlanSnapshot") -> str:
    check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
    return create_snapshot_id(execution_plan_snapshot)


@whitelist_for_serdes(
    storage_field_names={"job_snapshot_id": "pipeline_snapshot_id"},
    skip_when_empty_fields={"repository_load_data"},
)
class ExecutionPlanSnapshot(
    NamedTuple(
        "_ExecutionPlanSnapshot",
        [
            ("steps", Sequence["ExecutionStepSnap"]),
            ("artifacts_persisted", bool),
            ("job_snapshot_id", str),
            ("step_keys_to_execute", Sequence[str]),
            ("initial_known_state", Optional[KnownExecutionState]),
            ("snapshot_version", Optional[int]),
            ("executor_name", Optional[str]),
            ("repository_load_data", Optional[RepositoryLoadData]),
        ],
    )
):
    # serdes log
    # added executor_name
    # added step_keys_to_execute
    # added initial_known_state
    # added snapshot_version (if >=1, can be used to fully reconstruct the ExecutionPlan -
    #   can be used to track breaking changes to snapshot execution format if needed)
    # added step_output_versions
    # removed step_output_versions
    # added repository_load_data

    def __new__(
        cls,
        steps: Sequence["ExecutionStepSnap"],
        artifacts_persisted: bool,
        job_snapshot_id: str,
        step_keys_to_execute: Optional[Sequence[str]] = None,
        initial_known_state: Optional[KnownExecutionState] = None,
        snapshot_version: Optional[int] = None,
        executor_name: Optional[str] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ):
        return super(ExecutionPlanSnapshot, cls).__new__(
            cls,
            steps=check.sequence_param(steps, "steps", of_type=ExecutionStepSnap),
            artifacts_persisted=check.bool_param(artifacts_persisted, "artifacts_persisted"),
            job_snapshot_id=check.str_param(job_snapshot_id, "job_snapshot_id"),
            step_keys_to_execute=check.opt_sequence_param(
                step_keys_to_execute, "step_keys_to_execute", of_type=str
            ),
            initial_known_state=check.opt_inst_param(
                initial_known_state,
                "initial_known_state",
                KnownExecutionState,
            ),
            snapshot_version=check.opt_int_param(snapshot_version, "snapshot_version"),
            executor_name=check.opt_str_param(executor_name, "executor_name"),
            repository_load_data=check.opt_inst_param(
                repository_load_data, "repository_load_data", RepositoryLoadData
            ),
        )

    @property
    def step_deps(self):
        # Construct dependency dictionary (downstream to upstreams)
        deps = {step.key: set() for step in self.steps}

        for step in self.steps:
            for step_input in step.inputs:
                deps[step.key].update(
                    [output_handle.step_key for output_handle in step_input.upstream_output_handles]
                )
        return deps

    @property
    def can_reconstruct_plan(self):
        return self.snapshot_version and self.snapshot_version > 0


@whitelist_for_serdes
class ExecutionPlanSnapshotErrorData(
    NamedTuple("_ExecutionPlanSnapshotErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExecutionPlanSnapshotErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes(storage_field_names={"node_handle_id": "solid_handle_id"})
class ExecutionStepSnap(
    NamedTuple(
        "_ExecutionStepSnap",
        [
            ("key", str),
            ("inputs", Sequence["ExecutionStepInputSnap"]),
            ("outputs", Sequence["ExecutionStepOutputSnap"]),
            ("node_handle_id", str),
            ("kind", StepKind),
            ("metadata_items", Sequence["ExecutionPlanMetadataItemSnap"]),
            ("tags", Optional[Mapping[str, str]]),
            ("step_handle", Optional[StepHandleUnion]),
        ],
    )
):
    def __new__(
        cls,
        key: str,
        inputs: Sequence["ExecutionStepInputSnap"],
        outputs: Sequence["ExecutionStepOutputSnap"],
        node_handle_id: str,
        kind: StepKind,
        metadata_items: Sequence["ExecutionPlanMetadataItemSnap"],
        tags: Optional[Mapping[str, str]] = None,
        step_handle: Optional[StepHandleUnion] = None,
    ):
        return super(ExecutionStepSnap, cls).__new__(
            cls,
            key=check.str_param(key, "key"),
            inputs=check.sequence_param(inputs, "inputs", ExecutionStepInputSnap),
            outputs=check.sequence_param(outputs, "outputs", ExecutionStepOutputSnap),
            node_handle_id=check.str_param(node_handle_id, "node_handle_id"),
            kind=check.inst_param(kind, "kind", StepKind),
            metadata_items=check.sequence_param(
                metadata_items, "metadata_items", ExecutionPlanMetadataItemSnap
            ),
            tags=check.opt_nullable_mapping_param(tags, "tags", key_type=str, value_type=str),
            step_handle=check.opt_inst_param(step_handle, "step_handle", StepHandleTypes),
        )


@whitelist_for_serdes
class ExecutionStepInputSnap(
    NamedTuple(
        "_ExecutionStepInputSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("upstream_output_handles", Sequence[StepOutputHandle]),
            ("source", Optional[StepInputSourceUnion]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        upstream_output_handles: Sequence[StepOutputHandle],
        source: Optional[StepInputSourceUnion] = None,
    ):
        return super(ExecutionStepInputSnap, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(dagster_type_key, "dagster_type_key"),
            check.sequence_param(
                upstream_output_handles, "upstream_output_handles", of_type=StepOutputHandle
            ),
            check.opt_inst_param(source, "source", StepInputSourceUnion.__args__),  # type: ignore
        )

    @property
    def upstream_step_keys(self):
        return [output_handle.step_key for output_handle in self.upstream_output_handles]


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
class ExecutionStepOutputSnap(
    NamedTuple(
        "_ExecutionStepOutputSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("node_handle", Optional[NodeHandle]),
            ("properties", Optional[StepOutputProperties]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        node_handle: Optional[NodeHandle] = None,
        properties: Optional[StepOutputProperties] = None,
    ):
        return super(ExecutionStepOutputSnap, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(dagster_type_key, "dagster_type_key"),
            check.opt_inst_param(node_handle, "node_handle", NodeHandle),
            check.opt_inst_param(properties, "properties", StepOutputProperties),
        )


@whitelist_for_serdes
class ExecutionPlanMetadataItemSnap(
    NamedTuple("_ExecutionPlanMetadataItemSnap", [("key", str), ("value", str)])
):
    def __new__(cls, key: str, value: str):
        return super(ExecutionPlanMetadataItemSnap, cls).__new__(
            cls,
            check.str_param(key, "key"),
            check.str_param(value, "value"),
        )


def _snapshot_from_step_input(step_input):
    check.inst_param(
        step_input, "step_input", (StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput)
    )
    if isinstance(step_input, (UnresolvedMappedStepInput, UnresolvedCollectStepInput)):
        upstream_output_handles = step_input.get_step_output_handle_deps_with_placeholders()
    else:
        upstream_output_handles = step_input.get_step_output_handle_dependencies()
    return ExecutionStepInputSnap(
        name=step_input.name,
        dagster_type_key=step_input.dagster_type_key,
        upstream_output_handles=upstream_output_handles,
        source=step_input.source,
    )


def _snapshot_from_step_output(step_output: StepOutput) -> ExecutionStepOutputSnap:
    check.inst_param(step_output, "step_output", StepOutput)
    return ExecutionStepOutputSnap(
        name=step_output.name,
        dagster_type_key=step_output.dagster_type_key,
        node_handle=step_output.node_handle,
        properties=step_output.properties,
    )


# def _snapshot_from_execution_step(execution_step: Union[ExecutionStep, UnresolvedMappedExecutionStep, UnresolvedCollectExecutionStep]) -> ExecutionStepSnap:
def _snapshot_from_execution_step(execution_step: IExecutionStep) -> ExecutionStepSnap:
    check.inst_param(
        execution_step,
        "execution_step",
        (ExecutionStep, UnresolvedMappedExecutionStep, UnresolvedCollectExecutionStep),
    )
    return ExecutionStepSnap(
        key=execution_step.key,
        inputs=sorted(
            list(map(_snapshot_from_step_input, execution_step.step_inputs)), key=lambda si: si.name
        ),
        outputs=sorted(
            list(map(_snapshot_from_step_output, execution_step.step_outputs)),
            key=lambda so: so.name,
        ),
        node_handle_id=execution_step.node_handle.to_string(),
        kind=execution_step.kind,
        metadata_items=(
            sorted(
                [
                    ExecutionPlanMetadataItemSnap(key=key, value=value)
                    for key, value in execution_step.tags.items()
                ],
                key=lambda md: md.key,
            )
            if execution_step.tags
            else []
        ),
        tags=execution_step.tags,
        step_handle=execution_step.handle,
    )


def snapshot_from_execution_plan(
    execution_plan: ExecutionPlan, pipeline_snapshot_id: str
) -> ExecutionPlanSnapshot:
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")

    return ExecutionPlanSnapshot(
        steps=sorted(
            list(map(_snapshot_from_execution_step, execution_plan.steps)), key=lambda es: es.key
        ),
        artifacts_persisted=execution_plan.artifacts_persisted,
        job_snapshot_id=pipeline_snapshot_id,
        step_keys_to_execute=execution_plan.step_keys_to_execute,
        initial_known_state=execution_plan.known_state,
        snapshot_version=CURRENT_SNAPSHOT_VERSION,
        executor_name=execution_plan.executor_name,
        repository_load_data=execution_plan.repository_load_data,
    )
