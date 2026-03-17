"""Test the dagster pipeline CLI entry point produces valid YAML."""

from unittest.mock import patch

from dagster_buildkite.cli import dagster
from dagster_buildkite_tests.helpers import assert_valid_pipeline_yaml, get_test_buildkite_context
from pytest import CaptureFixture


def test_dagster_produces_valid_yaml(capsys: CaptureFixture[str]):
    ctx = get_test_buildkite_context()
    with patch("dagster_buildkite.cli.BuildkiteContext.create", return_value=ctx):
        dagster()
    assert_valid_pipeline_yaml(capsys.readouterr().out)
