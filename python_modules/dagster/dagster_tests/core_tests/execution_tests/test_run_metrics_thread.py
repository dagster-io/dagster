import logging
import time
from unittest.mock import patch

import dagster._core.execution.run_metrics_thread as run_metrics_thread
from dagster import DagsterInstance, DagsterRun
from dagster._core.execution.telemetry import RunTelemetryData
from dagster._utils.container import UNCONSTRAINED_CGROUP_MEMORY_LIMIT
from pytest import fixture, mark


@fixture()
def dagster_instance():
    return DagsterInstance.ephemeral()


@fixture()
def dagster_run():
    return DagsterRun(job_name="test", run_id="123")


@fixture()
def mock_container_metrics():
    return {
        "container.cpu_usage_ms": 50,
        "container.cpu_cfs_period_us": 10000,
        "container.cpu_cfs_quota_us": 1000,
        "container.cpu_limit_ms": 100,
        "container.cpu_percent": 50.0,
        "container.memory_usage": 16384,
        "container.memory_limit": 65536,
        "container.memory_percent": 25,
    }


@fixture()
def mock_containerized_utilization_metrics():
    return {
        "cpu_usage": 50,
        "cpu_cfs_quota_us": 1000,
        "cpu_cfs_period_us": 10000,
        "memory_usage": 16384,
        "memory_limit": 65536,
        "measurement_timestamp": 1010,
    }


def test_get_container_metrics(mock_containerized_utilization_metrics):
    with patch(
        "dagster._core.execution.run_metrics_thread.retrieve_containerized_utilization_metrics",
        return_value=mock_containerized_utilization_metrics,
    ):
        metrics = run_metrics_thread._get_container_metrics(  # noqa: SLF001
            previous_cpu_usage_ms=49200, previous_measurement_timestamp=1000
        )

        assert metrics
        assert isinstance(metrics, dict)
        assert metrics["container.cpu_usage_ms"] == 50000
        assert metrics["container.cpu_usage_rate_ms"] == 80
        assert metrics["container.cpu_limit_ms"] == 100
        assert metrics["container.memory_usage"] == 16384
        assert metrics["container.memory_limit"] == 65536
        assert metrics["container.memory_percent"] == 25
        assert metrics["measurement_timestamp"] == 1010

        # Calculation of expected cpu_percent
        # cpu_limit_ms = 100 ms per second-> derived from cpu cfs quota and period
        # cpu_usage_rate_ms = (50000 - 49200) / (1010 - 1000) = 80 ms per second
        # cpu_percent = 100% * 80 (used) / 100 (limit) = 80.0%
        assert metrics["container.cpu_percent"] == 80.0


def test_get_container_metrics_missing_limits(mock_containerized_utilization_metrics):
    del mock_containerized_utilization_metrics["cpu_cfs_quota_us"]
    del mock_containerized_utilization_metrics["cpu_cfs_period_us"]
    del mock_containerized_utilization_metrics["memory_limit"]

    with patch(
        "dagster._core.execution.run_metrics_thread.retrieve_containerized_utilization_metrics",
        return_value=mock_containerized_utilization_metrics,
    ):
        # should not throw
        metrics = run_metrics_thread._get_container_metrics(  # noqa: SLF001
            previous_cpu_usage_ms=49200, previous_measurement_timestamp=1000
        )

        assert metrics
        assert isinstance(metrics, dict)
        assert metrics["container.cpu_usage_ms"] == 50000
        assert metrics["container.cpu_usage_rate_ms"] == 80  # see previous test for calculation
        assert metrics["container.cpu_percent"] is None
        assert metrics["container.cpu_limit_ms"] is None
        assert metrics["container.memory_usage"] == 16384
        assert metrics["container.memory_limit"] is None
        assert metrics["container.memory_percent"] is None


@mark.parametrize(
    "cpu_cfs_quota_us, cpu_cfs_period_us, cgroup_memory_limit, expected_cpu_limit_ms, expected_memory_limit",
    [
        (None, None, None, None, None),
        (0, 0, 0, None, None),
        (10, -1, -1, None, None),
        (-1, 10, UNCONSTRAINED_CGROUP_MEMORY_LIMIT, None, None),
    ],
)
def test_get_container_metrics_edge_conditions(
    mock_containerized_utilization_metrics,
    cpu_cfs_quota_us,
    cpu_cfs_period_us,
    cgroup_memory_limit,
    expected_cpu_limit_ms,
    expected_memory_limit,
):
    """These limits are not valid if none, negative or zero values are provided and we should ignore them."""
    mock_containerized_utilization_metrics["cpu_cfs_quota_us"] = cpu_cfs_quota_us
    mock_containerized_utilization_metrics["cpu_cfs_period_us"] = cpu_cfs_period_us
    mock_containerized_utilization_metrics["memory_limit"] = cgroup_memory_limit

    with patch(
        "dagster._core.execution.run_metrics_thread.retrieve_containerized_utilization_metrics",
        return_value=mock_containerized_utilization_metrics,
    ):
        # should not throw
        metrics = run_metrics_thread._get_container_metrics(  # noqa: SLF001
            previous_cpu_usage_ms=49200, previous_measurement_timestamp=1000
        )

        assert metrics
        assert isinstance(metrics, dict)
        assert metrics["container.cpu_limit_ms"] == expected_cpu_limit_ms
        assert metrics["container.memory_limit"] == expected_memory_limit


@mark.parametrize(
    "test_case, platform_name, is_file, readable, link_path, expected",
    [
        ("non-linux OS should always evaluate to false", "darwin", True, True, "/sbin/init", False),
        ("standard linux, outside cgroup", "linux", True, True, "/sbin/init", False),
        ("standard linux, container cgroup", "linux", True, True, "/bin/bash", True),
        ("unreadable process file should evaluate to false", "linux", False, False, "", False),
    ],
)
def test_process_is_containerized(
    monkeypatch, test_case, platform_name, is_file, readable, link_path, expected
):
    monkeypatch.setattr("os.path.isfile", lambda x: is_file)
    monkeypatch.setattr("os.access", lambda x, y: readable)
    monkeypatch.setattr("os.readlink", lambda x: link_path)

    with patch.object(run_metrics_thread, "_get_platform_name", return_value=platform_name):
        assert run_metrics_thread._process_is_containerized() is expected, test_case  # noqa: SLF001


def test_metric_tags(dagster_instance, dagster_run):
    tags = run_metrics_thread._metric_tags(dagster_run)  # noqa: SLF001
    assert tags["job_name"] == "test"
    assert tags["run_id"] == "123"


def test_python_gc_metrics():
    python_runtime_metrics = run_metrics_thread._get_python_runtime_metrics()  # noqa: SLF001

    assert "python.runtime.gc_gen_0.collections" in python_runtime_metrics
    assert "python.runtime.gc_freeze_count" in python_runtime_metrics
    assert isinstance(python_runtime_metrics["python.runtime.gc_gen_0.collections"], int)
    assert isinstance(python_runtime_metrics["python.runtime.gc_freeze_count"], int)
    assert python_runtime_metrics["python.runtime.gc_gen_0.collections"] >= 0


def test_start_run_metrics_thread(dagster_instance, dagster_run, mock_container_metrics, caplog):
    logger = logging.getLogger("test_run_metrics")
    logger.setLevel(logging.DEBUG)

    with patch.object(dagster_instance.run_storage, "supports_run_telemetry", return_value=True):
        with patch(
            "dagster._core.execution.run_metrics_thread._get_container_metrics",
            return_value=mock_container_metrics,
        ):
            with patch(
                "dagster._core.execution.run_metrics_thread._process_is_containerized",
                return_value=True,
            ):
                thread, shutdown = run_metrics_thread.start_run_metrics_thread(
                    dagster_instance,
                    dagster_run,
                    logger=logger,
                    polling_interval=2.0,
                )

                time.sleep(0.1)

                assert thread.is_alive()
                assert "Starting run metrics thread" in caplog.messages[0]

                time.sleep(0.1)
                shutdown.set()

                thread.join()
                assert thread.is_alive() is False
                assert "Shutting down metrics capture thread" in caplog.messages[-1]


def test_start_run_metrics_thread_without_run_storage_support(
    dagster_instance, dagster_run, mock_container_metrics, caplog
):
    logger = logging.getLogger("test_run_metrics")
    logger.setLevel(logging.DEBUG)

    with patch.object(dagster_instance.run_storage, "supports_run_telemetry", return_value=False):
        thread, shutdown = run_metrics_thread.start_run_metrics_thread(
            dagster_instance,
            dagster_run,
            logger=logger,
            polling_interval=2.0,
        )

        assert thread is None
        assert shutdown is None
        assert "Run telemetry is not supported" in caplog.messages[-1]


def test_report_run_metrics(dagster_instance: DagsterInstance, dagster_run: DagsterRun):
    with patch.object(dagster_instance.run_storage, "add_run_telemetry") as mock_add_run_telemetry:
        metrics = {
            "foo": 1.0,
            "bar": 2.0,
        }
        tags = {
            "baz": "qux",
        }

        run_metrics_thread._report_run_metrics(dagster_instance, dagster_run, metrics, tags)  # noqa: SLF001

        mock_add_run_telemetry.assert_called_once_with(
            RunTelemetryData(run_id=dagster_run.run_id, datapoints={"foo": 1.0, "bar": 2.0}),
            tags=tags,
        )
