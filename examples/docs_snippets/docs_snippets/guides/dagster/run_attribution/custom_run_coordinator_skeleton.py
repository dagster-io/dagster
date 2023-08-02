# ruff: isort: skip_file

CUSTOM_HEADER_NAME = "X-SOME-HEADER"
# start_custom_run_coordinator_marker

from dagster import DagsterRun, QueuedRunCoordinator, SubmitRunContext


class CustomRunCoordinator(QueuedRunCoordinator):
    def submit_run(self, context: SubmitRunContext) -> DagsterRun:  # type: ignore  # (didactic)
        desired_header = context.get_request_header(CUSTOM_HEADER_NAME)
        ...


# end_custom_run_coordinator_marker
