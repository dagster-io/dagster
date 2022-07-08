from typing import List

from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import CommandStep


def build_dagit_ui_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":typescript: dagit-ui")
        .run(
            "cd js_modules/dagit",
            "pip install -U virtualenv",
            "tox -vv -e py39",
            "mv packages/core/coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
    ]
