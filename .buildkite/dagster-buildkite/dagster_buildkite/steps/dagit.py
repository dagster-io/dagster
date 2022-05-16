from typing import List

from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import CommandStep


def build_dagit_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":typescript: dagit webapp tests")
        .run(
            "cd js_modules/dagit",
            'echo -e "--- \033[0;32m:Running dagit webapp tests\033[0m"',
            "yarn install",
            "yarn workspace @dagster-io/dagit-core generate-graphql",
            "yarn workspace @dagster-io/dagit-core generate-perms",
            "yarn workspace @dagster-io/dagit-app lint",
            "yarn workspace @dagster-io/dagit-app ts",
            "yarn workspace @dagster-io/dagit-core ts",
            "yarn workspace @dagster-io/dagit-core jest --clearCache",
            "yarn workspace @dagster-io/dagit-core jest --collectCoverage --watchAll=false",
            "yarn workspace @dagster-io/dagit-core check-prettier",
            "yarn workspace @dagster-io/dagit-core check-lint",
            "yarn workspace @dagster-io/ui ts",
            "yarn workspace @dagster-io/ui lint",
            "yarn workspace @dagster-io/ui jest --clearCache",
            "yarn workspace @dagster-io/ui jest",
            "git diff --exit-code",
            # "tox -vv -e py39",
            "mv packages/core/coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(AvailablePythonVersion.get_default())
        .build(),
    ]
