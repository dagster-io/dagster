from pyspark.sql import DataFrame

from dagster import PipelineDefinition, ModeDefinition, ResourceDefinition, execute_solid
from dagster.seven import mock
from dagster_examples.airline_demo.solids import load_data_to_database_from_spark
from dagster_examples.airline_demo.types import DbInfo


def test_airline_demo_load_df():
    db_info_mock = DbInfo(
        engine=mock.MagicMock(),
        url='url',
        jdbc_url='url',
        dialect='dialect',
        load_table=mock.MagicMock(),
        host='host',
        db_name='db_name',
    )
    pipeline_def = PipelineDefinition(
        name='load_df_test',
        solid_defs=[load_data_to_database_from_spark],
        mode_defs=[
            ModeDefinition(
                resource_defs={'db_info': ResourceDefinition.hardcoded_resource(db_info_mock)}
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
    assert len(mat.metadata_entries) == 2
    entries = {me.label: me for me in mat.metadata_entries}
    assert entries['Host'].entry_data.text == 'host'
    assert entries['Db'].entry_data.text == 'db_name'
