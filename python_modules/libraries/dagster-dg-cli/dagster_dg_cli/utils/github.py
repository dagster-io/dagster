import base64
import os
import re
from typing import Any, NamedTuple
from urllib.parse import quote, urlparse

import requests


class Repository(NamedTuple):
    default_branch: str
    html_url: str


class PullRequest(NamedTuple):
    number: int
    html_url: str


_DEFAULT_GITHUB_API_URL = "https://api.github.com"
_REQUEST_TIMEOUT_SECONDS = 60


class GitHubError(Exception):
    """Base class for GitHub utility errors that should be shown to CLI users."""


class GitHubAuthError(GitHubError):
    """Raised when GitHub authentication is not configured."""


class _GitHubClient:
    def __init__(self, token: str, base_url: str | None = None):
        self._base_url = (base_url or _DEFAULT_GITHUB_API_URL).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "dagster-dg-cli",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
    ) -> requests.Response:
        url = f"{self._base_url}{path}"
        response = self._session.request(
            method,
            url,
            json=json,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response


def _ref_path(branch_name: str) -> str:
    return quote(branch_name, safe="/")


class GitHubRepositoryClient:
    def __init__(self, client: _GitHubClient, owner: str, repo: str):
        self._client = client
        self.owner = owner
        self.repo = repo

    def _repo_path(self, suffix: str = "") -> str:
        return f"/repos/{self.owner}/{self.repo}{suffix}"

    def get_repository(self) -> Repository:
        data = self._client.request("GET", self._repo_path()).json()
        return Repository(default_branch=data["default_branch"], html_url=data["html_url"])

    def workflow_exists(self, workflow_id: str) -> bool:
        try:
            self._client.request(
                "GET",
                self._repo_path(f"/actions/workflows/{quote(workflow_id, safe='')}"),
            )
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return False
            raise
        return True

    def get_branch_sha(self, branch_name: str) -> str:
        response = self._client.request(
            "GET",
            self._repo_path(f"/git/ref/heads/{_ref_path(branch_name)}"),
        )
        return response.json()["object"]["sha"]

    def branch_exists(self, branch_name: str) -> bool:
        response = self._client.request(
            "GET",
            self._repo_path(f"/git/matching-refs/heads/{_ref_path(branch_name)}"),
        )
        target_ref = f"refs/heads/{branch_name}"
        return any(ref["ref"] == target_ref for ref in response.json())

    def create_branch(self, branch_name: str, sha: str) -> None:
        self._client.request(
            "POST",
            self._repo_path("/git/refs"),
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )

    def create_file(self, path: str, message: str, content: bytes, branch_name: str) -> None:
        self._client.request(
            "PUT",
            self._repo_path(f"/contents/{quote(path, safe='/')}"),
            json={
                "message": message,
                "content": base64.b64encode(content).decode("utf-8"),
                "branch": branch_name,
            },
        )

    def create_empty_commit(self, branch_name: str, parent_sha: str, message: str) -> str:
        parent_commit = self._client.request(
            "GET",
            self._repo_path(f"/git/commits/{quote(parent_sha, safe='')}"),
        ).json()
        tree_sha = parent_commit["tree"]["sha"]
        commit = self._client.request(
            "POST",
            self._repo_path("/git/commits"),
            json={"message": message, "tree": tree_sha, "parents": [parent_sha]},
        ).json()
        commit_sha = commit["sha"]
        self._client.request(
            "PATCH",
            self._repo_path(f"/git/refs/heads/{_ref_path(branch_name)}"),
            json={"sha": commit_sha},
        )
        return commit_sha

    def create_pull_request(
        self,
        *,
        title: str,
        head: str,
        base: str,
        body: str,
        draft: bool,
    ) -> PullRequest:
        data = self._client.request(
            "POST",
            self._repo_path("/pulls"),
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
            },
        ).json()
        return PullRequest(number=data["number"], html_url=data["html_url"])

    def add_labels(self, issue_number: int, labels: list[str]) -> None:
        self._client.request(
            "POST",
            self._repo_path(f"/issues/{issue_number}/labels"),
            json={"labels": labels},
        )

    def dispatch_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: dict[str, str],
    ) -> None:
        self._client.request(
            "POST",
            self._repo_path(f"/actions/workflows/{quote(workflow_id, safe='')}/dispatches"),
            json={"ref": ref, "inputs": inputs},
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


def _get_github_client() -> _GitHubClient:
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubAuthError(
            "GitHub authentication not found. Set GH_TOKEN or GITHUB_TOKEN to make GitHub API calls."
        )
    return _GitHubClient(token=token, base_url=_get_github_base_url())


def get_authenticated_github_user_login() -> str:
    client = _get_github_client()
    return client.request("GET", "/user").json()["login"]


def get_github_repository(owner: str, repo: str) -> GitHubRepositoryClient:
    return GitHubRepositoryClient(_get_github_client(), owner, repo)
