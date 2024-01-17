import logging
import os
import re
from typing import Optional, TypedDict
from enum import Enum
import pendulum
from .typed_dict import init_optional_typeddict

class CGroupVersion(Enum):
    V1 = "V1"
    V2 = "V2"

class ContainerUtilizationMetrics(TypedDict):
    num_allocated_cores: Optional[int]
    cpu_usage: Optional[float]
    cpu_cfs_quota_us: Optional[float]
    cpu_cfs_period_us: Optional[float]
    memory_usage: Optional[float]
    memory_limit: Optional[int]
    measurement_timestamp: Optional[float]
    previous_cpu_usage: Optional[float]
    previous_measurement_timestamp: Optional[float]

def cpu_usage_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the CPU time in nanoseconds.

    We use cgroup files instead of the psutil library because psutil uses the host machine's CPU allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    default_path = "/sys/fs/cgroup/cpuacct/cpuacct.usage" if cgroup_version == CGroupVersion.V1 else 
    return os.getenv("DAGSTER_CPU_USAGE_PATH", "/sys/fs/cgroup/cpuacct/cpuacct.usage")


def cpu_cfs_quota_us_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the CPU quota in microseconds.

    We use cgroup files instead of the psutil library because psutil uses the host machine's CPU allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    return os.getenv("DAGSTER_CPU_CFS_QUOTA_US_PATH", "/sys/fs/cgroup/cpu/cpu.cfs_quota_us")


def cpu_cfs_period_us_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the CPU period in microseconds.

    We use cgroup files instead of the psutil library because psutil uses the host machine's CPU allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    return os.getenv("DAGSTER_CPU_CFS_PERIOD_US_PATH", "/sys/fs/cgroup/cpu/cpu.cfs_period_us")


def cpu_shares_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the CPU shares.

    We use cgroup files instead of the psutil library because psutil uses the host machine's CPU allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    return os.getenv("DAGSTER_CPU_SHARES_PATH", "/sys/fs/cgroup/cpu/cpu.shares")


def cpu_info_path(cgroup_version: CGroupVersion) -> str:
    """Path to the file containing the number of cores allocated to the container."""
    return os.getenv("DAGSTER_CPU_INFO_PATH", "/proc/cpuinfo")


def memory_usage_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the memory usage in bytes.

    We use cgroup files instead of the psutil library because psutil uses the host machine's memory allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    return os.getenv("DAGSTER_MEMORY_USAGE_PATH", "/sys/fs/cgroup/memory/memory.usage_in_bytes")


def memory_limit_path(cgroup_version: CGroupVersion) -> str:
    """Path to the cgroup file containing the memory limit in bytes.

    We use cgroup files instead of the psutil library because psutil uses the host machine's memory allocation in virtualized environments like Docker, K8s, ECS, etc.
    """
    return os.getenv("DAGSTER_MEMORY_LIMIT_PATH", "/sys/fs/cgroup/memory/memory.limit_in_bytes")


def retrieve_containerized_utilization_metrics(
    logger: Optional[logging.Logger],
    previous_measurement_timestamp: Optional[float],
    previous_cpu_usage: Optional[float],
) -> ContainerUtilizationMetrics:
    """Retrieve the CPU and memory utilization metrics from cgroup and proc files."""
    cgroup_version = _retrieve_cgroup_version_from_fs(logger)
    if cgroup_version is None:
        return init_optional_typeddict(ContainerUtilizationMetrics)
    return {
        "num_allocated_cores": _retrieve_containerized_num_allocated_cores(logger, cgroup_version),
        "cpu_usage": _retrieve_containerized_cpu_usage(logger, cgroup_version),
        "previous_cpu_usage": previous_cpu_usage,
        "previous_measurement_timestamp": previous_measurement_timestamp,
        "cpu_cfs_quota_us": _retrieve_containerized_cpu_cfs_quota_us(logger, cgroup_version),
        "cpu_cfs_period_us": _retrieve_containerized_cpu_cfs_period_us(logger, cgroup_version),
        "memory_usage": _retrieve_containerized_memory_usage(logger, cgroup_version),
        "memory_limit": _retrieve_containerized_memory_limit(logger, cgroup_version),
        "measurement_timestamp": pendulum.now("UTC").float_timestamp,
    }

def _retrieve_cgroup_version_from_fs(logger: Optional[logging.Logger]) -> Optional[CGroupVersion]:
    if not os.path.exists("/sys/fs/cgroup/"):
        if logger:
            logger.info("No cgroup directory found, assuming we are not running in a container")
        return None
    # The command stat -fc %T /sys/fs/cgroup/ should return either cgroup2fs (cgroup V2) or tmpfs (cgroup V1)
    try:
        with os.popen("stat -fc %T /sys/fs/cgroup/") as f:
            cgroup_version = f.read().strip()
            if cgroup_version == "cgroup2fs":
                return CGroupVersion.V2
            elif cgroup_version == "tmpfs":
                return CGroupVersion.V1
            else:
                if logger:
                    logger.info(f"Unknown cgroup version {cgroup_version}")
                return None
    except:
        if logger:
            logger.exception("Failed to retrieve cgroup version from /sys/fs/cgroup/")
        return None

def _retrieve_containerized_cpu_usage(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[float]:
    """Retrieve the CPU time in seconds from the cgroup file."""
    try:
        with open(cpu_usage_path(cgroup_version)) as f:
            return float(f.read()) / 1e9  # Cpuacct.usage is in nanoseconds
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve CPU time from cgroup: {e}")
        return None


def _retrieve_containerized_num_allocated_cores(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[int]:
    """Retrieve the number of cores from the /proc/cpuinfo file."""
    try:
        with open(cpu_info_path(cgroup_version)) as f:
            return len([line for line in f if line.startswith("processor")])
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve number of cores from /proc/cpuinfo: {e}")
        return None


def _retrieve_containerized_memory_usage(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[int]:
    """Retrieve the memory usage in bytes from the cgroup file."""
    try:
        with open(memory_usage_path(cgroup_version)) as f:
            return int(f.read())
    except Exception as e:
        if logger:
            logger.error(f"Failed to retrieve memory usage from cgroup: {e}")
        return None


def _retrieve_containerized_memory_limit(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[int]:
    """Retrieve the memory limit in bytes from the cgroup file."""
    try:
        with open(memory_limit_path(cgroup_version)) as f:
            return int(f.read())
    except:
        if logger:
            logger.exception("Failed to retrieve memory limit from cgroup")
        return None


def _retrieve_containerized_cpu_cfs_period_us(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[float]:
    """Retrieve the CPU period in microseconds from the cgroup file."""
    try:
        with open(cpu_cfs_period_us_path(cgroup_version)) as f:
            return float(f.read())
    except:
        if logger:
            logger.exception("Failed to retrieve CPU period from cgroup")
        return None


def _retrieve_containerized_cpu_cfs_quota_us(logger: Optional[logging.Logger], cgroup_version: CGroupVersion) -> Optional[float]:
    """Retrieve the CPU quota in microseconds from the cgroup file."""
    try:
        with open(cpu_cfs_quota_us_path(cgroup_version)) as f:
            return float(f.read())
    except:
        if logger:
            logger.exception("Failed to retrieve CPU quota from cgroup")
        return None
