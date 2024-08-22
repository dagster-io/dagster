import os
from glob import glob
from typing import List

from dagster_buildkite.defines import GIT_REPO_ROOT
from dagster_buildkite.python_packages import PythonPackages
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.steps.helm import build_helm_steps
from dagster_buildkite.steps.integration import build_integration_steps
from dagster_buildkite.steps.packages import build_library_packages_steps
from dagster_buildkite.steps.test_project import build_test_project_steps
from dagster_buildkite.utils import (
    BuildkiteStep,
    CommandStep,
    GroupStep,
    is_feature_branch,
    is_release_branch,
    safe_getenv,
    skip_if_no_non_docs_markdown_changes,
    skip_if_no_pyright_requirements_txt_changes,
    skip_if_no_python_changes,
    skip_if_no_yaml_changes,
)

branch_name = safe_getenv("BUILDKITE_BRANCH")


def build_repo_wide_steps() -> List[BuildkiteStep]:
    # Other linters may be run in per-package environments because they rely on the dependencies of
    # the target. `check-manifest`, `pyright`, and `ruff` are run for the whole repo at once.
    return [
        *build_check_changelog_steps(),
        *build_repo_wide_check_manifest_steps(),
        *build_repo_wide_pyright_steps(),
        *build_repo_wide_ruff_steps(),
        *build_repo_wide_prettier_steps(),
    ]


def build_dagster_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    # "Package" used loosely here to mean roughly "a directory with some python modules". For
    # instance, a directory of unrelated scripts counts as a package. All packages must have a
    # toxfile that defines the tests for that package.
    steps += build_library_packages_steps()

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


def build_repo_wide_ruff_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":zap: ruff")
        .run(
            "pip install -e python_modules/dagster[ruff] -e python_modules/dagster-pipes",
            "make check_ruff",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_skip(skip_if_no_python_changes())
        .build(),
    ]


def build_repo_wide_prettier_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":prettier: prettier")
        .run(
            "make install_prettier",
            "make check_prettier",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_skip(skip_if_no_yaml_changes() and skip_if_no_non_docs_markdown_changes())
        .build(),
    ]


def build_check_changelog_steps() -> List[CommandStep]:
    branch_name = safe_getenv("BUILDKITE_BRANCH")
    if not is_release_branch(branch_name):
        return []

    release_number = branch_name.split("-", 1)[-1].replace("-", ".")
    return [
        CommandStepBuilder(":memo: changelog")
        .on_test_image(AvailablePythonVersion.get_default())
        .run(f"python scripts/check_changelog.py {release_number}")
        .build()
    ]


def build_repo_wide_pyright_steps() -> List[BuildkiteStep]:
    return [
        GroupStep(
            group=":pyright: pyright",
            key="pyright",
            steps=[
                CommandStepBuilder(":pyright: make pyright")
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    "pip install -U uv",
                    "make install_pyright",
                    "make pyright",
                )
                .on_test_image(AvailablePythonVersion.get_default())
                .with_skip(skip_if_no_python_changes(overrides=["pyright"]))
                .build(),
                CommandStepBuilder(":pyright: make rebuild_pyright_pins")
                .run(
                    "curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y",
                    "pip install -U uv",
                    "make install_pyright",
                    "make rebuild_pyright_pins",
                )
                .on_test_image(AvailablePythonVersion.get_default())
                .with_skip(skip_if_no_pyright_requirements_txt_changes())
                .build(),
            ],
        )
    ]


def build_repo_wide_check_manifest_steps() -> List[CommandStep]:
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
        "pip install check-manifest",
        *(
            f"check-manifest {library}"
            for library in published_packages
            if not library.endswith("CONTRIBUTING.md")  # ignore md file in dir
        ),
    ]

    return [
        CommandStepBuilder(":white_check_mark: check-manifest")
        .on_test_image(AvailablePythonVersion.get_default())
        .run(*commands)
        .with_skip(skip_if_no_python_changes())
        .build()
    ]


def build_sql_schema_check_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":mysql: mysql-schema")
        .on_test_image(AvailablePythonVersion.get_default())
        .run(
            "pip install -e python_modules/dagster -e python_modules/dagster-pipes",
            "python scripts/check_schemas.py",
        )
        .with_skip(skip_mysql_if_no_changes_to_dependencies(["dagster"]))
        .build()
    ]


def build_graphql_python_client_backcompat_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":graphql: GraphQL Python Client backcompat")
        .on_test_image(AvailablePythonVersion.get_default())
        .run(
            "pip install -e python_modules/dagster[test] -e python_modules/dagster-pipes -e"
            " python_modules/dagster-graphql -e python_modules/automation",
            "dagster-graphql-client query check",
        )
        .with_skip(
            skip_graphql_if_no_changes_to_dependencies(["dagster", "dagster-graphql", "automation"])
        )
        .build()
    ]


def skip_mysql_if_no_changes_to_dependencies(dependencies: List[str]):
    if not is_feature_branch():
        return None

    for dependency in dependencies:
        if PythonPackages.get(dependency) in PythonPackages.with_changes:
            return None

    return "Skip unless mysql schemas might have changed"


def skip_graphql_if_no_changes_to_dependencies(dependencies: List[str]):
    if not is_feature_branch():
        return None

    for dependency in dependencies:
        if PythonPackages.get(dependency) in PythonPackages.with_changes:
            return None

    return "Skip unless GraphQL schemas might have changed"
