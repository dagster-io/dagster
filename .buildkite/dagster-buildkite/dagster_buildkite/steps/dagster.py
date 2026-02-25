import os

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.group_step_builder import GroupStepBuilder
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.uv import UV_PIN
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.steps.helm import build_helm_steps
from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.packages import (
    build_example_packages_steps,
    build_library_packages_steps,
)
from dagster_buildkite.steps.test_project import build_test_project_steps
from dagster_buildkite.utils import (
    skip_if_no_non_docs_markdown_changes,
    skip_if_no_pyright_requirements_txt_changes,
    skip_if_no_python_changes,
    skip_if_no_yaml_changes,
)


def build_buildkite_lint_steps() -> list[CommandStepConfiguration]:
    commands = [
        "pytest .buildkite/buildkite-shared/lints.py",
    ]
    return [
        add_test_image(
            CommandStepBuilder(":lint-roller: :buildkite:").run(*commands),
            AvailablePythonVersion.get_default(),
        ).build()
    ]


def build_repo_wide_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    # Other linters may be run in per-package environments because they rely on the dependencies of
    # the target. `pyright` and `ruff` are run for the whole repo at once.
    return [
        *build_check_changelog_steps(ctx),
        *build_repo_wide_pyright_steps(ctx),
        *build_repo_wide_ruff_steps(ctx),
        *build_repo_wide_prettier_steps(ctx),
        *build_buildkite_lint_steps(),
    ]


def build_dagster_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []

    # "Package" used loosely here to mean roughly "a directory with some python modules". For
    # instance, a directory of unrelated scripts counts as a package. All packages must have a
    # toxfile that defines the tests for that package.
    steps += build_library_packages_steps(ctx)

    steps += build_example_packages_steps(ctx)

    steps += build_helm_steps(ctx)
    steps += build_sql_schema_check_steps(ctx)
    steps += build_graphql_python_client_backcompat_steps(ctx)
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        steps += build_integration_steps(ctx)

    # Build images containing the dagster-test sample project. This is a dependency of certain
    # dagster core and extension lib tests. Run this after we build our library package steps
    # because need to know whether it's a dependency of any of them.
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        steps += build_test_project_steps()

    return steps


def build_repo_wide_ruff_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":zap: ruff", retry_automatically=False),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "uv pip install --system -e python_modules/dagster[ruff] -e python_modules/dagster-pipes -e python_modules/libraries/dagster-shared",
            "make check_ruff",
        )
        .skip(skip_if_no_python_changes(ctx))
        .build(),
    ]


def build_repo_wide_prettier_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":prettier: prettier", retry_automatically=False),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "make install_prettier",
            "make check_prettier",
        )
        .skip(skip_if_no_yaml_changes(ctx) and skip_if_no_non_docs_markdown_changes(ctx))
        .build(),
    ]


def build_check_changelog_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    if not ctx.is_release_branch:
        return []

    return [
        add_test_image(
            CommandStepBuilder(":memo: changelog").run(
                f"python scripts/check_changelog.py {ctx.release_version}"
            ),
            AvailablePythonVersion.get_default(),
        ).build(),
    ]


def build_repo_wide_pyright_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            name=":pyright: pyright",
            steps=[
                add_test_image(
                    CommandStepBuilder(":pyright: make pyright", retry_automatically=False),
                    AvailablePythonVersion.get_default(),
                )
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    f'pip install -U "{UV_PIN}"',
                    "uv venv",
                    "source .venv/bin/activate",
                    "make install_pyright",
                    "make pyright",
                )
                .skip(skip_if_no_python_changes(ctx, overrides=["pyright"]))
                # Run on a larger instance
                .on_queue(BuildkiteQueue.DOCKER)
                .build(),
                add_test_image(
                    CommandStepBuilder(
                        ":pyright: make rebuild_pyright_pins", retry_automatically=False
                    ),
                    AvailablePythonVersion.get_default(),
                )
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    f'pip install -U "{UV_PIN}"',
                    "uv venv",
                    "source .venv/bin/activate",
                    "make install_pyright",
                    "make rebuild_pyright_pins",
                )
                .skip(skip_if_no_pyright_requirements_txt_changes(ctx))
                .build(),
            ],
            key="pyright",
        ).build()
    ]


def build_sql_schema_check_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":mysql: mysql-schema")
            .run(
                "uv pip install --system -e python_modules/dagster -e python_modules/dagster-pipes -e python_modules/libraries/dagster-shared",
                "python scripts/check_schemas.py",
            )
            .skip(skip_mysql_if_no_changes_to_dependencies(ctx, ["dagster"])),
            AvailablePythonVersion.get_default(),
        ).build(),
    ]


def build_graphql_python_client_backcompat_steps(
    ctx: BuildkiteContext,
) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":graphql: GraphQL Python Client backcompat")
            .run(
                "uv pip install --system -e python_modules/dagster[test] -e python_modules/dagster-pipes"
                " -e python_modules/libraries/dagster-shared -e python_modules/dagster-graphql"
                " -e python_modules/automation",
                "dagster-graphql-client query check",
            )
            .skip(
                skip_graphql_if_no_changes_to_dependencies(
                    ctx, ["dagster", "dagster-graphql", "automation"]
                )
            ),
            AvailablePythonVersion.get_default(),
        ).build()
    ]


def skip_mysql_if_no_changes_to_dependencies(ctx: BuildkiteContext, dependencies: list[str]):
    if not ctx.is_feature_branch:
        return None

    for dependency in dependencies:
        if ctx.python_packages.get(dependency) in ctx.python_packages.with_changes:
            return None

    return "Skip unless mysql schemas might have changed"


def skip_graphql_if_no_changes_to_dependencies(ctx: BuildkiteContext, dependencies: list[str]):
    if not ctx.is_feature_branch:
        return None

    for dependency in dependencies:
        if ctx.python_packages.get(dependency) in ctx.python_packages.with_changes:
            return None

    return "Skip unless GraphQL schemas might have changed"
