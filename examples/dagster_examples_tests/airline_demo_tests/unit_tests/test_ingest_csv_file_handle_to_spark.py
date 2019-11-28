from dagster_examples.airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster_pyspark import pyspark_resource
from pyspark.sql import Row

from dagster import LocalFileHandle, ModeDefinition, execute_pipeline, pipeline, solid
from dagster.utils import file_relative_path


@solid
def collect_df(_, df):
    '''The pyspark Spark context will be stopped on pipeline termination, so we need to collect
    the pyspark DataFrame before pipeline completion.
    '''
    return df.collect()


def test_ingest_csv_file_handle_to_spark(spark_config):
    @solid
    def emit_num_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num.csv'))

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'spark': pyspark_resource})])
    def ingest_csv_file_test():
        return collect_df(ingest_csv_file_handle_to_spark(emit_num_csv_local_file()))

    result = execute_pipeline(
        ingest_csv_file_test,
        environment_dict={'resources': {'spark': {'config': {'spark_conf': spark_config}}}},
    )
    assert result.success

    df = result.result_for_solid('collect_df').output_value()
    assert df == [Row(num1='1', num2='2')]


def test_ingest_csv_file_with_special_handle_to_spark(spark_config):
    @solid
    def emit_num_special_csv_local_file(_):
        return LocalFileHandle(file_relative_path(__file__, '../num_with_special_chars.csv'))

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'spark': pyspark_resource})])
    def ingest_csv_file_test():
        return collect_df(ingest_csv_file_handle_to_spark(emit_num_special_csv_local_file()))

    result = execute_pipeline(
        ingest_csv_file_test,
        environment_dict={'resources': {'spark': {'config': {'spark_conf': spark_config}}}},
    )
    assert result.success

    df = result.result_for_solid('collect_df').output_value()

    assert df == [Row(num1='1', num2='2')]
