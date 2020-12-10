from __future__ import absolute_import

from dagster import check
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.snap import (
    ExecutionStepInputSnap,
    ExecutionStepOutputSnap,
    ExecutionStepSnap,
    PipelineSnapshot,
)
from dagster_graphql import dauphin

from .dagster_types import to_dauphin_dagster_type


class DauphinExecutionPlan(dauphin.ObjectType):
    class Meta:
        name = "ExecutionPlan"

    steps = dauphin.non_null_list("ExecutionStep")
    artifactsPersisted = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, external_execution_plan):
        super(DauphinExecutionPlan, self).__init__()
        self._external_execution_plan = check.inst_param(
            external_execution_plan, external_execution_plan, ExternalExecutionPlan
        )

    def resolve_steps(self, _graphene_info):
        return [
            DauphinExecutionStep(
                self._external_execution_plan,
                self._external_execution_plan.get_step_by_key(step.key),
            )
            for step in self._external_execution_plan.get_steps_in_plan()
        ]

    def resolve_artifactsPersisted(self, _graphene_info):
        return self._external_execution_plan.execution_plan_snapshot.artifacts_persisted


class DauphinExecutionStepOutput(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepOutput"

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull("DagsterType"))

    def __init__(self, pipeline_snapshot, step_output_snap):
        super(DauphinExecutionStepOutput, self).__init__()
        self._step_output_snap = check.inst_param(
            step_output_snap, "step_output_snap", ExecutionStepOutputSnap
        )
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
        )

    def resolve_name(self, _graphene_info):
        return self._step_output_snap.name

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(
            self._pipeline_snapshot, self._step_output_snap.dagster_type_key
        )


class DauphinExecutionStepInput(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepInput"

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull("DagsterType"))
    dependsOn = dauphin.non_null_list("ExecutionStep")

    def __init__(self, pipeline_snapshot, step_input_snap, external_execution_plan):
        super(DauphinExecutionStepInput, self).__init__()
        self._step_input_snap = check.inst_param(
            step_input_snap, "step_input_snap", ExecutionStepInputSnap
        )
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
        )
        self._external_execution_plan = check.inst_param(
            external_execution_plan, "external_execution_plan", ExternalExecutionPlan
        )

    def resolve_name(self, _graphene_info):
        return self._step_input_snap.name

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(
            self._pipeline_snapshot, self._step_input_snap.dagster_type_key
        )

    def resolve_dependsOn(self, graphene_info):
        return [
            graphene_info.schema.type_named("ExecutionStep")(
                self._external_execution_plan, self._external_execution_plan.get_step_by_key(key),
            )
            # We filter at this layer to ensure that we do not return outputs that
            # do not exist in the execution plan
            for key in filter(
                self._external_execution_plan.key_in_plan, self._step_input_snap.upstream_step_keys,
            )
        ]


class DauphinStepKind(dauphin.Enum):
    class Meta:
        name = "StepKind"

    COMPUTE = "COMPUTE"
    UNRESOLVED = "UNRESOLVED"

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in dauphin
        # so we can't do a dictionary lookup which is awesome
        if self == DauphinStepKind.COMPUTE:
            return "This is a user-defined computation step"
        if self == DauphinStepKind.UNRESOLVED:
            return "This is a computation step that has not yet been resolved"
        else:
            return None


class DauphinExecutionStep(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStep"

    key = dauphin.NonNull(dauphin.String)
    inputs = dauphin.non_null_list("ExecutionStepInput")
    outputs = dauphin.non_null_list("ExecutionStepOutput")
    solidHandleID = dauphin.NonNull(dauphin.String)
    kind = dauphin.NonNull("StepKind")
    metadata = dauphin.non_null_list("MetadataItemDefinition")

    def __init__(self, external_execution_plan, execution_step_snap):
        super(DauphinExecutionStep, self).__init__()
        self._external_execution_plan = check.inst_param(
            external_execution_plan, "external_execution_plan", ExternalExecutionPlan
        )
        self._plan_snapshot = external_execution_plan.execution_plan_snapshot
        self._step_snap = check.inst_param(
            execution_step_snap, "execution_step_snap", ExecutionStepSnap
        )

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named("MetadataItemDefinition")(key=mdi.key, value=mdi.value)
            for mdi in self._step_snap.metadata_items
        ]

    def resolve_inputs(self, graphene_info):
        return [
            graphene_info.schema.type_named("ExecutionStepInput")(
                self._external_execution_plan.represented_pipeline.pipeline_snapshot,
                inp,
                self._external_execution_plan,
            )
            for inp in self._step_snap.inputs
        ]

    def resolve_outputs(self, graphene_info):
        return [
            graphene_info.schema.type_named("ExecutionStepOutput")(
                self._external_execution_plan.represented_pipeline.pipeline_snapshot, out,
            )
            for out in self._step_snap.outputs
        ]

    def resolve_key(self, _graphene_info):
        return self._step_snap.key

    def resolve_solidHandleID(self, _graphene_info):
        return self._step_snap.solid_handle_id

    def resolve_kind(self, _graphene_info):
        return self._step_snap.kind
