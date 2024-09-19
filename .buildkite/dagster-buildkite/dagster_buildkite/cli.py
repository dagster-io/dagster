from pathlib import Path

from dagster_buildkite.git import GitInfo
from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps
from dagster_buildkite.pipelines.dagster_oss_nightly_pipeline import build_dagster_oss_nightly_steps
from dagster_buildkite.python_packages import PythonPackages
from dagster_buildkite.utils import buildkite_yaml_for_steps

CLI_HELP = """This CLI is used for generating Buildkite YAML. Each function corresponds to an entry
point defined in `setup.py`. Buildkite invokes these entry points when loading the specification for
a pipeline.
"""


def dagster() -> None:
    PythonPackages.load_from_git(GitInfo(directory=Path(".")))
    steps = build_dagster_oss_main_steps()
    buildkite_yaml = buildkite_yaml_for_steps(steps)
    print(buildkite_yaml)  # noqa: T201


def dagster_nightly() -> None:
    PythonPackages.load_from_git(GitInfo(directory=Path(".")))
    steps = build_dagster_oss_nightly_steps()
    buildkite_yaml = buildkite_yaml_for_steps(steps, custom_slack_channel="eng-buildkite-nightly")
    print(buildkite_yaml)  # noqa: T201
