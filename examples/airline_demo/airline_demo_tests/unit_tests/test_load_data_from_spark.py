import tempfile
from unittest import mock

from airline_demo.pipelines import local_parquet_io_manager
from airline_demo.resources import DbInfo
from airline_demo.solids import load_data_to_database_from_spark
from dagster import (
    ModeDefinition,
    OutputDefinition,
    ResourceDefinition,
    execute_pipeline,
    fs_io_manager,
    pipeline,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.utils import file_relative_path
from dagster_pyspark import pyspark_resource


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

    @solid(
        required_resource_keys={"pyspark"},
        output_defs=[OutputDefinition(io_manager_key="pyspark_io_manager")],
    )
    def emit_mock(context):
        return context.resources.pyspark.spark_session.read.csv(
            file_relative_path(__file__, "../data/test.csv")
        )

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "db_info": ResourceDefinition.hardcoded_resource(db_info_mock),
                    "pyspark": pyspark_resource,
                    "pyspark_step_launcher": no_step_launcher,
                    "pyspark_io_manager": local_parquet_io_manager,
                    "io_manager": fs_io_manager,
                }
            )
        ]
    )
    def load_df_test():
        load_data_to_database_from_spark(emit_mock())

    with tempfile.TemporaryDirectory() as temp_dir:
        solid_result = execute_pipeline(
            load_df_test,
            run_config={
                "solids": {"load_data_to_database_from_spark": {"config": {"table_name": "foo"}}},
                "resources": {
                    "io_manager": {"config": {"base_dir": temp_dir}},
                    "pyspark_io_manager": {"config": {"base_dir": temp_dir}},
                },
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
