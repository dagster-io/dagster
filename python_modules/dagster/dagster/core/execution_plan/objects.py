from collections import namedtuple
from enum import Enum
import toposort

from dagster import (
    check,
    config,
)
from dagster.core.definitions import (
    PipelineDefinition,
    Solid,
)
from dagster.core.errors import DagsterError
from dagster.core.execution_context import RuntimeExecutionContext
from dagster.core.types import DagsterType

from pyrsistent import (PClass, field)

# class StepOutputHandle(namedtuple('_StepOutputHandle', 'step output_name')):
#     def __new__(cls, step, output_name):
#         return super(StepOutputHandle, cls).__new__(
#             cls,
#             step=check.inst_param(step, 'step', ExecutionStep),
#             output_name=check.str_param(output_name, 'output_name'),
#         )

#     # Make this hashable so it be a key in a dictionary

#     def __str__(self):
#         return (
#             'StepOutputHandle'
#             '(step="{step.key}", output_name="{output_name}")'.format(
#                 step=self.step,
#                 output_name=self.output_name,
#             )
#         )

#     def __repr__(self):
#         return (
#             'StepOutputHandle'
#             '(step="{step.key}", output_name="{output_name}")'.format(
#                 step=self.step,
#                 output_name=self.output_name,
#             )
#         )

#     def __hash__(self):
#         return hash(self.step.key + self.output_name)

#     def __eq__(self, other):
#         return self.step.key == other.step.key and self.output_name == other.output_name


class StepSuccessData(namedtuple('_StepSuccessData', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(StepSuccessData, cls).__new__(
            cls,
            output_name=check.str_param(output_name, 'output_name'),
            value=value,
        )


class StepFailureData(namedtuple('_StepFailureData', 'dagster_error')):
    def __new__(cls, dagster_error):
        return super(StepFailureData, cls).__new__(
            cls,
            dagster_error=check.inst_param(dagster_error, 'dagster_error', DagsterError),
        )


class StepResult(namedtuple(
    '_StepResult',
    'success step tag success_data failure_data',
)):
    @staticmethod
    def success_result(step, tag, success_data):
        return StepResult(
            success=True,
            step=check.inst_param(step, 'step', ExecutionStep),
            tag=check.inst_param(tag, 'tag', StepTag),
            success_data=check.inst_param(success_data, 'success_data', StepSuccessData),
            failure_data=None,
        )

    @staticmethod
    def failure_result(step, tag, failure_data):
        return StepResult(
            success=False,
            step=check.inst_param(step, 'step', ExecutionStep),
            tag=check.inst_param(tag, 'tag', StepTag),
            success_data=None,
            failure_data=check.inst_param(failure_data, 'failure_data', StepFailureData),
        )


class StepTag(Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'
    INPUT_THUNK = 'INPUT_THUNK'
    VALUE_THUNK = 'VALUE_THUNK'


class StepInput(namedtuple('_StepInput', 'name dagster_type prev_output_handle')):
    def __new__(cls, name, dagster_type, prev_output_handle):
        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type=check.inst_param(dagster_type, 'dagster_type', DagsterType),
            prev_output_handle=check.inst_param(
                prev_output_handle,
                'prev_output_handle',
                StepOutputHandle,
            ),
        )


class StepOutput(namedtuple('_StepOutput', 'name dagster_type')):
    def __new__(cls, name, dagster_type):
        return super(StepOutput, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type=check.inst_param(dagster_type, 'dagster_type', DagsterType),
        )


class ExecutionStep(
    namedtuple(
        '_ExecutionStep',
        'key step_inputs step_input_dict step_outputs step_output_dict compute_fn tag solid',
    ),
):
    def __new__(cls, key, step_inputs, step_outputs, compute_fn, tag, solid):
        return super(ExecutionStep, cls).__new__(
            cls,
            key=check.str_param(key, 'key'),
            step_inputs=check.list_param(step_inputs, 'step_inputs', of_type=StepInput),
            step_input_dict={si.name: si
                             for si in step_inputs},
            step_outputs=check.list_param(step_outputs, 'step_outputs', of_type=StepOutput),
            step_output_dict={so.name: so
                              for so in step_outputs},
            compute_fn=check.callable_param(compute_fn, 'compute_fn'),
            tag=check.inst_param(tag, 'tag', StepTag),
            solid=check.inst_param(solid, 'solid', Solid),
        )

    def with_new_inputs(self, step_inputs):
        return ExecutionStep(
            key=self.key,
            step_inputs=step_inputs,
            step_outputs=self.step_outputs,
            compute_fn=self.compute_fn,
            tag=self.tag,
            solid=self.solid,
        )

    def has_step_output(self, name):
        check.str_param(name, 'name')
        return name in self.step_output_dict

    def step_output_named(self, name):
        check.str_param(name, 'name')
        return self.step_output_dict[name]

    def has_step_input(self, name):
        check.str_param(name, 'name')
        return name in self.step_input_dict

    def step_input_named(self, name):
        check.str_param(name, 'name')
        return self.step_input_dict[name]


class StepOutputHandle(PClass):
    step_key = field(type=str, mandatory=True)
    output_name = field(type=str, mandatory=True)

    # PClass fools lint
    # pylint: disable=E1101

    def __hash__(self):
        return hash(self.step_key + ':' + self.output_name)

    def __eq__(self, other):
        return self.step_key == other.step_key and self.output_name == other.output_name


ExecutionSubPlan = namedtuple(
    'ExecutionSubPlan',
    'steps terminal_step_output_handle',
)


class ExecutionPlan(object):
    def __init__(self, step_dict, deps):
        self.step_dict = check.dict_param(
            step_dict,
            'step_dict',
            key_type=str,
            value_type=ExecutionStep,
        )
        self.deps = check.dict_param(deps, 'deps', key_type=str, value_type=set)
        self.steps = list(step_dict.values())

    def get_step_by_key(self, key):
        return self.step_dict[key]

    def topological_steps(self):
        return list(self._topological_steps())

    def _topological_steps(self):
        ordered_step_keys = toposort.toposort_flatten(self.deps)
        for step_key in ordered_step_keys:
            yield self.step_dict[step_key]


class ExecutionPlanInfo(namedtuple('_ExecutionPlanInfo', 'context pipeline environment')):
    def __new__(cls, context, pipeline, environment):
        return super(ExecutionPlanInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(pipeline, 'pipeline', PipelineDefinition),
            check.inst_param(environment, 'environment', config.Environment),
        )

    @property
    def serialize_intermediates(self):
        return self.environment.execution.serialize_intermediates


class ExecutionSubsetInfo(namedtuple('_ExecutionSubsetInfo', 'subset inputs')):
    def __new__(cls, included_steps, inputs=None):
        return super(ExecutionSubsetInfo, cls).__new__(
            cls,
            set(check.list_param(included_steps, 'included_steps', of_type=str)),
            check.opt_dict_param(inputs, 'inputs'),
        )


StepCreationInfo = namedtuple('StepCreationInfo', 'step output_handle')
