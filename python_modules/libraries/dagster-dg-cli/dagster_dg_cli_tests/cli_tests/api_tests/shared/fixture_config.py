"""Configuration for API fixture recording scenarios."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FixtureScenario:
    """Configuration for a single fixture recording scenario."""

    command: str
    has_recording: bool
    depends_on: Optional[list[str]] = None  # Dependencies (run IDs, etc.)
