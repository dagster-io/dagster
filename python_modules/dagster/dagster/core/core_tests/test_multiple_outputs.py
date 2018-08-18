from dagster import (
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    config,
    execute_pipeline,
)


def test_multiple_outputs():
    def _t_fn(_context, _inputs):
        yield Result('output_one', 'foo')
        yield Result('output_two', 'bar')

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

    result = execute_pipeline(pipeline, config.Environment(sources={}))

    assert result.result_list[0].name == 'multiple_outputs'
    assert result.result_list[0].output_name == 'output_one'
    assert result.result_list[0].transformed_value == 'foo'

    assert result.result_list[1].name == 'multiple_outputs'
    assert result.result_list[1].output_name == 'output_two'
    assert result.result_list[1].transformed_value == 'bar'
