import os
import uuid

import botocore
import pyspark
from dagster_aws.s3.intermediate_store import S3IntermediateStore
from dagster_examples.airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster_pyspark import DataFrame
from pyspark.sql import Row, SparkSession

from dagster import (
    InputDefinition,
    LocalFileHandle,
    OutputDefinition,
    RunConfig,
    execute_pipeline,
    file_relative_path,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store

from .test_solids import spark_mode


def test_spark_data_frame_serialization_file_system_file_handle():
    @solid
    def nonce(_):
        return LocalFileHandle(file_relative_path(__file__, 'data/test.csv'))

    @pipeline(mode_defs=[spark_mode])
    def spark_df_test_pipeline():

        ingest_csv_file_handle_to_spark(nonce())

    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()
    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory, run_id=run_id
    )

    result = execute_pipeline(
        spark_df_test_pipeline,
        run_config=RunConfig(run_id=run_id, mode='spark'),
        environment_dict={'storage': {'filesystem': {}}},
        instance=instance,
    )

    assert result.success
    result_dir = os.path.join(
        intermediate_store.root,
        'intermediates',
        'ingest_csv_file_handle_to_spark.compute',
        'result',
    )

    assert '_SUCCESS' in os.listdir(result_dir)

    spark = spark_mode.resource_defs['spark'].resource_fn(None)

    df = spark.read.parquet(result_dir)
    assert isinstance(df, pyspark.sql.dataframe.DataFrame)
    assert df.head()[0] == '1'


def test_spark_data_frame_serialization_s3_file_handle(s3_bucket):
    @solid
    def nonce(context):
        with open(os.path.join(os.path.dirname(__file__), 'data/test.csv'), 'rb') as fd:
            return context.file_manager.write_data(fd.read())

    @pipeline(mode_defs=[spark_mode])
    def spark_df_test_pipeline():

        ingest_csv_file_handle_to_spark(nonce())

    run_id = str(uuid.uuid4())

    intermediate_store = S3IntermediateStore(s3_bucket=s3_bucket, run_id=run_id)

    result = execute_pipeline(
        spark_df_test_pipeline,
        environment_dict={'storage': {'s3': {'config': {'s3_bucket': s3_bucket}}}},
        run_config=RunConfig(run_id=run_id, mode='spark'),
    )

    assert result.success

    success_key = '/'.join(
        [
            intermediate_store.root.strip('/'),
            'intermediates',
            'ingest_csv_file_handle_to_spark.compute',
            'result',
            '_SUCCESS',
        ]
    )
    try:
        assert intermediate_store.object_store.s3.get_object(
            Bucket=intermediate_store.object_store.bucket, Key=success_key
        )
    except botocore.exceptions.ClientError:
        raise Exception('Couldn\'t find object at {success_key}'.format(success_key=success_key))


def test_spark_dataframe_output_csv():
    spark = SparkSession.builder.getOrCreate()
    num_df = (
        spark.read.format('csv')
        .options(header='true', inferSchema='true')
        .load(file_relative_path(__file__, 'num.csv'))
    )

    assert num_df.collect() == [Row(num1=1, num2=2)]

    @solid
    def emit(_):
        return num_df

    @solid(input_defs=[InputDefinition('df', DataFrame)], output_defs=[OutputDefinition(DataFrame)])
    def passthrough_df(_context, df):
        return df

    @pipeline
    def passthrough():
        passthrough_df(emit())

    with seven.TemporaryDirectory() as tempdir:
        file_name = os.path.join(tempdir, 'output.csv')
        result = execute_pipeline(
            passthrough,
            environment_dict={
                'solids': {
                    'passthrough_df': {
                        'outputs': [{'result': {'csv': {'path': file_name, 'header': True}}}]
                    }
                }
            },
        )

        from_file_df = (
            spark.read.format('csv').options(header='true', inferSchema='true').load(file_name)
        )

        assert (
            result.result_for_solid('passthrough_df').output_value().collect()
            == from_file_df.collect()
        )
