"""Data models for scaffold branch command and diagnostics."""

from typing import Any, Optional

from dagster_shared.record import record


@record
class Session:
    """A recorded session of the `scaffold branch` command, useful for evaluating effectiveness."""

    # isoformat
    timestamp: str
    # what code was used - semver for published package, commit hash for local development
    dg_version: str
    # the name of the branch created (even if AI not used)
    branch_name: str
    # the title of the PR created (even if AI not used)
    pr_title: str
    # the URL of the PR created. Used to identify the target repo. Empty string if local-only.
    pr_url: str
    # the commit hash of the branch base. Used to identify the state of the target repo.
    branch_base_sha: str
    # the commit hash of the generated first pass commit, if done.
    first_pass_sha: Optional[str]
    # collection of input information
    input: dict[str, Any]
    # collection of generated output
    output: dict[str, Any]


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
    allowed_tools: list[str]
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
