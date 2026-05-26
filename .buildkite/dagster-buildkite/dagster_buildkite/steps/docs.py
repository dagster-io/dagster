import logging

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.utils import oss_path


def build_repo_wide_format_docs_step(ctx: BuildkiteContext) -> GroupLeafStepConfiguration:
    return (
        CommandStepBuilder("yarn-format-check", [":notebook:"])
        .on_test_image(env=["COREPACK_ENABLE_DOWNLOAD_PROMPT=0"])
        .run(
            f"cd {oss_path('docs')}",
            "corepack enable",
            "yarn install",
            "yarn format_check",
        )
        .skip(_get_docs_step_skip_reason(ctx))
        .build()
    )


def build_build_docs_step(ctx: BuildkiteContext) -> GroupLeafStepConfiguration:
    return (
        CommandStepBuilder("build-docs")
        .on_test_image(env=["COREPACK_ENABLE_DOWNLOAD_PROMPT=0"])
        .run(
            f"cd {oss_path('docs')}",
            "corepack enable",
            "yarn install",
            "yarn test",
            "yarn lint-check",
            "yarn build-api-docs",
            "yarn build",
        )
        .skip(_get_docs_step_skip_reason(ctx))
        .build()
    )


def build_docstring_validation_step(ctx: BuildkiteContext) -> GroupLeafStepConfiguration:
    python_version = AvailablePythonVersion.get_default()
    return (
        CommandStepBuilder(
            f"docstring-validation-{python_version.value.replace('.', '-')}",
            [":pytest:"],
        )
        .on_test_image(python_version.value)
        .run(
            f"cd {oss_path('python_modules/automation')}",
            "uv pip install --system -e .[buildkite]",
            "python -m automation.dagster_docs.main check docstrings --all",
        )
        .skip(_get_docstring_validation_skip_reason(ctx))
        .build()
    )


def _get_docstring_validation_skip_reason(ctx: BuildkiteContext) -> str | None:
    if ctx.config.no_skip:
        return None
    if not ctx.is_feature_branch:
        return None
    if ctx.has_python_changes():
        return None
    return "No python changes"


def build_docs_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            "docs",
            [":book:"],
            steps=[
                build_build_docs_step(ctx),
                build_repo_wide_format_docs_step(ctx),
                build_docstring_validation_step(ctx),
            ],
        ).build()
    ]


def _get_docs_step_skip_reason(ctx: BuildkiteContext) -> str | None:
    if ctx.config.no_skip:
        return None

    if "BUILDKITE_DOCS" in ctx.message:
        return None

    if not ctx.is_feature_branch:
        return None

    # If anything changes in the docs directory
    if ctx.has_docs_changes():
        logging.info("Run docs steps because files in the dagster-oss/docs directory changed")
        return None

    # If anything changes in the examples directory. This is where our docs snippets live.
    if any(oss_path("examples") in path.parents for path in ctx.changed_files):
        logging.info("Run docs steps because files in the dagster-oss/examples directory changed")
        return None

    return "No docs changes"
