# isort: skip_file
# pylint: disable=unused-variable
CUSTOM_HEADER_NAME = "X-SOME-HEADER"
# start_custom_run_coordinator_marker

from dagster.core.run_coordinator import QueuedRunCoordinator, SubmitRunContext
from dagster.core.storage.pipeline_run import PipelineRun


class CustomRunCoordinator(QueuedRunCoordinator):
    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        desired_header = context.get_request_header(CUSTOM_HEADER_NAME)


# end_custom_run_coordinator_marker
