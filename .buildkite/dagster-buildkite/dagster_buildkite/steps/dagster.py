import os

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.packages import get_general_python_step_skip_reason
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.group_step_builder import GroupStepBuilder
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.utils import oss_path
from buildkite_shared.uv import UV_PIN
from dagster_buildkite.steps.helm import build_helm_steps
from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.packages import (
    build_example_packages_steps,
    build_library_packages_steps,
)
from dagster_buildkite.steps.test_project import build_test_project_steps


def build_buildkite_lint_steps() -> list[CommandStepConfiguration]:
    commands = [
        f"cd {oss_path('.')}",
        "pytest .buildkite/buildkite-shared/lints.py",
    ]
    return [CommandStepBuilder(":lint-roller: :buildkite:").run(*commands).on_test_image().build()]


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
        CommandStepBuilder(":zap: ruff", retry_automatically=False)
        .on_test_image()
        .run(
            f"uv pip install --system -e {oss_path('python_modules/dagster')}[ruff] -e {oss_path('python_modules/dagster-pipes')} -e {oss_path('python_modules/libraries/dagster-shared')}",
            f"make -C {oss_path('.')} check_ruff",
        )
        .skip(get_general_python_step_skip_reason(ctx))
        .build(),
    ]


def build_repo_wide_prettier_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder(":prettier: prettier", retry_automatically=False)
        .on_test_image()
        .run(
            f"make -C {oss_path('.')} install_prettier",
            f"make -C {oss_path('.')} check_prettier",
        )
        .skip(_get_prettier_step_skip_reason(ctx))
        .build(),
    ]


def build_check_changelog_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    skip_reason = _get_check_changelog_step_skip_reason(ctx)
    cmd = (
        f"python {oss_path('scripts/check_changelog.py')} {ctx.release_version}"
        if not skip_reason
        else "echo skipped"
    )
    return [
        CommandStepBuilder(":memo: changelog").run(cmd).on_test_image().skip(skip_reason).build(),
    ]


def build_repo_wide_pyright_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            name=":pyright: pyright",
            steps=[
                CommandStepBuilder(":pyright: make pyright", retry_automatically=False)
                .on_test_image()
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    f'pip install -U "{UV_PIN}"',
                    "uv venv",
                    "source .venv/bin/activate",
                    f"make -C {oss_path('.')} install_pyright",
                    f"make -C {oss_path('.')} pyright",
                )
                .skip(get_general_python_step_skip_reason(ctx, other_paths=["pyright"]))
                # Run on a larger instance
                .on_queue(BuildkiteQueue.DOCKER)
                .build(),
                CommandStepBuilder(":pyright: make rebuild_pyright_pins", retry_automatically=False)
                .on_test_image()
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    f'pip install -U "{UV_PIN}"',
                    "uv venv",
                    "source .venv/bin/activate",
                    f"make -C {oss_path('.')} install_pyright",
                    f"make -C {oss_path('.')} rebuild_pyright_pins",
                )
                .skip(_get_pyright_pin_step_skip_reason(ctx))
                .build(),
            ],
            key="pyright",
        ).build()
    ]


def build_sql_schema_check_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder(":mysql: mysql-schema")
        .run(
            f"uv pip install --system -e {oss_path('python_modules/dagster')} -e {oss_path('python_modules/dagster-pipes')} -e {oss_path('python_modules/libraries/dagster-shared')}",
            f"python {oss_path('scripts/check_schemas.py')}",
        )
        .skip(_get_sql_schema_check_skip_reason(ctx, ["dagster"]))
        .on_test_image()
        .build(),
    ]


def build_graphql_python_client_backcompat_steps(
    ctx: BuildkiteContext,
) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder(":graphql: GraphQL Python Client backcompat")
        .run(
            f"uv pip install --system -e {oss_path('python_modules/dagster')}[test] -e {oss_path('python_modules/dagster-pipes')}"
            f" -e {oss_path('python_modules/libraries/dagster-shared')} -e {oss_path('python_modules/dagster-graphql')}"
            f" -e {oss_path('python_modules/automation')}",
            "dagster-graphql-client query check",
        )
        .skip(
            _get_graphql_python_client_backcompat_skip_reason(
                ctx, ["dagster", "dagster-graphql", "automation"]
            )
        )
        .on_test_image()
        .build()
    ]


# ########################
# ##### SKIP HELPERS
# ########################


def _get_sql_schema_check_skip_reason(
    ctx: BuildkiteContext, sql_schema_dependencies: list[str]
) -> str | None:
    if ctx.config.no_skip:
        return None
    elif not ctx.is_feature_branch:
        return None
    elif any(ctx.has_package_changes(dep) for dep in sql_schema_dependencies):
        return None
    return "No MySQL schema changes"


def _get_graphql_python_client_backcompat_skip_reason(
    ctx: BuildkiteContext, gql_schema_dependencies: list[str]
) -> str | None:
    if ctx.config.no_skip:
        return None
    elif not ctx.is_feature_branch:
        return None
    elif any(ctx.has_package_changes(dep) for dep in gql_schema_dependencies):
        return None
    return "No GraphQL schema changes"


def _get_pyright_pin_step_skip_reason(ctx: BuildkiteContext) -> str | None:
    if ctx.config.no_skip:
        return None
    elif not ctx.is_feature_branch:
        return None
    elif ctx.has_pyright_requirements_txt_changes():
        return None
    return "No pyright requirements.txt changes"


def _get_prettier_step_skip_reason(ctx: BuildkiteContext) -> str | None:
    if ctx.config.no_skip:
        return None
    elif not ctx.is_feature_branch:
        return None
    elif ctx.has_yaml_changes():
        return None
    elif ctx.has_non_docs_markdown_changes():
        return None
    return "No yaml changes or markdown changes outside docs"


def _get_check_changelog_step_skip_reason(ctx: BuildkiteContext) -> str | None:
    if not ctx.is_release_branch:
        return "Not a release branch"
    return None
