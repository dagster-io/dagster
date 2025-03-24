from typing import List

from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.utils import (
    BuildkiteLeafStep,
    BuildkiteStep,
    GroupStep,
    skip_if_no_docs_changes,
)


def build_docs_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    docs_steps: List[BuildkiteLeafStep] = [
        CommandStepBuilder("build docs")
        .run(
            "cd docs",
            "yarn install",
            "yarn test",
            "yarn build-api-docs",
            "yarn build",
        )
        .with_skip(skip_if_no_docs_changes())
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
    ]

    steps += [
        GroupStep(
            group=":book: docs",
            key="docs",
            steps=docs_steps,
        )
    ]

    return steps
