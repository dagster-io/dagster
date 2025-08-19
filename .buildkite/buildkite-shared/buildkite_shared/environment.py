import os

from buildkite_shared.git import get_commit_message


def safe_getenv(env_var: str) -> str:
    assert env_var in os.environ, f"${env_var} must be set."
    return os.environ[env_var]


def is_feature_branch(branch_name: str = safe_getenv("BUILDKITE_BRANCH")) -> bool:
    return not (branch_name == "master" or branch_name.startswith("release"))


def is_release_branch(branch_name: str = safe_getenv("BUILDKITE_BRANCH")) -> bool:
    return branch_name.startswith("release-")


def run_all_tests() -> bool:
    return message_contains("NO_SKIP") or os.getenv("NO_SKIP") == "true"


def message_contains(substring: str) -> bool:
    return any(
        substring in message
        for message in [os.getenv("BUILDKITE_MESSAGE", ""), get_commit_message("HEAD")]
    )
