"""Test the prerelease-package pipeline CLI entry point produces valid YAML."""

from unittest.mock import patch

from buildkite_shared.test_utils import assert_valid_pipeline_yaml
from dagster_buildkite.cli import prerelease_package
from dagster_buildkite_tests.helpers import get_test_buildkite_context
from pytest import CaptureFixture


def test_prerelease_package_produces_valid_yaml(capsys: CaptureFixture[str]):
    ctx = get_test_buildkite_context()
    with patch("dagster_buildkite.cli.BuildkiteContext.create", return_value=ctx):
        prerelease_package()
    assert_valid_pipeline_yaml(capsys.readouterr().out)
