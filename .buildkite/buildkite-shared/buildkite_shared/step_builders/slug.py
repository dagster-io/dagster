"""Helpers for Buildkite step keys and labels.

Step keys must be unique within a pipeline; the label is what reviewers see
in the Buildkite UI. Each StepBuilder takes a `key` plus optional
`label_emojis` and assembles the displayed label by joining the emoji
shortcodes in front of the key.

`slugify_label` is kept around for callsites that need to derive a key from
arbitrary input strings (dynamic labels in tox runners, image-build helpers,
etc.). It strips emoji shortcodes, lowercases, collapses non-alphanumerics
to `-`, and raises if the result is empty.
"""

import re

_EMOJI_SHORTCODE = re.compile(r":[a-z0-9_+-]+:", re.IGNORECASE)
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify_label(label: str) -> str:
    stripped = _EMOJI_SHORTCODE.sub(" ", label).lower()
    slug = _NON_SLUG_CHARS.sub("-", stripped).strip("-")
    if not slug:
        raise ValueError(
            f"Cannot derive step key from label {label!r}: "
            "label must contain at least one alphanumeric character once "
            "Buildkite emoji shortcodes are stripped. Use a more descriptive label."
        )
    return slug


def make_label(key: str, label_emojis: list[str] | None) -> str:
    """Build the displayed Buildkite label by prefixing emoji shortcodes to the key."""
    if not label_emojis:
        return key
    return " ".join([*label_emojis, key])
