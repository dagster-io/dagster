import pytest

from dagster import (
    DagsterInvariantViolationError,
    ExpectationDefinition,
    ExpectationResult,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    config,
    execute_pipeline,
)


def test_multiple_outputs():
    def _t_fn(_context, _inputs, _config_dict):
        yield Result(output_name='output_one', value='foo')
        yield Result(output_name='output_two', value='bar')

    solid = SolidDefinition(
        name='multiple_outputs',
        inputs=[],
        outputs=[
            OutputDefinition(name='output_one'),
            OutputDefinition(name='output_two'),
        ],
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    result = execute_pipeline(pipeline, config.Environment())

    assert result.result_list[0].name == 'multiple_outputs'
    assert result.result_list[0].output_name == 'output_one'
    assert result.result_list[0].transformed_value == 'foo'

    assert result.result_list[1].name == 'multiple_outputs'
    assert result.result_list[1].output_name == 'output_two'
    assert result.result_list[1].transformed_value == 'bar'


def test_multiple_outputs_expectations():
    called = {}

    def _expect_fn_one(*_args, **_kwargs):
        called['expectation_one'] = True
        return ExpectationResult(success=True)

    def _expect_fn_two(*_args, **_kwargs):
        called['expectation_two'] = True
        return ExpectationResult(success=True)

    def _transform_fn(*_args, **_kwargs):
        yield Result('foo', 'output_one')
        yield Result('bar', 'output_two')

    solid = SolidDefinition(
        name='multiple_outputs',
        inputs=[],
        outputs=[
            OutputDefinition(
                name='output_one',
                expectations=[
                    ExpectationDefinition(name='some_expectation', expectation_fn=_expect_fn_one)
                ]
            ),
            OutputDefinition(
                name='output_two',
                expectations=[
                    ExpectationDefinition(
                        name='some_other_expectation', expectation_fn=_expect_fn_two
                    )
                ],
            ),
        ],
        transform_fn=_transform_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    result = execute_pipeline(pipeline, config.Environment())

    assert result.success
    assert called['expectation_one']
    assert called['expectation_two']


def test_wrong_multiple_output():
    def _t_fn(_context, _inputs, _config_dict):
        yield Result(output_name='mismatch', value='foo')

    solid = SolidDefinition(
        name='multiple_outputs',
        inputs=[],
        outputs=[
            OutputDefinition(name='output_one'),
        ],
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline, config.Environment())


def test_multiple_outputs_of_same_name_disallowed():
    # make this illegal until it is supported

    def _t_fn(_context, _inputs, _config_dict):
        yield Result(output_name='output_one', value='foo')
        yield Result(output_name='output_one', value='foo')

    solid = SolidDefinition(
        name='multiple_outputs',
        inputs=[],
        outputs=[
            OutputDefinition(name='output_one'),
        ],
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline, config.Environment())