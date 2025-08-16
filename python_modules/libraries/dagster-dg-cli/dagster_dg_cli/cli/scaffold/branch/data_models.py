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


@record
class PlanningRequest:
    """User input and context for plan generation.

    Records the complete context of a planning request including the user's
    original input, detected patterns, and metadata about the request.
    """

    correlation_id: str
    timestamp: str
    user_input: str
    input_type: str
    project_path: str
    detected_patterns: dict[str, Any]
    available_components: list[str]
    metadata: dict[str, Any]


@record
class PlanValidation:
    """Validation results for generated plans.

    Records the outcome of plan validation including any issues found
    and recommendations for improvement.
    """

    correlation_id: str
    timestamp: str
    plan_id: str
    is_valid: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    recommendations: list[str]
    metadata: dict[str, Any]


@record
class PlanExecution:
    """Record of plan execution progress and results.

    Tracks the execution of a generated plan including which steps
    were completed successfully and any failures encountered.
    """

    correlation_id: str
    timestamp: str
    plan_id: str
    executed_steps: list[str]
    failed_steps: list[str]
    skipped_steps: list[str]
    execution_metadata: dict[str, Any]
