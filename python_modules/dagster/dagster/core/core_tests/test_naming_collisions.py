import dagster
from dagster import config

from dagster.core.definitions import (
    SolidDefinition,
    InputDefinition,
    SourceDefinition,
    ArgumentDefinition,
)

from dagster.core.execution import (ExecutionContext, execute_single_solid, execute_pipeline)

from dagster.core import types


def test_execute_solid_with_input_same_name():
    solid = SolidDefinition(
        'a_thing',
        inputs=[
            InputDefinition(
                name='a_thing',
                sources=[
                    SourceDefinition(
                        source_type='a_source_type',
                        source_fn=lambda context, arg_dict: arg_dict['an_arg'],
                        argument_def_dict={'an_arg': ArgumentDefinition(types.String)},
                    ),
                ],
            ),
        ],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    result = execute_single_solid(
        ExecutionContext(),
        solid,
        environment=config.Environment(
            sources={
                'a_thing': {
                    'a_thing': config.Source(name='a_source_type', args={'an_arg': 'foo'})
                }
            }
        )
    )

    assert result.success
    assert result.transformed_value == 'foofoo'


def test_execute_two_solids_with_same_input_name():
    input_def = InputDefinition(
        name='a_thing',
        sources=[
            SourceDefinition(
                source_type='a_source_type',
                source_fn=lambda context, arg_dict: arg_dict['an_arg'],
                argument_def_dict={'an_arg': ArgumentDefinition(types.String)},
            ),
        ],
    )

    solid_one = SolidDefinition(
        'solid_one',
        inputs=[input_def],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    solid_two = SolidDefinition(
        'solid_two',
        inputs=[input_def],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(solids=[solid_one, solid_two])

    result = execute_pipeline(
        pipeline,
        environment=config.Environment(
            sources={
                'solid_one': {
                    'a_thing': config.Source(name='a_source_type', args={'an_arg': 'foo'})
                },
                'solid_two': {
                    'a_thing': config.Source(name='a_source_type', args={'an_arg': 'bar'})
                },
            }
        )
    )

    assert result.success

    assert result.result_named('solid_one').transformed_value == 'foofoo'
    assert result.result_named('solid_two').transformed_value == 'barbar'


def test_execute_dep_solid_different_input_name():
    first_solid = SolidDefinition(
        'first_solid',
        inputs=[
            InputDefinition(
                name='a_thing',
                sources=[
                    SourceDefinition(
                        source_type='a_source_type',
                        source_fn=lambda context, arg_dict: arg_dict['an_arg'],
                        argument_def_dict={'an_arg': ArgumentDefinition(types.String)},
                    ),
                ],
            ),
        ],
        transform_fn=lambda context, args: args['a_thing'] + args['a_thing'],
        output=dagster.OutputDefinition(),
    )

    second_solid = SolidDefinition(
        'second_solid',
        inputs=[
            InputDefinition(
                name='a_dependency',
                depends_on=first_solid,
            ),
        ],
        transform_fn=lambda context, args: args['a_dependency'] + args['a_dependency'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(solids=[first_solid, second_solid])
    result = dagster.execute_pipeline(
        pipeline,
        environment=config.Environment(
            sources={
                'first_solid': {
                    'a_thing': config.Source(name='a_source_type', args={'an_arg': 'bar'})
                }
            }
        )
    )

    assert result.success
    assert len(result.result_list) == 2
    assert result.result_list[0].transformed_value == 'barbar'
    assert result.result_list[1].transformed_value == 'barbarbarbar'


def test_execute_dep_solid_same_input_name():
    def s_fn(arg_dict, executed, key):
        executed[key] = True
        return arg_dict

    executed = {
        's1_t1_source': False,
        's2_t1_source': False,
        's2_t2_source': False,
    }

    table_one = SolidDefinition(
        'table_one',
        inputs=[
            InputDefinition(
                name='table_one',
                sources=[
                    SourceDefinition(
                        source_type='TABLE',
                        source_fn=
                        lambda context, arg_dict: s_fn(arg_dict, executed, 's1_t1_source'),
                        argument_def_dict={'name': ArgumentDefinition(types.String)},
                    ),
                ],
            ),
        ],
        transform_fn=lambda context, args: args['table_one'],
        output=dagster.OutputDefinition(),
    )

    table_two = SolidDefinition(
        'table_two',
        inputs=[
            InputDefinition(
                name='table_one',
                sources=[
                    SourceDefinition(
                        source_type='TABLE',
                        source_fn=
                        lambda context, arg_dict: s_fn(arg_dict, executed, 's2_t1_source'),
                        argument_def_dict={'name': ArgumentDefinition(types.String)},
                    ),
                ],
                depends_on=table_one,
            ),
            InputDefinition(
                name='table_two',
                sources=[
                    SourceDefinition(
                        source_type='TABLE',
                        source_fn=
                        lambda context, arg_dict: s_fn(arg_dict, executed, 's2_t2_source'),
                        argument_def_dict={'name': ArgumentDefinition(types.String)},
                    ),
                ],
            ),
        ],
        transform_fn=lambda context, args: args['table_two'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(solids=[table_one, table_two])

    sources = {
        'table_one': {
            'table_one': config.Source(name='TABLE', args={'name': 'table_one_instance'}),
        },
        'table_two': {
            'table_one': config.Source(name='TABLE', args={'name': 'table_one_instance'}),
            'table_two': config.Source(name='TABLE', args={'name': 'table_two_instance'}),
        },
    }

    complete_environment = config.Environment(sources=sources)

    both_solids_result = dagster.execute_pipeline(pipeline, environment=complete_environment)

    assert executed == {
        's1_t1_source': True,
        's2_t1_source': False,
        's2_t2_source': True,
    }

    assert both_solids_result.success

    assert len(both_solids_result.result_list) == 2
    assert both_solids_result.result_list[0].transformed_value == {'name': 'table_one_instance'}
    assert both_solids_result.result_list[1].transformed_value == {'name': 'table_two_instance'}

    # reset execution marks
    executed['s1_t1_source'] = False
    executed['s2_t1_source'] = False
    executed['s2_t2_source'] = False

    second_only_env = config.Environment(
        sources=sources,
        execution=config.Execution(from_solids=['table_two']),
    )

    second_solid_only_result = dagster.execute_pipeline(pipeline, environment=second_only_env)

    assert second_solid_only_result.success
    assert len(second_solid_only_result.result_list) == 1
    assert second_solid_only_result.result_list[0].name == 'table_two'
    assert second_solid_only_result.result_list[0].transformed_value == {
        'name': 'table_two_instance'
    }

    assert executed == {
        's1_t1_source': False,
        's2_t1_source': True,
        's2_t2_source': True,
    }

    # reset execution marks
    executed['s1_t1_source'] = False
    executed['s2_t1_source'] = False
    executed['s2_t2_source'] = False

    first_only_env = config.Environment(
        sources=sources,
        execution=config.Execution(through_solids=['table_one']),
    )

    first_solid_only_result = dagster.execute_pipeline(
        pipeline,
        environment=first_only_env,
    )

    assert first_solid_only_result.success
    assert len(first_solid_only_result.result_list) == 1
    assert first_solid_only_result.result_list[0].name == 'table_one'
    assert first_solid_only_result.result_list[0].transformed_value == {
        'name': 'table_one_instance'
    }

    assert executed == {
        's1_t1_source': True,
        's2_t1_source': False,
        's2_t2_source': False,
    }
