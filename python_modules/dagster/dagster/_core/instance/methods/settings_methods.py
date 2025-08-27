"""Settings methods for DagsterInstance."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

import dagster._check as check
from dagster._core.instance.config import (
    DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT,
    ConcurrencyConfig,
)

if TYPE_CHECKING:
    from dagster._core.launcher import RunLauncher
    from dagster._core.run_coordinator import RunCoordinator


class SettingsMethods:
    """Mixin class providing settings capabilities for DagsterInstance.

    This class contains all settings-related methods and properties that were
    previously in SettingsMixin, consolidating the functionality without
    the need for separate domain classes.
    """

    # These attributes are provided by DagsterInstance
    _run_monitoring_enabled: bool

    @property
    def is_ephemeral(self) -> bool:
        """Property that should be implemented by the concrete class."""
        raise NotImplementedError

    @property
    def run_launcher(self) -> "RunLauncher":
        """Property that should be implemented by the concrete class."""
        raise NotImplementedError

    @property
    def run_coordinator(self) -> "RunCoordinator":
        """Property that should be implemented by the concrete class."""
        raise NotImplementedError

    def get_settings(self, settings_key: str) -> Any:
        """Abstract method to get settings value - implemented by DagsterInstance."""
        raise NotImplementedError

    def get_backfill_settings(self) -> Mapping[str, Any]:
        return self.get_settings("backfills")

    def get_scheduler_settings(self) -> Mapping[str, Any]:
        return self.get_settings("schedules")

    def get_sensor_settings(self) -> Mapping[str, Any]:
        return self.get_settings("sensors")

    def get_auto_materialize_settings(self) -> Mapping[str, Any]:
        return self.get_settings("auto_materialize")

    @property
    def telemetry_enabled(self) -> bool:
        if self.is_ephemeral:
            return False

        dagster_telemetry_enabled_default = True

        telemetry_settings = self.get_settings("telemetry")

        if not telemetry_settings:
            return dagster_telemetry_enabled_default

        if "enabled" in telemetry_settings:
            return telemetry_settings["enabled"]
        else:
            return dagster_telemetry_enabled_default

    @property
    def nux_enabled(self) -> bool:
        if self.is_ephemeral:
            return False

        nux_enabled_by_default = True

        nux_settings = self.get_settings("nux")
        if not nux_settings:
            return nux_enabled_by_default

        if "enabled" in nux_settings:
            return nux_settings["enabled"]
        else:
            return nux_enabled_by_default

    # run monitoring

    @property
    def run_monitoring_enabled(self) -> bool:
        return self._run_monitoring_enabled

    @property
    def run_monitoring_settings(self) -> Any:
        return self.get_settings("run_monitoring")

    @property
    def run_monitoring_start_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("start_timeout_seconds", 180)

    @property
    def run_monitoring_cancel_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("cancel_timeout_seconds", 180)

    @property
    def run_monitoring_max_runtime_seconds(self) -> int:
        return self.run_monitoring_settings.get("max_runtime_seconds", 0)

    @property
    def code_server_settings(self) -> Any:
        return self.get_settings("code_servers")

    @property
    def code_server_process_startup_timeout(self) -> int:
        return self.code_server_settings.get(
            "local_startup_timeout", DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )

    @property
    def code_server_reload_timeout(self) -> int:
        return self.code_server_settings.get(
            "reload_timeout", DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )

    @property
    def wait_for_local_code_server_processes_on_shutdown(self) -> bool:
        return self.code_server_settings.get("wait_for_local_processes_on_shutdown", False)

    @property
    def run_monitoring_max_resume_run_attempts(self) -> int:
        return self.run_monitoring_settings.get("max_resume_run_attempts", 0)

    @property
    def run_monitoring_poll_interval_seconds(self) -> int:
        return self.run_monitoring_settings.get("poll_interval_seconds", 120)

    @property
    def cancellation_thread_poll_interval_seconds(self) -> int:
        return self.get_settings("run_monitoring").get(
            "cancellation_thread_poll_interval_seconds", 10
        )

    @property
    def run_retries_enabled(self) -> bool:
        return self.get_settings("run_retries").get("enabled", False)

    @property
    def run_retries_max_retries(self) -> int:
        return self.get_settings("run_retries").get("max_retries", 0)

    @property
    def run_retries_retry_on_asset_or_op_failure(self) -> bool:
        return self.get_settings("run_retries").get("retry_on_asset_or_op_failure", True)

    @property
    def auto_materialize_enabled(self) -> bool:
        return self.get_settings("auto_materialize").get("enabled", True)

    @property
    def freshness_enabled(self) -> bool:
        return self.get_settings("freshness").get("enabled", False)

    @property
    def auto_materialize_minimum_interval_seconds(self) -> int:
        return self.get_settings("auto_materialize").get("minimum_interval_seconds")

    @property
    def auto_materialize_run_tags(self) -> dict[str, str]:
        return self.get_settings("auto_materialize").get("run_tags", {})

    @property
    def auto_materialize_respect_materialization_data_versions(self) -> bool:
        return self.get_settings("auto_materialize").get(
            "respect_materialization_data_versions", False
        )

    @property
    def auto_materialize_max_tick_retries(self) -> int:
        return self.get_settings("auto_materialize").get("max_tick_retries", 3)

    @property
    def auto_materialize_use_sensors(self) -> bool:
        return self.get_settings("auto_materialize").get("use_sensors", True)

    @property
    def global_op_concurrency_default_limit(self) -> Optional[int]:
        return self.get_concurrency_config().pool_config.default_pool_limit

    # python logs

    @property
    def managed_python_loggers(self) -> Sequence[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        loggers: Sequence[str] = python_log_settings.get("managed_python_loggers", [])
        return loggers

    @property
    def python_log_level(self) -> Optional[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("python_log_level")

    def _initialize_run_monitoring(self) -> None:
        """Initialize run monitoring settings and validate configuration."""
        run_monitoring_enabled = self.run_monitoring_settings.get("enabled", False)
        self._run_monitoring_enabled = run_monitoring_enabled
        if self.run_monitoring_enabled and self.run_monitoring_max_resume_run_attempts:
            check.invariant(
                self.run_launcher.supports_resume_run,
                "The configured run launcher does not support resuming runs. Set"
                " max_resume_run_attempts to 0 to use run monitoring. Any runs with a failed"
                " run worker will be marked as failed, but will not be resumed.",
            )

    def get_python_log_dagster_handler_config(self) -> dict:
        """Extract dagster handler config from python_logs settings."""
        return self.get_settings("python_logs").get("dagster_handler_config", {})

    def get_concurrency_config(self) -> ConcurrencyConfig:
        """Get concurrency configuration from settings."""
        from dagster._core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator

        if isinstance(self.run_coordinator, QueuedRunCoordinator):
            run_coordinator_run_queue_config = self.run_coordinator.get_run_queue_config()
        else:
            run_coordinator_run_queue_config = None

        concurrency_settings = self.get_settings("concurrency")
        return ConcurrencyConfig.from_concurrency_settings(
            concurrency_settings, run_coordinator_run_queue_config
        )
