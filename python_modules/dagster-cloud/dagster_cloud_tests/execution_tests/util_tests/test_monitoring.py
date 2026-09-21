import logging
import threading
from unittest import mock

from dagster import DagsterRun, DagsterRunStatus
from dagster._core.launcher import CheckRunHealthResult, WorkerStatus
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.typed_dict import init_optional_typeddict
from dagster_cloud.execution.cloud_run_launcher.process import CloudProcessRunLauncher
from dagster_cloud.execution.monitoring import (
    CloudCodeServerHeartbeat,
    CloudCodeServerStatus,
    CloudCodeServerUtilizationMetrics,
    CloudRunWorkerStatus,
    run_worker_monitoring_thread_iteration,
)
from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.util import NON_ISOLATED_RUN_TAG_PAIR, SERVER_HANDLE_TAG


def test_cloud_run_worker_status_from_oss_worker_status():
    status = CloudRunWorkerStatus.from_check_run_health_result(
        "my-run", CheckRunHealthResult(WorkerStatus.RUNNING, "my-msg")
    )
    assert status.run_id == "my-run"
    assert status.status_type == WorkerStatus.RUNNING
    assert status.message == "my-msg"


def test_cloud_run_worker_status_with_run_worker_debug_info():
    status = CloudRunWorkerStatus.from_check_run_health_result(
        "my-run", CheckRunHealthResult(WorkerStatus.RUNNING, "my-msg"), "foobar"
    )
    assert status.run_id == "my-run"
    assert status.status_type == WorkerStatus.RUNNING
    assert status.message == "my-msg\nfoobar"


def test_cloud_run_worker_status_with_very_long_message():
    not_so_silent_scream = "".join(["A" for i in range(2000)])

    status = CloudRunWorkerStatus.from_check_run_health_result(
        "my-run",
        CheckRunHealthResult(WorkerStatus.RUNNING, not_so_silent_scream),
        not_so_silent_scream,
    )
    assert status.run_id == "my-run"
    assert status.status_type == WorkerStatus.RUNNING
    assert status.message == "".join(["A" for i in range(1000)])


def test_cloud_code_server_utilization_metrics_server_id_absent_by_default():
    heartbeat = CloudCodeServerHeartbeat(
        location_name="foo",
        server_status=CloudCodeServerStatus.RUNNING,
    )
    assert "utilization_metrics" not in heartbeat.metadata


def test_cloud_code_server_utilization_metrics_server_id_round_trips():
    utilization_metrics = init_optional_typeddict(CloudCodeServerUtilizationMetrics)
    utilization_metrics["server_id"] = "b3a9c2f0-1d45-4e9a-aaaa-bbbbbbbbbbbb"
    heartbeat = CloudCodeServerHeartbeat(
        location_name="foo",
        server_status=CloudCodeServerStatus.RUNNING,
        metadata={"utilization_metrics": utilization_metrics},
    )
    round_tripped = deserialize_value(serialize_value(heartbeat), CloudCodeServerHeartbeat)
    assert (
        round_tripped.metadata["utilization_metrics"].get("server_id")
        == "b3a9c2f0-1d45-4e9a-aaaa-bbbbbbbbbbbb"
    )


def test_thread_error(agent_instance, caplog):
    with mock.patch(
        "dagster_cloud.execution.monitoring.get_cloud_run_worker_statuses"
    ) as mock_get_statuses:
        mock_get_statuses.side_effect = Exception("Failure fetching statuses")

        deployments_to_check = {"foo"}
        statuses_dict = {}
        run_worker_monitoring_lock = threading.Lock()
        logger = logging.getLogger("dagster_cloud")

        run_worker_monitoring_thread_iteration(
            agent_instance, deployments_to_check, statuses_dict, run_worker_monitoring_lock, logger
        )

        assert "Failure fetching statuses" in caplog.text


def test_monitoring(
    agent_instance,
):
    with mock.patch.object(DagsterCloudAgentInstance, "get_runs") as mock_get_runs:
        mock_get_runs.return_value = [
            DagsterRun(
                job_name="foo",
                run_id="bar",
                run_config={},
                step_keys_to_execute=None,
                status=DagsterRunStatus.STARTED,
                tags={
                    NON_ISOLATED_RUN_TAG_PAIR[0]: NON_ISOLATED_RUN_TAG_PAIR[1],
                    SERVER_HANDLE_TAG: "non-existent-server",
                },
            )
        ]
        deployments_to_check = {"foo"}
        statuses_dict = {}
        run_worker_monitoring_lock = threading.Lock()
        logger = logging.getLogger("dagster_cloud")

        run_worker_monitoring_thread_iteration(
            agent_instance, deployments_to_check, statuses_dict, run_worker_monitoring_lock, logger
        )

        assert len(statuses_dict["foo"]) == 1
        assert statuses_dict["foo"][0].run_id == "bar"
        assert statuses_dict["foo"][0].status_type == WorkerStatus.FAILED


def test_monitoring_k8s_pod_debug_info(
    agent_instance,
):
    with mock.patch.object(DagsterCloudAgentInstance, "get_runs") as mock_get_runs:
        mock_get_runs.return_value = [
            DagsterRun(
                job_name="foo",
                run_id="bar",
                run_config={},
                step_keys_to_execute=None,
                status=DagsterRunStatus.STARTED,
                tags={},
            )
        ]
        deployments_to_check = {"foo"}
        statuses_dict = {}
        run_worker_monitoring_lock = threading.Lock()
        logger = logging.getLogger("dagster_cloud")

        with mock.patch.object(CloudProcessRunLauncher, "check_run_worker_health") as mock_check:
            mock_check.return_value = CheckRunHealthResult(WorkerStatus.FAILED, "my-msg")

            with mock.patch.object(
                CloudProcessRunLauncher, "get_run_worker_debug_info"
            ) as mock_debug:
                mock_debug.return_value = "my-debug-info"

                run_worker_monitoring_thread_iteration(
                    agent_instance,
                    deployments_to_check,
                    statuses_dict,
                    run_worker_monitoring_lock,
                    logger,
                )

        assert len(statuses_dict["foo"]) == 1
        assert statuses_dict["foo"][0].run_id == "bar"
        assert statuses_dict["foo"][0].status_type == WorkerStatus.FAILED
        assert statuses_dict["foo"][0].message == "my-msg\nmy-debug-info"
