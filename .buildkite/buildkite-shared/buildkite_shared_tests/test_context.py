"""Tests for buildkite_shared.context."""

import pytest
from buildkite_shared.context import BuildConfig


def test_from_env_accepts_values_that_are_not_bare_words() -> None:
    # Step labels routinely carry hyphens, dots, parens and spaces; a filter that
    # can't express them can't select the step it names.
    for raw, expected in [
        ("[STEP_FILTER=dagster-cloud-cli]", "dagster-cloud-cli"),
        ("[STEP_FILTER=dagster (1/2) cli_tests 3.12]", "dagster (1/2) cli_tests 3.12"),
        ("[STEP_FILTER=:pytest: ursula]", ":pytest: ursula"),
        # Surrounding whitespace would silently break the `substring in label` match.
        ("[STEP_FILTER=  ruff  ]", "ruff"),
    ]:
        assert BuildConfig.from_env({"BUILDKITE_MESSAGE": raw}).step_filter == expected


def test_from_env_layers_message_over_env_and_ignores_non_directives() -> None:
    config = BuildConfig.from_env(
        {
            "STEP_FILTER": "from-env",
            "REPEAT": "2",
            "BUILDKITE_MESSAGE": (
                "Fix flake [STEP_FILTER=dagster-cloud-cli] [REPEAT=5] "
                "[FW-1234] [skip ci] [UNRECOGNIZED=x] [see docs](http://example.com)"
            ),
        }
    )

    # Message wins over the env-var base layer.
    assert config.step_filter == "dagster-cloud-cli"
    assert config.repeat == 5
    # Bracketed text that isn't a directive leaves no trace: a tracker ID (hyphen in
    # the name), a two-word tag, an unknown field, a markdown link.
    assert config.no_skip is False
    assert config.refresh_durations is False

    # Env vars alone still work when the message carries no directives.
    env_only = BuildConfig.from_env({"STEP_FILTER": "from-env", "BUILDKITE_MESSAGE": "no magic"})
    assert env_only.step_filter == "from-env"
    assert env_only.repeat == 1


def test_from_env_flag_form_and_repeat_validation() -> None:
    flags = BuildConfig.from_env({"BUILDKITE_MESSAGE": "wip [NO_SKIP] [REFRESH_DURATIONS]"})
    assert flags.no_skip is True
    assert flags.refresh_durations is True
    assert flags.step_filter is None
    assert flags.repeat == 1

    # A widened VALUE class means junk reaches int(); fail with the field name in the
    # message rather than a bare "invalid literal for int()".
    for bad in ["[REPEAT=3 times]", "[REPEAT=abc]", "[REPEAT=0]", "[REPEAT=-1]"]:
        with pytest.raises(ValueError, match="REPEAT must be a positive integer"):
            BuildConfig.from_env({"BUILDKITE_MESSAGE": bad})
