import os
import re
from typing import List, Optional

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
        trigger_branch = _get_setting("INTERNAL_BRANCH") or "master"
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
                "DAGSTER_CHECKOUT_DEPTH": _get_setting("DAGSTER_CHECKOUT_DEPTH") or "100",
            },
        ),
    )

    # Full pipeline.
    steps += build_dagster_steps()

    return steps


def _get_setting(name: str) -> Optional[str]:
    """Load a setting defined either as an environment variable or in a `[<key>=<value>]`
    string in the commit message.
    """
    direct_specifier = os.getenv(name)
    commit_message = safe_getenv("BUILDKITE_MESSAGE")
    if direct_specifier:
        return direct_specifier
    else:
        m = re.search(r"\[" + name + r"=(\S+)\]", commit_message)
        return m.group(1) if m else None
