import os
import dagster
from dagster import check
import dagster.sqlalchemy_kernel as dagster_sa


def _get_sql_script_path(name):
    return os.path.join(os.path.dirname(__file__), 'sql_files', f'{name}.sql')


def _get_project_solid(name, inputs=None):
    return dagster_sa.sql_file_solid(_get_sql_script_path(name), inputs=inputs)


def define_full_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[dagster.dep_only_input(create_all_tables_solids)],
    )

    insert_deps = [dagster.dep_only_input(populate_num_table_solid)]

    insert_into_sum_table_solid, insert_into_sum_sq_table_solid = get_insert_solids(
        insert_deps=insert_deps
    )

    return dagster.pipeline(
        name='full_pipeline',
        description='Runs entire pipeline, both setup and running the transform',
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
    )


def get_insert_solids(insert_deps):
    insert_into_sum_table_solid = _get_project_solid(
        'insert_into_sum_table',
        inputs=insert_deps,
    )

    insert_into_sum_sq_table_solid = _get_project_solid(
        'insert_into_sum_sq_table',
        inputs=[dagster.dep_only_input(insert_into_sum_table_solid)],
    )
    return insert_into_sum_table_solid, insert_into_sum_sq_table_solid


def define_truncate_pipeline():
    truncate_solid = _get_project_solid('truncate_all_derived_tables')
    return dagster.pipeline(
        name='truncate_all_derived_tables',
        description=
        'Truncates all tables that are populated by the pipeline. Preserves source tables',
        solids=[truncate_solid]
    )


def define_rerun_pipeline():
    insert_into_sum_table_solid, insert_into_sum_sq_table_solid = get_insert_solids(
        insert_deps=None
    )

    return dagster.pipeline(
        name='rerun_pipeline',
        description=
        'Rerun the pipeline, populating the the derived tables. Assumes pipeline is setup',
        solids=[
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
    )


def define_setup_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[dagster.dep_only_input(create_all_tables_solids)],
    )

    return dagster.pipeline(
        name='setup_pipeline',
        description='Creates all tables and then populates source table',
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
        ],
    )
