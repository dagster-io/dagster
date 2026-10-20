"""Discovery of the repo and base branch a deploy is running against."""

import json

import pytest
from dagster_cloud_cli.core import git_repo_context
from git import Repo

_REPOSITORY_ENV_VARS = ("GITHUB_REPOSITORY", "CI_PROJECT_PATH")


@pytest.mark.parametrize(
    "remote,expected",
    [
        ("https://github.com/acme/proj", ("acme", "proj")),
        ("https://github.com/acme/proj.git", ("acme", "proj")),
        ("git@github.com:acme/proj.git", ("acme", "proj")),
        ("ssh://git@gitlab.com/acme/proj.git", ("acme", "proj")),
        ("https://gitlab.com/acme/proj/", ("acme", "proj")),
        ("git@gitlab.com:acme/team/proj.git", ("acme/team", "proj")),
        ("https://gitlab.example.com/acme/team/proj.git", ("acme/team", "proj")),
        ("not-a-remote", None),
    ],
)
def test_parse_owner_and_repo(remote, expected):
    assert git_repo_context.parse_owner_and_repo(remote) == expected


@pytest.mark.parametrize(
    "env_var,value,expected",
    [
        ("GITHUB_REPOSITORY", "acme/from-ci", ("acme", "from-ci")),
        ("CI_PROJECT_PATH", "acme/team/from-ci", ("acme/team", "from-ci")),
    ],
)
def test_prefers_the_ci_provided_repository(monkeypatch, env_var, value, expected):
    # Set by the provider from its own event, so it beats parsing a remote.
    for name in _REPOSITORY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(env_var, value)
    assert git_repo_context.discover_repo_owner_and_name(".") == expected


def test_reports_nothing_without_a_repository(monkeypatch, tmp_path):
    for name in _REPOSITORY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    # tmp_path is not a checkout, so there is no remote to read.
    assert git_repo_context.discover_repo_owner_and_name(str(tmp_path)) == (None, None)


_BRANCH_ENV_VARS = (
    "GITHUB_BASE_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF_TYPE",
    "GITHUB_EVENT_NAME",
    "GITHUB_EVENT_PATH",
    "CI_MERGE_REQUEST_TARGET_BRANCH_NAME",
    "CI_DEFAULT_BRANCH",
)


@pytest.fixture
def github_push(monkeypatch, tmp_path):
    """A GitHub Actions run whose repo's default branch is ``main``."""
    for env_var in _BRANCH_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"repository": {"default_branch": "main"}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_TYPE", "branch")
    return monkeypatch


# On a pull request the checkout is the head branch, but the binding wants the
# branch authoring pull requests should target.
def test_base_branch_prefers_the_pull_request_base(github_push, tmp_path):
    github_push.setenv("GITHUB_EVENT_NAME", "pull_request")
    github_push.setenv("GITHUB_BASE_REF", "main")
    github_push.setenv("GITHUB_REF_NAME", "feature/some-branch")
    assert git_repo_context.discover_base_branch(str(tmp_path)) == "main"


def test_base_branch_uses_a_push_to_the_default_branch(github_push, tmp_path):
    github_push.setenv("GITHUB_REF_NAME", "main")
    assert git_repo_context.discover_base_branch(str(tmp_path)) == "main"


@pytest.mark.parametrize(
    "event_name,ref_type,ref_name",
    [
        ("push", "branch", "feature/some-branch"),
        ("push", "tag", "v1.2.3"),
        ("workflow_dispatch", "branch", "main"),
    ],
)
def test_base_branch_ignores_refs_that_are_not_the_default_branch(
    github_push, tmp_path, event_name, ref_type, ref_name
):
    github_push.setenv("GITHUB_EVENT_NAME", event_name)
    github_push.setenv("GITHUB_REF_TYPE", ref_type)
    github_push.setenv("GITHUB_REF_NAME", ref_name)
    # tmp_path is not a checkout, so there is no origin/HEAD to fall back to.
    assert git_repo_context.discover_base_branch(str(tmp_path)) is None


def test_base_branch_prefers_the_merge_request_target(monkeypatch, tmp_path):
    for env_var in _BRANCH_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "release")
    monkeypatch.setenv("CI_DEFAULT_BRANCH", "main")
    assert git_repo_context.discover_base_branch(str(tmp_path)) == "release"


def test_base_branch_uses_the_gitlab_default_branch(monkeypatch, tmp_path):
    for env_var in _BRANCH_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("CI_DEFAULT_BRANCH", "main")
    assert git_repo_context.discover_base_branch(str(tmp_path)) == "main"


def test_base_branch_reports_nothing_outside_a_checkout(monkeypatch, tmp_path):
    for env_var in _BRANCH_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    assert git_repo_context.discover_base_branch(str(tmp_path)) is None


def test_reads_a_checkout(monkeypatch, tmp_path):
    for env_var in (*_REPOSITORY_ENV_VARS, *_BRANCH_ENV_VARS):
        monkeypatch.delenv(env_var, raising=False)
    repo = Repo.init(tmp_path)
    repo.create_remote("origin", "git@github.com:acme/proj.git")
    repo.git.update_ref("refs/remotes/origin/main", repo.index.commit("init").hexsha)
    repo.git.symbolic_ref("refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    # The project may sit below the checkout root.
    project_dir = tmp_path / "proj"
    project_dir.mkdir()

    assert git_repo_context.discover_repo_owner_and_name(str(project_dir)) == ("acme", "proj")
    assert git_repo_context.discover_base_branch(str(project_dir)) == "main"
