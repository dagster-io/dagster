from pathlib import Path
from typing import Optional

import mock
import pytest
from dagster._utils.container import CGroupVersion, retrieve_containerized_utilization_metrics
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
    cpu_usage_val: Optional[float],
    cpu_cores_val: Optional[int],
    cpu_quota_val: Optional[float],
    cpu_period_val: Optional[float],
    memory_usage_val: Optional[int],
    memory_limit_val: Optional[int],
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
    cpu_usage_val: Optional[float],
    cpu_cores_val: Optional[int],
    cpu_quota_and_period_val: Optional[str],
    memory_usage_val: Optional[int],
    memory_limit_val: Optional[int],
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
