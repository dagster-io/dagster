from collections import defaultdict

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    PipelineDefinition,
    SolidInstance,
    execute_pipeline,
    lambda_solid,
    solid,
)


def test_aliased_solids():
    @lambda_solid()
    def first():
        return ['first']

    @lambda_solid(inputs=[InputDefinition(name="prev")])
    def not_first(prev):
        return prev + ['not_first']

    pipeline = PipelineDefinition(
        solids=[first, not_first],
        dependencies={
            'not_first': {'prev': DependencyDefinition('first')},
            SolidInstance('not_first', alias='second'): {'prev': DependencyDefinition('not_first')},
            SolidInstance('not_first', alias='third'): {'prev': DependencyDefinition('second')},
        },
    )

    result = execute_pipeline(pipeline)
    assert result.success
    solid_result = result.result_for_solid('third')
    assert solid_result.transformed_value() == ['first', 'not_first', 'not_first', 'not_first']


def test_only_aliased_solids():
    @lambda_solid()
    def first():
        return ['first']

    @lambda_solid(inputs=[InputDefinition(name="prev")])
    def not_first(prev):
        return prev + ['not_first']

    pipeline = PipelineDefinition(
        solids=[first, not_first],
        dependencies={
            SolidInstance('first', alias='the_root'): {},
            SolidInstance('not_first', alias='the_consequence'): {
                'prev': DependencyDefinition('the_root')
            },
        },
    )

    result = execute_pipeline(pipeline)
    assert result.success
    solid_result = result.result_for_solid('the_consequence')
    assert solid_result.transformed_value() == ['first', 'not_first']


def test_aliased_configs():
    @solid(inputs=[], config_field=Field(Int))
    def load_constant(context):
        return context.solid_config

    pipeline = PipelineDefinition(
        solids=[load_constant],
        dependencies={
            SolidInstance(load_constant.name, 'load_a'): {},
            SolidInstance(load_constant.name, 'load_b'): {},
        },
    )

    result = execute_pipeline(
        pipeline, {'solids': {'load_a': {'config': 2}, 'load_b': {'config': 3}}}
    )

    assert result.success
    assert result.result_for_solid('load_a').transformed_value() == 2
    assert result.result_for_solid('load_b').transformed_value() == 3


def test_aliased_solids_context():
    record = defaultdict(set)

    @solid
    def log_things(context):
        solid_value = context.solid.name
        solid_def_value = context.solid_def.name
        record[solid_def_value].add(solid_value)

    pipeline = PipelineDefinition(
        solids=[log_things],
        dependencies={
            SolidInstance('log_things', 'log_a'): {},
            SolidInstance('log_things', 'log_b'): {},
        },
    )

    result = execute_pipeline(pipeline)
    assert result.success

    assert dict(record) == {'log_things': set(['log_a', 'log_b'])}
