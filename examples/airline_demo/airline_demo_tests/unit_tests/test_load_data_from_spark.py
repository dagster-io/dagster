from airline_demo.resources import DbInfo
from airline_demo.solids import load_data_to_database_from_spark
from dagster import ModeDefinition, ResourceDefinition, execute_pipeline, pipeline, solid
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.seven import mock
from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame


def test_airline_demo_load_df():
    db_info_mock = DbInfo(
        engine=mock.MagicMock(),
        url="url",
        jdbc_url="url",
        dialect="dialect",
        load_table=mock.MagicMock(),
        host="host",
        db_name="db_name",
    )

    @solid
    def emit_mock(_):
        return mock.MagicMock(spec=DataFrame)

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "db_info": ResourceDefinition.hardcoded_resource(db_info_mock),
                    "pyspark": pyspark_resource,
                    "pyspark_step_launcher": no_step_launcher,
                }
            )
        ]
    )
    def load_df_test():
        load_data_to_database_from_spark(emit_mock())

    solid_result = execute_pipeline(
        load_df_test,
        run_config={
            "solids": {"load_data_to_database_from_spark": {"config": {"table_name": "foo"}}}
        },
    ).result_for_solid("load_data_to_database_from_spark")

    assert solid_result.success
    mats = solid_result.materializations_during_compute
    assert len(mats) == 1
    mat = mats[0]
    assert len(mat.metadata_entries) == 2
    entries = {me.label: me for me in mat.metadata_entries}
    assert entries["Host"].entry_data.text == "host"
    assert entries["Db"].entry_data.text == "db_name"
