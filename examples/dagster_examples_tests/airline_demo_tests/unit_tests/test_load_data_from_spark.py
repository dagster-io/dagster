from pyspark.sql import DataFrame

from dagster import PipelineDefinition, ModeDefinition, ResourceDefinition, execute_solid
from dagster.seven import mock
from dagster_examples.airline_demo.solids import load_data_to_database_from_spark


def test_airline_demo_load_df():
    pipeline_def = PipelineDefinition(
        name='load_df_test',
        solids=[load_data_to_database_from_spark],
        mode_definitions=[
            ModeDefinition(
                resources={'db_info': ResourceDefinition.hardcoded_resource(mock.MagicMock())}
            )
        ],
    )

    solid_result = execute_solid(
        pipeline_def,
        'load_data_to_database_from_spark',
        inputs={'data_frame': mock.MagicMock(spec=DataFrame)},
        environment_dict={
            'solids': {'load_data_to_database_from_spark': {'config': {'table_name': 'foo'}}}
        },
    )
    assert solid_result.success
    mats = solid_result.materializations_during_compute
    assert len(mats) == 1
    mat = mats[0]
    # This is obviously a dumb thing to materialize
    # Can improve when https://github.com/dagster-io/dagster/issues/1438 is complete
    assert mat.path == 'Persisted Db Table: foo'

    assert solid_result.result_value('table_name') == 'foo'
