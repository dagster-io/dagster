from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.utils import skip_if_no_docs_changes


def build_repo_wide_format_docs_step() -> GroupLeafStepConfiguration:
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
        .skip_if(skip_if_no_docs_changes())
        .build()
    )


def build_build_docs_step():
    return (
        add_test_image(CommandStepBuilder("build docs"), AvailablePythonVersion.get_default())
        .run(
            "cd docs",
            "yarn install",
            "yarn test",
            "yarn build-api-docs",
            "yarn build",
        )
        .skip_if(skip_if_no_docs_changes())
        .build()
    )


def build_docstring_validation_step() -> GroupLeafStepConfiguration:
<<<<<<< HEAD
    return (
        add_test_image(
            CommandStepBuilder(":memo: docstring validation", retry_automatically=False),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "uv pip install --system -e python_modules/automation[buildkite]",
            "python -m automation.dagster_docs.main check docstrings --all",
        )
        .build()
=======
    return build_tox_step(
        root_dir="python_modules/automation",
        tox_env=f"py{AvailablePythonVersion.get_default().value.replace('.', '')}",
        base_label="docstring validation",
        command_type="pytest",
        extra_commands_post=["python -m automation.dagster_docs.main check docstrings --all"],
>>>>>>> 34b237331a (Fix python syntax errors in docstring)
    )


def build_docs_steps() -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            name=":book: docs",
            key="docs",
            steps=[
                build_build_docs_step(),
                build_repo_wide_format_docs_step(),
                build_docstring_validation_step(),
            ],
        ).build()
    ]
