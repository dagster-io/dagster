import logging
import os
import re
from typing import Optional

from buildkite_shared.environment import is_release_branch, safe_getenv
from buildkite_shared.packages import run_all_tests
from buildkite_shared.quarantine import (
    filter_and_print_steps_by_quarantined,
    get_buildkite_quarantined_objects,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.step_builders.trigger_step_builder import TriggerStepBuilder
from dagster_buildkite.steps.dagster import build_dagster_steps, build_repo_wide_steps
from dagster_buildkite.steps.dagster_ui import (
    build_dagster_ui_components_steps,
    build_dagster_ui_core_steps,
    skip_if_no_dagster_ui_changes,
)
from dagster_buildkite.steps.docs import build_docs_steps


def filter_steps_by_quarantined(steps, skip_quarantined_steps, mute_quarantined_steps):
    if not skip_quarantined_steps and not mute_quarantined_steps:
        return steps, [], []

    skip_quarantined_keys = set(
        key.strip() for key in skip_quarantined_steps.split(",") if key.strip()
    )
    mute_quarantined_keys = set(
        key.strip() for key in mute_quarantined_steps.split(",") if key.strip()
    )
    filtered_steps = []
    skipped_steps = []
    muted_steps = []

    for step in steps:
        # Handle both individual steps and step groups
        if "group" in step:
            # For step groups, check if any of the steps in the group are quarantined
            group_steps = step["steps"]
            filtered_group_steps = []
            for group_step in group_steps:
                stripped_label = re.sub(r":[^:]+:", "", group_step.get("label") or "").strip()
                if stripped_label in skip_quarantined_keys:
                    skipped_steps.append(group_step)
                elif stripped_label in mute_quarantined_keys:
                    group_step["soft_fail"] = True
                    muted_steps.append(group_step)
                    filtered_group_steps.append(group_step)
                else:
                    filtered_group_steps.append(group_step)

            if filtered_group_steps:
                step["steps"] = filtered_group_steps
                filtered_steps.append(step)
        else:
            # For individual steps, check if the step key is in quarantined list
            stripped_label = re.sub(r":[^:]+:", "", step.get("label") or "").strip()
            if stripped_label in skip_quarantined_keys:
                skipped_steps.append(step)
            elif stripped_label in mute_quarantined_keys:
                step["soft_fail"] = True
                muted_steps.append(step)
                filtered_steps.append(step)
            else:
                filtered_steps.append(step)

    return filtered_steps, skipped_steps, muted_steps


def build_dagster_oss_main_steps() -> list[StepConfiguration]:
    branch_name = safe_getenv("BUILDKITE_BRANCH")
    commit_hash = safe_getenv("BUILDKITE_COMMIT")
    oss_contribution = os.getenv("OSS_CONTRIBUTION")

    steps: list[StepConfiguration] = []

    # Trigger a build on the internal pipeline for dagster PRs.
    # master/release branches always trigger
    # Feature branches only trigger if [INTERNAL_BRANCH=<branch>] is in the commit message
    if (
        not oss_contribution
        and not os.getenv("CI_DISABLE_INTEGRATION_TESTS")
        and not os.getenv("TRIGGERED_BY_INTERNAL")
    ):
        if branch_name == "master" or is_release_branch(branch_name):
            pipeline_name = "internal"
            trigger_branch = branch_name  # build on matching internal release branch
            async_step = True
            oss_compat_slim = False
        else:  # feature branch
            pipeline_name = "oss-internal-compatibility"
            trigger_branch = (
                _get_setting("INTERNAL_BRANCH")
                or _get_setting("BUILDKITE_FOLDER_BRANCH")
                or "master"
            )
            async_step = False
            # Use OSS_COMPAT_SLIM by default unless an internal branch is explicitly specified or
            # the commit message contains "NO_SKIP"
            oss_compat_slim = _get_setting("OSS_COMPAT_SLIM") or not (
                _get_setting("INTERNAL_BRANCH")
                or _get_setting("BUILDKITE_FOLDER_BRANCH")
                or run_all_tests()
            )

        dagster_commit_hash = safe_getenv("BUILDKITE_COMMIT")
        steps.append(
            TriggerStepBuilder(
                label=f":link: {pipeline_name} from dagster@{dagster_commit_hash[:10]}",
                pipeline=pipeline_name,
            )
            .with_build_params(
                {
                    "env": {
                        "DAGSTER_BRANCH": branch_name,
                        "DAGSTER_COMMIT_HASH": commit_hash,
                        "DAGSTER_UI_ONLY_OSS_CHANGE": (
                            "1" if not skip_if_no_dagster_ui_changes() else ""
                        ),
                        "DAGSTER_CHECKOUT_DEPTH": _get_setting("DAGSTER_CHECKOUT_DEPTH") or "100",
                        "OSS_COMPAT_SLIM": "1" if oss_compat_slim else "",
                        "DAGSTER_FROM_OSS": "1" if pipeline_name == "internal" else "0",
                    },
                    "branch": trigger_branch,
                }
            )
            .with_async(async_step)
            .build(),
        )

    # Full pipeline.
    steps += build_repo_wide_steps()
    steps += build_docs_steps()
    steps += build_dagster_ui_components_steps()
    steps += build_dagster_ui_core_steps()
    steps += build_dagster_steps()

    BUILDKITE_TEST_QUARANTINE_TOKEN = os.getenv("BUILDKITE_TEST_QUARANTINE_TOKEN")
    BUILDKITE_ORGANIZATION_SLUG = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
    BUILDKITE_STEP_SUITE_SLUG = os.getenv("BUILDKITE_STEP_SUITE_SLUG")

    buildkite_suite_mute_quarantined_objects = get_buildkite_quarantined_objects(
        BUILDKITE_TEST_QUARANTINE_TOKEN,
        BUILDKITE_ORGANIZATION_SLUG,
        BUILDKITE_STEP_SUITE_SLUG,
        "muted",
        suppress_errors=True,
    )
    logging.info(
        f"buildkite_suite_mute_quarantined_objects = {buildkite_suite_mute_quarantined_objects}"
    )
    buildkite_suite_skip_quarantined_objects = get_buildkite_quarantined_objects(
        BUILDKITE_TEST_QUARANTINE_TOKEN,
        BUILDKITE_ORGANIZATION_SLUG,
        BUILDKITE_STEP_SUITE_SLUG,
        "skipped",
        suppress_errors=True,
    )
    logging.info(
        f"buildkite_suite_skip_quarantined_objects = {buildkite_suite_skip_quarantined_objects}"
    )

    return filter_and_print_steps_by_quarantined(
        steps,
        {obj.name for obj in buildkite_suite_skip_quarantined_objects},
        {obj.name for obj in buildkite_suite_mute_quarantined_objects},
    )


def _get_setting(name: str) -> Optional[str]:
    """Load a setting defined either as an environment variable or in a `[<key>=<value>]`
    string in the commit message.
    """
    direct_specifier = os.getenv(name)
    commit_message = safe_getenv("BUILDKITE_MESSAGE")
    if direct_specifier:
        return direct_specifier
    else:
        m = re.search(r"\[" + name + r"=([^\]]+)\]", commit_message)
        return m.group(1) if m else None
