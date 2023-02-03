import os
import re
import subprocess
from typing import List, Optional, Tuple

from dagster_buildkite.steps.dagit_ui import skip_if_no_dagit_changes
from dagster_buildkite.steps.dagster import build_dagster_steps
from dagster_buildkite.steps.trigger import build_trigger_step
from dagster_buildkite.utils import BuildkiteStep, is_release_branch, safe_getenv


def build_dagster_oss_main_steps() -> List[BuildkiteStep]:
    branch_name = safe_getenv("BUILDKITE_BRANCH")
    commit_hash = safe_getenv("BUILDKITE_COMMIT")

    steps: List[BuildkiteStep] = []

    # Trigger a build on the internal pipeline for dagster PRs. Feature branches use the
    # `oss-internal-compatibility` pipeline, master/release branches use the full `internal`
    # pipeline. Feature branches use internal' `master` branch by default, but this can be
    # overridden by setting the `INTERNAL_BRANCH` environment variable or passing
    # `[INTERNAL_BRANCH=<branch>]` in the commit message. Master/release branches
    # always run on the matching internal branch.
    if branch_name == "master" or is_release_branch(branch_name):
        pipeline_name = "internal"
        trigger_branch = branch_name  # build on matching internal release branch
        async_step = True
    else:  # feature branch
        pipeline_name = "oss-internal-compatibility"
        trigger_branch = _get_internal_branch_specifier() or "master"
        async_step = False

    steps.append(
        build_trigger_step(
            pipeline=pipeline_name,
            trigger_branch=trigger_branch,
            async_step=async_step,
            env={
                "DAGSTER_BRANCH": branch_name,
                "DAGSTER_COMMIT_HASH": commit_hash,
                "DAGIT_ONLY_OSS_CHANGE": "1" if not skip_if_no_dagit_changes() else "",
            },
        ),
    )

    # Full pipeline.
    steps += build_dagster_steps()

    return steps


def _is_path_only_diff(paths: Tuple[str, ...]) -> bool:
    base_branch = safe_getenv("BUILDKITE_PULL_REQUEST_BASE_BRANCH")

    try:
        pr_commit = safe_getenv("BUILDKITE_COMMIT")
        origin_base = "origin/" + base_branch
        diff_files = (
            subprocess.check_output(["git", "diff", origin_base, pr_commit, "--name-only"])
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        return all(filepath.startswith(paths) for (filepath) in diff_files)

    except subprocess.CalledProcessError:
        return False


def _get_internal_branch_specifier() -> Optional[str]:
    direct_specifier = os.getenv("INTERNAL_BRANCH")
    commit_message = safe_getenv("BUILDKITE_MESSAGE")
    if direct_specifier:
        return direct_specifier
    else:
        m = re.search(r"\[INTERNAL_BRANCH=(\S+)\]", commit_message)
        return m.group(1) if m else None
