import json

import pytest

from dagster import (
    Int,
    InputDefinition,
    OutputDefinition,
    PipelineConfigEvaluationError,
    PipelineDefinition,
    Result,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
    RuntimeType,
    output_schema,
)
from dagster.core.definitions.environment_configs import (
    solid_has_config_entry,
    solid_has_configurable_outputs,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import create_environment_config
from dagster.core.execution_plan.materialization_thunk import MATERIALIZATION_THUNK_OUTPUT
from dagster.core.execution_plan.objects import StepOutputHandle
from dagster.utils.test import get_temp_file_name, get_temp_file_names


def single_int_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    return PipelineDefinition(name='single_int_output_pipeline', solids=[return_one])


def single_string_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.String))
    def return_foo():
        return 'foo'

    return PipelineDefinition(name='single_string_output_pipeline', solids=[return_foo])


def multiple_output_pipeline():
    @solid(
        outputs=[OutputDefinition(types.Int, 'number'), OutputDefinition(types.String, 'string')]
    )
    def return_one_and_foo(_context):
        yield Result(1, 'number')
        yield Result('foo', 'string')

    return PipelineDefinition(name='multiple_output_pipeline', solids=[return_one_and_foo])


def single_int_named_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.Int, name='named'))
    def return_named_one():
        return Result(1, 'named')

    return PipelineDefinition(name='single_int_named_output_pipeline', solids=[return_named_one])


def no_input_no_output_pipeline():
    @solid(outputs=[])
    def take_nothing_return_nothing(_context):
        pass

    return PipelineDefinition(
        name='no_input_no_output_pipeline', solids=[take_nothing_return_nothing]
    )


def one_input_no_output_pipeline():
    @solid(inputs=[InputDefinition('dummy')], outputs=[])
    def take_input_return_nothing(_context, **_kwargs):
        pass

    return PipelineDefinition(
        name='one_input_no_output_pipeline', solids=[take_input_return_nothing]
    )


def test_solid_has_config_entry():
    pipeline = single_int_output_pipeline()
    assert solid_has_configurable_outputs(pipeline.solid_named('return_one').definition)
    assert solid_has_config_entry(pipeline.solid_named('return_one').definition)


def test_basic_json_default_output_config_schema():
    env = create_environment_config(
        single_int_output_pipeline(),
        {'solids': {'return_one': {'outputs': [{'result': {'json': {'path': 'foo'}}}]}}},
    )

    assert env.solids['return_one']
    assert env.solids['return_one'].outputs == [{'result': {'json': {'path': 'foo'}}}]


def test_basic_json_named_output_config_schema():
    env = create_environment_config(
        single_int_named_output_pipeline(),
        {'solids': {'return_named_one': {'outputs': [{'named': {'json': {'path': 'foo'}}}]}}},
    )

    assert env.solids['return_named_one']
    assert env.solids['return_named_one'].outputs == [{'named': {'json': {'path': 'foo'}}}]


def test_basic_json_misnamed_output_config_schema():
    with pytest.raises(PipelineConfigEvaluationError) as exc_context:
        create_environment_config(
            single_int_named_output_pipeline(),
            {
                'solids': {
                    'return_named_one': {'outputs': [{'wrong_name': {'json': {'path': 'foo'}}}]}
                }
            },
        )

    assert len(exc_context.value.errors) == 1
    assert 'Error 1: Undefined field "wrong_name"' in exc_context.value.message
    assert 'at path root:solids:return_named_one:outputs[0]' in exc_context.value.message


def test_no_outputs_no_inputs_config_schema():
    assert create_environment_config(no_input_no_output_pipeline())

    with pytest.raises(PipelineConfigEvaluationError) as exc_context:
        create_environment_config(no_input_no_output_pipeline(), {'solids': {'return_one': {}}})

    assert len(exc_context.value.errors) == 1
    assert 'Error 1: Undefined field "return_one" at path root:solids' in exc_context.value.message


def test_no_outputs_one_input_config_schema():
    assert create_environment_config(
        one_input_no_output_pipeline(),
        {'solids': {'take_input_return_nothing': {'inputs': {'dummy': {'value': 'value'}}}}},
    )

    with pytest.raises(PipelineConfigEvaluationError) as exc_context:
        create_environment_config(
            one_input_no_output_pipeline(),
            {
                'solids': {
                    'take_input_return_nothing': {
                        'inputs': {'dummy': {'value': 'value'}},
                        'outputs': {},
                    }
                }
            },
        )

    assert len(exc_context.value.errors) == 1
    exp_msg = 'Error 1: Undefined field "outputs" at path root:solids:take_input_return_nothing'
    assert exp_msg in exc_context.value.message


def test_basic_int_execution_plan():
    execution_plan = create_execution_plan(
        single_int_output_pipeline(),
        {'solids': {'return_one': {'outputs': [{'result': {'json': {'path': 'dummy.json'}}}]}}},
    )

    assert len(execution_plan.steps) == 3

    steps = execution_plan.topological_steps()

    assert steps[0].key == 'return_one.transform'
    assert steps[1].key == 'return_one.outputs.result.materialize.0'
    assert steps[2].key == 'return_one.outputs.result.materialize.join'


def test_basic_int_json_materialization():
    pipeline = single_int_output_pipeline()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline,
            {'solids': {'return_one': {'outputs': [{'result': {'json': {'path': filename}}}]}}},
        )

        assert result.success

        with open(filename, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 1}


def test_basic_string_json_materialization():
    pipeline = single_string_output_pipeline()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline,
            {'solids': {'return_foo': {'outputs': [{'result': {'json': {'path': filename}}}]}}},
        )

        assert result.success

        with open(filename, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 'foo'}


def test_basic_int_and_string_execution_plan():
    pipeline = multiple_output_pipeline()
    execution_plan = create_execution_plan(
        pipeline,
        {
            'solids': {
                'return_one_and_foo': {
                    'outputs': [
                        {'string': {'json': {'path': 'dummy_string.json'}}},
                        {'number': {'json': {'path': 'dummy_number.json'}}},
                    ]
                }
            }
        },
    )

    assert len(execution_plan.steps) == 5
    steps = execution_plan.topological_steps()
    assert steps[0].key == 'return_one_and_foo.transform'

    assert_plan_topological_level(
        steps,
        [1, 2],
        [
            'return_one_and_foo.outputs.string.materialize.0',
            'return_one_and_foo.outputs.number.materialize.0',
        ],
    )

    assert_plan_topological_level(
        steps,
        [3, 4],
        [
            'return_one_and_foo.outputs.string.materialize.join',
            'return_one_and_foo.outputs.number.materialize.join',
        ],
    )

    transform_step = execution_plan.get_step_by_key('return_one_and_foo.transform')

    string_mat_step = execution_plan.get_step_by_key(
        'return_one_and_foo.outputs.string.materialize.0'
    )
    assert len(string_mat_step.step_inputs) == 1
    assert string_mat_step.step_inputs[0].prev_output_handle == StepOutputHandle.from_step(
        step=transform_step, output_name='string'
    )

    string_mat_join_step = execution_plan.get_step_by_key(
        'return_one_and_foo.outputs.string.materialize.join'
    )
    assert len(string_mat_join_step.step_inputs) == 1
    assert string_mat_join_step.step_inputs[0].prev_output_handle == StepOutputHandle.from_step(
        step=string_mat_step, output_name=MATERIALIZATION_THUNK_OUTPUT
    )


def test_basic_int_and_string_json_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(2) as file_tuple:
        filename_one, filename_two = file_tuple  # pylint: disable=E0632
        result = execute_pipeline(
            pipeline,
            {
                'solids': {
                    'return_one_and_foo': {
                        'outputs': [
                            {'string': {'json': {'path': filename_one}}},
                            {'number': {'json': {'path': filename_two}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, 'r') as ff_1:
            value = json.loads(ff_1.read())
            assert value == {'value': 'foo'}

        with open(filename_two, 'r') as ff_2:
            value = json.loads(ff_2.read())
            assert value == {'value': 1}


def read_file_contents(path):
    with open(path, 'r') as ff:
        return ff.read()


def test_basic_int_and_string_json_multiple_materialization_execution_plan():
    pipeline = multiple_output_pipeline()
    execution_plan = create_execution_plan(
        pipeline,
        {
            'solids': {
                'return_one_and_foo': {
                    'outputs': [
                        {'string': {'json': {'path': 'foo'}}},
                        {'string': {'json': {'path': 'bar'}}},
                        {'number': {'json': {'path': 'baaz'}}},
                        {'number': {'json': {'path': 'quux'}}},
                    ]
                }
            }
        },
    )

    steps = execution_plan.topological_steps()

    assert len(steps) == 7

    assert_plan_topological_level(
        steps,
        [1, 2, 3, 4],
        [
            'return_one_and_foo.outputs.number.materialize.0',
            'return_one_and_foo.outputs.number.materialize.1',
            'return_one_and_foo.outputs.string.materialize.0',
            'return_one_and_foo.outputs.string.materialize.1',
        ],
    )

    assert_plan_topological_level(
        steps,
        [5, 6],
        [
            'return_one_and_foo.outputs.number.materialize.join',
            'return_one_and_foo.outputs.string.materialize.join',
        ],
    )


def test_basic_int_and_string_json_multiple_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(4) as file_tuple:
        # False positive for unbalanced tuple unpacking
        # pylint: disable=E0632
        filename_one, filename_two, filename_three, filename_four = file_tuple
        result = execute_pipeline(
            pipeline,
            {
                'solids': {
                    'return_one_and_foo': {
                        'outputs': [
                            {'string': {'json': {'path': filename_one}}},
                            {'string': {'json': {'path': filename_two}}},
                            {'number': {'json': {'path': filename_three}}},
                            {'number': {'json': {'path': filename_four}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 'foo'}

        with open(filename_two, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 'foo'}

        with open(filename_three, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 1}

        with open(filename_four, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 1}


def assert_step_before(steps, first_step, second_step):
    step_keys = [step.key for step in steps]
    assert step_keys.index(first_step) < step_keys.index(second_step)


def assert_plan_topological_level(steps, step_nums, step_keys):
    assert set(steps[step_num].key for step_num in step_nums) == set(step_keys)


def test_basic_int_multiple_serializations_execution_plan():
    execution_plan = create_execution_plan(
        single_int_output_pipeline(),
        {
            'solids': {
                'return_one': {
                    'outputs': [
                        {'result': {'json': {'path': 'dummy_one.json'}}},
                        {'result': {'json': {'path': 'dummy_two.json'}}},
                    ]
                }
            }
        },
    )

    assert len(execution_plan.steps) == 4

    steps = execution_plan.topological_steps()
    assert steps[0].key == 'return_one.transform'

    assert_plan_topological_level(
        steps,
        [1, 2],
        ['return_one.outputs.result.materialize.0', 'return_one.outputs.result.materialize.1'],
    )

    assert steps[3].key == 'return_one.outputs.result.materialize.join'


def test_basic_int_json_multiple_materializations():
    pipeline = single_int_output_pipeline()

    with get_temp_file_names(2) as file_tuple:
        filename_one, filename_two = file_tuple  # pylint: disable=E0632
        result = execute_pipeline(
            pipeline,
            {
                'solids': {
                    'return_one': {
                        'outputs': [
                            {'result': {'json': {'path': filename_one}}},
                            {'result': {'json': {'path': filename_two}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 1}

        with open(filename_two, 'r') as ff:
            value = json.loads(ff.read())
            assert value == {'value': 1}


@output_schema(Int)
def return_int(*_args, **_kwargs):
    return 1


class SomeRuntimeType(RuntimeType):
    def __init__(self):
        super(SomeRuntimeType, self).__init__(
            key='SomeType', name='SomeType', output_schema=return_int
        )


def test_basic_bad_output_materialization():
    @lambda_solid(output=OutputDefinition(SomeRuntimeType))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(name='single_int_output_pipeline', solids=[return_one])

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(
            pipeline_def, environment_dict={'solids': {'return_one': {'outputs': [{'result': 2}]}}}
        )

    assert str(exc_info.value) == (
        'materialize_runtime_value on type SomeType has returned value '
        '1 of type int. You must return a string (and ideally a valid file path).'
    )
