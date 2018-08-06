import sqlalchemy as sa
import dagster
from dagster import (config, InputDefinition)
import dagster.sqlalchemy_kernel as dagster_sa
from dagster.utils.test import script_relative_path

from dagster.sqlalchemy_kernel.subquery_builder_experimental import sql_file_solid


def in_mem_engine():
    engine = sa.create_engine('sqlite://', echo=False)
    return engine


def in_mem_context():
    return dagster_sa.create_sql_alchemy_context_from_engine(engine=in_mem_engine())


def pipeline_engine(pipeline_result):
    return pipeline_result.context.resources.sa.engine


def create_persisted_context():
    full_path = script_relative_path('testdb.db')
    engine = sa.create_engine(f'sqlite:///{full_path}', echo=False)
    return dagster_sa.create_sql_alchemy_context_from_engine(engine=engine)


def create_mem_sql_pipeline_context_tuple(solids):
    default_def = dagster.PipelineContextDefinition(
        argument_def_dict={},
        context_fn=lambda _pipeline, _args: in_mem_context(),
    )
    persisted_def = dagster.PipelineContextDefinition(
        argument_def_dict={},
        context_fn=lambda _pipeline, _args: create_persisted_context(),
    )
    return dagster.PipelineDefinition(
        solids=solids, context_definitions={
            'default': default_def,
            'persisted': persisted_def
        }
    )


def _get_sql_script_path(name):
    return script_relative_path(f'../../sql_project_example/sql_files/{name}.sql')


def _get_project_solid(name, inputs=None):
    return sql_file_solid(_get_sql_script_path(name), inputs=inputs)


def test_sql_create_tables():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    pipeline = create_mem_sql_pipeline_context_tuple(solids=[create_all_tables_solids])

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())
    assert pipeline_result.success

    assert set(pipeline_engine(pipeline_result).table_names()) == set(
        ['num_table', 'sum_sq_table', 'sum_table']
    )


def test_sql_populate_tables():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[
            InputDefinition(create_all_tables_solids.name, depends_on=create_all_tables_solids)
        ]
    )

    pipeline = create_mem_sql_pipeline_context_tuple(
        solids=[create_all_tables_solids, populate_num_table_solid]
    )

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())

    assert pipeline_result.success

    assert pipeline_engine(pipeline_result).execute('SELECT * FROM num_table').fetchall() == [
        (1, 2), (3, 4)
    ]


def create_full_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[InputDefinition('create_all_tables_solids', depends_on=create_all_tables_solids)],
    )

    insert_into_sum_table_solid = _get_project_solid(
        'insert_into_sum_table',
        inputs=[InputDefinition('populate_num_table_solid', depends_on=populate_num_table_solid)],
    )

    insert_into_sum_sq_table_solid = _get_project_solid(
        'insert_into_sum_sq_table',
        inputs=[
            InputDefinition('insert_into_sum_sq_table', depends_on=insert_into_sum_table_solid)
        ],
    )

    return create_mem_sql_pipeline_context_tuple(
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
    )


def test_full_in_memory_pipeline():

    pipeline = create_full_pipeline()
    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())
    assert pipeline_result.success

    engine = pipeline_engine(pipeline_result)
    assert engine.execute('SELECT * FROM num_table').fetchall() == [(1, 2), (3, 4)]
    assert engine.execute('SELECT * FROM sum_table').fetchall() == [(1, 2, 3), (3, 4, 7)]
    assert engine.execute('SELECT * FROM sum_sq_table').fetchall() == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_full_persisted_pipeline():
    pipeline = create_full_pipeline()
    pipeline_result = dagster.execute_pipeline(
        pipeline,
        environment=config.Environment(
            sources={}, context=config.Context(name='persisted', args={})
        )
    )

    assert pipeline_result.success
