from pathlib import Path
from unittest import mock

import pytest
from dagster._utils.container import (
    CGroupVersion,
    _retrieve_containerized_cpu_cfs_period_us_v2,
    _retrieve_containerized_cpu_cfs_quota_us_v2,
    _retrieve_containerized_memory_limit_v2,
    _retrieve_containerized_memory_usage_v2,
    retrieve_containerized_utilization_metrics,
)
from dagster._utils.env import environ


@pytest.fixture
def temp_dir(tmp_path: Path):
    with environ(
        {
            "DAGSTER_CPU_USAGE_PATH": f"{tmp_path}/cpuacct.usage",
            "DAGSTER_CPU_INFO_PATH": f"{tmp_path}/cpuinfo",
            "DAGSTER_CPU_CFS_QUOTA_US_PATH": f"{tmp_path}/cpu.cfs_quota_us",
            "DAGSTER_CPU_CFS_PERIOD_US_PATH": f"{tmp_path}/cpu.cfs_period_us",
            "DAGSTER_MEMORY_USAGE_PATH_V1": f"{tmp_path}/memory.usage_in_bytes",
            "DAGSTER_MEMORY_LIMIT_PATH_V1": f"{tmp_path}/memory.limit_in_bytes",
            "DAGSTER_CPU_STAT_PATH": f"{tmp_path}/cpu.stat",
            "DAGSTER_CPU_MAX_PATH": f"{tmp_path}/cpu.max",
            "DAGSTER_MEMORY_USAGE_PATH_V2": f"{tmp_path}/memory.current",
            "DAGSTER_MEMORY_LIMIT_PATH_V2": f"{tmp_path}/memory.max",
        }
    ):
        yield tmp_path


@pytest.fixture
def cgroup_version_mock():
    with mock.patch("dagster._utils.container._retrieve_cgroup_version") as mock_cgroup_version:
        yield mock_cgroup_version


@pytest.mark.parametrize("cpu_usage_val", [1.0, None], ids=["cpu-set", "cpu-not-set"])
@pytest.mark.parametrize("cpu_cores_val", [1, None], ids=["cpu-cores-set", "cpu-cores-not-set"])
@pytest.mark.parametrize("cpu_quota_val", [1.0, None], ids=["cpu-quota-set", "cpu-quota-not-set"])
@pytest.mark.parametrize(
    "cpu_period_val", [1.0, None], ids=["cpu-period-set", "cpu-period-not-set"]
)
@pytest.mark.parametrize(
    "memory_usage_val", [1, None], ids=["memory-usage-set", "memory-usage-not-set"]
)
@pytest.mark.parametrize(
    "memory_limit_val", [1, None], ids=["memory-limit-set", "memory-limit-not-set"]
)
@pytest.mark.parametrize(
    "was_cpu_previously_retrieved",
    [True, False],
    ids=["last-cpu-time-retrieved", "last-cpu-time-not-retrieved"],
)
@pytest.mark.parametrize(
    "was_previous_timestamp_previously_set",
    [True, False],
    ids=["previous-timestamp-set", "previous-timestamp-not-set"],
)
def test_containerized_utilization_metrics_cgroup_v1(
    temp_dir: str,
    cpu_usage_val: float | None,
    cpu_cores_val: int | None,
    cpu_quota_val: float | None,
    cpu_period_val: float | None,
    memory_usage_val: int | None,
    memory_limit_val: int | None,
    was_cpu_previously_retrieved: bool,
    was_previous_timestamp_previously_set: bool,
    cgroup_version_mock: mock.Mock,
):
    cgroup_version_mock.return_value = CGroupVersion.V1

    if cpu_usage_val:
        with open(f"{temp_dir}/cpuacct.usage", "w") as f:
            f.write(str(cpu_usage_val * 1e9))

    if cpu_cores_val:
        with open(f"{temp_dir}/cpuinfo", "w") as f:
            f.write("\n".join([f"processor : {i}" for i in range(cpu_cores_val)]))

    if cpu_quota_val:
        with open(f"{temp_dir}/cpu.cfs_quota_us", "w") as f:
            f.write(str(cpu_quota_val))

    if cpu_period_val:
        with open(f"{temp_dir}/cpu.cfs_period_us", "w") as f:
            f.write(str(cpu_period_val))

    if memory_usage_val:
        with open(f"{temp_dir}/memory.usage_in_bytes", "w") as f:
            f.write(str(memory_usage_val))

    if memory_limit_val:
        with open(f"{temp_dir}/memory.limit_in_bytes", "w") as f:
            f.write(str(memory_limit_val))

    previous_cpu_usage = 1.0 if was_cpu_previously_retrieved else None
    previous_measurement_timestamp = 1.0 if was_previous_timestamp_previously_set else None
    utilization_metrics = retrieve_containerized_utilization_metrics(
        logger=None,
        previous_measurement_timestamp=previous_measurement_timestamp,
        previous_cpu_usage=previous_cpu_usage,
    )
    assert utilization_metrics["cpu_usage"] == (1.0 if cpu_usage_val else None)
    assert utilization_metrics["num_allocated_cores"] == (1 if cpu_cores_val else None)

    assert utilization_metrics["cpu_cfs_quota_us"] == (1.0 if cpu_quota_val else None)
    assert utilization_metrics["cpu_cfs_period_us"] == (1.0 if cpu_period_val else None)

    assert utilization_metrics["memory_usage"] == (1 if memory_usage_val else None)
    assert utilization_metrics["memory_limit"] == (1 if memory_limit_val else None)
    assert utilization_metrics["previous_cpu_usage"] == (
        1.0 if was_cpu_previously_retrieved else None
    )
    assert utilization_metrics["previous_measurement_timestamp"] == (
        1.0 if was_previous_timestamp_previously_set else None
    )


@pytest.mark.parametrize("cpu_usage_val", [1.0, None], ids=["cpu-set", "cpu-not-set"])
@pytest.mark.parametrize("cpu_cores_val", [1, None], ids=["cpu-cores-set", "cpu-cores-not-set"])
@pytest.mark.parametrize(
    "cpu_quota_and_period_val", ["1 1", None], ids=["cpu-max-set", "cpu-max-not-set"]
)
@pytest.mark.parametrize(
    "memory_usage_val", [1, None], ids=["memory-usage-set", "memory-usage-not-set"]
)
@pytest.mark.parametrize(
    "memory_limit_val", [1, None], ids=["memory-limit-set", "memory-limit-not-set"]
)
@pytest.mark.parametrize(
    "was_cpu_previously_retrieved",
    [True, False],
    ids=["last-cpu-time-retrieved", "last-cpu-time-not-retrieved"],
)
@pytest.mark.parametrize(
    "was_previous_timestamp_previously_set",
    [True, False],
    ids=["previous-timestamp-set", "previous-timestamp-not-set"],
)
def test_containerized_utilization_metrics_cgroup_v2(
    temp_dir: str,
    cpu_usage_val: float | None,
    cpu_cores_val: int | None,
    cpu_quota_and_period_val: str | None,
    memory_usage_val: int | None,
    memory_limit_val: int | None,
    was_cpu_previously_retrieved: bool,
    was_previous_timestamp_previously_set: bool,
    cgroup_version_mock: mock.Mock,
):
    if cpu_usage_val:
        with open(f"{temp_dir}/cpu.stat", "w") as f:
            f.write(f"usage_usec {int(cpu_usage_val * 1e6)}")

    if cpu_cores_val:
        with open(f"{temp_dir}/cpuinfo", "w") as f:
            f.write("\n".join([f"processor : {i}" for i in range(cpu_cores_val)]))

    if cpu_quota_and_period_val:
        with open(f"{temp_dir}/cpu.max", "w") as f:
            f.write(str(cpu_quota_and_period_val))

    if memory_usage_val:
        with open(f"{temp_dir}/memory.current", "w") as f:
            f.write(str(memory_usage_val))

    if memory_limit_val:
        with open(f"{temp_dir}/memory.max", "w") as f:
            f.write(str(memory_limit_val))

    cgroup_version_mock.return_value = CGroupVersion.V2

    previous_cpu_usage = 1.0 if was_cpu_previously_retrieved else None
    previous_measurement_timestamp = 1.0 if was_previous_timestamp_previously_set else None
    utilization_metrics = retrieve_containerized_utilization_metrics(
        logger=None,
        previous_measurement_timestamp=previous_measurement_timestamp,
        previous_cpu_usage=previous_cpu_usage,
    )
    assert utilization_metrics["cpu_usage"] == (1.0 if cpu_usage_val else None)
    assert utilization_metrics["num_allocated_cores"] == (1 if cpu_cores_val else None)

    assert utilization_metrics["cpu_cfs_quota_us"] == (1.0 if cpu_quota_and_period_val else None)
    assert utilization_metrics["cpu_cfs_period_us"] == (1.0 if cpu_quota_and_period_val else None)

    assert utilization_metrics["memory_usage"] == (1 if memory_usage_val else None)
    assert utilization_metrics["memory_limit"] == (1 if memory_limit_val else None)
    assert utilization_metrics["previous_cpu_usage"] == (
        1.0 if was_cpu_previously_retrieved else None
    )
    assert utilization_metrics["previous_measurement_timestamp"] == (
        1.0 if was_previous_timestamp_previously_set else None
    )


def test_cgroup_v2_missing_files_return_partial_metrics(temp_dir: str, cgroup_version_mock: mock.Mock):
    with open(f"{temp_dir}/cpu.stat", "w") as f:
        f.write("usage_usec 1000000")

    with open(f"{temp_dir}/cpuinfo", "w") as f:
        f.write("processor : 0")

    cgroup_version_mock.return_value = CGroupVersion.V2

    utilization_metrics = retrieve_containerized_utilization_metrics(logger=None)

    assert utilization_metrics["cpu_usage"] == 1.0
    assert utilization_metrics["num_allocated_cores"] == 1
    assert utilization_metrics["cpu_cfs_quota_us"] is None
    assert utilization_metrics["cpu_cfs_period_us"] is None
    assert utilization_metrics["memory_usage"] is None
    assert utilization_metrics["memory_limit"] is None


def test_cgroup_v2_missing_files_do_not_log_exceptions(cgroup_version_mock: mock.Mock):
    logger = mock.Mock()
    with mock.patch("dagster._utils.container._retrieve_containerized_num_allocated_cores", return_value=1):
        with mock.patch("dagster._utils.container._retrieve_containerized_cpu_usage_v2", return_value=1.0):
            cgroup_version_mock.return_value = CGroupVersion.V2

            retrieve_containerized_utilization_metrics(logger=logger)

    logger.error.assert_not_called()
    logger.exception.assert_not_called()


def test_cgroup_v2_empty_override_files_return_none(temp_dir: str):
    Path(f"{temp_dir}/cpu.max").write_text("")
    Path(f"{temp_dir}/memory.current").write_text("")
    Path(f"{temp_dir}/memory.max").write_text("")

    assert _retrieve_containerized_cpu_cfs_quota_us_v2(logger=None) is None
    assert _retrieve_containerized_cpu_cfs_period_us_v2(logger=None) is None
    assert _retrieve_containerized_memory_usage_v2(logger=None) is None
    assert _retrieve_containerized_memory_limit_v2(logger=None) is None


def test_cgroup_v2_empty_override_files_do_not_log_exceptions(temp_dir: str):
    logger = mock.Mock()
    Path(f"{temp_dir}/cpu.max").write_text("")
    Path(f"{temp_dir}/memory.current").write_text("")
    Path(f"{temp_dir}/memory.max").write_text("")

    assert _retrieve_containerized_cpu_cfs_quota_us_v2(logger=logger) is None
    assert _retrieve_containerized_cpu_cfs_period_us_v2(logger=logger) is None
    assert _retrieve_containerized_memory_usage_v2(logger=logger) is None
    assert _retrieve_containerized_memory_limit_v2(logger=logger) is None

    logger.error.assert_not_called()
    logger.exception.assert_not_called()


def test_cgroup_v2_cpu_max_with_unlimited_quota_returns_none_for_quota(temp_dir: str):
    Path(f"{temp_dir}/cpu.max").write_text("max 100000")

    assert _retrieve_containerized_cpu_cfs_quota_us_v2(logger=None) is None
    assert _retrieve_containerized_cpu_cfs_period_us_v2(logger=None) == 100000.0


def test_cgroup_v2_memory_max_with_unlimited_limit_returns_none(temp_dir: str):
    Path(f"{temp_dir}/memory.max").write_text("max")

    assert _retrieve_containerized_memory_limit_v2(logger=None) is None


def test_cgroup_v2_unlimited_values_do_not_log_exceptions(temp_dir: str):
    logger = mock.Mock()
    Path(f"{temp_dir}/cpu.max").write_text("max 100000")
    Path(f"{temp_dir}/memory.max").write_text("max")

    assert _retrieve_containerized_cpu_cfs_quota_us_v2(logger=logger) is None
    assert _retrieve_containerized_cpu_cfs_period_us_v2(logger=logger) == 100000.0
    assert _retrieve_containerized_memory_limit_v2(logger=logger) is None

    logger.error.assert_not_called()
    logger.exception.assert_not_called()
