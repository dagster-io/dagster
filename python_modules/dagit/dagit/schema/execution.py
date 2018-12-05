import graphene

from dagster import check
import dagster.core.execution_plan

from . import pipelines
from .utils import non_null_list


class ExecutionPlan(graphene.ObjectType):
    steps = non_null_list(lambda: ExecutionStep)
    pipeline = graphene.NonNull(lambda: pipelines.Pipeline)

    def __init__(self, pipeline, execution_plan):
        super(ExecutionPlan, self).__init__()
        self.execution_plan = check.inst_param(
            execution_plan,
            'execution_plan',
            dagster.core.execution_plan.ExecutionPlan,
        )
        self.pipeline = check.inst_param(pipeline, 'pipeline', pipelines.Pipeline)

    def resolve_steps(self, _info):
        return [ExecutionStep(cn) for cn in self.execution_plan.topological_steps()]


class ExecutionStepOutput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(lambda: pipelines.Type))

    def __init__(self, execution_step_output):
        super(ExecutionStepOutput, self).__init__()
        self.execution_step_output = check.inst_param(
            execution_step_output,
            'execution_step_output',
            dagster.core.execution_plan.StepOutput,
        )

    def resolve_name(self, _info):
        return self.execution_step_output.name

    def resolve_type(self, _info):
        return pipelines.Type.from_dagster_type(
            dagster_type=self.execution_step_output.dagster_type
        )


class ExecutionStepInput(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.Field(graphene.NonNull(lambda: pipelines.Type))
    dependsOn = graphene.Field(graphene.NonNull(lambda: ExecutionStep))

    def __init__(self, execution_step_input):
        super(ExecutionStepInput, self).__init__()
        self.execution_step_input = check.inst_param(
            execution_step_input,
            'execution_step_input',
            dagster.core.execution_plan.StepInput,
        )

    def resolve_name(self, _info):
        return self.execution_step_input.name

    def resolve_type(self, _info):
        return pipelines.Type.from_dagster_type(dagster_type=self.execution_step_input.dagster_type)

    def resolve_dependsOn(self, _info):
        return ExecutionStep(self.execution_step_input.prev_output_handle.step)


class StepTag(graphene.Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in graphene
        # so we can't do a dictionary lookup which is awesome
        if self == StepTag.TRANSFORM:
            return 'This is the user-defined transform step'
        elif self == StepTag.INPUT_EXPECTATION:
            return 'Expectation defined on an input'
        elif self == StepTag.OUTPUT_EXPECTATION:
            return 'Expectation defined on an output'
        elif self == StepTag.JOIN:
            return '''Sometimes we fan out compute on identical values
(e.g. multiple expectations in parallel). We synthesizie these in a join step to consolidate to
a single output that the next computation can depend on.
'''
        elif self == StepTag.SERIALIZE:
            return '''This is a special system-defined step to serialize
an intermediate value if the pipeline is configured to do that.'''
        else:
            return 'Unknown enum {value}'.format(value=self)


class ExecutionStep(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    inputs = non_null_list(lambda: ExecutionStepInput)
    outputs = non_null_list(lambda: ExecutionStepOutput)
    solid = graphene.NonNull(lambda: pipelines.Solid)
    tag = graphene.NonNull(lambda: StepTag)

    def __init__(self, execution_step):
        super(ExecutionStep, self).__init__()
        self.execution_step = check.inst_param(
            execution_step,
            'execution_step',
            dagster.core.execution_plan.ExecutionStep,
        )

    def resolve_inputs(self, _info):
        return [ExecutionStepInput(inp) for inp in self.execution_step.step_inputs]

    def resolve_outputs(self, _info):
        return [ExecutionStepOutput(out) for out in self.execution_step.step_outputs]

    def resolve_name(self, _info):
        return self.execution_step.key

    def resolve_solid(self, _info):
        return pipelines.Solid(self.execution_step.solid)

    def resolve_tag(self, _info):
        return self.execution_step.tag
