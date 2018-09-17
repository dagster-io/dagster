import os
import dagster
import dagster.sqlalchemy as dagster_sa

from dagster import (
    DependencyDefinition,
    InputDefinition,
)


def _get_sql_script_path(name):
    return os.path.join(os.path.dirname(__file__), 'sql_files', '{name}.sql'.format(name=name))


def _get_project_solid(name, inputs=None):
    return dagster_sa.sql_file_solid(_get_sql_script_path(name), inputs=inputs)


def define_full_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[InputDefinition(create_all_tables_solids.name)],
    )

    insert_into_sum_table_solid = _get_project_solid(
        'insert_into_sum_table',
        inputs=[InputDefinition(populate_num_table_solid.name)],
    )

    insert_into_sum_sq_table_solid = _get_project_solid(
        'insert_into_sum_sq_table',
        inputs=[InputDefinition(insert_into_sum_table_solid.name)],
    )

    return dagster.PipelineDefinition(
        name='full_pipeline',
        description='Runs entire pipeline, both setup and running the transform',
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
        dependencies={
            populate_num_table_solid.name: {
                create_all_tables_solids.name: DependencyDefinition(create_all_tables_solids.name)
            },
            insert_into_sum_table_solid.name: {
                populate_num_table_solid.name: DependencyDefinition(populate_num_table_solid.name),
            },
            insert_into_sum_sq_table_solid.name: {
                insert_into_sum_table_solid.name: DependencyDefinition(insert_into_sum_table_solid),
            }
        },
    )


def define_truncate_pipeline():
    truncate_solid = _get_project_solid('truncate_all_derived_tables')
    return dagster.PipelineDefinition(
        name='truncate_all_derived_tables',
        description=
        'Truncates all tables that are populated by the pipeline. Preserves source tables',
        solids=[truncate_solid]
    )


def define_rerun_pipeline():
    insert_into_sum_table_solid = _get_project_solid(
        'insert_into_sum_table',
        inputs=None,
    )

    insert_into_sum_sq_table_solid = _get_project_solid(
        'insert_into_sum_sq_table', inputs=[InputDefinition(insert_into_sum_table_solid.name)]
    )

    return dagster.PipelineDefinition(
        name='rerun_pipeline',
        description=
        'Rerun the pipeline, populating the the derived tables. Assumes pipeline is setup',
        solids=[
            insert_into_sum_table_solid,
            insert_into_sum_sq_table_solid,
        ],
        dependencies={
            insert_into_sum_sq_table_solid.name: {
                insert_into_sum_table_solid.name:
                DependencyDefinition(insert_into_sum_table_solid.name),
            }
        }
    )


def define_setup_pipeline():
    create_all_tables_solids = _get_project_solid('create_all_tables')

    populate_num_table_solid = _get_project_solid(
        'populate_num_table',
        inputs=[InputDefinition(create_all_tables_solids.name)],
    )

    return dagster.PipelineDefinition(
        name='setup_pipeline',
        description='Creates all tables and then populates source table',
        solids=[
            create_all_tables_solids,
            populate_num_table_solid,
        ],
        dependencies={
            populate_num_table_solid.name: {
                create_all_tables_solids.name: DependencyDefinition(create_all_tables_solids.name),
            }
        }
    )
