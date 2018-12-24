from collections import namedtuple
from enum import Enum
import toposort
from six import string_types

from pyrsistent import (
    CheckedPVector,
    CheckedPMap,
    PClass,
    field,
)

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


ExecutionSubPlan = namedtuple(
    'ExecutionSubPlan',
    'steps terminal_step_output_handle',
)


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


def str_field():
    return field(type=string_types, mandatory=True)


def list_field():
    return field(type=list, mandatory=True)


def enum_field(enum_type):
    def _factory(str_or_enum):
        if isinstance(str_or_enum, StepTag):
            # in-memory
            return str_or_enum
        if isinstance(str_or_enum, string_types):
            # deserialization
            return StepTag(str_or_enum)

        check.failed(
            'Unsupported value for enum {enum_type}: {enum_value}'.format(
                enum_type=enum_type,
                enum_value=str_or_enum,
            )
        )

    return field(
        type=enum_type,
        mandatory=True,
        serializer=lambda _format, enum_value: enum_value.value,
        factory=_factory,
    )


class StepOutputHandle(PClass):
    step_key = str_field()
    output_name = str_field()

    # PClass fools lint
    # pylint: disable=E1101

    def __hash__(self):
        return hash(self.step_key + ':' + self.output_name)

    def __eq__(self, other):
        return self.step_key == other.step_key and self.output_name == other.output_name


class StepInputMeta(PClass):
    name = str_field()
    dagster_type_name = str_field()
    prev_output_handle = field(type=StepOutputHandle, mandatory=True)


class StepInput(PClass):
    @staticmethod
    def from_props(name, dagster_type, prev_output_handle):
        return StepInput(
            meta=StepInputMeta(
                name=name,
                dagster_type_name=dagster_type.name,
                prev_output_handle=prev_output_handle,
            ),
            dagster_type=dagster_type,
        )

    # PClass fools lint
    # pylint: disable=E1101

    @property
    def name(self):
        return self.meta.name

    @property
    def prev_output_handle(self):
        return self.meta.prev_output_handle

    meta = field(type=StepInputMeta, mandatory=True)
    dagster_type = field(type=DagsterType, mandatory=True)


class StepOutputMeta(PClass):
    name = str_field()
    dagster_type_name = str_field()


class StepOutput(PClass):
    @staticmethod
    def from_props(name, dagster_type):
        return StepOutput(
            meta=StepOutputMeta(name=name, dagster_type_name=dagster_type.name),
            dagster_type=dagster_type,
        )

    # PClass fools lint
    # pylint: disable=E1101

    @property
    def name(self):
        return self.meta.name

    meta = field(type=StepOutputMeta, mandatory=True)
    dagster_type = field(type=DagsterType, mandatory=True)


class StepInputMetaVector(CheckedPVector):
    __type__ = StepInputMeta


class StepOutputMetaVector(CheckedPVector):
    __type__ = StepOutputMeta


class ExecutionStepMeta(PClass):
    key = str_field()
    step_input_metas = field(type=StepInputMetaVector, mandatory=True)
    step_output_metas = field(type=StepOutputMetaVector, mandatory=True)
    tag = enum_field(StepTag)
    solid_name = str_field()

    step_kind_data = field(type=dict, mandatory=True)


class ExecutionStep(
    namedtuple(
        '_ExecutionStep',
        'meta step_inputs step_outputs step_input_dict step_output_dict compute_fn solid',
    ),
):
    def __new__(cls, key, step_inputs, step_outputs, compute_fn, tag, solid, step_kind_data=None):
        return super(ExecutionStep, cls).__new__(
            cls,
            meta=ExecutionStepMeta(
                key=key,
                step_input_metas=StepInputMetaVector(
                    [step_input.meta for step_input in step_inputs]
                ),
                step_output_metas=StepOutputMetaVector(
                    [step_output.meta for step_output in step_outputs]
                ),
                tag=tag,
                solid_name=solid.name,
                step_kind_data=check.opt_dict_param(
                    step_kind_data,
                    'step_kind_data',
                    key_type=str,
                    value_type=str,
                ),
            ),
            step_inputs=check.list_param(step_inputs, 'step_inputs', of_type=StepInput),
            step_outputs=check.list_param(step_outputs, 'step_outputs', of_type=StepOutput),
            step_input_dict={si.name: si
                             for si in step_inputs},
            step_output_dict={so.name: so
                              for so in step_outputs},
            compute_fn=check.callable_param(compute_fn, 'compute_fn'),
            solid=check.inst_param(solid, 'solid', Solid),
        )

    @property
    def key(self):
        return self.meta.key

    @property
    def tag(self):
        return self.meta.tag

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


class ExecutionStepMetaVector(CheckedPVector):
    __type__ = ExecutionStepMeta


class DepVector(CheckedPVector):
    __type__ = string_types


class DepMap(CheckedPMap):
    __key_type__ = string_types
    __value_type__ = DepVector


class ExecutionPlanMeta(PClass):
    step_metas = field(type=ExecutionStepMetaVector, mandatory=True)
    deps = field(type=DepMap, mandatory=True)


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

        # We topologically sort here the store the serializable meta information
        # in the topological order.
        ordered_step_keys = toposort.toposort_flatten(self.deps)
        step_metas = []
        for step_key in ordered_step_keys:
            step_metas.append(step_dict[step_key].meta)

        self.meta = ExecutionPlanMeta(
            step_metas=ExecutionStepMetaVector(step_metas),
            deps={dep_key: DepVector(deps_for_key)
                  for dep_key, deps_for_key in deps.items()},
        )

    def get_step_by_key(self, key):
        return self.step_dict[key]

    def topological_steps(self):
        return list(self._topological_steps())

    def _topological_steps(self):
        # PClass fools lint
        for step_meta in self.meta.step_metas:  # pylint: disable=E1133
            yield self.step_dict[step_meta.key]
