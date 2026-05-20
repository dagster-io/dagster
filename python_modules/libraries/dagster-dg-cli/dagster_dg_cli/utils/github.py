import base64
import os
import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from githubkit import GitHub
    from githubkit.versions.latest.models import FullRepository, PullRequest


class GitHubError(Exception):
    """Base class for GitHub utility errors that should be shown to CLI users."""


class GitHubAuthError(GitHubError):
    """Raised when GitHub authentication is not configured."""


class GitHubRepositoryClient:
    def __init__(self, github: "GitHub", owner: str, repo: str):
        self.github = github
        self.owner = owner
        self.repo = repo

    def get_repository(self) -> "FullRepository":
        return self.github.rest.repos.get(self.owner, self.repo).parsed_data

    def workflow_exists(self, workflow_id: str) -> bool:
        # Keep githubkit imports lazy so non-GitHub CLI paths can import this module without it.
        from githubkit.exception import RequestFailed

        try:
            self.github.rest.actions.get_workflow(self.owner, self.repo, workflow_id)
        except RequestFailed as exc:
            if exc.response.status_code == 404:
                return False
            raise
        return True

    def get_branch_sha(self, branch_name: str) -> str:
        response = self.github.rest.git.get_ref(self.owner, self.repo, f"heads/{branch_name}")
        return response.parsed_data.object_.sha

    def branch_exists(self, branch_name: str) -> bool:
        response = self.github.rest.git.list_matching_refs(
            self.owner,
            self.repo,
            f"heads/{branch_name}",
        )
        target_ref = f"refs/heads/{branch_name}"
        return any(ref.ref == target_ref for ref in response.parsed_data)

    def create_branch(self, branch_name: str, sha: str) -> None:
        self.github.rest.git.create_ref(
            self.owner,
            self.repo,
            ref=f"refs/heads/{branch_name}",
            sha=sha,
        )

    def create_file(self, path: str, message: str, content: bytes, branch_name: str) -> None:
        self.github.rest.repos.create_or_update_file_contents(
            self.owner,
            self.repo,
            path,
            message=message,
            content=base64.b64encode(content).decode("utf-8"),
            branch=branch_name,
        )

    def create_pull_request(
        self,
        *,
        title: str,
        head: str,
        base: str,
        body: str,
        draft: bool,
    ) -> "PullRequest":
        return self.github.rest.pulls.create(
            self.owner,
            self.repo,
            title=title,
            head=head,
            base=base,
            body=body,
            draft=draft,
        ).parsed_data

    def add_labels(self, issue_number: int, labels: list[str]) -> None:
        self.github.rest.issues.add_labels(
            self.owner,
            self.repo,
            issue_number,
            labels=labels,
        )

    def dispatch_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: dict[str, str],
    ) -> None:
        self.github.rest.actions.create_workflow_dispatch(
            self.owner,
            self.repo,
            workflow_id,
            ref=ref,
            inputs=inputs,
        )


def _get_allowed_github_hosts() -> set[str]:
    allowed_hosts = {"github.com"}
    server_url = os.getenv("GITHUB_SERVER_URL")
    if server_url:
        host = urlparse(server_url).hostname
        if host:
            allowed_hosts.add(host)
    return allowed_hosts


def _get_github_base_url() -> str | None:
    api_url = os.getenv("GITHUB_API_URL")
    if api_url:
        return api_url

    server_url = os.getenv("GITHUB_SERVER_URL")
    if not server_url:
        return None

    parsed_server_url = urlparse(server_url)
    if parsed_server_url.hostname == "github.com":
        return None

    return f"{server_url.rstrip('/')}/api/v3"


def parse_github_remote_url(remote_url: str) -> tuple[str, str] | None:
    ssh_match = re.match(
        r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", remote_url
    )
    if ssh_match and ssh_match.group("host") in _get_allowed_github_hosts():
        return ssh_match.group("owner"), ssh_match.group("repo")

    parsed_url = urlparse(remote_url)
    if parsed_url.hostname not in _get_allowed_github_hosts():
        return None

    path_parts = [part for part in parsed_url.path.split("/") if part]
    if len(path_parts) != 2:
        return None

    owner, repo = path_parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def get_github_client() -> "GitHub":
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubAuthError(
            "GitHub authentication not found. Set GH_TOKEN or GITHUB_TOKEN to make GitHub API calls."
        )

    # Keep githubkit imports lazy so non-GitHub CLI paths can import this module without it.
    from githubkit import GitHub

    base_url = _get_github_base_url()
    if base_url:
        return GitHub(auth=token, base_url=base_url)

    return GitHub(auth=token)


def get_authenticated_github_user_login() -> str:
    client = get_github_client()
    return client.rest.users.get_authenticated().parsed_data.login


def get_github_repository(owner: str, repo: str) -> GitHubRepositoryClient:
    return GitHubRepositoryClient(get_github_client(), owner, repo)
