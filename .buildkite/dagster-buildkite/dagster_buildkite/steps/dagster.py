import os

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.packages import get_general_python_step_skip_reason
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.utils import oss_path
from dagster_buildkite.steps.helm import build_helm_steps
from dagster_buildkite.steps.integration import (
    build_azure_live_test_suite_steps,
    build_backcompat_suite_steps,
    build_celery_k8s_suite_steps,
    build_daemon_suite_steps,
    build_k8s_suite_steps,
)
from dagster_buildkite.steps.packages import (
    PackageSpec,
    build_example_packages_steps,
    build_library_packages_steps,
)
from dagster_buildkite.steps.test_project import build_test_project_steps


def build_buildkite_lint_steps() -> list[CommandStepConfiguration]:
    commands = [
        f"cd {oss_path('.')}",
        "pytest .buildkite/buildkite-shared/lints.py",
    ]
    return [
        CommandStepBuilder("buildkite-lints", [":lint-roller:"])
        .run(*commands)
        .on_test_image()
        .build()
    ]


def build_repo_wide_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    # Other linters may be run in per-package environments because they rely on the dependencies of
    # the target. `pyright` and `ruff` are run for the whole repo at once.
    return [
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
        # Bundle the test-project image build with every suite that depends on
        # it into one Buildkite group so reviewers can scan the docker-dependent
        # block as a unit (and the internal pipeline can attach a status gate
        # to it). Suites that do not depend on the image stay outside.
        steps += build_test_project_and_dependents_group(ctx)
        steps += PackageSpec(
            oss_path(os.path.join("integration_tests", "python_modules", "dagster-k8s-test-infra")),
        ).build_steps(ctx)
        steps += build_azure_live_test_suite_steps(ctx)

    return steps


def build_test_project_and_dependents_group(
    ctx: BuildkiteContext,
) -> list[StepConfiguration]:
    """Wrap the test-project Docker image build and every integration suite that
    depends on it into one Buildkite group.

    Buildkite forbids nested groups, so the per-suite groups produced by
    PackageSpec are flattened to their leaf command steps. Each leaf still
    carries the suite name in its label.

    Order matters: the suite builders mutate `build_test_project_for` via
    `test_project_depends_fn`, and `build_test_project_steps()` reads that
    set, so suites must be assembled before the image build.
    """
    dependent_steps: list[StepConfiguration] = []
    dependent_steps += build_backcompat_suite_steps(ctx)
    dependent_steps += build_celery_k8s_suite_steps(ctx)
    dependent_steps += build_k8s_suite_steps(ctx)
    dependent_steps += build_daemon_suite_steps(ctx)

    image_steps = build_test_project_steps()

    leaves: list[GroupLeafStepConfiguration] = []
    for s in [*image_steps, *dependent_steps]:
        if "group" in s:
            leaves.extend(s["steps"])
        else:
            leaves.append(s)

    return [
        GroupStepBuilder(
            "test-project-and-dependents",
            [":docker:"],
            steps=leaves,
        ).build()
    ]


def build_repo_wide_ruff_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder("ruff", [":zap:"])
        .on_test_image()
        .run(
            f"uv pip install --system -e {oss_path('python_modules/dagster')}[ruff] -e {oss_path('python_modules/dagster-pipes')} -e {oss_path('python_modules/libraries/dagster-shared')}",
            f"just -f {oss_path('justfile')} check_ruff",
        )
        .skip(get_general_python_step_skip_reason(ctx))
        .build(),
    ]


def build_repo_wide_prettier_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder("prettier", [":prettier:"])
        .on_test_image()
        .run(
            f"just -f {oss_path('justfile')} install_prettier",
            f"just -f {oss_path('justfile')} check_prettier",
        )
        .skip(_get_prettier_step_skip_reason(ctx))
        .build(),
    ]


def build_repo_wide_pyright_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    return [
        GroupStepBuilder(
            "pyright-ty",
            [":pyright:", ":ty:"],
            steps=[
                CommandStepBuilder("pyright", [":pyright:"])
                .on_test_image()
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    "uv venv",
                    "source .venv/bin/activate",
                    f"just -f {oss_path('justfile')} install_pyright",
                    # Cap Node.js heap at 4GB. Without this, pyright (which runs
                    # on Node.js) can exceed physical memory under pressure,
                    # causing V8's garbage collector to thrash on swapped pages
                    # and hang silently for the full job timeout. With the cap,
                    # it OOMs immediately with a clear error instead.
                    "export NODE_OPTIONS=--max-old-space-size=4096",
                    f"just -f {oss_path('justfile')} pyright",
                )
                .skip(get_general_python_step_skip_reason(ctx, other_paths=["pyright"]))
                # Run on a larger instance
                .on_queue(BuildkiteQueue.DOCKER)
                .build(),
                CommandStepBuilder("pyright-rebuild-pyright-pins", [":pyright:"])
                .on_test_image()
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    "uv venv",
                    "source .venv/bin/activate",
                    f"just -f {oss_path('justfile')} install_pyright",
                    # Cap Node.js heap at 4GB. Without this, pyright (which runs
                    # on Node.js) can exceed physical memory under pressure,
                    # causing V8's garbage collector to thrash on swapped pages
                    # and hang silently for the full job timeout. With the cap,
                    # it OOMs immediately with a clear error instead.
                    "export NODE_OPTIONS=--max-old-space-size=4096",
                    f"just -f {oss_path('justfile')} rebuild_pyright_pins",
                )
                .skip(_get_pyright_pin_step_skip_reason(ctx))
                # Run on a larger instance
                .on_queue(BuildkiteQueue.DOCKER)
                .build(),
                CommandStepBuilder("ty", [":ty:"])
                .on_test_image()
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    f"just -f {oss_path('justfile')} ty",
                )
                .skip(get_general_python_step_skip_reason(ctx, other_paths=["pyright"]))
                # Run on a larger instance
                .on_queue(BuildkiteQueue.DOCKER)
                .build(),
            ],
        ).build()
    ]


def build_sql_schema_check_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder("mysql-schema", [":mysql:"])
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
        CommandStepBuilder("graphql-python-client-backcompat", [":graphql:"])
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
