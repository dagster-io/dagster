import os
from typing import Optional

from . import git_context

# Loads event details from within a gitlab pipeline


class GitlabEvent:
    def __init__(self, project_dir: str):
        # https://docs.gitlab.com/ee/ci/variables/predefined_variables.html
        self.commit_sha = os.environ["CI_COMMIT_SHA"]
        self.branch_name = os.environ.get("CI_COMMIT_REF_NAME", "")
        self.job_url = os.environ["CI_JOB_URL"]
        self.project_name = os.environ["CI_PROJECT_NAME"]
        self.project_url = os.environ["CI_PROJECT_URL"]

        self.merge_request_iid: Optional[str] = os.environ.get("CI_MERGE_REQUEST_IID")

        self.branch_url = f"{self.project_url}/-/tree/{self.branch_name}"

        if self.merge_request_iid:
            self.merge_request_url = f"{self.project_url}/-/merge_requests/{self.merge_request_iid}"
        else:
            self.merge_request_url = None

        self.git_metadata = git_context.get_git_commit_metadata(project_dir)


def get_gitlab_event(project_dir) -> GitlabEvent:
    return GitlabEvent(project_dir)
