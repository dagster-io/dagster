"""Tests for buildkite_shared.step_builders.slug."""

import pytest
from buildkite_shared.step_builders.slug import slugify_label


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        (":robot_face: AI analysis", "ai-analysis"),
        (":pytest: dagster-cloud-cli 3.12", "dagster-cloud-cli-3-12"),
        (":pytest: dagster (1/2) cli_tests 3.12", "dagster-1-2-cli-tests-3-12"),
        (":zap: ruff (oss)", "ruff-oss"),
        ("Honeycomb Trace", "honeycomb-trace"),
        (":white_check_mark: required-gate", "required-gate"),
        (":docker: docker-dependent-gate", "docker-dependent-gate"),
        (":rocket: publish static resources", "publish-static-resources"),
        (":robot_face: dogfood cypress tests", "dogfood-cypress-tests"),
        (":notebook: yarn format_check", "yarn-format-check"),
        # Multiple emoji shortcodes get stripped.
        (":zap: :test_tube: test-project + dependents", "test-project-dependents"),
        # Underscores in label become hyphens.
        ("dogfood_rollout_status", "dogfood-rollout-status"),
        # Leading/trailing whitespace and runs of separators collapse.
        ("  :pytest:   foo   bar  ", "foo-bar"),
    ],
)
def test_slugify_label_examples(label: str, expected: str) -> None:
    assert slugify_label(label) == expected


def test_slugify_label_raises_on_emoji_only_label() -> None:
    with pytest.raises(ValueError, match="Cannot derive step key from label"):
        slugify_label(":pipeline:")


def test_slugify_label_raises_on_empty_label() -> None:
    with pytest.raises(ValueError, match="Cannot derive step key from label"):
        slugify_label("")


def test_slugify_label_raises_on_punctuation_only_label() -> None:
    with pytest.raises(ValueError, match="Cannot derive step key from label"):
        slugify_label("!!! @@@ ###")
