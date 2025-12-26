"""Git integration utilities for branch deployment auto-detection."""

from dagster_shared.plus.git import (
    find_git_repo_root,
    get_git_metadata_for_branch_deployment,
    get_local_branch_name,
    get_local_repo_name,
    read_git_commit_metadata,
)

__all__ = [
    "find_git_repo_root",
    "get_git_metadata_for_branch_deployment",
    "get_local_branch_name",
    "get_local_repo_name",
    "read_git_commit_metadata",
]
