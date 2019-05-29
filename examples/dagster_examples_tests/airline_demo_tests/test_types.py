import os
import uuid

import botocore
import pyspark

from dagster import (
    DependencyDefinition,
    PipelineDefinition,
    RunConfig,
    RunStorageMode,
    execute_pipeline,
    lambda_solid,
)

from dagster.core.storage.intermediate_store import FileSystemIntermediateStore

from dagster_aws.s3.intermediate_store import S3IntermediateStore

from dagster_examples.airline_demo.solids import ingest_csv_to_spark

from .test_solids import spark_mode


def test_spark_data_frame_serialization_file_system():
    with open(os.path.join(os.path.dirname(__file__), 'data/test.csv'), 'rb') as fd:
        input_csv_file = fd.read()

    @lambda_solid
    def nonce():
        return input_csv_file

    pipeline_def = PipelineDefinition(
        [nonce, ingest_csv_to_spark],
        dependencies={'ingest_csv_to_spark': {'input_csv_file': DependencyDefinition('nonce')}},
        mode_definitions=[spark_mode],
    )

    run_id = str(uuid.uuid4())

    storage_mode = RunStorageMode.FILESYSTEM
    intermediate_store = FileSystemIntermediateStore(run_id=run_id)

    result = execute_pipeline(
        pipeline_def, run_config=RunConfig(run_id=run_id, storage_mode=storage_mode, mode='spark')
    )

    assert result.success
    result_dir = os.path.join(
        intermediate_store.root, 'intermediates', 'ingest_csv_to_spark.compute', 'result'
    )

    assert '_SUCCESS' in os.listdir(result_dir)

    spark = spark_mode.resource_defs['spark'].resource_fn(None)

    df = spark.read.parquet(result_dir)
    assert isinstance(df, pyspark.sql.dataframe.DataFrame)
    assert df.head()[0] == '1'


def test_spark_data_frame_serialization_s3():
    with open(os.path.join(os.path.dirname(__file__), 'data/test.csv'), 'rb') as fd:
        input_csv_file = fd.read()

    @lambda_solid
    def nonce():
        return input_csv_file

    pipeline_def = PipelineDefinition(
        [nonce, ingest_csv_to_spark],
        dependencies={'ingest_csv_to_spark': {'input_csv_file': DependencyDefinition('nonce')}},
        mode_definitions=[spark_mode],
    )

    run_id = str(uuid.uuid4())

    storage_mode = RunStorageMode.S3
    intermediate_store = S3IntermediateStore(s3_bucket='dagster-airflow-scratch', run_id=run_id)

    result = execute_pipeline(
        pipeline_def,
        environment_dict={'storage': {'s3': {'s3_bucket': 'dagster-airflow-scratch'}}},
        run_config=RunConfig(run_id=run_id, storage_mode=storage_mode, mode='spark'),
    )

    assert result.success

    success_key = '/'.join(
        [
            intermediate_store.root.strip('/'),
            'intermediates',
            'ingest_csv_to_spark.compute',
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
