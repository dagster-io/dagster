from dagster import pipeline, solid, execute_pipeline, LocalFileHandle, ModeDefinition
from dagster_examples.airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster_examples.airline_demo.resources import spark_session_local
from dagster.utils import file_relative_path

from pyspark.sql import Row

# for dep graphs
# pylint: disable=no-value-for-parameter


def test_ingest_csv_file_handle_to_spark():
    @solid
    def emit_num_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num.csv'))

    @pipeline(mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})])
    def ingest_csv_file_test(_):
        return ingest_csv_file_handle_to_spark(emit_num_csv_local_file())

    result = execute_pipeline(ingest_csv_file_test)
    assert result.success

    df = result.result_for_solid('ingest_csv_file_handle_to_spark').result_value()

    assert df.collect() == [Row(num1='1', num2='2')]


def test_ingest_csv_file_with_special_handle_to_spark():
    @solid
    def emit_num_special_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num_with_special_chars.csv'))

    @pipeline(mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})])
    def ingest_csv_file_test(_):
        return ingest_csv_file_handle_to_spark(emit_num_special_csv_local_file())

    result = execute_pipeline(ingest_csv_file_test)
    assert result.success

    df = result.result_for_solid('ingest_csv_file_handle_to_spark').result_value()

    assert df.collect() == [Row(num1='1', num2='2')]
