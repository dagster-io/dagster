import json

import pytest

from dagster import (
    InputDefinition,
    OutputDefinition,
    PipelineConfigEvaluationError,
    PipelineDefinition,
    Result,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)

from dagster.utils.test import get_temp_file_name

from dagster.core.config_types import (
    solid_has_config_entry,
    solid_has_materializable_outputs,
    is_materializeable,
)

from dagster.core.execution import create_typed_environment


def single_int_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    return PipelineDefinition(name='single_int_output_pipeline', solids=[return_one])


def single_int_named_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.Int, name='named'))
    def return_named_one():
        return Result(1, 'named')

    return PipelineDefinition(name='single_int_named_output_pipeline', solids=[return_named_one])


def no_input_no_output_pipeline():
    @solid(outputs=[])
    def take_nothing_return_nothing(_info):
        pass

    return PipelineDefinition(
        name='no_input_no_output_pipeline', solids=[take_nothing_return_nothing]
    )


def one_input_no_output_pipeline():
    @solid(inputs=[InputDefinition('dummy')], outputs=[])
    def take_input_return_nothing(_info, **_kwargs):
        pass

    return PipelineDefinition(
        name='one_input_no_output_pipeline', solids=[take_input_return_nothing]
    )


def test_solid_has_config_entry():
    pipeline = single_int_output_pipeline()
    assert is_materializeable(types.Int)
    assert solid_has_materializable_outputs(pipeline.solid_named('return_one').definition)
    assert solid_has_config_entry(pipeline.solid_named('return_one').definition)


def test_basic_json_default_output_config_schema():
    env = create_typed_environment(
        single_int_output_pipeline(),
        {
            'solids': {
                'return_one': {
                    'outputs': [
                        {
                            'result': {
                                'json': {
                                    'path': 'foo',
                                },
                            },
                        },
                    ],
                },
            },
        },
    )

    assert env.solids['return_one']
    assert env.solids['return_one'].outputs == [{'result': {'json': {'path': 'foo'}}}]


def test_basic_json_named_output_config_schema():
    env = create_typed_environment(
        single_int_named_output_pipeline(),
        {
            'solids': {
                'return_named_one': {
                    'outputs': [
                        {
                            'named': {
                                'json': {
                                    'path': 'foo',
                                },
                            },
                        },
                    ],
                },
            },
        },
    )

    assert env.solids['return_named_one']
    assert env.solids['return_named_one'].outputs == [{'named': {'json': {'path': 'foo'}}}]


def test_basic_json_misnamed_output_config_schema():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        create_typed_environment(
            single_int_named_output_pipeline(),
            {
                'solids': {
                    'return_named_one': {
                        'outputs': [
                            {
                                'wrong_name': {
                                    'json': {
                                        'path': 'foo',
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        )

    assert len(exc_info.value.errors) == 1
    assert 'Error 1: Undefined field "wrong_name"' in exc_info.value.message
    assert 'at path root:solids:return_named_one:outputs[0]' in exc_info.value.message


def test_no_outputs_no_inputs_config_schema():
    assert create_typed_environment(no_input_no_output_pipeline())

    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        create_typed_environment(no_input_no_output_pipeline(), {'solids': {'return_one': {}}})

    assert len(exc_info.value.errors) == 1
    assert 'Error 1: Undefined field "return_one" at path root:solids' in exc_info.value.message


def test_no_outputs_one_input_config_schema():
    assert create_typed_environment(
        one_input_no_output_pipeline(),
        {
            'solids': {
                'take_input_return_nothing': {
                    'inputs': {
                        'dummy': 'value',
                    },
                },
            },
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        create_typed_environment(
            one_input_no_output_pipeline(),
            {
                'solids': {
                    'take_input_return_nothing': {
                        'inputs': {
                            'dummy': 'value',
                        },
                        'outputs': {},
                    },
                },
            },
        )

    assert len(exc_info.value.errors) == 1
    exp_msg = 'Error 1: Undefined field "outputs" at path root:solids:take_input_return_nothing'
    assert exp_msg in exc_info.value.message


def test_basic_json_materialization():
    pipeline = single_int_output_pipeline()

    # with get_temp_file_name() as filename:
    filename = '/tmp/test_materialization'
    result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'return_one': {
                    'outputs': [
                        {
                            'result': {
                                'json': {
                                    'path': filename,
                                },
                            },
                        },
                    ],
                },
            },
        },
    )

    assert result.success

    with open(filename, 'r') as ff:
        value = json.loads(ff.read())
        assert value == {'value': 1}
