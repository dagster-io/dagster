"""Tests for the dagster pipeline CLI entry point and package change detection."""

from pathlib import Path
from unittest.mock import patch

import pytest
from buildkite_shared.context import PythonPackage, discover_python_packages
from buildkite_shared.test_utils import assert_valid_pipeline_yaml, get_step_skip
from buildkite_shared.utils import oss_path
from dagster_buildkite.cli import dagster
from dagster_buildkite.defines import GIT_REPO_ROOT
from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps
from dagster_buildkite_tests.helpers import get_test_buildkite_context
from pytest import CaptureFixture

# ########################
# ##### FIXTURES
# ########################


@pytest.fixture(autouse=True)
def _chdir_to_repo_root(monkeypatch):
    monkeypatch.chdir(GIT_REPO_ROOT)


@pytest.fixture(scope="session")
def packages() -> dict[str, PythonPackage]:
    return {pkg.name: pkg for pkg in sorted(discover_python_packages(Path(GIT_REPO_ROOT)))}


# ########################
# ##### HELPERS
# ########################


def _build_steps(changed_files, packages):
    ctx = get_test_buildkite_context(changed_files=changed_files, packages=packages)
    return build_dagster_oss_main_steps(ctx)


# ########################
# ##### TESTS
# ########################


def test_dagster_produces_valid_yaml(capsys: CaptureFixture[str]):
    ctx = get_test_buildkite_context()
    with patch("dagster_buildkite.cli.BuildkiteContext.create", return_value=ctx):
        dagster()
    assert_valid_pipeline_yaml(capsys.readouterr().out)


def test_python_package_change_detection(packages):
    # No changes: packages are skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "dagster") is not None
    assert get_step_skip(steps, "dagster-graphql") is not None

    # Source change runs own package
    steps = _build_steps(
        [oss_path("python_modules/dagster-graphql/dagster_graphql/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster-graphql") is None

    # Source change runs direct dependent
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster-graphql") is None

    # Source change runs transitive dependent (dagster-pipes -> dagster -> dagster-graphql)
    steps = _build_steps(
        [oss_path("python_modules/dagster-pipes/dagster_pipes/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster") is None
    assert get_step_skip(steps, "dagster-graphql") is None

    # Test-only change runs own package but not dependents
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster_tests/some_test.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster") is None
    assert get_step_skip(steps, "dagster-graphql") is not None


def test_docs_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "docs") is not None

    # Docs file change: runs
    steps = _build_steps([oss_path("docs/content/some_page.mdx")], packages)
    assert get_step_skip(steps, "docs") is None


def test_helm_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "helm") is not None

    # Helm file change: runs
    steps = _build_steps([oss_path("helm/dagster/values.yaml")], packages)
    assert get_step_skip(steps, "helm") is None


def test_pyright_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "pyright") is not None

    # Python file change: runs
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "pyright") is None


def test_prettier_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "prettier") is not None

    # YAML change: runs
    steps = _build_steps([oss_path("some_config.yaml")], packages)
    assert get_step_skip(steps, "prettier") is None

    # Python-only change: still skipped
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "prettier") is not None


def test_ui_components_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "dagster-ui-components") is not None

    # ui-components JS change: runs
    steps = _build_steps(
        [oss_path("js_modules/ui-components/src/some_file.ts")],
        packages,
    )
    assert get_step_skip(steps, "dagster-ui-components") is None

    # Python-only change: still skipped
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster-ui-components") is not None


def test_ui_core_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "dagster-ui-core") is not None

    # JS change: runs
    steps = _build_steps(
        [oss_path("js_modules/dagit/src/some_file.ts")],
        packages,
    )
    assert get_step_skip(steps, "dagster-ui-core") is None

    # dagster-graphql source change: runs (graphql schema may change)
    steps = _build_steps(
        [oss_path("python_modules/dagster-graphql/dagster_graphql/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster-ui-core") is None

    # Unrelated change (no JS, no graphql): still skipped
    steps = _build_steps(
        [oss_path("python_modules/libraries/dagster-aws/dagster_aws/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "dagster-ui-core") is not None


def test_sql_schema_check_steps(packages):
    # No changes: skipped
    steps = _build_steps([], packages)
    assert get_step_skip(steps, "mysql-schema") is not None

    # dagster source change: runs
    steps = _build_steps(
        [oss_path("python_modules/dagster/dagster/some_module.py")],
        packages,
    )
    assert get_step_skip(steps, "mysql-schema") is None
