import warnings
from base64 import b64decode
from json import JSONDecodeError, loads
from typing import Optional

from dagster._core.run_coordinator import QueuedRunCoordinator, SubmitRunContext
from dagster._core.storage.pipeline_run import PipelineRun


class CustomRunCoordinator(QueuedRunCoordinator):

    # start_email_marker
    def get_email(self, jwt_claims_header: Optional[str]) -> Optional[str]:
        if not jwt_claims_header:
            return None

        split_header_tokens = jwt_claims_header.split(".")
        if len(split_header_tokens) < 2:
            return None

        decoded_claims_json_str = b64decode(split_header_tokens[1])
        try:
            claims_json = loads(decoded_claims_json_str)
            return claims_json.get("email")
        except JSONDecodeError:
            return None

    # end_email_marker

    # start_submit_marker
    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        pipeline_run = context.run
        jwt_claims_header = context.get_request_header("X-Amzn-Oidc-Data")
        email = self.get_email(jwt_claims_header)
        if email:
            self._instance.add_run_tags(pipeline_run.run_id, {"user": email})
        else:
            warnings.warn(f"Couldn't decode JWT header {jwt_claims_header}")
        return super().submit_run(context)

    # end_submit_marker
