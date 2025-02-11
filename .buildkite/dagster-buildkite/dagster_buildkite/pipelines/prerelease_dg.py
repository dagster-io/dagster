from typing import List

from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.utils import BlockStep, BuildkiteStep


def build_prerelease_dg_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    input_step: BlockStep = {
        "block": ":question: Choose veresion",
        "prompt": None,
        "fields": [
            {
                "text": "Enter the version to publish",
                "required": False,
                "key": "version-to-release",
                "default": None,
                "hint": "Leave blank to auto-increment the minor version",
            },
        ],
    }
    steps.append(input_step)

    steps.append(
        CommandStepBuilder(":package: Build and publish package")
        .run(
            "pip install build",
            "sh ./scripts/build_and_publish_dg_and_components.sh",
        )
        .on_test_image(AvailablePythonVersion.get_default(), env=["PYPI_TOKEN"])
        .build()
    )

    return steps
