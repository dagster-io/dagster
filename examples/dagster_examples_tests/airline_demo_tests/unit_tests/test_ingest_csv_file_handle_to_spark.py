from dagster_examples.airline_demo.resources import spark_session_local
from dagster_examples.airline_demo.solids import ingest_csv_file_handle_to_spark
from pyspark.sql import Row

from dagster import LocalFileHandle, ModeDefinition, execute_pipeline, pipeline, solid
from dagster.utils import file_relative_path

# for dep graphs


def test_ingest_csv_file_handle_to_spark():
    @solid
    def emit_num_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num.csv'))

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'spark': spark_session_local})])
    def ingest_csv_file_test():
        return ingest_csv_file_handle_to_spark(emit_num_csv_local_file())

    result = execute_pipeline(ingest_csv_file_test)
    assert result.success

    df = result.result_for_solid('ingest_csv_file_handle_to_spark').output_value()

    assert df.collect() == [Row(num1='1', num2='2')]


def test_ingest_csv_file_with_special_handle_to_spark():
    @solid
    def emit_num_special_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num_with_special_chars.csv'))

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'spark': spark_session_local})])
    def ingest_csv_file_test():
        return ingest_csv_file_handle_to_spark(emit_num_special_csv_local_file())

    result = execute_pipeline(ingest_csv_file_test)
    assert result.success

    df = result.result_for_solid('ingest_csv_file_handle_to_spark').output_value()

    assert df.collect() == [Row(num1='1', num2='2')]
