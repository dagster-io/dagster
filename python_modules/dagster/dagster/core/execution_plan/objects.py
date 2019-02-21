from collections import namedtuple
from enum import Enum

import six

from dagster import check
from dagster.core.definitions import Solid, PipelineDefinition
from dagster.core.errors import DagsterError
from dagster.core.execution_context import PipelineExecutionContext, StepExecutionContext
from dagster.core.types.runtime import RuntimeType
from dagster.core.utils import toposort, toposort_flatten
from dagster.utils import merge_dicts


class StepOutputValue(namedtuple('_StepOutputValue', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(StepOutputValue, cls).__new__(
            cls, output_name=check.str_param(output_name, 'output_name'), value=value
        )


class StepOutputHandle(namedtuple('_StepOutputHandle', 'step output_name')):
    def __new__(cls, step, output_name):
        return super(StepOutputHandle, cls).__new__(
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


class ExecutionStepEventType(Enum):
    STEP_OUTPUT = 'STEP_OUTPUT'
    STEP_FAILURE = 'STEP_FAILURE'


class ExecutionStepEvent(
    namedtuple('_ExecutionStepEvent', 'event_type step success_data failure_data tags')
):
    def __new__(cls, event_type, step, success_data, failure_data, tags):
        return super(ExecutionStepEvent, cls).__new__(
            cls,
            check.inst_param(event_type, 'event_type', ExecutionStepEventType),
            check.inst_param(step, 'step', ExecutionStep),
            check.opt_inst_param(success_data, 'success_data', StepSuccessData),
            check.opt_inst_param(failure_data, 'failure_data', StepFailureData),
            check.dict_param(tags, 'tags'),
        )

    @property
    def is_step_success(self):
        return not self.is_step_failure

    @property
    def is_successful_output(self):
        return self.event_type == ExecutionStepEventType.STEP_OUTPUT

    @property
    def is_step_failure(self):
        return self.event_type == ExecutionStepEventType.STEP_FAILURE

    @staticmethod
    def step_output_event(step_context, success_data):
        check.inst_param(step_context, 'step_context', StepExecutionContext)

        return ExecutionStepEvent(
            event_type=ExecutionStepEventType.STEP_OUTPUT,
            step=step_context.step,
            success_data=check.inst_param(success_data, 'success_data', StepSuccessData),
            failure_data=None,
            tags=step_context.tags,
        )

    @staticmethod
    def step_failure_event(step_context, failure_data):
        check.inst_param(step_context, 'step_context', StepExecutionContext)

        return ExecutionStepEvent(
            event_type=ExecutionStepEventType.STEP_FAILURE,
            step=step_context.step,
            success_data=None,
            failure_data=check.inst_param(failure_data, 'failure_data', StepFailureData),
            tags=step_context.tags,
        )

    def reraise_user_error(self):
        check.invariant(self.event_type == ExecutionStepEventType.STEP_FAILURE)
        if self.failure_data.dagster_error.is_user_code_error:
            six.reraise(*self.failure_data.dagster_error.original_exc_info)
        else:
            raise self.failure_data.dagster_error

    @property
    def kind(self):
        return self.step.kind


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
            'pipeline_context key step_inputs step_input_dict step_outputs step_output_dict '
            'compute_fn kind solid tags'
        ),
    )
):
    def __new__(
        cls, pipeline_context, key, step_inputs, step_outputs, compute_fn, kind, solid, tags=None
    ):
        return super(ExecutionStep, cls).__new__(
            cls,
            pipeline_context=check.inst_param(
                pipeline_context, 'pipeline_context', PipelineExecutionContext
            ),
            key=check.str_param(key, 'key'),
            step_inputs=check.list_param(step_inputs, 'step_inputs', of_type=StepInput),
            step_input_dict={si.name: si for si in step_inputs},
            step_outputs=check.list_param(step_outputs, 'step_outputs', of_type=StepOutput),
            step_output_dict={so.name: so for so in step_outputs},
            compute_fn=check.callable_param(compute_fn, 'compute_fn'),
            kind=check.inst_param(kind, 'kind', StepKind),
            solid=check.inst_param(solid, 'solid', Solid),
            tags=merge_dicts(
                merge_dicts(
                    {
                        'step_key': key,
                        'pipeline': pipeline_context.pipeline_def.name,
                        'solid': solid.name,
                        'solid_definition': solid.definition.name,
                    },
                    check.opt_dict_param(tags, 'tags'),
                ),
                pipeline_context.tags,
            ),
        )

    @property
    def pipeline_name(self):
        return self.pipeline_context.pipeline_def.name

    @property
    def solid_name(self):
        return self.solid.name

    @property
    def solid_definition_name(self):
        return self.solid.definition.name

    def __getnewargs__(self):
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
            pipeline_context=self.pipeline_context,
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


class ExecutionPlan(namedtuple('_ExecutionPlan', 'pipeline_def step_dict, deps, steps')):
    def __new__(cls, pipeline_def, step_dict, deps):
        return super(ExecutionPlan, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            step_dict=check.dict_param(
                step_dict, 'step_dict', key_type=str, value_type=ExecutionStep
            ),
            deps=check.dict_param(deps, 'deps', key_type=str, value_type=set),
            steps=list(step_dict.values()),
        )

    def has_step(self, key):
        check.str_param(key, 'key')
        return key in self.step_dict

    def get_step_by_key(self, key):
        check.str_param(key, 'key')
        return self.step_dict[key]

    def topological_steps(self):
        return [step for step_level in self.topological_step_levels() for step in step_level]

    def topological_step_levels(self):
        return [
            [self.step_dict[step_key]]
            for step_key_level in toposort(self.deps)
            for step_key in step_key_level
        ]
