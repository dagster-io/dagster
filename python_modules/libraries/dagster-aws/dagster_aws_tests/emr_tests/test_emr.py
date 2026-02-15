import copy
import gzip
import io
import threading
import time
from unittest import mock

import pytest
from dagster._utils.test import create_test_pipeline_execution_context
from moto import mock_emr

from dagster_aws.emr import EmrClusterState, EmrError, EmrJobRunner
from dagster_aws.utils.mrjob.utils import _boto3_now

REGION = "us-west-1"


@mock_emr
def test_emr_create_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context.log, emr_cluster_config)
    assert cluster_id.startswith("j-")


@mock_emr
def test_emr_add_tags_and_describe_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)

    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)

    emr.add_tags(context.log, {"foobar": "v1", "baz": "123"}, cluster_id)

    tags = emr.describe_cluster(cluster_id)["Cluster"]["Tags"]  # pyright: ignore[reportOptionalSubscript]

    assert {"Key": "baz", "Value": "123"} in tags
    assert {"Key": "foobar", "Value": "v1"} in tags


@mock_emr
def test_emr_describe_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context.log, emr_cluster_config)
    cluster_info = cluster.describe_cluster(cluster_id)["Cluster"]  # pyright: ignore[reportOptionalSubscript]
    assert cluster_info["Name"] == "test-emr"
    assert EmrClusterState(cluster_info["Status"]["State"]) == EmrClusterState.Waiting


@mock_emr
def test_emr_id_from_name(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context.log, emr_cluster_config)
    assert cluster.cluster_id_from_name("test-emr") == cluster_id

    with pytest.raises(EmrError) as exc_info:
        cluster.cluster_id_from_name("cluster-doesnt-exist")

    assert "cluster cluster-doesnt-exist not found in region us-west-1" in str(exc_info.value)


def test_emr_construct_step_dict():
    cmd = ["pip", "install", "dagster"]

    assert EmrJobRunner.construct_step_dict_for_command("test_step", cmd) == {
        "Name": "test_step",
        "ActionOnFailure": "CONTINUE",
        "HadoopJarStep": {"Jar": "command-runner.jar", "Args": cmd},
    }

    assert EmrJobRunner.construct_step_dict_for_command(
        "test_second_step", cmd, action_on_failure="CANCEL_AND_WAIT"
    ) == {
        "Name": "test_second_step",
        "ActionOnFailure": "CANCEL_AND_WAIT",
        "HadoopJarStep": {"Jar": "command-runner.jar", "Args": cmd},
    }


@mock_emr
def test_emr_log_location_for_cluster(emr_cluster_config, mock_s3_bucket):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)
    assert emr.log_location_for_cluster(cluster_id) == (mock_s3_bucket.name, "elasticmapreduce/")

    # Should raise when the log URI is missing
    emr_cluster_config = copy.deepcopy(emr_cluster_config)
    del emr_cluster_config["LogUri"]
    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)
    with pytest.raises(EmrError) as exc_info:
        emr.log_location_for_cluster(cluster_id)

    assert "Log URI not specified, cannot retrieve step execution logs" in str(exc_info.value)


@mock_emr
def test_emr_retrieve_logs(emr_cluster_config, mock_s3_bucket):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)
    assert emr.log_location_for_cluster(cluster_id) == (mock_s3_bucket.name, "elasticmapreduce/")

    def create_log():
        time.sleep(0.5)
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as fo:
            fo.write(b"some log")

        prefix = "elasticmapreduce/{cluster_id}/steps/{step_id}".format(
            cluster_id=cluster_id, step_id="s-123456123456"
        )

        for name in ["stdout.gz", "stderr.gz"]:
            mock_s3_bucket.Object(prefix + "/" + name).put(Body=out.getvalue())

    thread = threading.Thread(target=create_log, args=(), daemon=True)
    thread.start()

    stdout_log, stderr_log = emr.retrieve_logs_for_step_id(
        context.log, cluster_id, "s-123456123456"
    )
    assert stdout_log == "some log"
    assert stderr_log == "some log"


def test_wait_for_log(mock_s3_bucket):
    def create_log():
        time.sleep(0.5)
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as fo:
            fo.write(b"foo bar")

        mock_s3_bucket.Object("some_log_file").put(Body=out.getvalue())

    thread = threading.Thread(target=create_log, args=(), daemon=True)
    thread.start()

    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    res = emr.wait_for_log(
        context.log,
        log_bucket=mock_s3_bucket.name,
        log_key="some_log_file",
        waiter_delay=1,
        waiter_max_attempts=2,
    )
    assert res == "foo bar"

    with pytest.raises(EmrError) as exc_info:
        emr.wait_for_log(
            context.log,
            log_bucket=mock_s3_bucket.name,
            log_key="does_not_exist",
            waiter_delay=1,
            waiter_max_attempts=1,
        )
    assert "EMR log file did not appear on S3 after waiting" in str(exc_info.value)


@mock_emr
def test_is_emr_step_complete(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION, check_cluster_every=1)

    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)

    step_name = "test_step"
    step_cmd = ["ls", "/"]
    step_ids = emr.add_job_flow_steps(
        context.log, cluster_id, [emr.construct_step_dict_for_command(step_name, step_cmd)]
    )

    def get_step_dict(step_id, step_state):
        return {
            "Step": {
                "Id": step_id,
                "Name": step_name,
                "Config": {"Jar": "command-runner.jar", "Properties": {}, "Args": step_cmd},
                "ActionOnFailure": "CONTINUE",
                "Status": {
                    "State": step_state,
                    "StateChangeReason": {"Message": "everything is hosed"},
                    "Timeline": {"StartDateTime": _boto3_now()},
                },
            },
        }

    emr_step_id = step_ids[0]
    describe_step_returns = [
        get_step_dict(emr_step_id, "PENDING"),
        get_step_dict(emr_step_id, "RUNNING"),
        get_step_dict(emr_step_id, "COMPLETED"),
        get_step_dict(emr_step_id, "FAILED"),
    ]
    with (
        mock.patch.object(EmrJobRunner, "describe_step", side_effect=describe_step_returns),
        mock.patch.object(
            EmrJobRunner, "retrieve_logs_for_step_id", return_value=("stdout", "stderr")
        ) as retrieve_logs,
    ):
        assert not emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)
        assert not emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)
        assert emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)

        with pytest.raises(EmrError) as exc_info:
            emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)
        assert "failed" in str(exc_info.value)
        # Check diagnostics are included in error
        assert exc_info.value.diagnostics is not None
        assert exc_info.value.diagnostics.step_id == emr_step_id
        assert exc_info.value.diagnostics.cluster_id == cluster_id
        assert exc_info.value.diagnostics.stderr_excerpt is not None
        assert exc_info.value.diagnostics.stdout_excerpt is not None
        retrieve_logs.assert_called_once()


@mock_emr
def test_emr_step_failure_diagnostics_with_config(emr_cluster_config):
    """Test that failure diagnostics use FailureLogConfig settings."""
    from dagster_aws.emr import FailureLogConfig

    context = create_test_pipeline_execution_context()
    config = FailureLogConfig(
        retrieve_logs=True,
        stderr_lines=10,
        stdout_lines=5,
        wait_timeout=60,
    )
    emr = EmrJobRunner(region=REGION, check_cluster_every=1, failure_log_config=config)

    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)
    step_ids = emr.add_job_flow_steps(
        context.log,
        cluster_id,
        [emr.construct_step_dict_for_command("test", ["ls"])],
    )
    emr_step_id = step_ids[0]

    # Create multi-line logs to test excerpt truncation
    long_stderr = "\n".join([f"stderr line {i}" for i in range(20)])
    long_stdout = "\n".join([f"stdout line {i}" for i in range(20)])

    failed_step = {
        "Step": {
            "Id": emr_step_id,
            "Name": "test",
            "Config": {"Jar": "command-runner.jar", "Properties": {}, "Args": ["ls"]},
            "ActionOnFailure": "CONTINUE",
            "Status": {
                "State": "FAILED",
                "StateChangeReason": {"Message": "Step failed due to error"},
                "Timeline": {"StartDateTime": _boto3_now()},
            },
        },
    }

    with (
        mock.patch.object(EmrJobRunner, "describe_step", return_value=failed_step),
        mock.patch.object(
            EmrJobRunner, "retrieve_logs_for_step_id", return_value=(long_stdout, long_stderr)
        ),
    ):
        with pytest.raises(EmrError) as exc_info:
            emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)

        diagnostics = exc_info.value.diagnostics
        assert diagnostics is not None
        # Check stderr was truncated to 10 lines
        assert diagnostics.stderr_excerpt.count("\n") == 9  # 10 lines = 9 newlines
        assert "stderr line 19" in diagnostics.stderr_excerpt
        assert "stderr line 10" in diagnostics.stderr_excerpt
        # Check stdout was truncated to 5 lines
        assert diagnostics.stdout_excerpt.count("\n") == 4  # 5 lines = 4 newlines
        assert "stdout line 19" in diagnostics.stdout_excerpt
        assert "stdout line 15" in diagnostics.stdout_excerpt


@mock_emr
def test_emr_step_failure_logs_disabled(emr_cluster_config):
    """Test that log retrieval can be disabled via config."""
    from dagster_aws.emr import FailureLogConfig

    context = create_test_pipeline_execution_context()
    config = FailureLogConfig(retrieve_logs=False)
    emr = EmrJobRunner(region=REGION, check_cluster_every=1, failure_log_config=config)

    cluster_id = emr.run_job_flow(context.log, emr_cluster_config)
    step_ids = emr.add_job_flow_steps(
        context.log,
        cluster_id,
        [emr.construct_step_dict_for_command("test", ["ls"])],
    )
    emr_step_id = step_ids[0]

    failed_step = {
        "Step": {
            "Id": emr_step_id,
            "Name": "test",
            "Config": {"Jar": "command-runner.jar", "Properties": {}, "Args": ["ls"]},
            "ActionOnFailure": "CONTINUE",
            "Status": {
                "State": "FAILED",
                "StateChangeReason": {"Message": "Test failure"},
                "Timeline": {"StartDateTime": _boto3_now()},
            },
        },
    }

    with (
        mock.patch.object(EmrJobRunner, "describe_step", return_value=failed_step),
        mock.patch.object(EmrJobRunner, "retrieve_logs_for_step_id") as retrieve_logs_mock,
    ):
        with pytest.raises(EmrError) as exc_info:
            emr.is_emr_step_complete(context.log, cluster_id, emr_step_id)

        # Logs should not be retrieved when disabled
        retrieve_logs_mock.assert_not_called()
        diagnostics = exc_info.value.diagnostics
        assert diagnostics.stderr_excerpt is None
        assert diagnostics.stdout_excerpt is None
        assert "Log retrieval disabled" in diagnostics.error_retrieving_logs


def test_emr_error_message_formatting():
    """Test that EmrError formats diagnostics correctly."""
    from dagster_aws.emr import StepFailureDiagnostics

    diagnostics = StepFailureDiagnostics(
        step_id="s-123",
        cluster_id="j-456",
        state_change_reason="Out of memory",
        stderr_excerpt="Error: OOM killed",
        stdout_excerpt="Processing...",
        logs_s3_uri="s3://bucket/logs/j-456/steps/s-123/",
    )

    error = EmrError("EMR step s-123 failed", diagnostics=diagnostics)

    error_str = str(error)
    assert "Cluster ID: j-456" in error_str
    assert "Step ID: s-123" in error_str
    assert "Reason: Out of memory" in error_str
    assert "Full logs: s3://bucket/logs/j-456/steps/s-123/" in error_str
    assert "--- stderr (last lines) ---" in error_str
    assert "Error: OOM killed" in error_str
    assert "--- stdout (last lines) ---" in error_str
    assert "Processing..." in error_str
