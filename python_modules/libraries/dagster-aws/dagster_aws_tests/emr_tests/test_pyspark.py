import os
import subprocess
import sys
from unittest import mock

import pytest
from dagster_aws.emr import EmrError, EmrJobRunner
from dagster_aws.emr.pyspark_step_launcher import EmrPySparkStepLauncher, emr_pyspark_step_launcher
from dagster_aws.s3 import s3_resource
from dagster_pyspark import DataFrame, pyspark_resource
from moto import mock_emr
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import IOManager, execute_pipeline, graph, io_manager, op, reconstructable
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.errors import DagsterSubprocessError
from dagster.utils.merger import deep_merge_dicts
from dagster.utils.test import create_test_pipeline_execution_context

S3_BUCKET = "dagster-scratch-80542c2"


BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG = {
    "local_pipeline_package_path": os.path.abspath(os.path.dirname(__file__)),
    "cluster_id": os.environ.get("EMR_CLUSTER_ID"),
    "staging_bucket": S3_BUCKET,
    "region_name": "us-west-1",
    "deploy_local_pipeline_package": True,
}


@io_manager(required_resource_keys={"pyspark"})
def s3_io_manager(_):
    class S3ParquetIOManager(IOManager):
        def _get_path(self, context):
            return f"s3a://{S3_BUCKET}/{context.run_id}_{context.step_key}_{context.name}"

        def handle_output(self, context, obj):
            # handle ints as well as dataframes (lol)
            if isinstance(obj, int):
                obj = context.resources.pyspark.spark_session.createDataFrame([[obj]], ["val"])
            obj.write.parquet(self._get_path(context), mode="overwrite")

        def load_input(self, context):
            df = context.resources.pyspark.spark_session.read.parquet(
                self._get_path(context.upstream_output)
            )
            if context.upstream_output.dagster_type != DataFrame:
                return df.head()[0]
            return df

    return S3ParquetIOManager()


@op(required_resource_keys={"pyspark_step_launcher", "pyspark"})
def make_df_solid(context) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="John", age=19), Row(name="Jennifer", age=29), Row(name="Henry", age=50)]
    context.log.info("hello there!")
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@op(
    name="blah",
    description="this is a test",
    config_schema={"foo": str, "bar": int},
    required_resource_keys={"pyspark_step_launcher"},
)
def filter_df_solid(context, people: DataFrame) -> DataFrame:
    context.log.info("im here!")
    return people.filter(people["age"] < 30)


RESOURCES_PROD = {
    "pyspark_step_launcher": emr_pyspark_step_launcher,
    "pyspark": pyspark_resource,
    "s3": s3_resource,
    "io_manager": s3_io_manager,
}

RESOURCES_LOCAL = {"pyspark_step_launcher": no_step_launcher, "pyspark": pyspark_resource}


@graph
def pyspark_pipe():
    filter_df_solid(make_df_solid())


def define_pyspark_pipe_local():
    return pyspark_pipe.to_job(name="ppl", resource_defs=RESOURCES_LOCAL)


def define_pyspark_pipe_prod():
    return pyspark_pipe.to_job(
        name="ppp",
        resource_defs=RESOURCES_PROD,
        config={
            "ops": {"blah": {"config": {"foo": "a string", "bar": 123}}},
            "resources": {
                "pyspark_step_launcher": {"config": BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG},
            },
        },
    )


@op(required_resource_keys={"pyspark_step_launcher", "pyspark"})
def do_nothing_solid(_):
    pass


@graph
def do_nothing_pipe():
    do_nothing_solid()


def define_do_nothing_pipe_local():
    return do_nothing_pipe.to_job(resource_defs=RESOURCES_LOCAL)


def define_do_nothing_pipe_prod():
    return do_nothing_pipe.to_job(
        resource_defs=RESOURCES_PROD,
    )


def test_local():
    result = execute_pipeline(
        pipeline=reconstructable(define_pyspark_pipe_local),
        run_config={"solids": {"blah": {"config": {"foo": "a string", "bar": 123}}}},
    )
    assert result.success


@mock_emr
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher.read_events")
@mock.patch("dagster_aws.emr.emr.EmrJobRunner.is_emr_step_complete")
def test_pyspark_emr(mock_is_emr_step_complete, mock_read_events, mock_s3_bucket):
    mock_read_events.return_value = execute_pipeline(
        reconstructable(define_do_nothing_pipe_local)
    ).events_by_step_key["do_nothing_solid"]

    run_job_flow_args = dict(
        Instances={
            "InstanceCount": 1,
            "KeepJobFlowAliveWhenNoSteps": True,
            "MasterInstanceType": "c3.medium",
            "Placement": {"AvailabilityZone": "us-west-1a"},
            "SlaveInstanceType": "c3.xlarge",
        },
        JobFlowRole="EMR_EC2_DefaultRole",
        LogUri="s3://{bucket}/log".format(bucket=mock_s3_bucket.name),
        Name="cluster",
        ServiceRole="EMR_DefaultRole",
        VisibleToAllUsers=True,
    )

    # Doing cluster setup outside of a solid here, because run_job_flow is not yet plumbed through
    # to the pyspark EMR resource.
    job_runner = EmrJobRunner(region="us-west-1")
    context = create_test_pipeline_execution_context()
    cluster_id = job_runner.run_job_flow(context.log, run_job_flow_args)

    result = execute_pipeline(
        pipeline=reconstructable(define_do_nothing_pipe_prod),
        mode="prod",
        run_config={
            "resources": {
                "pyspark_step_launcher": {
                    "config": deep_merge_dicts(
                        BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG,
                        {"cluster_id": cluster_id, "staging_bucket": mock_s3_bucket.name},
                    ),
                }
            },
        },
    )
    assert result.success
    assert mock_is_emr_step_complete.called


def sync_code():
    # Sync remote dagster packages with local dagster code
    sync_code_command = [
        "rsync",
        "-av",
        "-progress",
        "--inplace",
        "--exclude='js_modules/'",
        "--exclude='.git/'",
        "--exclude='docs/'",
        "--exclude='examples/'",
        "--exclude='*.pyc'",
        "--exclude='*/.tox/*'",
        "-e",
        '"ssh -i {aws_emr_pem_file}"'.format(aws_emr_pem_file=os.environ["AWS_EMR_PEM_FILE"]),
        os.environ["DAGSTER_DIR"],
        os.environ["AWS_EMR_NODE_ADDRESS"] + ":~/",
    ]
    if (
        subprocess.call(
            " ".join(sync_code_command), stdout=sys.stdout, stderr=sys.stderr, shell=True
        )
        != 0
    ):
        raise DagsterSubprocessError("Failed to sync code to EMR")

    # Install dagster packages on remote node
    remote_install_dagster_packages_command = ["sudo", "python3", "-m", "pip", "install"] + [
        token
        for package_subpath in ["dagster", "libraries/dagster-pyspark", "libraries/dagster-aws"]
        for token in ["-e", "/home/hadoop/dagster/python_modules/" + package_subpath]
    ]

    install_dagster_packages_command = [
        "ssh",
        "-i",
        os.environ["AWS_EMR_PEM_FILE"],
        os.environ["AWS_EMR_NODE_ADDRESS"],
        "'" + " ".join(remote_install_dagster_packages_command) + "'",
    ]
    if (
        subprocess.call(
            " ".join(install_dagster_packages_command),
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=True,
        )
        != 0
    ):
        raise DagsterSubprocessError("Failed to install dagster packages on EMR")


@pytest.mark.skipif(
    "AWS_EMR_TEST_DO_IT_LIVE" not in os.environ,
    reason="This test is slow and requires a live EMR cluster; run only upon explicit request",
)
def test_do_it_live_emr():
    sync_code()

    del os.environ["AWS_ACCESS_KEY_ID"]
    del os.environ["AWS_SECRET_ACCESS_KEY"]
    result = execute_pipeline(
        reconstructable(define_pyspark_pipe_prod),
        mode="prod",
    )
    assert result.success


@mock.patch("boto3.resource")
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher.wait_for_completion")
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher._log_logs_from_s3")
@mock.patch("dagster.core.events.log_step_event")
def test_fetch_logs_on_fail(
    _mock_log_step_event, mock_log_logs, mock_wait_for_completion, _mock_boto3_resource
):
    mock_context = mock.MagicMock()
    mock_wait_for_completion.side_effect = EmrError()

    step_launcher = EmrPySparkStepLauncher(
        region_name="",
        staging_bucket="",
        staging_prefix="",
        spark_config=None,
        action_on_failure="",
        cluster_id="",
        local_job_package_path="",
        deploy_local_job_package=False,
        wait_for_logs=True,
    )

    with pytest.raises(EmrError):
        for _ in step_launcher.wait_for_completion_and_log(mock_context, None, None, None, None):
            pass

    assert mock_log_logs.call_count == 1
