import logging
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class RunLauncherInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for run launcher operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # Core launcher and coordinator access
    @property
    def run_coordinator(self):
        return self._instance.run_coordinator

    @property
    def run_launcher(self):
        return self._instance.run_launcher

    # Storage access
    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    @property
    def event_log_storage(self):
        return self._instance.event_log_storage

    # Configuration access
    @property
    def run_monitoring_enabled(self):
        return self._instance.run_monitoring_enabled

    @property
    def run_monitoring_max_resume_run_attempts(self):
        return self._instance.run_monitoring_max_resume_run_attempts

    # Instance operations
    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)

    def report_engine_event(self, message, dagster_run, engine_event_data=None):
        return self._instance.report_engine_event(message, dagster_run, engine_event_data)

    def report_dagster_event(
        self,
        dagster_event,
        run_id: str,
        log_level: Union[str, int] = logging.INFO,
        batch_metadata=None,
        timestamp=None,
    ):
        return self._instance.report_dagster_event(
            dagster_event, run_id, log_level, batch_metadata, timestamp
        )

    def report_run_failed(self, dagster_run, message=None, job_failure_data=None):
        return self._instance.report_run_failed(dagster_run, message, job_failure_data)

    # Instance access for daemon monitoring (required for count_resume_run_attempts)
    @property
    def instance(self):
        return self._instance
