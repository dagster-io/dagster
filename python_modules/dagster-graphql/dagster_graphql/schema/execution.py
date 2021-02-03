import graphene
from dagster import check
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.snap import (
    ExecutionStepInputSnap,
    ExecutionStepOutputSnap,
    ExecutionStepSnap,
    PipelineSnapshot,
)

from .dagster_types import GrapheneDagsterType, to_dagster_type
from .metadata import GrapheneMetadataItemDefinition
from .util import non_null_list


class GrapheneExecutionStepOutput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(GrapheneDagsterType))

    class Meta:
        name = "ExecutionStepOutput"

    def __init__(self, pipeline_snapshot, step_output_snap):
        super().__init__()
        self._step_output_snap = check.inst_param(
            step_output_snap, "step_output_snap", ExecutionStepOutputSnap
        )
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
        )

    def resolve_name(self, _graphene_info):
        return self._step_output_snap.name

    def resolve_type(self, _graphene_info):
        return to_dagster_type(self._pipeline_snapshot, self._step_output_snap.dagster_type_key)


class GrapheneExecutionStepInput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(GrapheneDagsterType))
    dependsOn = non_null_list(lambda: GrapheneExecutionStep)

    class Meta:
        name = "ExecutionStepInput"

    def __init__(self, pipeline_snapshot, step_input_snap, external_execution_plan):
        super().__init__()
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
        return to_dagster_type(self._pipeline_snapshot, self._step_input_snap.dagster_type_key)

    def resolve_dependsOn(self, _graphene_info):
        return [
            GrapheneExecutionStep(
                self._external_execution_plan,
                self._external_execution_plan.get_step_by_key(key),
            )
            # We filter at this layer to ensure that we do not return outputs that
            # do not exist in the execution plan
            for key in filter(
                self._external_execution_plan.key_in_plan,
                self._step_input_snap.upstream_step_keys,
            )
        ]


class GrapheneStepKind(graphene.Enum):
    COMPUTE = "COMPUTE"
    UNRESOLVED = "UNRESOLVED"

    class Meta:
        name = "StepKind"

    @property
    def description(self):
        if self == GrapheneStepKind.COMPUTE:
            return "This is a user-defined computation step"
        if self == GrapheneStepKind.UNRESOLVED:
            return "This is a computation step that has not yet been resolved"
        else:
            return None


class GrapheneExecutionStep(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    inputs = non_null_list(GrapheneExecutionStepInput)
    outputs = non_null_list(GrapheneExecutionStepOutput)
    solidHandleID = graphene.NonNull(graphene.String)
    kind = graphene.NonNull(GrapheneStepKind)
    metadata = non_null_list(GrapheneMetadataItemDefinition)

    class Meta:
        name = "ExecutionStep"

    def __init__(self, external_execution_plan, execution_step_snap):
        super().__init__()
        self._external_execution_plan = check.inst_param(
            external_execution_plan, "external_execution_plan", ExternalExecutionPlan
        )
        self._plan_snapshot = external_execution_plan.execution_plan_snapshot
        self._step_snap = check.inst_param(
            execution_step_snap, "execution_step_snap", ExecutionStepSnap
        )

    def resolve_metadata(self, _graphene_info):
        return [
            GrapheneMetadataItemDefinition(key=mdi.key, value=mdi.value)
            for mdi in self._step_snap.metadata_items
        ]

    def resolve_inputs(self, _graphene_info):
        return [
            GrapheneExecutionStepInput(
                self._external_execution_plan.represented_pipeline.pipeline_snapshot,
                inp,
                self._external_execution_plan,
            )
            for inp in self._step_snap.inputs
        ]

    def resolve_outputs(self, _graphene_info):
        return [
            GrapheneExecutionStepOutput(
                self._external_execution_plan.represented_pipeline.pipeline_snapshot,
                out,
            )
            for out in self._step_snap.outputs
        ]

    def resolve_key(self, _graphene_info):
        return self._step_snap.key

    def resolve_solidHandleID(self, _graphene_info):
        return self._step_snap.solid_handle_id

    def resolve_kind(self, _graphene_info):
        return self._step_snap.kind


class GrapheneExecutionPlan(graphene.ObjectType):
    steps = non_null_list(GrapheneExecutionStep)
    artifactsPersisted = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "ExecutionPlan"

    def __init__(self, external_execution_plan):
        super().__init__()
        self._external_execution_plan = check.inst_param(
            external_execution_plan, external_execution_plan, ExternalExecutionPlan
        )

    def resolve_steps(self, _graphene_info):
        return [
            GrapheneExecutionStep(
                self._external_execution_plan,
                self._external_execution_plan.get_step_by_key(step.key),
            )
            for step in self._external_execution_plan.get_steps_in_plan()
        ]

    def resolve_artifactsPersisted(self, _graphene_info):
        return self._external_execution_plan.execution_plan_snapshot.artifacts_persisted


types = [
    GrapheneExecutionPlan,
    GrapheneExecutionStep,
    GrapheneExecutionStepInput,
    GrapheneExecutionStepOutput,
    GrapheneStepKind,
]
