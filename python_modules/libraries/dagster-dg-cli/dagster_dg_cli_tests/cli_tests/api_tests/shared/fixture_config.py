"""Configuration for API fixture recording scenarios."""

from dataclasses import dataclass


@dataclass
class FixtureScenario:
    """Configuration for a single fixture recording scenario."""

    command: str
    has_recording: bool
    depends_on: list[str] | None = None  # Dependencies (run IDs, etc.)
