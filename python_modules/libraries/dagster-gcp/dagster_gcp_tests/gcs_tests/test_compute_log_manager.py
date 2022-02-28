import os
import sys
import tempfile

from dagster_gcp.gcs import GCSComputeLogManager
from google.cloud import storage  # type: ignore

from dagster import DagsterEventType, job, op
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.core.test_utils import environ

HELLO_WORLD = "Hello World"
SEPARATOR = os.linesep if (os.name == "nt" and sys.version_info < (3,)) else "\n"
EXPECTED_LOGS = [
    'STEP_START - Started execution of step "easy".',
    'STEP_OUTPUT - Yielded output "result" of type "Any"',
    'STEP_SUCCESS - Finished execution of step "easy"',
]


def test_compute_log_manager(gcs_bucket):
    @job
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # pylint: disable=print-call
            return "easy"

        easy()

    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            run_store = SqliteRunStorage.from_local(temp_dir)
            event_store = SqliteEventLogStorage(temp_dir)
            manager = GCSComputeLogManager(
                bucket=gcs_bucket, prefix="my_prefix", local_dir=temp_dir
            )
            instance = DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=run_store,
                event_storage=event_store,
                compute_log_manager=manager,
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=DefaultRunLauncher(),
                ref=InstanceRef.from_dir(temp_dir),
            )
            result = simple.execute_in_process(instance=instance)
            compute_steps = [
                event.step_key
                for event in result.all_node_events
                if event.event_type == DagsterEventType.STEP_START
            ]
            assert len(compute_steps) == 1
            step_key = compute_steps[0]

            stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data

            # Check GCS directly
            stderr_gcs = (
                storage.Client()
                .bucket(gcs_bucket)
                .blob(f"my_prefix/storage/{result.run_id}/compute_logs/easy.err")
                .download_as_bytes()
                .decode("utf-8")
            )

            for expected in EXPECTED_LOGS:
                assert expected in stderr_gcs

            # Check download behavior by deleting locally cached logs
            compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
            for filename in os.listdir(compute_logs_dir):
                os.unlink(os.path.join(compute_logs_dir, filename))

            stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
            assert stdout.data == HELLO_WORLD + SEPARATOR

            stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
            for expected in EXPECTED_LOGS:
                assert expected in stderr.data


def test_compute_log_manager_with_envvar(gcs_bucket):
    @job
    def simple():
        @op
        def easy(context):
            context.log.info("easy")
            print(HELLO_WORLD)  # pylint: disable=print-call
            return "easy"

        easy()

    with open(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), encoding="utf8") as f:
        with tempfile.TemporaryDirectory() as temp_dir:
            with environ({"ENV_VAR": f.read(), "DAGSTER_HOME": temp_dir}):
                run_store = SqliteRunStorage.from_local(temp_dir)
                event_store = SqliteEventLogStorage(temp_dir)
                manager = GCSComputeLogManager(
                    bucket=gcs_bucket,
                    prefix="my_prefix",
                    local_dir=temp_dir,
                    json_credentials_envvar="ENV_VAR",
                )
                instance = DagsterInstance(
                    instance_type=InstanceType.PERSISTENT,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=run_store,
                    event_storage=event_store,
                    compute_log_manager=manager,
                    run_coordinator=DefaultRunCoordinator(),
                    run_launcher=DefaultRunLauncher(),
                    ref=InstanceRef.from_dir(temp_dir),
                )
                result = simple.execute_in_process(instance=instance)
                compute_steps = [
                    event.step_key
                    for event in result.all_node_events
                    if event.event_type == DagsterEventType.STEP_START
                ]
                assert len(compute_steps) == 1
                step_key = compute_steps[0]

                stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
                assert stdout.data == HELLO_WORLD + SEPARATOR

                stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
                for expected in EXPECTED_LOGS:
                    assert expected in stderr.data

                # Check GCS directly
                stderr_gcs = (
                    storage.Client()
                    .bucket(gcs_bucket)
                    .blob(f"my_prefix/storage/{result.run_id}/compute_logs/easy.err")
                    .download_as_bytes()
                    .decode("utf-8")
                )

                for expected in EXPECTED_LOGS:
                    assert expected in stderr_gcs

                # Check download behavior by deleting locally cached logs
                compute_logs_dir = os.path.join(temp_dir, result.run_id, "compute_logs")
                for filename in os.listdir(compute_logs_dir):
                    os.unlink(os.path.join(compute_logs_dir, filename))

                stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
                assert stdout.data == HELLO_WORLD + SEPARATOR

                stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
                for expected in EXPECTED_LOGS:
                    assert expected in stderr.data


def test_compute_log_manager_from_config(gcs_bucket):
    s3_prefix = "foobar"

    dagster_yaml = """
compute_logs:
  module: dagster_gcp.gcs.compute_log_manager
  class: GCSComputeLogManager
  config:
    bucket: "{bucket}"
    local_dir: "/tmp/cool"
    prefix: "{prefix}"
""".format(
        bucket=gcs_bucket, prefix=s3_prefix
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "dagster.yaml"), "wb", encoding="utf8") as f:
            f.write(dagster_yaml.encode("utf-8"))

        instance = DagsterInstance.from_config(tempdir)

    assert isinstance(instance.compute_log_manager, GCSComputeLogManager)
