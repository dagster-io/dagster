import os

import botocore
import pyspark
from airline_demo.solids import ingest_csv_file_handle_to_spark
from dagster import (
    InputDefinition,
    LocalFileHandle,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    file_relative_path,
    local_file_manager,
    pipeline,
    seven,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.core.storage.temp_file_manager import tempfile_resource
from dagster_aws.s3 import s3_file_manager, s3_plus_default_intermediate_storage_defs, s3_resource
from dagster_aws.s3.intermediate_storage import S3IntermediateStorage
from dagster_pyspark import DataFrame, pyspark_resource
from pyspark.sql import Row, SparkSession

spark_local_fs_mode = ModeDefinition(
    name="spark",
    resource_defs={
        "pyspark": pyspark_resource,
        "tempfile": tempfile_resource,
        "s3": s3_resource,
        "pyspark_step_launcher": no_step_launcher,
        "file_manager": local_file_manager,
    },
    intermediate_storage_defs=s3_plus_default_intermediate_storage_defs,
)

spark_s3_mode = ModeDefinition(
    name="spark",
    resource_defs={
        "pyspark": pyspark_resource,
        "tempfile": tempfile_resource,
        "s3": s3_resource,
        "pyspark_step_launcher": no_step_launcher,
        "file_manager": s3_file_manager,
    },
    intermediate_storage_defs=s3_plus_default_intermediate_storage_defs,
)


def test_spark_data_frame_serialization_file_system_file_handle(spark_config):
    @solid
    def nonce(_):
        return LocalFileHandle(file_relative_path(__file__, "data/test.csv"))

    @pipeline(mode_defs=[spark_local_fs_mode])
    def spark_df_test_pipeline():
        ingest_csv_file_handle_to_spark(nonce())

    instance = DagsterInstance.ephemeral()

    result = execute_pipeline(
        spark_df_test_pipeline,
        mode="spark",
        run_config={
            "intermediate_storage": {"filesystem": {}},
            "resources": {"pyspark": {"config": {"spark_conf": spark_config}}},
        },
        instance=instance,
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, run_id=result.run_id
    )

    assert result.success
    result_dir = os.path.join(
        intermediate_storage.root,
        "intermediates",
        "ingest_csv_file_handle_to_spark.compute",
        "result",
    )

    assert "_SUCCESS" in os.listdir(result_dir)

    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(result_dir)
    assert isinstance(df, pyspark.sql.dataframe.DataFrame)
    assert df.head()[0] == "1"


def test_spark_data_frame_serialization_s3_file_handle(s3_bucket, spark_config):
    @solid(required_resource_keys={"file_manager"})
    def nonce(context):
        with open(os.path.join(os.path.dirname(__file__), "data/test.csv"), "rb") as fd:
            return context.resources.file_manager.write_data(fd.read())

    @pipeline(mode_defs=[spark_s3_mode])
    def spark_df_test_pipeline():

        ingest_csv_file_handle_to_spark(nonce())

    result = execute_pipeline(
        spark_df_test_pipeline,
        run_config={
            "intermediate_storage": {"s3": {"config": {"s3_bucket": s3_bucket}}},
            "resources": {
                "pyspark": {"config": {"spark_conf": spark_config}},
                "file_manager": {"config": {"s3_bucket": s3_bucket}},
            },
        },
        mode="spark",
    )

    assert result.success

    intermediate_storage = S3IntermediateStorage(s3_bucket=s3_bucket, run_id=result.run_id)

    success_key = "/".join(
        [
            intermediate_storage.root.strip("/"),
            "intermediates",
            "ingest_csv_file_handle_to_spark.compute",
            "result",
            "_SUCCESS",
        ]
    )
    try:
        assert intermediate_storage.object_store.s3.get_object(
            Bucket=intermediate_storage.object_store.bucket, Key=success_key
        )
    except botocore.exceptions.ClientError:
        raise Exception("Couldn't find object at {success_key}".format(success_key=success_key))


def test_spark_dataframe_output_csv(spark_config):
    spark = SparkSession.builder.getOrCreate()
    num_df = (
        spark.read.format("csv")
        .options(header="true", inferSchema="true")
        .load(file_relative_path(__file__, "num.csv"))
    )

    assert num_df.collect() == [Row(num1=1, num2=2)]

    @solid
    def emit(_):
        return num_df

    @solid(input_defs=[InputDefinition("df", DataFrame)], output_defs=[OutputDefinition(DataFrame)])
    def passthrough_df(_context, df):
        return df

    @pipeline(mode_defs=[spark_local_fs_mode])
    def passthrough():
        passthrough_df(emit())

    with seven.TemporaryDirectory() as tempdir:
        file_name = os.path.join(tempdir, "output.csv")
        result = execute_pipeline(
            passthrough,
            run_config={
                "resources": {"pyspark": {"config": {"spark_conf": spark_config}}},
                "solids": {
                    "passthrough_df": {
                        "outputs": [{"result": {"csv": {"path": file_name, "header": True}}}]
                    }
                },
            },
        )

        from_file_df = (
            spark.read.format("csv").options(header="true", inferSchema="true").load(file_name)
        )

        assert (
            result.result_for_solid("passthrough_df").output_value().collect()
            == from_file_df.collect()
        )
