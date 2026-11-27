"""Discover which repo, and which branch, a deploy is running against.

Reported with the deploy so the server knows where a code location's UI-authored
components belong. Everything here is best-effort: a deploy that isn't run from
a checkout, or has no remote, simply reports nothing.
"""

import json
import logging
import os
import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from git import Repo

logger = logging.getLogger("dagster_cloud_cli")

# git@github.com:acme/proj.git, https://github.com/acme/proj.git, ssh://git@host/acme/proj.
# The owner may span several segments: GitLab namespaces nest (``group/subgroup``).
_REMOTE_PATTERN = re.compile(
    r"^(?:[a-z+]+://[^/]+/|[^@/:]+@[^:/]+:)(?P<owner>.+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def _open_repo(project_dir: str) -> "Repo | None":
    try:
        # Imported lazily: GitPython raises at import time when no git binary is on PATH.
        from git import InvalidGitRepositoryError, NoSuchPathError, Repo
    except ImportError:
        logger.debug("git is unavailable", exc_info=True)
        return None
    try:
        return Repo(project_dir, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return None


def parse_owner_and_repo(remote_url: str) -> tuple[str, str] | None:
    """``(owner, repo)`` from a git remote URL, or None if it isn't one."""
    match = _REMOTE_PATTERN.search(remote_url.strip())
    if not match:
        return None
    return match.group("owner"), match.group("repo")


def discover_repo_owner_and_name(project_dir: str) -> tuple[str | None, str | None]:
    """The owner and repo this deploy is running against.

    Prefers ``GITHUB_REPOSITORY`` / ``CI_PROJECT_PATH`` (``owner/repo``), which
    CI sets from the provider's own event rather than from anything a user typed.
    """
    from_env = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("CI_PROJECT_PATH")
    if from_env and "/" in from_env:
        owner, _, name = from_env.rpartition("/")
        return owner, name

    remote = _origin_url(project_dir)
    parsed = parse_owner_and_repo(remote) if remote else None
    return parsed if parsed else (None, None)


def discover_git_provider(project_dir: str) -> str | None:
    """``"github"`` or ``"gitlab"``, or None when it can't be told.

    Taken from the CI system when there is one, since a self-hosted GitLab's
    hostname need not mention GitLab; otherwise from the origin remote's host.
    """
    if os.environ.get("GITLAB_CI"):
        return "gitlab"
    if os.environ.get("GITHUB_ACTIONS"):
        return "github"

    remote = _origin_url(project_dir)
    host = _remote_host(remote) if remote else ""
    if "gitlab" in host:
        return "gitlab"
    if "github" in host:
        return "github"
    return None


def _origin_url(project_dir: str) -> str | None:
    repo = _open_repo(project_dir)
    if repo is None:
        return None
    from git import GitCommandError

    try:
        return repo.remote("origin").url
    except (ValueError, GitCommandError):
        return None


def _remote_host(remote_url: str) -> str:
    if "://" in remote_url:
        return (urlparse(remote_url).hostname or "").lower()
    # scp-like syntax, e.g. git@gitlab.com:acme/proj.git
    return remote_url.rpartition("@")[2].partition(":")[0].lower()


def _github_default_branch() -> str | None:
    """The repo's default branch, from the GitHub Actions event payload."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    try:
        with open(event_path, encoding="utf-8") as f:
            return json.load(f).get("repository", {}).get("default_branch")
    except (OSError, ValueError, AttributeError):
        return None


def discover_base_branch(project_dir: str) -> str | None:
    """The branch pull requests should target.

    Deliberately **not** the checked-out branch: on a pull request the checkout
    is the head branch, and recording that would point every authoring pull
    request at a feature branch that may already be merged.

    - ``GITHUB_BASE_REF`` / ``CI_MERGE_REQUEST_TARGET_BRANCH_NAME``: set only on
      pull/merge-request runs.
    - ``GITHUB_REF_NAME``: trusted only on a push to the default branch; on other
      pushes, tags, or manual runs it names a feature branch or tag.
    - ``CI_DEFAULT_BRANCH``: GitLab sets the default branch directly.
    - Otherwise, the remote's default branch.
    """
    base_ref = os.environ.get("GITHUB_BASE_REF") or os.environ.get(
        "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
    )
    if base_ref:
        return base_ref

    gitlab_default_branch = os.environ.get("CI_DEFAULT_BRANCH")
    if gitlab_default_branch:
        return gitlab_default_branch

    ref_name = os.environ.get("GITHUB_REF_NAME")
    if (
        ref_name
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("GITHUB_REF_TYPE") == "branch"
        and ref_name == _github_default_branch()
    ):
        return ref_name

    repo = _open_repo(project_dir)
    if repo is None:
        return None
    from git import RemoteReference, SymbolicReference

    try:
        target = SymbolicReference(repo, "refs/remotes/origin/HEAD").reference
    except (TypeError, ValueError):
        # No origin/HEAD, or it isn't symbolic.
        return None
    return target.remote_head if isinstance(target, RemoteReference) else None


def discover_repo_root(project_dir: str) -> str | None:
    """The checkout root, which a project directory may sit below.

    The binding's defs path is repo-relative, and in a workspace the project
    root is a subdirectory of the repo, so the two differ.
    """
    repo = _open_repo(project_dir)
    return str(repo.working_tree_dir) if repo and repo.working_tree_dir else None
