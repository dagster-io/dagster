from typing import List

from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from dagster_buildkite.utils import (
    skip_if_no_docs_changes,
)
from dagster_buildkite.images.versions import add_test_image


def build_docs_steps() -> List[StepConfiguration]:
    steps: List[StepConfiguration] = []

    docs_steps: List[GroupLeafStepConfiguration] = [
        add_test_image(
            CommandStepBuilder("build docs"), AvailablePythonVersion.get_default()
        )
        .run(
            "cd docs",
            "yarn install",
            "yarn test",
            "yarn build-api-docs",
            "yarn build",
        )
        .skip_if(skip_if_no_docs_changes())
        .build(),
    ]

    steps += [
        GroupStepBuilder(
            name=":book: docs",
            key="docs",
            steps=docs_steps,
        ).build()
    ]

    return steps
