import json
import logging
import os
import pathlib
import subprocess
from contextlib import contextmanager
from typing import Optional

from dagster_cloud_cli import ui
from dagster_cloud_cli.core.pex_builder import util

# Loads event details from within a github action


class GithubEvent:
    def __init__(self, project_dir: str):
        self.github_server_url = os.environ["GITHUB_SERVER_URL"]
        self.github_sha = os.environ["GITHUB_SHA"]
        self.github_repository = os.environ["GITHUB_REPOSITORY"]
        self.github_run_id = os.environ["GITHUB_RUN_ID"]
        self.github_run_url = (
            f"{self.github_server_url}/{self.github_repository}/actions/runs/{self.github_run_id}"
        )
        action_path = os.getenv("GITHUB_ACTION_PATH")
        self.github_action_path = pathlib.Path(action_path) if action_path else None
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if not event_path:
            raise ValueError("GITHUB_EVENT_PATH not set")

        # json details: https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads
        self.event = event = json.load(open(event_path, encoding="utf-8"))

        # get some commonly used fields
        # not all events have "action", eg https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push
        self.action = event.get("action")
        self.repo_name = event["repository"]["full_name"]

        self.branch_name: Optional[str] = None
        self.branch_url: Optional[str] = None
        self.pull_request_url: Optional[str] = None
        self.pull_request_id: Optional[str] = None
        self.pull_request_status: Optional[str] = None

        if "pull_request" in self.event:
            pull_request = self.event["pull_request"]
            # For PRs GITHUB_SHA is not the last commit in the branch, but head sha is
            self.github_sha = pull_request["head"]["sha"]
            self.branch_name = pull_request["head"]["ref"]
            self.branch_url = f"{self.github_server_url}/{self.repo_name}/tree/{self.branch_name}"
            self.pull_request_url = pull_request["html_url"]
            self.pull_request_id = str(pull_request["number"])
            self.pull_request_status = (
                "merged" if pull_request.get("merged") else pull_request["state"]
            ).upper()

        self.commit_url = f"{self.github_server_url}/{self.repo_name}/tree/{self.github_sha}"

        git_metadata = get_git_commit_metadata(project_dir)
        self.timestamp = float(git_metadata["timestamp"])
        self.commit_msg = git_metadata["message"]
        self.author_name = git_metadata["name"]
        self.author_email = git_metadata["email"]

    def get_github_repo(self):
        import github3

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return None
        gh = github3.login(token=token)
        repo_owner, repo_name = self.github_repository.split("/", 1)
        return gh.repository(repo_owner, repo_name)

    def get_github_avatar_url(self) -> Optional[str]:
        repo = self.get_github_repo()
        if not repo:
            return
        commit = repo.commit(self.github_sha)
        return commit.author.get("avatar_url") if commit.author else None

    def update_pr_comment(
        self, body: str, orig_author: Optional[str] = None, orig_text: Optional[str] = None
    ):
        # orig_author and orig_text are used to identify an existing comment which is updated.
        # if not provided, or not found, a new comment is created
        import github3.exceptions

        if not self.pull_request_id:
            return

        try:
            repo = self.get_github_repo()
            if not repo:
                return
            pr = repo.pull_request(int(self.pull_request_id))

            for comment in pr.issue_comments():
                if comment.user.login == orig_author and orig_text in comment.body:
                    comment.edit(body)
                    return

            pr.create_comment(body)

        except github3.exceptions.GitHubException:
            logging.exception("Ignoring error when updating PR comment")


def get_git_commit_metadata(project_dir: str) -> dict[str, str]:
    commands = {
        "timestamp": f"git -C {project_dir} log -1 --format=%cd --date=unix".split(),
        "message": f"git -C {project_dir} log -1 --format=%s".split(),
        "email": f"git -C {project_dir} log -1 --format=%ae".split(),
        "name": f"git -C {project_dir} log -1 --format=%an".split(),
    }
    metadata = {}
    for key, command in commands.items():
        logging.debug("Running %r", command)
        proc = subprocess.run(command, capture_output=True, check=False)
        if proc.returncode:
            logging.error(f"git command failed: {proc.stdout}\n{proc.stderr}")
        metadata[key] = proc.stdout.decode("utf-8").strip()

    return metadata


def get_github_event(project_dir) -> GithubEvent:
    return GithubEvent(project_dir)


def update_pr_comment(github_event: GithubEvent, action, deployment_name, location_name):
    """Add or update the status comment on a github PR."""
    # This reuses the src/create_or_update_comment.py script.
    # We can't reuse actions/utils/notify here because we need to run this once for every location.
    # To repeat an action github provides a matrix strategy but we don't use matrix due to latency
    # concerns (it would launch a new container for every location)
    if not github_event.pull_request_id:
        ui.print("Not within a PR, not adding PR comment.")
        return

    if not github_event.github_action_path:
        ui.warn("Unable to locate notification script, not adding PR comment.")
        return

    script_path = github_event.github_action_path.parent.parent / "src/create_or_update_comment.py"
    if not script_path.exists():
        ui.warn(f"Did not find {script_path}, not adding PR comment.")

    env = {name: value for name, value in os.environ.items() if not name.startswith("PEX_")}
    pr_id = str(github_event.pull_request_id)

    env.update(
        {
            "INPUT_PR": pr_id,
            "INPUT_ACTION": action,
            "INPUT_DEPLOYMENT": deployment_name,
            "INPUT_LOCATION_NAME": location_name,
            "GITHUB_RUN_URL": github_event.github_run_url,
        }
    )
    env = {name: value for name, value in env.items() if value is not None}
    proc = util.run_python_subprocess([str(script_path)], env=env)
    if proc.returncode:
        ui.error(f"Could not update PR comment: {proc.stdout}\n{proc.stderr}")


@contextmanager
def log_group(title: str):
    try:
        yield
    finally:
        pass


def log_error(title: str, msg: str):
    pass


if __name__ == "__main__":
    pass
