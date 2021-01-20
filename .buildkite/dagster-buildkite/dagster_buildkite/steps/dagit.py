from typing import List

from ..defines import SupportedPython
from ..step_builder import StepBuilder


def dagit_steps() -> List[dict]:
    return [
        StepBuilder("dagit webapp tests")
        .run(
            "pip install -e python_modules/dagster[test] -qqq",
            "pip install -e python_modules/dagster-graphql -qqq",
            "pip install -e python_modules/libraries/dagster-cron -qqq",
            "pip install -e python_modules/libraries/dagster-slack -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -e examples/legacy_examples -qqq",
            "cd js_modules/dagit",
            "yarn install",
            "yarn run ts",
            "yarn run jest --collectCoverage --watchAll=false",
            "yarn run check-prettier",
            "yarn run check-lint",
            "yarn run download-schema",
            "yarn run generate-types",
            "git diff --exit-code",
            "mv coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
