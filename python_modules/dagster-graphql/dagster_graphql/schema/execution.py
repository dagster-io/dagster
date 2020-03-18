from __future__ import absolute_import

from dagster_graphql import dauphin
from dagster_graphql.schema.runtime_types import to_dauphin_dagster_type

from dagster import check
from dagster.core.execution.plan.objects import ExecutionStep, StepInput, StepOutput
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.snap.pipeline_snapshot import PipelineSnapshot


class DauphinExecutionPlan(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionPlan'

    steps = dauphin.non_null_list('ExecutionStep')
    pipeline = dauphin.NonNull('PipelineReference')
    artifactsPersisted = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, pipeline, execution_plan):
        super(DauphinExecutionPlan, self).__init__(pipeline=pipeline)
        self._execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    def resolve_steps(self, _graphene_info):
        return [
            DauphinExecutionStep(self._execution_plan, step)
            for step in self._execution_plan.topological_steps()
        ]

    def resolve_artifactsPersisted(self, _graphene_info):
        return self._execution_plan.artifacts_persisted


class DauphinExecutionStepOutput(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepOutput'

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull('RuntimeType'))

    def __init__(self, pipeline_snapshot, step_output):
        super(DauphinExecutionStepOutput, self).__init__()
        self._step_output = check.inst_param(step_output, 'step_output', StepOutput)
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

    def resolve_name(self, _graphene_info):
        return self._step_output.name

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(self._pipeline_snapshot, self._step_output.dagster_type.key)


class DauphinExecutionStepInput(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepInput'

    name = dauphin.NonNull(dauphin.String)
    type = dauphin.Field(dauphin.NonNull('RuntimeType'))
    dependsOn = dauphin.non_null_list('ExecutionStep')

    def __init__(self, pipeline_snapshot, execution_plan, step_input):
        super(DauphinExecutionStepInput, self).__init__()
        self._step_input = check.inst_param(step_input, 'step_input', StepInput)
        self._execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

    def resolve_name(self, _graphene_info):
        return self._step_input.name

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(self._pipeline_snapshot, self._step_input.dagster_type.key)

    def resolve_dependsOn(self, graphene_info):
        return [
            graphene_info.schema.type_named('ExecutionStep')(
                self._execution_plan, self._execution_plan.get_step_by_key(key)
            )
            for key in self._step_input.dependency_keys
        ]


class DauphinStepKind(dauphin.Enum):
    class Meta(object):
        name = 'StepKind'

    COMPUTE = 'COMPUTE'

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in dauphin
        # so we can't do a dictionary lookup which is awesome
        if self == DauphinStepKind.COMPUTE:
            return 'This is the user-defined computation step'
        else:
            return None


class DauphinExecutionStep(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStep'

    key = dauphin.NonNull(dauphin.String)
    inputs = dauphin.non_null_list('ExecutionStepInput')
    outputs = dauphin.non_null_list('ExecutionStepOutput')
    solidHandleID = dauphin.NonNull(dauphin.String)
    kind = dauphin.NonNull('StepKind')
    metadata = dauphin.non_null_list('MetadataItemDefinition')

    def __init__(self, execution_plan, execution_step):
        super(DauphinExecutionStep, self).__init__()
        self._execution_step = check.inst_param(execution_step, 'execution_step', ExecutionStep)
        self._execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named('MetadataItemDefinition')(key=key, value=value)
            for key, value in self._execution_step.tags.items()
        ]

    def resolve_inputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('ExecutionStepInput')(
                self._execution_plan.pipeline_def.get_pipeline_snapshot(),
                self._execution_plan,
                inp,
            )
            for inp in self._execution_step.step_inputs
        ]

    def resolve_outputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('ExecutionStepOutput')(
                self._execution_plan.pipeline_def.get_pipeline_snapshot(), out,
            )
            for out in self._execution_step.step_outputs
        ]

    def resolve_key(self, _graphene_info):
        return self._execution_step.key

    def resolve_solidHandleID(self, _graphene_info):
        return str(self._execution_step.solid_handle)

    def resolve_kind(self, _graphene_info):
        return self._execution_step.kind
