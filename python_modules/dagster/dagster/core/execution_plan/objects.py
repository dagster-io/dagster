from collections import namedtuple
from enum import Enum
import toposort

from dagster import (
    check,
    config,
)
from dagster.core.definitions import (
    ExecutionGraph,
    Solid,
)
from dagster.core.errors import DagsterError
from dagster.core.execution_context import RuntimeExecutionContext
from dagster.core.types import DagsterType


class StepOutputHandle(namedtuple('_StepOutputHandle', 'step output_name')):
    def __new__(cls, step, output_name):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step=check.inst_param(step, 'step', ExecutionStep),
            output_name=check.str_param(output_name, 'output_name'),
        )

    # Make this hashable so it be a key in a dictionary

    def __str__(self):
        return (
            'StepOutputHandle'
            '(step="{step.key}", output_name="{output_name}")'.format(
                step=self.step,
                output_name=self.output_name,
            )
        )

    def __repr__(self):
        return (
            'StepOutputHandle'
            '(step="{step.key}", output_name="{output_name}")'.format(
                step=self.step,
                output_name=self.output_name,
            )
        )

    def __hash__(self):
        return hash(self.step.key + self.output_name)

    def __eq__(self, other):
        return self.step.key == other.step.key and self.output_name == other.output_name


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


class StepInput(object):
    def __init__(self, name, dagster_type, prev_output_handle):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.prev_output_handle = check.inst_param(
            prev_output_handle,
            'prev_output_handle',
            StepOutputHandle,
        )


class StepOutput(object):
    def __init__(self, name, dagster_type):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)


class ExecutionStep(object):
    def __init__(self, key, step_inputs, step_outputs, compute_fn, tag, solid):
        self.key = check.str_param(key, 'key')

        self.step_inputs = check.list_param(step_inputs, 'step_inputs', of_type=StepInput)
        self._step_input_dict = {si.name: si for si in step_inputs}

        self.step_outputs = check.list_param(step_outputs, 'step_outputs', of_type=StepOutput)
        self._step_output_dict = {so.name: so for so in step_outputs}

        self.compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self.tag = check.inst_param(tag, 'tag', StepTag)
        self.solid = check.inst_param(solid, 'solid', Solid)

    def has_step_output(self, name):
        check.str_param(name, 'name')
        return name in self._step_output_dict

    def step_output_named(self, name):
        check.str_param(name, 'name')
        return self._step_output_dict[name]

    def has_step_input(self, name):
        check.str_param(name, 'name')
        return name in self._step_input_dict

    def step_input_named(self, name):
        check.str_param(name, 'name')
        return self._step_input_dict[name]


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
        sorted_step_guids = toposort.toposort_flatten(self.deps)
        for step_guid in sorted_step_guids:
            yield self.step_dict[step_guid]


class ExecutionPlanInfo(namedtuple('_ExecutionPlanInfo', 'context execution_graph environment')):
    def __new__(cls, context, execution_graph, environment):
        return super(ExecutionPlanInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(execution_graph, 'execution_graph', ExecutionGraph),
            check.inst_param(environment, 'environment', config.Environment),
        )

    @property
    def pipeline(self):
        return self.execution_graph.pipeline

    @property
    def serialize_intermediates(self):
        return self.environment.execution.serialize_intermediates
