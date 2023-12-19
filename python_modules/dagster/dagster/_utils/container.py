import logging
from typing import Optional, TypedDict

import pendulum


class UtilizationMetrics(TypedDict):
    num_allocated_cores: Optional[int]
    cpu_time: Optional[float]
    cpu_utilization: Optional[float]
    memory_utilization: Optional[float]
    memory_limit: Optional[int]
    measurement_timestamp: float


def retrieve_containerized_utilization_metrics(
    logger: Optional[logging.Logger],
    last_cpu_measurement_time: Optional[float],
    last_cpu_measurement_value: Optional[float],
) -> UtilizationMetrics:
    """Retrieve the CPU and memory utilization metrics from cgroup and proc files."""
    measurement_timestamp = pendulum.now("UTC").timestamp()
    cpu_time = _retrieve_containerized_cpu_time(logger)
    num_cores = _retrieve_containerized_num_allocated_cores(logger)
    if cpu_time and last_cpu_measurement_time and last_cpu_measurement_value and num_cores:
        cpu_utilization = (
            (cpu_time - last_cpu_measurement_value)
            / (measurement_timestamp - last_cpu_measurement_time)
            / num_cores
        )
    else:
        cpu_utilization = None

    cur_mem_usage = _retrieve_containerized_memory_usage(logger)
    cur_mem_limit = _retrieve_containerized_memory_limit(logger)
    if cur_mem_usage and cur_mem_limit:
        memory_utilization = cur_mem_usage / cur_mem_limit
    else:
        memory_utilization = None
    return {
        "num_allocated_cores": num_cores,
        "cpu_time": cpu_time,
        "cpu_utilization": cpu_utilization,
        "memory_utilization": memory_utilization,
        "memory_limit": cur_mem_limit,
        "measurement_timestamp": measurement_timestamp,
    }


def _retrieve_containerized_cpu_time(logger: Optional[logging.Logger]) -> Optional[float]:
    """Retrieve the CPU time in seconds from the cgroup file."""
    try:
        with open("/sys/fs/cgroup/cpu/cpuacct.usage") as f:
            return float(f.read()) / 1e9  # Cpuacct.usage is in nanoseconds
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve CPU time from cgroup: {e}")
        return None


def _retrieve_containerized_num_allocated_cores(logger: Optional[logging.Logger]) -> Optional[int]:
    """Retrieve the number of cores from the /proc/cpuinfo file."""
    try:
        with open("/proc/cpuinfo") as f:
            return len([line for line in f if line.startswith("processor")])
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve number of cores from /proc/cpuinfo: {e}")
        return None


def _retrieve_containerized_memory_usage(logger: Optional[logging.Logger]) -> Optional[int]:
    """Retrieve the memory usage in bytes from the cgroup file."""
    try:
        with open("/sys/fs/cgroup/memory/memory.usage_in_bytes") as f:
            return int(f.read())
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve memory usage from cgroup: {e}")
        return None


def _retrieve_containerized_memory_limit(logger: Optional[logging.Logger]) -> Optional[int]:
    """Retrieve the memory limit in bytes from the cgroup file."""
    try:
        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
            return int(f.read())
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve memory limit from cgroup: {e}")
        return None
