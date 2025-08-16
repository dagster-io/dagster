"""Data models for scaffold branch diagnostics."""

from typing import Any, Optional

from dagster_shared.record import record


@record
class DiagnosticsEntry:
    """Individual diagnostics log entry."""

    correlation_id: str
    timestamp: str
    level: str
    category: str
    message: str
    data: dict[str, Any]


@record
class AIInteraction:
    """Record of AI interaction with Claude."""

    correlation_id: str
    timestamp: str
    prompt: str
    response: str
    token_count: Optional[int]
    tools_used: list[str]
    duration_ms: float


@record
class ContextGathering:
    """Record of context gathering operations."""

    correlation_id: str
    timestamp: str
    files_analyzed: list[str]
    patterns_detected: list[str]
    decisions_made: dict[str, Any]


@record
class PerformanceMetrics:
    """Performance timing data for operations."""

    correlation_id: str
    timestamp: str
    operation: str
    duration_ms: float
    phase: str
