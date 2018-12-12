from __future__ import absolute_import

from dagster import check
import dagster.core.execution_plan

from dagit.schema import dauphene


class ExecutionPlan(dauphene.ObjectType):
    steps = dauphene.non_null_list('ExecutionStep')
    pipeline = dauphene.NonNull('Pipeline')

    def __init__(self, pipeline, execution_plan):
        super(ExecutionPlan, self).__init__(pipeline=pipeline)
        self.execution_plan = check.inst_param(
            execution_plan,
            'execution_plan',
            dagster.core.execution_plan.ExecutionPlan,
        )

    def resolve_steps(self, _info):
        return [ExecutionStep(cn) for cn in self.execution_plan.topological_steps()]


class ExecutionStepOutput(dauphene.ObjectType):
    name = dauphene.NonNull(dauphene.String)
    type = dauphene.Field(dauphene.NonNull('Type'))

    def __init__(self, execution_step_output):
        super(ExecutionStepOutput, self).__init__()
        self.execution_step_output = check.inst_param(
            execution_step_output,
            'execution_step_output',
            dagster.core.execution_plan.StepOutput,
        )

    def resolve_name(self, _info):
        return self.execution_step_output.name

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(
            info, dagster_type=self.execution_step_output.dagster_type
        )


class ExecutionStepInput(dauphene.ObjectType):
    name = dauphene.NonNull(dauphene.String)
    type = dauphene.Field(dauphene.NonNull('Type'))
    dependsOn = dauphene.Field(dauphene.NonNull('ExecutionStep'))

    def __init__(self, execution_step_input):
        super(ExecutionStepInput, self).__init__()
        self.execution_step_input = check.inst_param(
            execution_step_input,
            'execution_step_input',
            dagster.core.execution_plan.StepInput,
        )

    def resolve_name(self, _info):
        return self.execution_step_input.name

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(
            info, dagster_type=self.execution_step_input.dagster_type
        )

    def resolve_dependsOn(self, info):
        return info.schema.ExecutionStep(self.execution_step_input.prev_output_handle.step)


class StepTag(dauphene.Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'

    @property
    def description(self):
        # self ends up being the internal class "EnumMeta" in dauphene
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


class ExecutionStep(dauphene.ObjectType):
    name = dauphene.NonNull(dauphene.String)
    inputs = dauphene.non_null_list('ExecutionStepInput')
    outputs = dauphene.non_null_list('ExecutionStepOutput')
    solid = dauphene.NonNull('Solid')
    tag = dauphene.NonNull('StepTag')

    def __init__(self, execution_step):
        super(ExecutionStep, self).__init__()
        self.execution_step = check.inst_param(
            execution_step,
            'execution_step',
            dagster.core.execution_plan.ExecutionStep,
        )

    def resolve_inputs(self, info):
        return [info.schema.ExecutionStepInput(inp) for inp in self.execution_step.step_inputs]

    def resolve_outputs(self, info):
        return [info.schema.ExecutionStepOutput(out) for out in self.execution_step.step_outputs]

    def resolve_name(self, _info):
        return self.execution_step.key

    def resolve_solid(self, info):
        return info.schema.Solid(self.execution_step.solid)

    def resolve_tag(self, _info):
        return self.execution_step.tag
