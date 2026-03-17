"""Step inspection helpers for Buildkite pipeline tests."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from buildkite_shared.context import BuildkiteContext

_ENV_DEFAULTS = {
    "BUILDKITE_BRANCH": "test-feature-branch",
    "BUILDKITE_COMMIT": "abc1234567890123abc1234567890123abcd1234",
    "BUILDKITE_MESSAGE": "test commit message",
    "BUILDKITE_BUILD_AUTHOR": "test-author",
    "BUILDKITE_SOURCE": "webhook",
    "BUILDKITE_PIPELINE_SLUG": "dagster",
}


def get_test_buildkite_context(
    env: dict[str, str] = {}, changed_files: Iterable[Path] | None = None
) -> BuildkiteContext:
    """Return a BuildkiteContext with test data."""
    return BuildkiteContext.create(
        env={**_ENV_DEFAULTS, **env},
        changed_files=changed_files,
    )


def assert_valid_pipeline_yaml(captured_out: str) -> dict[str, Any]:
    """Parse captured stdout as YAML and verify basic pipeline structure."""
    pipeline = yaml.safe_load(captured_out)
    assert isinstance(pipeline, dict), "output should be a YAML dict"
    assert "steps" in pipeline, "pipeline should have 'steps' key"
    assert isinstance(pipeline["steps"], list), "'steps' should be a list"
    assert "env" in pipeline, "pipeline should have 'env' key"
    assert "CI_NAME" in pipeline["env"]
    assert "CI_BRANCH" in pipeline["env"]
    return pipeline
