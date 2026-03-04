import logging
import re

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.quarantine import (
    filter_and_print_steps_by_quarantined,
    get_buildkite_quarantined_objects,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from dagster_buildkite.steps.dagster import build_dagster_steps, build_repo_wide_steps
from dagster_buildkite.steps.dagster_ui import (
    build_dagster_ui_components_steps,
    build_dagster_ui_core_steps,
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


def build_dagster_oss_main_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []

    # Note: we used to trigger an internal build (oss-internal-compatibility/internal),
    # but with monorepo, that became unnecessary because the majority of edits
    # now come from the internal repo

    # Full pipeline.
    steps += build_repo_wide_steps(ctx)
    steps += build_docs_steps(ctx)
    steps += build_dagster_ui_components_steps(ctx)
    steps += build_dagster_ui_core_steps(ctx)
    steps += build_dagster_steps(ctx)

    buildkite_suite_mute_quarantined_objects = get_buildkite_quarantined_objects(
        ctx.get_env("BUILDKITE_TEST_QUARANTINE_TOKEN"),
        ctx.get_env("BUILDKITE_ORGANIZATION_SLUG"),
        ctx.get_env("BUILDKITE_STEP_SUITE_SLUG"),
        "muted",
        suppress_errors=True,
    )
    logging.info(
        f"buildkite_suite_mute_quarantined_objects = {buildkite_suite_mute_quarantined_objects}"
    )
    buildkite_suite_skip_quarantined_objects = get_buildkite_quarantined_objects(
        ctx.get_env("BUILDKITE_TEST_QUARANTINE_TOKEN"),
        ctx.get_env("BUILDKITE_ORGANIZATION_SLUG"),
        ctx.get_env("BUILDKITE_STEP_SUITE_SLUG"),
        "skipped",
        suppress_errors=True,
    )
    logging.info(
        f"buildkite_suite_skip_quarantined_objects = {buildkite_suite_skip_quarantined_objects}"
    )

    return filter_and_print_steps_by_quarantined(
        ctx,
        steps,
        {obj.name for obj in buildkite_suite_skip_quarantined_objects},
        {obj.name for obj in buildkite_suite_mute_quarantined_objects},
    )
