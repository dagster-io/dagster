"""Configuration for API fixture recording commands."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FixtureCommand:
    """Configuration for a single fixture recording command."""

    command: str
    depends_on: Optional[list[str]] = None  # Dependencies (run IDs, etc.)
