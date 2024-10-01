import gc
import logging
import os
import os.path
import threading
from sys import platform
from typing import Dict, Optional, Tuple, Union

import dagster._check as check
from dagster._core.execution.telemetry import RunTelemetryData
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun
from dagster._utils.container import retrieve_containerized_utilization_metrics

DEFAULT_RUN_METRICS_POLL_INTERVAL_SECONDS = 15.0
DEFAULT_RUN_METRICS_SHUTDOWN_SECONDS = 30


def _get_platform_name() -> str:
    platform_name = platform
    return platform_name.casefold()


def _process_is_containerized() -> bool:
    """Detect if the current process is running in a container under linux."""
    if _get_platform_name() != "linux":
        return False

    # the root process (pid==1) under linux is expected to be 'init'
    # this test should be simpler and more robust than testing for cgroup v1, v2 or docker
    file = "/proc/1/exe"
    if os.path.isfile(file) and os.access(file, os.R_OK):
        target = os.readlink(file)
        return os.path.split(target)[-1] != "init"

    # /proc/1/exe should exist on linux; if it doesn't, we don't know what kind of system we're on
    return False


def _metric_tags(dagster_run: DagsterRun) -> Dict[str, str]:
    location_name = os.getenv("DAGSTER_CLOUD_LOCATION_NAME", None)

    # organization and deployment name are added by the graphql mutation
    tags = {
        "job_name": dagster_run.job_name,
        "location_name": location_name,
        "run_id": dagster_run.run_id,
    }
    # filter out none values
    return {k: v for k, v in tags.items() if v is not None}


def _get_container_metrics(
    previous_cpu_usage_ms: Optional[float] = None,
    previous_measurement_timestamp: Optional[float] = None,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Union[float, None]]:
    metrics = retrieve_containerized_utilization_metrics(logger=logger)

    # calculate cpu_limit
    cpu_quota_us = metrics.get("cpu_cfs_quota_us")
    cpu_period_us = metrics.get("cpu_cfs_period_us")
    cpu_usage = metrics.get("cpu_usage")
    cpu_usage_ms = None
    if cpu_usage is not None:
        cpu_usage_ms = cpu_usage * 1000  # convert from seconds to milliseconds

    cpu_limit_ms = None
    if cpu_quota_us and cpu_quota_us > 0 and cpu_period_us and cpu_period_us > 0:
        # Why the 1000 factor is a bit counterintuitive:
        # quota / period -> fraction of cpu per unit of time
        # 1000 * quota / period -> ms/sec of cpu
        cpu_limit_ms = (1000.0 * cpu_quota_us) / cpu_period_us

    cpu_usage_rate_ms = None
    measurement_timestamp = metrics.get("measurement_timestamp")
    if (
        previous_cpu_usage_ms
        and cpu_usage_ms
        and previous_measurement_timestamp
        and measurement_timestamp
    ):
        cpu_usage_rate_ms = (cpu_usage_ms - previous_cpu_usage_ms) / (
            measurement_timestamp - previous_measurement_timestamp
        )

    cpu_percent = None
    if cpu_limit_ms and cpu_limit_ms > 0 and cpu_usage_rate_ms and cpu_usage_rate_ms > 0:
        cpu_percent = 100.0 * cpu_usage_rate_ms / cpu_limit_ms

    memory_percent = None
    memory_limit = metrics.get("memory_limit")
    memory_usage = metrics.get("memory_usage")
    if memory_limit and memory_limit > 0 and memory_usage and memory_usage > 0:
        memory_percent = 100.0 * memory_usage / memory_limit

    return {
        "container.cpu_usage_ms": cpu_usage_ms,
        "container.cpu_cfs_period_us": cpu_period_us,
        "container.cpu_cfs_quota_us": cpu_quota_us,
        "container.cpu_limit_ms": cpu_limit_ms,
        "container.cpu_percent": cpu_percent,
        "container.memory_usage": memory_usage,
        "container.memory_limit": memory_limit,
        "container.memory_percent": memory_percent,
        "measurement_timestamp": measurement_timestamp,
    }


def _get_python_runtime_metrics() -> Dict[str, float]:
    gc_stats = gc.get_stats()

    stats_dict = {}
    for index, gen_dict in enumerate(gc_stats):
        gen_metrics = {
            f"python.runtime.gc_gen_{index}.{key}": value for key, value in gen_dict.items()
        }
        stats_dict.update(gen_metrics)

    return {**stats_dict, "python.runtime.gc_freeze_count": gc.get_freeze_count()}


def _report_run_metrics(
    instance: DagsterInstance,
    dagster_run: DagsterRun,
    metrics: Dict[str, float],
    run_tags: Dict[str, str],
):
    datapoints: Dict[str, float] = {}
    for metric, value in metrics.items():
        if value is None:
            continue
        try:
            datapoints[metric] = float(value)
        except ValueError:
            logging.warning(f"Failed to convert metric value to float: {metric}={value}, skipping")

    telemetry_data = RunTelemetryData(run_id=dagster_run.run_id, datapoints=datapoints)

    instance._run_storage.add_run_telemetry(  # noqa: SLF001
        telemetry_data, tags=run_tags
    )


def _capture_metrics(
    instance: DagsterInstance,
    dagster_run: DagsterRun,
    container_metrics_enabled: bool,
    python_metrics_enabled: bool,
    shutdown_event: threading.Event,
    polling_interval: float = DEFAULT_RUN_METRICS_POLL_INTERVAL_SECONDS,
    logger: Optional[logging.Logger] = None,
) -> bool:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.bool_param(container_metrics_enabled, "container_metrics_enabled")
    check.bool_param(python_metrics_enabled, "python_metrics_enabled")
    check.inst_param(shutdown_event, "shutdown_event", threading.Event)
    check.float_param(polling_interval, "polling_interval")
    check.opt_inst_param(logger, "logger", logging.Logger)

    if not (container_metrics_enabled or python_metrics_enabled):
        raise Exception("No metrics enabled")

    run_tags = _metric_tags(dagster_run)

    if logger:
        logger.debug(f"Starting metrics capture thread with tags: {run_tags}")
        logger.debug(f"  [container_metrics_enabled={container_metrics_enabled}]")
        logger.debug(f"  [python_metrics_enabled={python_metrics_enabled}]")

    previous_cpu_usage_ms = None
    previous_measurement_timestamp = None
    while not shutdown_event.is_set():
        try:
            metrics = {}

            if container_metrics_enabled:
                container_metrics = _get_container_metrics(
                    previous_cpu_usage_ms=previous_cpu_usage_ms,
                    previous_measurement_timestamp=previous_measurement_timestamp,
                    logger=logger,
                )
                previous_cpu_usage_ms = container_metrics.get("container.cpu_usage_ms")
                previous_measurement_timestamp = container_metrics.get("measurement_timestamp")
                metrics.update(container_metrics)

            if python_metrics_enabled:
                python_metrics = _get_python_runtime_metrics()
                metrics.update(python_metrics)

            if len(metrics) > 0:
                _report_run_metrics(
                    instance,
                    dagster_run=dagster_run,
                    metrics=metrics,
                    run_tags=run_tags,
                )

        except:
            if logger:
                logger.error("Exception during capture of metrics, will cease capturing")
            return False  # terminate the thread safely without interrupting the main thread

        shutdown_event.wait(polling_interval)
    if logger:
        logger.debug("Shutting down metrics capture thread")
    return True


def start_run_metrics_thread(
    instance: DagsterInstance,
    dagster_run: DagsterRun,
    container_metrics_enabled: Optional[bool] = True,
    python_metrics_enabled: Optional[bool] = False,
    logger: Optional[logging.Logger] = None,
    polling_interval: float = DEFAULT_RUN_METRICS_POLL_INTERVAL_SECONDS,
) -> Tuple[threading.Thread, threading.Event]:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.opt_inst_param(logger, "logger", logging.Logger)
    check.opt_bool_param(container_metrics_enabled, "container_metrics_enabled")
    check.opt_bool_param(python_metrics_enabled, "python_metrics_enabled")
    check.float_param(polling_interval, "polling_interval")

    container_metrics_enabled = container_metrics_enabled and _process_is_containerized()

    # TODO - ensure at least one metrics source is enabled
    assert container_metrics_enabled or python_metrics_enabled, "No metrics enabled"

    if logger:
        logger.debug("Starting run metrics thread")

    instance.report_engine_event(
        f"Starting run metrics thread with container_metrics_enabled={container_metrics_enabled} and "
        f"python_metrics_enabled={python_metrics_enabled}",
        dagster_run=dagster_run,
        run_id=dagster_run.run_id,
    )

    shutdown_event = threading.Event()
    thread = threading.Thread(
        target=_capture_metrics,
        args=(
            instance,
            dagster_run,
            container_metrics_enabled,
            python_metrics_enabled,
            shutdown_event,
            polling_interval,
            logger,
        ),
        name="run-metrics",
        daemon=True,
    )
    thread.start()
    return thread, shutdown_event


def stop_run_metrics_thread(
    thread: threading.Thread,
    stop_event: threading.Event,
    timeout: Optional[int] = DEFAULT_RUN_METRICS_SHUTDOWN_SECONDS,
) -> bool:
    thread = check.not_none(thread)
    stop_event = check.not_none(stop_event)

    stop_event.set()
    if thread.is_alive():
        thread.join(timeout=timeout)

    return not thread.is_alive()
