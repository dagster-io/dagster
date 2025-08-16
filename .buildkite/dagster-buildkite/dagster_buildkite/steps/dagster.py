import os
from glob import glob

from buildkite_shared.environment import is_release_branch, safe_getenv
from buildkite_shared.python_packages import PythonPackages
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.group_step_builder import GroupStepBuilder
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.uv import UV_PIN
from dagster_buildkite.defines import GIT_REPO_ROOT
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.steps.helm import build_helm_steps
from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.packages import (
    build_example_packages_steps,
    build_library_packages_steps,
)
from dagster_buildkite.steps.test_project import build_test_project_steps
from dagster_buildkite.utils import (
    is_feature_branch,
    skip_if_no_non_docs_markdown_changes,
    skip_if_no_pyright_requirements_txt_changes,
    skip_if_no_python_changes,
    skip_if_no_yaml_changes,
)

branch_name = safe_getenv("BUILDKITE_BRANCH")


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


def build_repo_wide_steps() -> list[StepConfiguration]:
    # Other linters may be run in per-package environments because they rely on the dependencies of
    # the target. `check-manifest`, `pyright`, and `ruff` are run for the whole repo at once.
    return [
        *build_check_changelog_steps(),
        *build_repo_wide_check_manifest_steps(),
        *build_repo_wide_pyright_steps(),
        *build_repo_wide_ruff_steps(),
        *build_repo_wide_prettier_steps(),
        *build_buildkite_lint_steps(),
    ]


def build_dagster_steps() -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []

    # "Package" used loosely here to mean roughly "a directory with some python modules". For
    # instance, a directory of unrelated scripts counts as a package. All packages must have a
    # toxfile that defines the tests for that package.
    steps += build_library_packages_steps()

    steps += build_example_packages_steps()

    steps += build_helm_steps()
    steps += build_sql_schema_check_steps()
    steps += build_graphql_python_client_backcompat_steps()
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        steps += build_integration_steps()

    # Build images containing the dagster-test sample project. This is a dependency of certain
    # dagster core and extension lib tests. Run this after we build our library package steps
    # because need to know whether it's a dependency of any of them.
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        steps += build_test_project_steps()

    return steps


def build_repo_wide_ruff_steps() -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":zap: ruff", retry_automatically=False),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "uv pip install --system -e python_modules/dagster[ruff] -e python_modules/dagster-pipes -e python_modules/libraries/dagster-shared",
            "make check_ruff",
        )
        .skip_if(skip_if_no_python_changes())
        .build(),
    ]


def build_repo_wide_prettier_steps() -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":prettier: prettier", retry_automatically=False),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "make install_prettier",
            "make check_prettier",
        )
        .skip_if(skip_if_no_yaml_changes() and skip_if_no_non_docs_markdown_changes())
        .build(),
    ]


def build_check_changelog_steps() -> list[CommandStepConfiguration]:
    branch_name = safe_getenv("BUILDKITE_BRANCH")
    if not is_release_branch(branch_name):
        return []

    release_number = branch_name.split("-", 1)[-1].replace("-", ".")
    return [
        add_test_image(
            CommandStepBuilder(":memo: changelog").run(
                f"python scripts/check_changelog.py {release_number}"
            ),
            AvailablePythonVersion.get_default(),
        ).build(),
    ]


def build_repo_wide_pyright_steps() -> list[StepConfiguration]:
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
                .skip_if(skip_if_no_python_changes(overrides=["pyright"]))
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
                .skip_if(skip_if_no_pyright_requirements_txt_changes())
                .build(),
            ],
            key="pyright",
        ).build()
    ]


def build_repo_wide_check_manifest_steps() -> list[CommandStepConfiguration]:
    published_packages = [
        "python_modules/dagit",
        "python_modules/dagster",
        "python_modules/dagster-graphql",
        "python_modules/dagster-webserver",
        *(
            os.path.relpath(p, GIT_REPO_ROOT)
            for p in glob(f"{GIT_REPO_ROOT}/python_modules/libraries/*")
        ),
    ]

    commands = [
        "uv pip install --system check-manifest",
        *(
            f"check-manifest {library}"
            for library in published_packages
            if not library.endswith("CONTRIBUTING.md")  # ignore md file in dir
        ),
    ]

    return [
        add_test_image(
            CommandStepBuilder(":white_check_mark: check-manifest")
            .run(*commands)
            .skip_if(skip_if_no_python_changes()),
            AvailablePythonVersion.get_default(),
        ).build(),
    ]


def build_sql_schema_check_steps() -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":mysql: mysql-schema")
            .run(
                "uv pip install --system -e python_modules/dagster -e python_modules/dagster-pipes -e python_modules/libraries/dagster-shared",
                "python scripts/check_schemas.py",
            )
            .skip_if(skip_mysql_if_no_changes_to_dependencies(["dagster"])),
            AvailablePythonVersion.get_default(),
        ).build(),
    ]


def build_graphql_python_client_backcompat_steps() -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":graphql: GraphQL Python Client backcompat")
            .run(
                "uv pip install --system -e python_modules/dagster[test] -e python_modules/dagster-pipes"
                " -e python_modules/libraries/dagster-shared -e python_modules/dagster-graphql"
                " -e python_modules/automation",
                "dagster-graphql-client query check",
            )
            .skip_if(
                skip_graphql_if_no_changes_to_dependencies(
                    ["dagster", "dagster-graphql", "automation"]
                )
            ),
            AvailablePythonVersion.get_default(),
        ).build()
    ]


def skip_mysql_if_no_changes_to_dependencies(dependencies: list[str]):
    if not is_feature_branch():
        return None

    for dependency in dependencies:
        if PythonPackages.get(dependency) in PythonPackages.with_changes:
            return None

    return "Skip unless mysql schemas might have changed"


def skip_graphql_if_no_changes_to_dependencies(dependencies: list[str]):
    if not is_feature_branch():
        return None

    for dependency in dependencies:
        if PythonPackages.get(dependency) in PythonPackages.with_changes:
            return None

    return "Skip unless GraphQL schemas might have changed"
