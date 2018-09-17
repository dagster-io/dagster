from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    config,
    execute_pipeline,
    lambda_solid,
)


def test_aliased_solids():
    @lambda_solid()
    def first():
        return ['first']

    @lambda_solid(inputs=[InputDefinition(name="prev")])
    def not_first(prev):
        return prev + ['not_first']

    pipeline = PipelineDefinition.create_from_solid_map(
        solid_map={
            'first': first,
            'not_first': not_first,
            'second': not_first,
            'third': not_first,
        },
        dependencies={
            'not_first': {
                'prev': DependencyDefinition('first'),
            },
            'second': {
                'prev': DependencyDefinition('not_first'),
            },
            'third': {
                'prev': DependencyDefinition('second'),
            },
        },
    )

    result = execute_pipeline(pipeline)
    assert result.success
    solid_result = result.result_for_solid('third')
    assert solid_result.transformed_value() == ['first', 'not_first', 'not_first', 'not_first']
