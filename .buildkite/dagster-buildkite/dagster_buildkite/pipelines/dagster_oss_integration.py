from typing import List

from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.test_project import build_test_project_steps
from dagster_buildkite.utils import BuildkiteStep


def build_dagster_oss_integration_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []
    steps += build_test_project_steps()
    steps += build_integration_steps()
    return steps
