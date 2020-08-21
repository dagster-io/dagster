import os
import sys

import boto3
import six
from dagster_aws.s3 import S3ComputeLogManager
from moto import mock_s3

from dagster import DagsterEventType, execute_pipeline, pipeline, seven, solid
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import CliApiRunLauncher
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy.compute".',
    'STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).',
    'STEP_SUCCESS - Finished execution of step "easy.compute"',
]


@mock_s3
def test_compute_log_manager(s3_bucket):
    @pipeline
    def simple():
        @solid
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # pylint: disable=print-call
            return "easy"

        easy()

    # Uses mock S3
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=s3_bucket)

    with seven.TemporaryDirectory() as temp_dir:
        run_store = SqliteRunStorage.from_local(temp_dir)
        event_store = SqliteEventLogStorage(temp_dir)
        manager = S3ComputeLogManager(bucket=s3_bucket, prefix="my_prefix", local_dir=temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=manager,
            run_launcher=CliApiRunLauncher(),
        )
        result = execute_pipeline(simple, instance=instance)
        compute_steps = [
            event.step_key
            for event in result.step_event_list
            if event.event_type == DagsterEventType.STEP_START
        ]
        assert len(compute_steps) == 1
        step_key = compute_steps[0]

        stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
        assert stdout.data == HELLO_WORLD + SEPARATOR

        stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
        for expected in EXPECTED_LOGS:
            assert expected in stderr.data

        # Check S3 directly
        s3_object = s3.get_object(
            Bucket=s3_bucket,
            Key="{prefix}/storage/{run_id}/compute_logs/easy.compute.err".format(
                prefix="my_prefix", run_id=result.run_id
            ),
        )
        stderr_s3 = six.ensure_str(s3_object["Body"].read())
        for expected in EXPECTED_LOGS:
            assert expected in stderr_s3

        # Check download behavior by deleting locally cached logs
        compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
        for filename in os.listdir(compute_logs_dir):
            os.unlink(os.path.join(compute_logs_dir, filename))

        stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
        assert stdout.data == HELLO_WORLD + SEPARATOR

        stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
        for expected in EXPECTED_LOGS:
            assert expected in stderr.data


@mock_s3
def test_compute_log_manager_from_config(s3_bucket):
    s3_prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "{s3_bucket}"
    local_dir: "/tmp/cool"
    prefix: "{s3_prefix}"
""".format(
        s3_bucket=s3_bucket, s3_prefix=s3_prefix
    )

    with seven.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(six.ensure_binary(dagster_yaml))

        instance = DagsterInstance.from_config(tempdir)
    assert instance.compute_log_manager._s3_bucket == s3_bucket  # pylint: disable=protected-access
    assert instance.compute_log_manager._s3_prefix == s3_prefix  # pylint: disable=protected-access
