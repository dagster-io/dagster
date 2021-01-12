import os
import sys
import tempfile

from dagster import DagsterEventType, execute_pipeline, pipeline, solid
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster_aws.s3 import S3ComputeLogManager

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


def test_compute_log_manager(mock_s3_bucket):
    @pipeline
    def simple():
        @solid
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # pylint: disable=print-call
            return "easy"

        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        run_store = SqliteRunStorage.from_local(temp_dir)
        event_store = SqliteEventLogStorage(temp_dir)
        manager = S3ComputeLogManager(
            bucket=mock_s3_bucket.name, prefix="my_prefix", local_dir=temp_dir
        )
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=manager,
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=DefaultRunLauncher(),
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
        s3_object = mock_s3_bucket.Object(
            key="{prefix}/storage/{run_id}/compute_logs/easy.err".format(
                prefix="my_prefix", run_id=result.run_id
            ),
        )
        stderr_s3 = s3_object.get()["Body"].read().decode("utf-8")
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


def test_compute_log_manager_from_config(mock_s3_bucket):
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
        s3_bucket=mock_s3_bucket.name, s3_prefix=s3_prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)
    assert (
        instance.compute_log_manager._s3_bucket  # pylint: disable=protected-access
        == mock_s3_bucket.name
    )
    assert instance.compute_log_manager._s3_prefix == s3_prefix  # pylint: disable=protected-access
