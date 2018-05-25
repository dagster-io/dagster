import sqlalchemy as sa
import dagster
import dagster.sqlalchemy_kernel as dagster_sa
from dagster.utils.test import script_relative_path


def in_mem_engine():
    engine = sa.create_engine('sqlite://')
    return engine


def in_mem_context():
    return dagster_sa.DagsterSqlAlchemyExecutionContext(engine=in_mem_engine())


def _get_sql_script_path(name):
    return script_relative_path(f'../../sql_project_example/sql_files/{name}.sql')


def _get_project_solid(name, inputs=None):
    return dagster_sa.sql_file_solid(_get_sql_script_path(name), inputs=inputs)


def test_sql_create_tables():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    pipeline = dagster.pipeline(solids=[create_all_tables_solids])

    context = in_mem_context()
    results = dagster.execute_pipeline(context, pipeline, {}, throw_on_error=True)

    for result in results:
        assert result.success

    assert set(context.engine.table_names()) == set(['num_table', 'sum_sq_table', 'sum_table'])


def test_sql_populate_tables():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table', inputs=[dagster.dep_only_input(create_all_tables_solids)]
    )

    pipeline = dagster.pipeline(solids=[create_all_tables_solids, populate_num_table_solid])

    context = in_mem_context()
    results = dagster.execute_pipeline(context, pipeline, {}, throw_on_error=True)

    for result in results:
        assert result.success

    assert context.engine.execute('SELECT * FROM num_table').fetchall() == [(1, 2), (3, 4)]


def create_full_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[dagster.dep_only_input(create_all_tables_solids)],
    )

    insert_into_sum_table_solid = _get_project_solid(
        'insert_into_sum_table',
        inputs=[dagster.dep_only_input(populate_num_table_solid)],
    )

    insert_into_sum_sq_table_solid = _get_project_solid(
        'insert_into_sum_sq_table',
        inputs=[dagster.dep_only_input(insert_into_sum_table_solid)],
    )

    return dagster.pipeline(
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
    )


def test_full_in_memory_pipeline():

    pipeline = create_full_pipeline()
    context = in_mem_context()
    results = dagster.execute_pipeline(context, pipeline, {}, throw_on_error=True)

    for result in results:
        assert result.success

    assert context.engine.execute('SELECT * FROM num_table').fetchall() == [(1, 2), (3, 4)]
    assert context.engine.execute('SELECT * FROM sum_table').fetchall() == [(1, 2, 3), (3, 4, 7)]
    assert context.engine.execute('SELECT * FROM sum_sq_table').fetchall() == [
        (1, 2, 3, 9), (3, 4, 7, 49)
    ]


def test_full_persisted_pipeline():
    full_path = script_relative_path('testdb.db')
    engine = sa.create_engine(f'sqlite:///{full_path}', echo=True)
    context = dagster_sa.DagsterSqlAlchemyExecutionContext(engine=engine)

    pipeline = create_full_pipeline()
    results = dagster.execute_pipeline(context, pipeline, {}, throw_on_error=True)

    for result in results:
        assert result.success
