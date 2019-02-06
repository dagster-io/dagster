from dagster import (
    CompositeSolidDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    execute_pipeline,
    lambda_solid,
    Int,
)


def test_composite_solid_output_only():
    @lambda_solid
    def return_one():
        return 1

    return_one_wrapper = CompositeSolidDefinition(
        name='return_one_wrapper',
        solid_defs=[return_one],
        output_mapping={'return_one': {'result': OutputDefinition(Int, 'outer_num')}},
    )

    pipeline_def = PipelineDefinition(name='test_composite_solid', solids=[return_one_wrapper])

    result = execute_pipeline(pipeline_def)
    assert result.success
    assert result.result_for_solid('return_one_wrapper').transformed_value('outer_num') == 1


def test_composite_with_input():
    @lambda_solid(inputs=[InputDefinition('inner_num', Int)], output=OutputDefinition(Int))
    def add_one(inner_num):
        return inner_num + 1

    add_one_wrapper = CompositeSolidDefinition(
        name='add_one_wrapper',
        solid_defs=[add_one],
        input_mapping={'add_one': {'inner_num': InputDefinition('num', Int)}},
        output_mapping={'add_one': {'result': OutputDefinition(Int, 'outer_num')}},
    )

    pipeline_def = PipelineDefinition(name='test_composite_with_input', solids=[add_one_wrapper])

    result = execute_pipeline(
        pipeline_def, environment={'solids': {'add_one_wrapper': {'inputs': {'num': {'value': 2}}}}}
    )

    assert result.success
    assert result.result_for_solid('add_one_wrapper').transformed_value('outer_num') == 3
