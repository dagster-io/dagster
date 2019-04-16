from collections import namedtuple
from enum import Enum


from dagster import check
from dagster.core.definitions import Solid, PipelineDefinition
from dagster.core.intermediates_manager import StepOutputHandle, RunStorageMode
from dagster.core.types.runtime import RuntimeType
from dagster.core.utils import toposort
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo


class StepOutputValue(namedtuple('_StepOutputValue', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(StepOutputValue, cls).__new__(
            cls, output_name=check.str_param(output_name, 'output_name'), value=value
        )


class SingleOutputStepCreationData(namedtuple('SingleOutputStepCreationData', 'step output_name')):
    '''
    It is very common for step creation to involve processing a single value (e.g. an input thunk).
    This tuple is meant to be used by those functions to return both a new step and the output
    that deals with the value in question.
    '''

    @property
    def step_output_handle(self):
        return StepOutputHandle.from_step(self.step, self.output_name)


class StepOutputData(
    namedtuple(
        '_StepOutputData', 'step_output_handle value_repr storage_object_id storage_mode_value'
    )
):
    def __new__(cls, step_output_handle, value_repr, storage_object_id, storage_mode_value):
        check.inst_param(RunStorageMode(storage_mode_value), 'storage_mode', RunStorageMode)
        return super(StepOutputData, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, 'step_output_handle', StepOutputHandle
            ),
            value_repr=check.str_param(value_repr, 'value_repr'),
            storage_object_id=check.str_param(storage_object_id, 'storage_object_id'),
            storage_mode_value=check.str_param(storage_mode_value, 'storage_mode_value'),
        )

    @property
    def output_name(self):
        return self.step_output_handle.output_name

    @property
    def storage_mode(self):
        return RunStorageMode(self.storage_mode_value)


class StepFailureData(namedtuple('_StepFailureData', 'error')):
    def __new__(cls, error):
        return super(StepFailureData, cls).__new__(
            cls, error=check.inst_param(error, 'error', SerializableErrorInfo)
        )


class StepSuccessData(namedtuple('_StepSuccessData', 'duration_ms')):
    def __new__(cls, duration_ms):
        return super(StepSuccessData, cls).__new__(
            cls, duration_ms=check.float_param(duration_ms, 'duration_ms')
        )


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


class StepOutput(namedtuple('_StepOutput', 'name runtime_type optional')):
    def __new__(cls, name, runtime_type, optional):
        return super(StepOutput, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            runtime_type=check.inst_param(runtime_type, 'runtime_type', RuntimeType),
            optional=check.bool_param(optional, 'optional'),
        )


class ExecutionStep(
    namedtuple(
        '_ExecutionStep',
        (
            'pipeline_name key step_inputs step_input_dict step_outputs step_output_dict '
            'compute_fn kind solid tags'
        ),
    )
):
    def __new__(
        cls, pipeline_name, key, step_inputs, step_outputs, compute_fn, kind, solid, tags=None
    ):
        return super(ExecutionStep, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            key=check.str_param(key, 'key'),
            step_inputs=check.list_param(step_inputs, 'step_inputs', of_type=StepInput),
            step_input_dict={si.name: si for si in step_inputs},
            step_outputs=check.list_param(step_outputs, 'step_outputs', of_type=StepOutput),
            step_output_dict={so.name: so for so in step_outputs},
            compute_fn=check.callable_param(compute_fn, 'compute_fn'),
            kind=check.inst_param(kind, 'kind', StepKind),
            solid=check.inst_param(solid, 'solid', Solid),
            tags=merge_dicts(
                {
                    'step_key': key,
                    'pipeline': pipeline_name,
                    'solid': solid.name,
                    'solid_definition': solid.definition.name,
                },
                check.opt_dict_param(tags, 'tags'),
            ),
        )

    @property
    def solid_name(self):
        return self.solid.name

    @property
    def solid_definition_name(self):
        return self.solid.definition.name

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


class ExecutionPlan(
    namedtuple('_ExecutionPlan', 'pipeline_def step_dict deps steps artifacts_persisted')
):
    def __new__(cls, pipeline_def, step_dict, deps, artifacts_persisted):
        return super(ExecutionPlan, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            step_dict=check.dict_param(
                step_dict, 'step_dict', key_type=str, value_type=ExecutionStep
            ),
            deps=check.dict_param(deps, 'deps', key_type=str, value_type=set),
            steps=list(step_dict.values()),
            artifacts_persisted=check.bool_param(artifacts_persisted, 'artifacts_persisted'),
        )

    def get_step_output(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        step = self.get_step_by_key(step_output_handle.step_key)
        return step.step_output_named(step_output_handle.output_name)

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
            [self.step_dict[step_key] for step_key in step_key_level]
            for step_key_level in toposort(self.deps)
        ]
