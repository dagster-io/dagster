"""Step inspection helpers for Buildkite pipeline tests."""

from collections.abc import Iterable
from pathlib import Path

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
