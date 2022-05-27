import os
from glob import glob
from typing import List

from ..defines import GIT_REPO_ROOT
from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import BuildkiteStep, CommandStep, safe_getenv
from .docs import build_docs_steps
from .helm import build_helm_steps
from .packages import build_packages_steps
from .test_images import build_test_image_steps

branch_name = safe_getenv("BUILDKITE_BRANCH")


def build_dagster_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    # "Package" used loosely here to mean roughly "a directory with some python modules". For
    # instances, a directory of unrelated scripts counts as a package. All packages must have a
    # toxfile that defines the tests for that package.
    steps += build_packages_steps()


    return steps


def build_repo_wide_black_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":python-black: black")
        .run("pip install -e python_modules/dagster[black]", "make check_black")
        .on_integration_image(AvailablePythonVersion.get_default())
        .build(),
    ]


def build_repo_wide_isort_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":isort: isort")
        .run("pip install -e python_modules/dagster[isort]", "make check_isort")
        .on_integration_image(AvailablePythonVersion.get_default())
        .build(),
    ]


def build_repo_wide_check_manifest_steps() -> List[CommandStep]:
    published_packages = [
        "python_modules/dagit",
        "python_modules/dagster",
        "python_modules/dagster-graphql",
        *(
            os.path.relpath(p, GIT_REPO_ROOT)
            for p in glob(f"{GIT_REPO_ROOT}/python_modules/libraries/*")
        ),
    ]

    commands = [
        "pip install check-manifest",
        *(f"check-manifest {library}" for library in published_packages),
    ]

    return [
        CommandStepBuilder(":white_check_mark: check-manifest")
        .on_integration_image(AvailablePythonVersion.get_default())
        .run(*commands)
        .build()
    ]


def build_sql_schema_check_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":mysql: mysql-schema")
        .on_integration_image(AvailablePythonVersion.get_default())
        .run("pip install -e python_modules/dagster", "python scripts/check_schemas.py")
        .build()
    ]


def build_graphql_python_client_backcompat_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":graphql: GraphQL Python Client backcompat")
        .on_integration_image(AvailablePythonVersion.get_default())
        .run(
            "pip install -e python_modules/dagster[test] -e python_modules/dagster-graphql -e python_modules/automation",
            "dagster-graphql-client query check",
        )
        .build()
    ]
