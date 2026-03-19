"""Tests for the dagster pipeline CLI entry point and package change detection."""

from unittest.mock import patch

import pytest
from buildkite_shared.test_utils import assert_valid_pipeline_yaml, get_step_skip, oss_path
from dagster_buildkite.cli import dagster
from dagster_buildkite.defines import GIT_REPO_ROOT
from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps
from dagster_buildkite_tests.helpers import get_test_buildkite_context
from pytest import CaptureFixture


@pytest.fixture(autouse=True)
def _chdir_to_repo_root(monkeypatch):
    monkeypatch.chdir(GIT_REPO_ROOT)


def test_dagster_produces_valid_yaml(capsys: CaptureFixture[str]):
    ctx = get_test_buildkite_context()
    with patch("dagster_buildkite.cli.BuildkiteContext.create", return_value=ctx):
        dagster()
    assert_valid_pipeline_yaml(capsys.readouterr().out)


def test_source_change_runs_own_package():
    ctx = get_test_buildkite_context(
        changed_files=[oss_path("python_modules/dagster-graphql/dagster_graphql/some_module.py")]
    )
    steps = build_dagster_oss_main_steps(ctx)
    assert get_step_skip(steps, "dagster-graphql") is None


def test_source_change_runs_dependent_package():
    ctx = get_test_buildkite_context(
        changed_files=[oss_path("python_modules/dagster/dagster/some_module.py")],
    )
    steps = build_dagster_oss_main_steps(ctx)
    # dagster-graphql depends on dagster, so a dagster source change should trigger it
    assert get_step_skip(steps, "dagster-graphql") is None


def test_test_change_runs_own_package():
    ctx = get_test_buildkite_context(
        changed_files=[
            oss_path("python_modules/dagster-graphql/dagster_graphql_tests/some_test.py")
        ],
    )
    steps = build_dagster_oss_main_steps(ctx)
    assert get_step_skip(steps, "dagster-graphql") is None


def test_test_change_does_not_run_dependent_package():
    # Change only a test file in dagster. dagster-graphql depends on dagster,
    # but a test-only change should not propagate downstream.
    ctx = get_test_buildkite_context(
        changed_files=[oss_path("python_modules/dagster/dagster_tests/some_test.py")],
    )
    steps = build_dagster_oss_main_steps(ctx)
    assert get_step_skip(steps, "dagster") is None  # own package still runs
    assert get_step_skip(steps, "dagster-graphql") is not None  # downstream does not
