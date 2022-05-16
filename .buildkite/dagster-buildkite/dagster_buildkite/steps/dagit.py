from typing import List

from ..defines import SupportedPython
from ..utils import CommandStep
from ..step_builder import StepBuilder


def dagit_steps() -> List[CommandStep]:
    return [
        StepBuilder("dagit webapp tests")
        .run(
            "cd js_modules/dagit",
            "tox -vv -e py37",
            "mv packages/core/coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
