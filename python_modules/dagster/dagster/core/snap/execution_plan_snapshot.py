from collections import namedtuple

from dagster import check
from dagster.core.execution.plan.inputs import StepInput, UnresolvedStepInput
from dagster.core.execution.plan.outputs import StepOutput, StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.plan.step import ExecutionStep, StepKind, UnresolvedExecutionStep
from dagster.serdes import create_snapshot_id, whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


def create_execution_plan_snapshot_id(execution_plan_snapshot):
    check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
    return create_snapshot_id(execution_plan_snapshot)


@whitelist_for_serdes
class ExecutionPlanSnapshot(
    namedtuple(
        "_ExecutionPlanSnapshot",
        "steps artifacts_persisted pipeline_snapshot_id step_keys_to_execute",
    )
):
    # serdes log
    # added step_keys_to_execute
    def __new__(cls, steps, artifacts_persisted, pipeline_snapshot_id, step_keys_to_execute=None):
        return super(ExecutionPlanSnapshot, cls).__new__(
            cls,
            steps=check.list_param(steps, "steps", of_type=ExecutionStepSnap),
            artifacts_persisted=check.bool_param(artifacts_persisted, "artifacts_persisted"),
            pipeline_snapshot_id=check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id"),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, "step_keys_to_execute", of_type=str
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


@whitelist_for_serdes
class ExecutionPlanSnapshotErrorData(namedtuple("_ExecutionPlanSnapshotErrorData", "error")):
    def __new__(cls, error):
        return super(ExecutionPlanSnapshotErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExecutionStepSnap(
    namedtuple("_ExecutionStepSnap", "key inputs outputs solid_handle_id kind metadata_items")
):
    def __new__(cls, key, inputs, outputs, solid_handle_id, kind, metadata_items):
        return super(ExecutionStepSnap, cls).__new__(
            cls,
            key=check.str_param(key, "key"),
            inputs=check.list_param(inputs, "inputs", ExecutionStepInputSnap),
            outputs=check.list_param(outputs, "outputs", ExecutionStepOutputSnap),
            solid_handle_id=check.str_param(solid_handle_id, "solid_handle_id"),
            kind=check.inst_param(kind, "kind", StepKind),
            metadata_items=check.list_param(
                metadata_items, "metadata_items", ExecutionPlanMetadataItemSnap
            ),
        )


@whitelist_for_serdes
class ExecutionStepInputSnap(
    namedtuple("_ExecutionStepInputSnap", "name dagster_type_key upstream_output_handles")
):
    def __new__(cls, name, dagster_type_key, upstream_output_handles):
        return super(ExecutionStepInputSnap, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(dagster_type_key, "dagster_type_key"),
            check.list_param(
                upstream_output_handles, "upstream_output_handles", of_type=StepOutputHandle
            ),
        )

    @property
    def upstream_step_keys(self):
        return [output_handle.step_key for output_handle in self.upstream_output_handles]


@whitelist_for_serdes
class ExecutionStepOutputSnap(namedtuple("_ExecutionStepOutputSnap", "name dagster_type_key")):
    def __new__(cls, name, dagster_type_key):
        return super(ExecutionStepOutputSnap, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(dagster_type_key, "dagster_type_key"),
        )


@whitelist_for_serdes
class ExecutionPlanMetadataItemSnap(namedtuple("_ExecutionPlanMetadataItemSnap", "key value")):
    def __new__(cls, key, value):
        return super(ExecutionPlanMetadataItemSnap, cls).__new__(
            cls,
            check.str_param(key, "key"),
            check.str_param(value, "value"),
        )


def _snapshot_from_step_input(step_input):
    check.inst_param(step_input, "step_input", (StepInput, UnresolvedStepInput))
    if isinstance(step_input, UnresolvedStepInput):
        upstream_output_handles = step_input.get_step_output_handle_deps_with_placeholders()
    else:
        upstream_output_handles = step_input.get_step_output_handle_dependencies()
    return ExecutionStepInputSnap(
        name=step_input.name,
        dagster_type_key=step_input.dagster_type_key,
        upstream_output_handles=upstream_output_handles,
    )


def _snapshot_from_step_output(step_output):
    check.inst_param(step_output, "step_output", StepOutput)
    return ExecutionStepOutputSnap(
        name=step_output.name, dagster_type_key=step_output.dagster_type_key
    )


def _snapshot_from_execution_step(execution_step):
    check.inst_param(execution_step, "execution_step", (ExecutionStep, UnresolvedExecutionStep))
    return ExecutionStepSnap(
        key=execution_step.key,
        inputs=sorted(
            list(map(_snapshot_from_step_input, execution_step.step_inputs)), key=lambda si: si.name
        ),
        outputs=sorted(
            list(map(_snapshot_from_step_output, execution_step.step_outputs)),
            key=lambda so: so.name,
        ),
        solid_handle_id=execution_step.solid_handle.to_string(),
        kind=execution_step.kind,
        metadata_items=sorted(
            [
                ExecutionPlanMetadataItemSnap(key=key, value=value)
                for key, value in execution_step.tags.items()
            ],
            key=lambda md: md.key,
        )
        if execution_step.tags
        else [],
    )


def snapshot_from_execution_plan(execution_plan, pipeline_snapshot_id):
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")

    return ExecutionPlanSnapshot(
        steps=sorted(
            list(map(_snapshot_from_execution_step, execution_plan.steps)), key=lambda es: es.key
        ),
        artifacts_persisted=execution_plan.artifacts_persisted,
        pipeline_snapshot_id=pipeline_snapshot_id,
        step_keys_to_execute=execution_plan.step_keys_to_execute,
    )
