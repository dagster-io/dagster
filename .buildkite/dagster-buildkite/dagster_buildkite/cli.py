import os
from typing import List

from .defines import DO_COVERAGE
from .steps.coverage import build_coverage_step
from .steps.dagit import build_dagit_steps
from .steps.dagster import build_dagster_steps
from .steps.integration import build_integration_steps
from .steps.trigger import build_trigger_step
from .steps.wait import build_wait_step
from .utils import BuildkiteStep, buildkite_yaml_for_steps, is_pr_and_dagit_only, is_release_branch, safe_getenv

CLI_HELP = """This CLI is used for generating Buildkite YAML.
"""


def dagster() -> None:
    all_steps: List[BuildkiteStep] = []
    all_steps += build_dagit_steps()
    dagit_only: bool = is_pr_and_dagit_only()

    branch_name = safe_getenv("BUILDKITE_BRANCH")
    commit_hash = safe_getenv("BUILDKITE_COMMIT")
    build_creator_email = os.getenv("BUILDKITE_BUILD_CREATOR_EMAIL")
    oss_contribution = os.getenv("OSS_CONTRIBUTION")

    if (
        build_creator_email
        and build_creator_email.endswith("@elementl.com")
        and build_creator_email != "devtools@elementl.com"
        and not oss_contribution
    ):
        if branch_name == "master" or is_release_branch(branch_name):
            pipeline_name = "internal"
            trigger_branch = branch_name
            async_step = True
        else:
            pipeline_name = "oss-internal-compatibility"
            trigger_branch = "master"
            async_step = False

        # Trigger builds of the internal pipeline for builds on master
        all_steps.append(
            build_trigger_step(
                pipeline=pipeline_name,
                trigger_branch=trigger_branch,
                async_step=async_step,
                env={
                    "DAGSTER_BRANCH": branch_name,
                    "DAGSTER_COMMIT_HASH": commit_hash,
                    "DAGIT_ONLY_OSS_CHANGE": "1" if dagit_only else "",
                },
            ),
        )

    # If we're on a PR/feature branch and are only making dagit changes, skip the
    # remaining steps since they're not relevant to the diff.
    if not dagit_only:
        all_steps += build_dagster_steps()

        all_steps.append(build_wait_step())

        if DO_COVERAGE:
            all_steps += [build_coverage_step()]

    buildkite_yaml = buildkite_yaml_for_steps(all_steps)
    print(buildkite_yaml)  # pylint: disable=print-call


def integration() -> None:
    buildkite_yaml = buildkite_yaml_for_steps(build_integration_steps())
    print(buildkite_yaml)  # pylint: disable=print-call
