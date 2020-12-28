from .defines import DO_COVERAGE
from .steps.dagit import dagit_steps
from .steps.dagster import coverage_step, dagster_steps
from .steps.integration import integration_steps
from .steps.wait import wait_step
from .utils import buildkite_yaml_for_steps, is_phab_and_dagit_only

CLI_HELP = """This CLI is used for generating Buildkite YAML.
"""


def dagster():
    all_steps = dagit_steps()
    dagit_only = is_phab_and_dagit_only()

    # If we're in a Phabricator diff and are only making dagit changes, skip the
    # remaining steps since they're not relevant to the diff.
    if not dagit_only:
        all_steps += dagster_steps()

        if DO_COVERAGE:
            all_steps += [wait_step(), coverage_step()]

    buildkite_yaml = buildkite_yaml_for_steps(all_steps)
    print(buildkite_yaml)  # pylint: disable=print-call


def integration():
    buildkite_yaml = buildkite_yaml_for_steps(integration_steps())
    print(buildkite_yaml)  # pylint: disable=print-call
