import os

from .defines import DO_COVERAGE
from .steps.dagit import dagit_steps
from .steps.dagster import coverage_step, dagster_steps
from .steps.integration import integration_steps
from .steps.trigger import trigger_step
from .steps.wait import wait_step
from .utils import buildkite_yaml_for_steps, is_pr_and_dagit_only, is_release_branch

CLI_HELP = """This CLI is used for generating Buildkite YAML.
"""


def dagster():
    all_steps = dagit_steps()
    dagit_only = is_pr_and_dagit_only()

    branch_name = os.getenv("BUILDKITE_BRANCH")
    build_creator_email = os.getenv("BUILDKITE_BUILD_CREATOR_EMAIL")

    if build_creator_email and build_creator_email.endswith("@elementl.com"):

        if branch_name == "master" or is_release_branch(branch_name):
            pipeline_name = "internal"
            trigger_branch = branch_name
        else:
            pipeline_name = "oss-internal-compatibility"
            trigger_branch = "master"

        # Trigger builds of the internal pipeline for builds on master
        all_steps += [
            trigger_step(
                pipeline=pipeline_name,
                trigger_branch=trigger_branch,
                async_step=True,
                env={
                    "DAGSTER_BRANCH": branch_name,
                    "DAGSTER_COMMIT_HASH": os.getenv("BUILDKITE_COMMIT"),
                },
            ),
        ]

    # If we're in a Phabricator diff and are only making dagit changes, skip the
    # remaining steps since they're not relevant to the diff.
    if not dagit_only:
        all_steps += dagster_steps()

        all_steps += [wait_step()]

        if DO_COVERAGE:
            all_steps += [coverage_step()]

    buildkite_yaml = buildkite_yaml_for_steps(all_steps)
    print(buildkite_yaml)  # pylint: disable=print-call


def integration():
    buildkite_yaml = buildkite_yaml_for_steps(integration_steps())
    print(buildkite_yaml)  # pylint: disable=print-call
