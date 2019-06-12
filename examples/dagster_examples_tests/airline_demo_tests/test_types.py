import os
import uuid

try:
    # Python 2 tempfile doesn't have tempfile.TemporaryDirectory
    import backports.tempfile as tempfile
except ImportError:
    import tempfile

import botocore
import pyspark
from pyspark.sql import SparkSession, Row

from dagster import (
    InputDefinition,
    LocalFileHandle,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    execute_solid,
    file_relative_path,
    lambda_solid,
    pipeline,
    solid,
)

from dagster.core.storage.intermediate_store import FileSystemIntermediateStore

from dagster_aws.s3.intermediate_store import S3IntermediateStore

from dagster_examples.airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster_examples.airline_demo.types import SparkDataFrameType

from .test_solids import spark_mode


def test_spark_data_frame_serialization_file_system_file_handle():
    @lambda_solid
    def nonce():
        return LocalFileHandle(file_relative_path(__file__, 'data/test.csv'))

    @pipeline(mode_definitions=[spark_mode])
    def spark_df_test_pipeline(_):
        # pylint: disable=no-value-for-parameter
        ingest_csv_file_handle_to_spark(nonce())

    run_id = str(uuid.uuid4())

    intermediate_store = FileSystemIntermediateStore(run_id=run_id)

    result = execute_pipeline(
        spark_df_test_pipeline,
        run_config=RunConfig(run_id=run_id, mode='spark'),
        environment_dict={'storage': {'filesystem': {}}},
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


def test_spark_data_frame_serialization_s3_file_handle():
    @solid
    def nonce(context):
        with open(os.path.join(os.path.dirname(__file__), 'data/test.csv'), 'rb') as fd:
            return context.file_manager.write_data(fd.read())

    @pipeline(mode_definitions=[spark_mode])
    def spark_df_test_pipeline(_):
        # pylint: disable=no-value-for-parameter
        ingest_csv_file_handle_to_spark(nonce())

    run_id = str(uuid.uuid4())

    intermediate_store = S3IntermediateStore(s3_bucket='dagster-airflow-scratch', run_id=run_id)

    result = execute_pipeline(
        spark_df_test_pipeline,
        environment_dict={'storage': {'s3': {'config': {'s3_bucket': 'dagster-airflow-scratch'}}}},
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

    @solid(
        inputs=[InputDefinition('df', SparkDataFrameType)],
        outputs=[OutputDefinition(SparkDataFrameType)],
    )
    def passthrough_df(_context, df):
        return df

    with tempfile.TemporaryDirectory() as tempdir:
        file_name = os.path.join(tempdir, 'output.csv')
        result = execute_solid(
            PipelineDefinition(name='passthrough', solids=[passthrough_df]),
            'passthrough_df',
            inputs={'df': num_df},
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

        assert result.result_value().collect() == from_file_df.collect()
