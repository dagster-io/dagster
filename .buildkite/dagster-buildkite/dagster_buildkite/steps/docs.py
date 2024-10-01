from typing import List

from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.steps.packages import (
    build_dagster_ui_screenshot_steps,
    build_example_packages_steps,
)
from dagster_buildkite.steps.tox import build_tox_step
from dagster_buildkite.utils import (
    BuildkiteLeafStep,
    BuildkiteStep,
    GroupStep,
    skip_if_no_docs_changes,
)


def build_docs_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    docs_steps: List[BuildkiteLeafStep] = [
        # Make sure snippets in built docs match source.
        # If this test is failing, it's because you may have either:
        #   (1) Updated the code that is referenced by a literal include in the documentation
        #   (2) Directly modified the inline snapshot of a literalinclude instead of updating
        #       the underlying code that the literalinclude is pointing to.
        # To fix this, run 'make mdx-format' in the /docs directory to update the snapshots.
        # Be sure to check the diff to make sure the literalincludes are as you expect them."
        CommandStepBuilder("docs code snippets")
        .run("cd docs", "make next-dev-install", "make mdx-format", "git diff --exit-code")
        .with_skip(skip_if_no_docs_changes())
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
        # Make sure the docs site can build end-to-end.
        CommandStepBuilder("docs next")
        .run(
            "cd docs/next",
            "yarn install",
            "yarn test",
            "yarn build-master",
        )
        .with_skip(skip_if_no_docs_changes())
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
        # Make sure docs sphinx build runs.
        CommandStepBuilder("docs apidoc build")
        .run(
            "cd docs",
            "pip install -U uv",
            "make apidoc-build",
            # "echo '--- Checking git diff (ignoring whitespace) after docs build...'",
            # "git diff --ignore-all-space --stat",
            # "git diff --exit-code --ignore-all-space --no-patch",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
        # Verify screenshot integrity.
        build_tox_step("docs", "audit-screenshots", skip_reason=skip_if_no_docs_changes()),
    ]

    steps += [
        GroupStep(
            group=":book: docs",
            key="docs",
            steps=docs_steps,
        )
    ]

    steps += build_example_packages_steps()
    steps += build_dagster_ui_screenshot_steps()

    return steps
