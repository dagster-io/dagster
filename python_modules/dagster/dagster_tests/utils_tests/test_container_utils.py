import mock
import pytest
from dagster._utils.container import retrieve_containerized_utilization_metrics


@pytest.fixture(name="cpu_time")
def mock_cpu_time():
    with mock.patch(
        "dagster._utils.container._retrieve_containerized_cpu_time",
    ) as mocker:
        yield mocker


@pytest.fixture(name="num_cores")
def mock_num_cores():
    with mock.patch(
        "dagster._utils.container._retrieve_containerized_num_allocated_cores"
    ) as mocker:
        yield mocker


@pytest.fixture(name="mem_usage")
def mock_mem_usage():
    with mock.patch("dagster._utils.container._retrieve_containerized_memory_usage") as mocker:
        yield mocker


@pytest.fixture(name="mem_limit")
def mock_mem_limit():
    with mock.patch("dagster._utils.container._retrieve_containerized_memory_limit") as mocker:
        yield mocker


@pytest.mark.parametrize("cpu_time_retrieved", [True, False])
@pytest.mark.parametrize("cpu_cores_retrieved", [True, False])
@pytest.mark.parametrize("memory_usage_retrieved", [True, False])
@pytest.mark.parametrize("memory_limit_retrieved", [True, False])
@pytest.mark.parametrize("last_cpu_time_retrieved", [True, False])
@pytest.mark.parametrize("previous_timestamp_set", [True, False])
def test_containerized_utilization_metrics(
    cpu_time_retrieved,
    cpu_cores_retrieved,
    memory_usage_retrieved,
    memory_limit_retrieved,
    last_cpu_time_retrieved,
    previous_timestamp_set,
    cpu_time,
    num_cores,
    mem_usage,
    mem_limit,
):
    cpu_time.return_value = 1.0 if cpu_time_retrieved else None
    num_cores.return_value = 1 if cpu_cores_retrieved else None
    mem_usage.return_value = 1 if memory_usage_retrieved else None
    mem_limit.return_value = 1 if memory_limit_retrieved else None
    last_cpu_time = 1.0 if last_cpu_time_retrieved else None
    last_cpu_timestamp = 1.0 if previous_timestamp_set else None
    utilization_metrics = retrieve_containerized_utilization_metrics(
        logger=None,
        last_cpu_measurement_time=last_cpu_timestamp,
        last_cpu_measurement_value=last_cpu_time,
    )
    assert utilization_metrics["cpu_time"] == (1.0 if cpu_time_retrieved else None)
    assert utilization_metrics["num_allocated_cores"] == (1 if cpu_cores_retrieved else None)
    assert utilization_metrics["memory_utilization"] == (
        1 if memory_usage_retrieved and memory_limit_retrieved else None
    )
    assert utilization_metrics["memory_limit"] == (1 if memory_limit_retrieved else None)
    if (
        cpu_time_retrieved
        and last_cpu_time_retrieved
        and previous_timestamp_set
        and cpu_cores_retrieved
    ):
        assert utilization_metrics["cpu_utilization"] == 0.0
    else:
        assert utilization_metrics["cpu_utilization"] is None
