import tempfile

from airline_demo.pipelines import local_parquet_io_manager
from airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster import (
    LocalFileHandle,
    ModeDefinition,
    execute_pipeline,
    fs_io_manager,
    local_file_manager,
    pipeline,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.utils import file_relative_path
from dagster_pyspark import pyspark_resource
from pyspark.sql import Row


@solid
def collect_df(df):
    """The pyspark Spark context will be stopped on pipeline termination, so we need to collect
    the pyspark DataFrame before pipeline completion.
    """
    return df.collect()


def test_ingest_csv_file_handle_to_spark(spark_config):
    @solid
    def emit_num_csv_local_file():
        return LocalFileHandle(file_relative_path(__file__, "../num.csv"))

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "pyspark": pyspark_resource,
                    "pyspark_step_launcher": no_step_launcher,
                    "pyspark_io_manager": local_parquet_io_manager,
                    "file_manager": local_file_manager,
                    "io_manager": fs_io_manager,
                }
            )
        ]
    )
    def ingest_csv_file_test():
        return collect_df(ingest_csv_file_handle_to_spark(emit_num_csv_local_file()))

    with tempfile.TemporaryDirectory() as temp_dir:
        result = execute_pipeline(
            ingest_csv_file_test,
            run_config={
                "resources": {
                    "pyspark": {"config": {"spark_conf": spark_config}},
                    "pyspark_io_manager": {"config": {"base_dir": temp_dir}},
                    "io_manager": {"config": {"base_dir": temp_dir}},
                }
            },
        )
        assert result.success

        df = result.result_for_solid("collect_df").output_value()
        assert df == [Row(num1="1", num2="2")]


def test_ingest_csv_file_with_special_handle_to_spark(spark_config):
    @solid
    def emit_num_special_csv_local_file():
        return LocalFileHandle(file_relative_path(__file__, "../num_with_special_chars.csv"))

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "pyspark": pyspark_resource,
                    "pyspark_step_launcher": no_step_launcher,
                    "file_manager": local_file_manager,
                    "pyspark_io_manager": local_parquet_io_manager,
                    "io_manager": fs_io_manager,
                }
            )
        ]
    )
    def ingest_csv_file_test():
        return collect_df(ingest_csv_file_handle_to_spark(emit_num_special_csv_local_file()))

    with tempfile.TemporaryDirectory() as temp_dir:
        result = execute_pipeline(
            ingest_csv_file_test,
            run_config={
                "resources": {
                    "pyspark": {"config": {"spark_conf": spark_config}},
                    "pyspark_io_manager": {"config": {"base_dir": temp_dir}},
                    "io_manager": {"config": {"base_dir": temp_dir}},
                }
            },
        )
        assert result.success

        df = result.result_for_solid("collect_df").output_value()

        assert df == [Row(num1="1", num2="2")]
