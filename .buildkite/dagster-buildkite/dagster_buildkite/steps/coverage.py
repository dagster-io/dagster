from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.utils import CommandStep

from ..images.versions import BUILDKITE_COVERAGE_IMAGE_VERSION


def build_coverage_step() -> CommandStep:
    return (
        CommandStepBuilder(":coverage:")
        .run(
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            'buildkite-agent artifact download "lcov.*" tmp/',
            "cd tmp",
            "coverage debug sys",
            "coverage debug data",
            "coverage combine",
            # coveralls-lcov is currently not working - fails with:
            # converter.rb:63:in `initialize': No such file or directory @ rb_sysopen - jest/mocks/dagre_layout.worker.ts
            # "coveralls-lcov -v -n lcov.* > coverage.js.json",
            "coveralls",  # add '--merge=coverage.js.json' to report JS coverage
        )
        .on_python_image(
            "buildkite-coverage:py3.8.7-{version}".format(version=BUILDKITE_COVERAGE_IMAGE_VERSION),
            [
                "COVERALLS_REPO_TOKEN",  # exported by /env in ManagedSecretsBucket
                "CI_NAME",
                "CI_BUILD_NUMBER",
                "CI_BUILD_URL",
                "CI_BRANCH",
                "CI_PULL_REQUEST",
            ],
        )
        .build()
    )
