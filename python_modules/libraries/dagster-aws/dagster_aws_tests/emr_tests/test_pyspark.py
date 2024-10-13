import os
import subprocess
import sys
from unittest import mock

import pytest
from dagster import reconstructable
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.input import In
from dagster._core.definitions.no_step_launcher import no_step_launcher
from dagster._core.definitions.output import Out
from dagster._core.errors import DagsterSubprocessError
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import deep_merge_dicts
from dagster._utils.test import create_test_pipeline_execution_context
from dagster_pyspark import DataFrame, pyspark_resource
from moto import mock_emr
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster_aws.emr import EmrError, EmrJobRunner
from dagster_aws.emr.pyspark_step_launcher import EmrPySparkStepLauncher, emr_pyspark_step_launcher
from dagster_aws.s3 import s3_resource

S3_BUCKET = "dagster-scratch-80542c2"


BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG = {
    "local_pipeline_package_path": os.path.abspath(os.path.dirname(__file__)),
    "cluster_id": os.environ.get("EMR_CLUSTER_ID"),
    "staging_bucket": S3_BUCKET,
    "region_name": "us-west-1",
    "deploy_local_pipeline_package": True,
}


@op(
    out=Out(DataFrame),
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def make_df_solid(context):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [
        Row(name="John", age=19),
        Row(name="Jennifer", age=29),
        Row(name="Henry", age=50),
    ]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@op(
    name="blah",
    description="this is a test",
    config_schema={"foo": str, "bar": int},
    ins={"people": In(DataFrame)},
    out=Out(DataFrame),
    required_resource_keys={"pyspark_step_launcher"},
)
def filter_df_solid(_, people):
    return people.filter(people["age"] < 30)


PROD_RESOURCES = {
    "pyspark_step_launcher": emr_pyspark_step_launcher,
    "pyspark": pyspark_resource,
    "s3": s3_resource,
}

LOCAL_RESOURCES = {
    "pyspark_step_launcher": no_step_launcher,
    "pyspark": pyspark_resource,
}


@graph
def pyspark_graph():
    filter_df_solid(make_df_solid())


def define_pyspark_job_prod():
    return pyspark_graph.to_job(resource_defs=PROD_RESOURCES)


def define_pyspark_job_local():
    return pyspark_graph.to_job(resource_defs=LOCAL_RESOURCES)


@op(
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def noop_op(_):
    pass


@graph
def noop_graph():
    noop_op()


def define_noop_job_prod():
    return noop_graph.to_job(resource_defs=PROD_RESOURCES, executor_def=in_process_executor)


def define_noop_job_local():
    return noop_graph.to_job(resource_defs=LOCAL_RESOURCES, executor_def=in_process_executor)


@pytest.mark.skipif(sys.version_info >= (3, 11), reason="no pyspark support on 3.11")
def test_local():
    result = define_pyspark_job_local().execute_in_process(
        run_config={"ops": {"blah": {"config": {"foo": "a string", "bar": 123}}}},
    )
    assert result.success


@mock_emr
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher.read_events")
@mock.patch("dagster_aws.emr.emr.EmrJobRunner.is_emr_step_complete")
@pytest.mark.skipif(sys.version_info >= (3, 11), reason="no pyspark support on 3.11")
def test_pyspark_emr(mock_is_emr_step_complete, mock_read_events, mock_s3_bucket):
    with instance_for_test() as instance:
        with execute_job(reconstructable(define_noop_job_local), instance=instance) as result:
            mock_read_events.return_value = instance.all_logs(result.run_id)

    run_job_flow_args = dict(
        Instances={
            "InstanceCount": 1,
            "KeepJobFlowAliveWhenNoSteps": True,
            "MasterInstanceType": "c3.medium",
            "Placement": {"AvailabilityZone": "us-west-1a"},
            "SlaveInstanceType": "c3.xlarge",
        },
        JobFlowRole="EMR_EC2_DefaultRole",
        LogUri=f"s3://{mock_s3_bucket.name}/log",
        Name="cluster",
        ServiceRole="EMR_DefaultRole",
        VisibleToAllUsers=True,
    )

    # Doing cluster setup outside of a solid here, because run_job_flow is not yet plumbed through
    # to the pyspark EMR resource.
    job_runner = EmrJobRunner(region="us-west-1")
    context = create_test_pipeline_execution_context()
    cluster_id = job_runner.run_job_flow(context.log, run_job_flow_args)

    with instance_for_test() as instance:
        with execute_job(
            reconstructable(define_noop_job_prod),
            instance=instance,
            raise_on_error=True,
            run_config={
                "resources": {
                    "pyspark_step_launcher": {
                        "config": deep_merge_dicts(
                            BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG,
                            {
                                "cluster_id": cluster_id,
                                "staging_bucket": mock_s3_bucket.name,
                            },
                        ),
                    }
                },
            },
        ) as result:
            assert result.success
            assert mock_is_emr_step_complete.called


def sync_code():
    # Sync remote dagster packages with local dagster code
    sync_code_command = [
        "rsync",
        "-av",
        "-progress",
        "--exclude='js_modules/'",
        "--exclude='.git/'",
        "--exclude='docs/'",
        "-e",
        '"ssh -i {aws_emr_pem_file}"'.format(aws_emr_pem_file=os.environ["AWS_EMR_PEM_FILE"]),
        os.environ["DAGSTER_DIR"],
        os.environ["AWS_EMR_NODE_ADDRESS"] + ":~/",
    ]
    if (
        subprocess.call(
            " ".join(sync_code_command),
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=True,
        )
        != 0
    ):
        raise DagsterSubprocessError("Failed to sync code to EMR")

    # Install dagster packages on remote node
    remote_install_dagster_packages_command = [
        "sudo",
        "python3",
        "-m",
        "pip",
        "install",
    ] + [
        token
        for package_subpath in ["dagster", "libraries/dagster-pyspark"]
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

    with instance_for_test() as instance:
        with execute_job(
            reconstructable(define_pyspark_job_prod),
            instance=instance,
            run_config={
                "ops": {"blah": {"config": {"foo": "a string", "bar": 123}}},
                "resources": {
                    "pyspark_step_launcher": {"config": BASE_EMR_PYSPARK_STEP_LAUNCHER_CONFIG},
                },
            },
        ) as result:
            assert result.success


@mock.patch("boto3.resource")
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher.wait_for_completion")
@mock.patch("dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher._log_logs_from_s3")
@mock.patch("dagster._core.events.log_step_event")
@pytest.mark.skipif(sys.version_info >= (3, 11), reason="no pyspark support on 3.11")
def test_fetch_logs_on_fail(
    _mock_log_step_event, mock_log_logs, mock_wait_for_completion, _mock_boto3_resource
):
    mock_log = mock.MagicMock()
    mock_step_context = mock.MagicMock()
    mock_step_context.log = mock_log
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
        for _ in step_launcher.wait_for_completion_and_log(None, None, None, mock_step_context):
            pass

    assert mock_log_logs.call_count == 1
