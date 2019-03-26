import os
import shutil
import uuid

import pyspark


from dagster import (
    DependencyDefinition,
    lambda_solid,
    PipelineDefinition,
    RunConfig,
    RunStorageMode,
)
from dagster.core.execution import execute_pipeline, yield_pipeline_execution_context
from dagster.core.object_store import FileSystemObjectStore, S3ObjectStore

from airline_demo.solids import ingest_csv_to_spark
from airline_demo.types import SparkDataFrameType

from .test_solids import _spark_context


def test_spark_data_frame_serialization_file_system():
    path_to_test_csv = os.path.join(os.path.dirname(__file__), 'data/test.csv')

    @lambda_solid
    def nonce():
        return path_to_test_csv

    pipeline_def = PipelineDefinition(
        [nonce, ingest_csv_to_spark],
        dependencies={'ingest_csv_to_spark': {'input_csv': DependencyDefinition('nonce')}},
        context_definitions=_spark_context(),
    )

    run_id = str(uuid.uuid4())

    storage_mode = RunStorageMode.FILESYSTEM
    object_store = FileSystemObjectStore(run_id=run_id)

    result = execute_pipeline(
        pipeline_def, run_config=RunConfig(run_id=run_id, storage_mode=storage_mode)
    )

    assert result.success
    result_dir = os.path.join(
        object_store.root, 'intermediates', 'ingest_spark_to_csv.transform', 'result'
    )

    assert '_SUCCESS' in os.listdir(result_dir)

    spark = _spark_context()['test'].resources['spark'].resource_fn(None)

    df = spark.read.parquet(result_dir)
    assert isinstance(df, pyspark.sql.dataframe.DataFrame)
    assert df.head()[0] == '1'


def test_spark_data_frame_serialization_s3():
    path_to_test_csv = os.path.join(os.path.dirname(__file__), 'data/test.csv')

    @lambda_solid
    def nonce():
        return path_to_test_csv

    pipeline_def = PipelineDefinition(
        [nonce, ingest_csv_to_spark],
        dependencies={'ingest_csv_to_spark': {'input_csv': DependencyDefinition('nonce')}},
        context_definitions=_spark_context(),
    )

    run_id = str(uuid.uuid4())

    storage_mode = RunStorageMode.S3
    object_store = S3ObjectStore(s3_bucket='dagster-airflow-scratch', run_id=run_id)

    result = execute_pipeline(
        pipeline_def,
        environment_dict={'storage': {'s3': {'s3_bucket': 'dagster-airflow-scratch'}}},
        run_config=RunConfig(run_id=run_id, storage_mode=storage_mode),
    )

    assert result.success

    assert object_store.s3.get_object(
        Bucket=object_store.bucket,
        Key='/'.join(
            [
                object_store.root.strip(object_store.bucket).strip('/'),
                'files',
                'intermediates',
                'ingest_spark_to_csv.transform',
                'result',
                '_SUCCESS',
            ]
        ),
    )
