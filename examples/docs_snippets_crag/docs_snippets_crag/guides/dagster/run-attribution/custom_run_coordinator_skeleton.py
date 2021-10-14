"""isort:skip_file"""

# start_custom_run_coordinator_marker

from dagster.core.run_coordinator import QueuedRunCoordinator, SubmitRunContext
from dagster.core.storage.pipeline_run import PipelineRun


class CustomRunCoordinator(QueuedRunCoordinator):
    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        pass


# end_custom_run_coordinator_marker

CUSTOM_HEADER_NAME = "X-SOME-HEADER"

# start_flask_header_marker

from flask import has_request_context, request

desired_header = request.headers.get(CUSTOM_HEADER_NAME) if has_request_context() else None

# end_flask_header_marker
