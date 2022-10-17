import os
import re
from typing import List, Optional

from dagster_buildkite.defines import DO_COVERAGE
from dagster_buildkite.steps.coverage import build_coverage_step
from dagster_buildkite.steps.dagit_ui import build_dagit_ui_steps
from dagster_buildkite.steps.dagster import build_dagster_steps, build_repo_wide_steps
from dagster_buildkite.steps.docs import build_docs_steps
from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.trigger import build_trigger_step
from dagster_buildkite.steps.wait import build_wait_step
from dagster_buildkite.utils import BuildkiteStep, is_release_branch, safe_getenv


def build_dagster_oss_main_steps() -> List[BuildkiteStep]:

    branch_name = safe_getenv("BUILDKITE_BRANCH")
    commit_hash = safe_getenv("BUILDKITE_COMMIT")
    build_creator_email = os.getenv("BUILDKITE_BUILD_CREATOR_EMAIL")
    oss_contribution = os.getenv("OSS_CONTRIBUTION")
    do_coverage = DO_COVERAGE

    steps: List[BuildkiteStep] = []

    # Trigger a build on the internal pipeline for Elementl dev PRs. Feature branches use the
    # `oss-internal-compatibility` pipeline, master/release branches use the full `internal`
    # pipeline. Feature branches use internal' `master` branch by default, but this can be
    # overridden by setting the `INTERNAL_BRANCH` environment variable or passing
    # `[INTERNAL_BRANCH=<branch>]` in the commit message. Master/release branches
    # always run on the matching internal branch.
    if (
        build_creator_email
        and build_creator_email.endswith("@elementl.com")
        and build_creator_email != "devtools@elementl.com"
        and not oss_contribution
    ):
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
                },
            ),
        )

    # Always include repo wide steps
    steps += build_repo_wide_steps()

    # Full pipeline.
    steps += build_docs_steps()
    steps += build_dagit_ui_steps()
    steps += build_dagster_steps()
    steps += build_integration_steps()

    if do_coverage:
        steps.append(build_wait_step())
        steps.append(build_coverage_step())

    return steps


def _get_internal_branch_specifier() -> Optional[str]:
    direct_specifier = os.getenv("INTERNAL_BRANCH")
    commit_message = safe_getenv("BUILDKITE_MESSAGE")
    if direct_specifier:
        return direct_specifier
    else:
        m = re.search(r"\[INTERNAL_BRANCH=(\S+)\]", commit_message)
        return m.group(1) if m else None
