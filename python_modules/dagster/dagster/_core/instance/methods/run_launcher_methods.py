import sys
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from dagster import check
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES
from dagster._utils.error import serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.launcher.base import RunLauncher
    from dagster._core.run_coordinator.base import BaseWorkspaceRequestContext, RunCoordinator
    from dagster._core.storage.dagster_run import DagsterRun


class RunLauncherMethods:
    """Mixin class containing run launcher-related functionality for DagsterInstance.

    This class provides methods for run submission, launching, and resumption functionality.
    All methods are implemented as instance methods that DagsterInstance inherits.
    """

    # Abstract methods that DagsterInstance provides
    @abstractmethod
    def get_run_by_id(self, run_id: str) -> Optional["DagsterRun"]: ...

    @property
    @abstractmethod
    def run_coordinator(self) -> "RunCoordinator": ...

    @property
    @abstractmethod
    def run_launcher(self) -> "RunLauncher": ...

    @property
    @abstractmethod
    def run_monitoring_enabled(self) -> bool: ...

    @property
    @abstractmethod
    def run_monitoring_max_resume_run_attempts(self) -> int: ...

    # These methods are provided by EventMethods mixin
    # (no abstract declarations needed since EventMethods implements them)

    def submit_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> "DagsterRun":
        """Submit a pipeline run to the coordinator.

        This method delegates to the ``RunCoordinator``, configured on the instance, and will
        call its implementation of ``RunCoordinator.submit_run()`` to send the run to the
        coordinator for execution. Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``PipelineRunStatus.NOT_STARTED`` state. They also must have a non-null
        ExternalPipelineOrigin.

        Args:
            run_id (str): The id of the run.
        """
        from dagster._core.run_coordinator import SubmitRunContext

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to submit_run"
            )

        check.not_none(
            run.remote_job_origin,
            "External pipeline origin must be set for submitted runs",
        )
        check.not_none(
            run.job_code_origin,
            "Python origin must be set for submitted runs",
        )

        try:
            submitted_run = self.run_coordinator.submit_run(
                SubmitRunContext(run, workspace=workspace)
            )
        except:
            from dagster._core.events import EngineEventData

            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(  # type: ignore[attr-defined]
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)  # type: ignore[attr-defined]
            raise

        return submitted_run

    def launch_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> "DagsterRun":
        """Launch a pipeline run.

        This method is typically called using `instance.submit_run` rather than being invoked
        directly. This method delegates to the ``RunLauncher``, if any, configured on the instance,
        and will call its implementation of ``RunLauncher.launch_run()`` to begin the execution of
        the specified run. Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and should be in the
        ``PipelineRunStatus.NOT_STARTED`` state.

        Args:
            run_id (str): The id of the run the launch.
        """
        from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
        from dagster._core.launcher import LaunchRunContext

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to launch_run"
            )

        launch_started_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_STARTING.value,
            job_name=run.job_name,
        )
        self.report_dagster_event(launch_started_event, run_id=run.run_id)  # type: ignore[attr-defined]

        run = self.get_run_by_id(run_id)
        if run is None:
            check.failed(f"Failed to reload run {run_id}")

        # At this point run cannot be None due to check.failed above
        assert run is not None
        try:
            self.run_launcher.launch_run(LaunchRunContext(dagster_run=run, workspace=workspace))
        except:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(  # type: ignore[attr-defined]  # type: ignore[attr-defined]
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)  # type: ignore[attr-defined]
            raise

        return run

    def resume_run(
        self,
        run_id: str,
        workspace: "BaseWorkspaceRequestContext",
        attempt_number: int,
    ) -> "DagsterRun":
        """Resume a pipeline run.

        This method should be called on runs which have already been launched, but whose run workers
        have died.

        Args:
            run_id (str): The id of the run the launch.
        """
        from dagster._core.events import EngineEventData
        from dagster._core.launcher import ResumeRunContext
        from dagster._daemon.monitoring import RESUME_RUN_LOG_MESSAGE

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to resume_run"
            )
        if run.status not in IN_PROGRESS_RUN_STATUSES:
            raise DagsterInvariantViolationError(
                f"Run {run_id} is not in a state that can be resumed"
            )

        self.report_engine_event(  # type: ignore[attr-defined]
            RESUME_RUN_LOG_MESSAGE,
            run,
        )

        try:
            self.run_launcher.resume_run(
                ResumeRunContext(
                    dagster_run=run,
                    workspace=workspace,
                    resume_attempt_number=attempt_number,
                )
            )
        except:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(  # type: ignore[attr-defined]  # type: ignore[attr-defined]
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)  # type: ignore[attr-defined]
            raise

        return run

    def count_resume_run_attempts(self, run_id: str) -> int:
        """Count resume run attempts."""
        from typing import cast

        from dagster._daemon.monitoring import count_resume_run_attempts

        # Cast is safe since this mixin is only used by DagsterInstance
        return count_resume_run_attempts(cast("DagsterInstance", self), run_id)

    def run_will_resume(self, run_id: str) -> bool:
        """Check if run will resume."""
        if not self.run_monitoring_enabled:
            return False
        return self.count_resume_run_attempts(run_id) < self.run_monitoring_max_resume_run_attempts
