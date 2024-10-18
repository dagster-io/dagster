import os
import re
from typing import List, Optional

from dagster_buildkite.steps.dagster import build_dagster_steps, build_repo_wide_steps
from dagster_buildkite.steps.dagster_ui import (
    build_dagster_ui_components_steps,
    build_dagster_ui_core_steps,
    skip_if_no_dagster_ui_changes,
)
from dagster_buildkite.steps.docs import build_docs_steps
from dagster_buildkite.steps.trigger import build_trigger_step
from dagster_buildkite.utils import BuildkiteStep, is_release_branch, message_contains, safe_getenv


def build_dagster_oss_main_steps() -> List[BuildkiteStep]:
    branch_name = safe_getenv("BUILDKITE_BRANCH")
    commit_hash = safe_getenv("BUILDKITE_COMMIT")
    oss_contribution = os.getenv("OSS_CONTRIBUTION")

    steps: List[BuildkiteStep] = []

    # Trigger a build on the internal pipeline for dagster PRs.
    # master/release branches always trigger
    # Feature branches only trigger if [INTERNAL_BRANCH=<branch>] is in the commit message
    if not oss_contribution and not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        if branch_name == "master" or is_release_branch(branch_name):
            pipeline_name = "internal"
            trigger_branch = branch_name  # build on matching internal release branch
            async_step = True
            oss_compat_slim = False
        else:  # feature branch
            pipeline_name = "oss-internal-compatibility"
            trigger_branch = _get_setting("INTERNAL_BRANCH") or "master"
            async_step = False
            # Use OSS_COMPAT_SLIM by default unless an internal branch is explicitly specified or
            # the commit message contains "NO_SKIP"
            oss_compat_slim = _get_setting("OSS_COMPAT_SLIM") or not (
                _get_setting("INTERNAL_BRANCH") or message_contains("NO_SKIP")
            )

        steps.append(
            build_trigger_step(
                pipeline=pipeline_name,
                trigger_branch=trigger_branch,
                async_step=async_step,
                env={
                    "DAGSTER_BRANCH": branch_name,
                    "DAGSTER_COMMIT_HASH": commit_hash,
                    "DAGSTER_UI_ONLY_OSS_CHANGE": (
                        "1" if not skip_if_no_dagster_ui_changes() else ""
                    ),
                    "DAGSTER_CHECKOUT_DEPTH": _get_setting("DAGSTER_CHECKOUT_DEPTH") or "100",
                    "OSS_COMPAT_SLIM": "1" if oss_compat_slim else "",
                    "DAGSTER_FROM_OSS": "1" if pipeline_name == "internal" else "0",
                },
            ),
        )

    # Full pipeline.
    steps += build_repo_wide_steps()
    steps += build_docs_steps()
    steps += build_dagster_ui_components_steps()
    steps += build_dagster_ui_core_steps()
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
