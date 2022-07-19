from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps

from .utils import buildkite_yaml_for_steps

CLI_HELP = """This CLI is used for generating Buildkite YAML. Each function corresponds to an entry
point defined in `setup.py`. Buildkite invokes these entry points when loading the specification for
a pipeline.
"""


def dagster() -> None:
    steps = build_dagster_oss_main_steps()
    buildkite_yaml = buildkite_yaml_for_steps(steps)
    print(buildkite_yaml)  # pylint: disable=print-call
