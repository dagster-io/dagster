from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.uv import UV_PIN
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.utils import skip_if_no_docs_changes


def build_repo_wide_format_docs_step(ctx: BuildkiteContext) -> GroupLeafStepConfiguration:
    return (
        add_test_image(
            CommandStepBuilder(":notebook: yarn format_check"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "cd docs",
            "yarn install",
            "yarn format_check",
        )
        .skip(skip_if_no_docs_changes(ctx))
        .build()
    )


def build_build_docs_step(ctx: BuildkiteContext):
    return (
        add_test_image(CommandStepBuilder("build docs"), AvailablePythonVersion.get_default())
        .run(
            "cd docs",
            f'pip install -U "{UV_PIN}"',
            "yarn install",
            "yarn test",
            "yarn build-api-docs",
            "yarn build",
        )
        .skip(skip_if_no_docs_changes(ctx))
        .build()
    )


def build_docstring_validation_step() -> GroupLeafStepConfiguration:
    python_version = AvailablePythonVersion.get_default()
    tox_env = f"py{python_version.value.replace('.', '')}"
    return (
        add_test_image(
            CommandStepBuilder(
                f":pytest: docstring validation {python_version.value}", retry_automatically=False
            ),
            python_version,
        )
        .run(
            "cd python_modules/automation",
            f'pip install -U "{UV_PIN}"',
            "uv pip install --system -e .[buildkite]",
            f"echo -e '--- \\033[0;32m:pytest: Running tox env: {tox_env}\\033[0m'",
            f"tox -vv -e {tox_env}",
            "python -m automation.dagster_docs.main check docstrings --all",
        )
        .build()
    )


def build_docs_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            name=":book: docs",
            key="docs",
            steps=[
                build_build_docs_step(ctx),
                build_repo_wide_format_docs_step(ctx),
                build_docstring_validation_step(),
            ],
        ).build()
    ]
