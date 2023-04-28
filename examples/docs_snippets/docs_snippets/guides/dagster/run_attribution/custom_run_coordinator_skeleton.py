# isort: skip_file

CUSTOM_HEADER_NAME = "X-SOME-HEADER"
# start_custom_run_coordinator_marker

from dagster._core.run_coordinator import QueuedRunCoordinator, SubmitRunContext
from dagster._core.storage.dagster_run import DagsterRun


class CustomRunCoordinator(QueuedRunCoordinator):
    def submit_run(self, context: SubmitRunContext) -> DagsterRun:  # type: ignore  # (didactic)
        desired_header = context.get_request_header(CUSTOM_HEADER_NAME)
        ...


# end_custom_run_coordinator_marker
