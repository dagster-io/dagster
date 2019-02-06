from collections import namedtuple
from contextlib import contextmanager
import copy
from enum import Enum

import toposort
import six

from dagster import check
from dagster.utils import merge_dicts
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.definitions import PipelineDefinition, Solid, SolidOutputHandle
from dagster.core.errors import DagsterError
from dagster.core.execution_context import RuntimeExecutionContext
from dagster.core.types.runtime import RuntimeType

from .create_plan_tracker import create_plan_tracker


class StepOutputHandle:
    '''
    StepOutputHandle, abstractly, is a pointer to a particular output on a particular step
    '''

    @staticmethod
    def create(step, output_name):
        return ConcreteStepOutputHandle(step, output_name)

    @staticmethod
    def subplan_begin_sentinel():
        return SubplanBeginStepOutputHandle()


class ConcreteStepOutputHandle(
    namedtuple('_ConcreteStepOutputHandle', 'step output_name'), StepOutputHandle
):
    '''
    ConcreteStepOutputHandle is the case where there is a pointer to an actual ExecutionStep
    and an actual output.
    '''

    def __new__(cls, step, output_name):
        return super(ConcreteStepOutputHandle, cls).__new__(
            cls,
            step=check.inst_param(step, 'step', ExecutionStep),
            output_name=check.str_param(output_name, 'output_name'),
        )

    # Make this hashable so it be a key in a dictionary

    def __str__(self):
        return 'StepOutputHandle' '(step="{step.key}", output_name="{output_name}")'.format(
            step=self.step, output_name=self.output_name
        )

    def __repr__(self):
        return 'StepOutputHandle' '(step="{step.key}", output_name="{output_name}")'.format(
            step=self.step, output_name=self.output_name
        )

    def __hash__(self):
        return hash(self.step.key + self.output_name)

    def __eq__(self, other):
        return self.step.key == other.step.key and self.output_name == other.output_name


class SubplanBeginStepOutputHandle(StepOutputHandle):
    '''
    SubplanBeginStepOutputHandle is used when a step needs an output handle in order
    to index into collections keyed by StepOutputHandle, but there is no single step
    to point to. Instead, the subplan execution machinery injects a value into the
    intermediate result collection indexed by a singleton instance of this object.
    '''


class StepSuccessData(namedtuple('_StepSuccessData', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(StepSuccessData, cls).__new__(
            cls, output_name=check.str_param(output_name, 'output_name'), value=value
        )


class StepFailureData(namedtuple('_StepFailureData', 'dagster_error')):
    def __new__(cls, dagster_error):
        return super(StepFailureData, cls).__new__(
            cls, dagster_error=check.inst_param(dagster_error, 'dagster_error', DagsterError)
        )


class StepResult(namedtuple('_StepResult', 'success step kind success_data failure_data')):
    @staticmethod
    def success_result(step, kind, success_data):
        return StepResult(
            success=True,
            step=check.inst_param(step, 'step', ExecutionStep),
            kind=check.inst_param(kind, 'kind', StepKind),
            success_data=check.inst_param(success_data, 'success_data', StepSuccessData),
            failure_data=None,
        )

    @staticmethod
    def failure_result(step, kind, failure_data):
        return StepResult(
            success=False,
            step=check.inst_param(step, 'step', ExecutionStep),
            kind=check.inst_param(kind, 'kind', StepKind),
            success_data=None,
            failure_data=check.inst_param(failure_data, 'failure_data', StepFailureData),
        )

    def reraise_user_error(self):
        check.invariant(not self.success)
        if self.failure_data.dagster_error.is_user_code_error:
            six.reraise(*self.failure_data.dagster_error.original_exc_info)
        else:
            raise self.failure_data.dagster_error


class StepKind(Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'
    INPUT_THUNK = 'INPUT_THUNK'
    MATERIALIZATION_THUNK = 'MATERIALIZATION_THUNK'
    VALUE_THUNK = 'VALUE_THUNK'
    UNMARSHAL_INPUT = 'UNMARSHAL_INPUT'
    MARSHAL_OUTPUT = 'MARSHAL_OUTPUT'
    SUBPLAN_EXECUTOR = 'SUBPLAN_EXECUTOR'


class StepInput(namedtuple('_StepInput', 'name runtime_type prev_output_handle')):
    def __new__(cls, name, runtime_type, prev_output_handle):
        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            runtime_type=check.inst_param(runtime_type, 'runtime_type', RuntimeType),
            prev_output_handle=check.inst_param(
                prev_output_handle, 'prev_output_handle', StepOutputHandle
            ),
        )


class StepOutput(namedtuple('_StepOutput', 'name runtime_type')):
    def __new__(cls, name, runtime_type):
        return super(StepOutput, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            runtime_type=check.inst_param(runtime_type, 'runtime_type', RuntimeType),
        )


class ExecutionStep(
    namedtuple(
        '_ExecutionStep',
        (
            'key step_inputs step_input_dict step_outputs step_output_dict compute_fn kind solid '
            'tags subplan'
        ),
    )
):
    def __new__(cls, key, step_inputs, step_outputs, compute_fn, kind, solid, tags, subplan=None):
        if subplan:
            check.invariant(kind == StepKind.SUBPLAN_EXECUTOR)

        check.param_invariant('pipeline' in tags, 'tags', 'Step must have pipeline tag')
        check.param_invariant('solid' in tags, 'tags', 'Step must have solid tag')
        check.param_invariant('solid_definition' in tags, 'tags', 'Step must have solid tag')
        check.dict_param(tags, 'tags', key_type=str, value_type=str)

        return super(ExecutionStep, cls).__new__(
            cls,
            key=check.str_param(key, 'key'),
            step_inputs=check.list_param(step_inputs, 'step_inputs', of_type=StepInput),
            step_input_dict={si.name: si for si in step_inputs},
            step_outputs=check.list_param(step_outputs, 'step_outputs', of_type=StepOutput),
            step_output_dict={so.name: so for so in step_outputs},
            compute_fn=check.callable_param(compute_fn, 'compute_fn'),
            kind=check.inst_param(kind, 'kind', StepKind),
            solid=check.inst_param(solid, 'solid', Solid),
            tags=merge_dicts({'step_key': key}, tags),
            subplan=check.opt_inst_param(subplan, 'subplan', ExecutionPlan),
        )

    @property
    def pipeline_name(self):
        return self.tags['pipeline']

    @property
    def solid_name(self):
        return self.tags['solid']

    @property
    def solid_definition_name(self):
        return self.tags['solid_definition']

    def __getnewargs__(self):
        # print('getnewargs was called')
        return (
            self.key,
            self.step_inputs,
            self.step_outputs,
            self.compute_fn,
            self.kind,
            self.solid,
        )

    def with_new_inputs(self, step_inputs):
        return ExecutionStep(
            key=self.key,
            step_inputs=step_inputs,
            step_outputs=self.step_outputs,
            compute_fn=self.compute_fn,
            kind=self.kind,
            solid=self.solid,
            tags=self.tags,
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


class ExecutionValueSubplan(
    namedtuple('ExecutionValueSubplan', 'steps terminal_step_output_handle')
):
    '''
    A frequent pattern in the execution engine is to take a single value
    (e.g. an input or an output of a transform) and then flow that value
    value through a sequence of system-injected steps (e.g. expectations
    or materializations). This object captures that pattern. It contains
    all of the steps that comprise that Subplan and also a single output
    handle that points to output that further steps down the plan can
    depend on.
    '''

    def __new__(cls, steps, terminal_step_output_handle):
        return super(ExecutionValueSubplan, cls).__new__(
            cls,
            check.list_param(steps, 'steps', of_type=ExecutionStep),
            check.inst_param(
                terminal_step_output_handle, 'terminal_step_output_handle', StepOutputHandle
            ),
        )

    @staticmethod
    def empty(terminal_step_output_handle):
        return ExecutionValueSubplan([], terminal_step_output_handle)


class ExecutionPlan(object):
    def __init__(self, plan_id, step_dict, deps):
        self.plan_id = check.str_param(plan_id, 'plan_id')
        self.step_dict = check.dict_param(
            step_dict, 'step_dict', key_type=str, value_type=ExecutionStep
        )
        self.deps = check.dict_param(deps, 'deps', key_type=str, value_type=set)
        self.steps = self.topological_steps()

    def has_step(self, key):
        check.str_param(key, 'key')
        return key in self.step_dict

    def get_step_by_key(self, key):
        check.str_param(key, 'key')
        return self.step_dict[key]

    def topological_steps(self):
        return list(self._topological_steps())

    def _topological_steps(self):
        ordered_step_keys = toposort.toposort_flatten(self.deps)
        for step_key in ordered_step_keys:
            yield self.step_dict[step_key]


class CreateExecutionPlanInfo(
    namedtuple('_ExecutionPlanInfo', 'context pipeline environment plan_tracker')
):
    def __new__(cls, context, pipeline, environment):
        return super(CreateExecutionPlanInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(pipeline, 'pipeline', PipelineDefinition),
            check.inst_param(environment, 'environment', EnvironmentConfig),
            create_plan_tracker(pipeline),
        )

    def plan_id_for_solid(self, solid):
        return self.plan_tracker.plan_stacks[solid.name][-1]


class StepOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        return dict.__setitem__(self, key, val)


# This is the state that is built up during the execution plan build process.
# steps is just a list of the steps that have been created
# step_output_map maps logical solid outputs (solid_name, output_name) to particular
# step outputs. This covers the case where a solid maps to multiple steps
# and one wants to be able to attach to the logical output of a solid during execution
class PlanBuilder:
    def __init__(self, plan_id, solid_names, existing_plans, pipeline_name, initial_tags=None):
        self._plan_id = check.str_param(plan_id, 'plan_id')
        self._solid_names = check.list_param(solid_names, 'solid_names', of_type=str)
        self._existing_plans = check.dict_param(
            existing_plans, 'existing_plans', key_type=str, value_type=ExecutionPlan
        )

        self._steps = []
        self._step_output_map = StepOutputMap()
        self._plan_output_map = {}
        self._tags = check.opt_dict_param(
            initial_tags, 'initial_tags', key_type=str, value_type=str
        )
        self._tags['pipeline'] = pipeline_name

    def add_step(self, step):
        check.inst_param(step, 'step', ExecutionStep)
        self._steps.append(step)

    def add_steps(self, steps):
        check.list_param(steps, 'steps', of_type=ExecutionStep)
        self._steps.extend(steps)

    def get_steps(self):
        return copy.copy(self._steps)

    def get_existing_plan(self, plan_id):
        return self._existing_plans[plan_id]

    def get_step_output_handle_for_plan_id(self, plan_id):
        check.str_param(plan_id, 'plan_id')
        return self._plan_output_map[plan_id]

    def set_step_output_handle_for_plan_id(self, plan_id, step_output_handle):
        check.str_param(plan_id, 'plan_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(plan_id not in self._plan_output_map)
        self._plan_output_map[plan_id] = step_output_handle

    def get_step_output_for_solid_output_handle(self, solid_output_handle):
        check.inst_param(solid_output_handle, 'solid_output_handle', SolidOutputHandle)
        return self._step_output_map[solid_output_handle]

    def set_step_output_for_solid_output_handle(self, solid_output_handle, step_output_handle):
        check.inst_param(solid_output_handle, 'solid_output_handle', SolidOutputHandle)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(solid_output_handle not in self._step_output_map)
        self._step_output_map[solid_output_handle] = step_output_handle

    @property
    def plan_id(self):
        return self._plan_id

    def get_solid_names(self):
        return copy.copy(self._solid_names)

    def get_tags(self, **additional_tags):
        additional_tags.update(self._tags)
        return additional_tags

    @contextmanager
    def push_tags(self, **kwargs):
        old_tags = copy.copy(self._tags)
        self._tags.update(kwargs)
        try:
            yield
        finally:
            self._tags = old_tags


# class StepOutputMap(dict):
#     def __getitem__(self, key):
#         check.inst_param(key, 'key', SolidOutputHandle)
#         return dict.__getitem__(self, key)

#     def __setitem__(self, key, val):
#         check.inst_param(key, 'key', SolidOutputHandle)
#         check.inst_param(val, 'val', StepOutputHandle)
#         return dict.__setitem__(self, key, val)
