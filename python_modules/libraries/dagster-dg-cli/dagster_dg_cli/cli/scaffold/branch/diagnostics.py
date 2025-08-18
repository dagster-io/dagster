"""Structured diagnostics system for scaffold branch operations."""

import json
import tempfile
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Optional, Union, get_args

from dagster_dg_cli.cli.scaffold.branch.models import (
    AIInteraction,
    ContextGathering,
    DiagnosticsEntry,
    PerformanceMetrics,
)

# Type alias for diagnostics levels
DiagnosticsLevel = Literal["off", "error", "info", "debug"]

# Valid diagnostics levels extracted from the Literal type
VALID_DIAGNOSTICS_LEVELS = get_args(DiagnosticsLevel)


class ClaudeDiagnosticsService:
    """Central diagnostics service for scaffold branch operations."""

    def __init__(
        self,
        level: DiagnosticsLevel = "off",
        output_dir: Optional[Path] = None,
        correlation_id: Optional[str] = None,
    ):
        self.level = level
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.output_dir = output_dir or Path(tempfile.gettempdir()) / "dg" / "diagnostics"
        self.entries: list[DiagnosticsEntry] = []
        self._output_file: Optional[Path] = None

        # Ensure output directory exists and create output file if diagnostics are enabled
        if self.level != "off":
            self.output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scaffold_diagnostics_{timestamp}_{self.correlation_id[:8]}.jsonl"
            self._output_file = self.output_dir / filename

            # Initialize file with session metadata as first line
            session_metadata = {
                "type": "session_start",
                "correlation_id": self.correlation_id,
                "timestamp": datetime.now().isoformat(),
                "level": self.level,
            }
            with self._output_file.open("w") as f:
                f.write(json.dumps(session_metadata) + "\n")

    @property
    def output_file(self) -> Optional[Path]:
        """Get the current output file path."""
        return self._output_file

    def _should_log(self, entry_level: DiagnosticsLevel) -> bool:
        """Check if entry should be logged based on current diagnostics level."""
        if self.level == "off":
            return False

        # Define hierarchy as mapping for cleaner logic
        level_priority = {"error": 0, "info": 1, "debug": 2}

        current_priority = level_priority.get(self.level)
        entry_priority = level_priority.get(entry_level)

        # Both levels must be valid for logging to proceed
        if current_priority is None or entry_priority is None:
            return False

        return entry_priority <= current_priority

    def log(
        self,
        level: DiagnosticsLevel,
        category: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a diagnostics entry."""
        if not self._should_log(level):
            return

        entry = DiagnosticsEntry(
            correlation_id=self.correlation_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            category=category,
            message=message,
            data=data or {},
        )

        self.entries.append(entry)

        # Stream entry to file immediately if file exists
        if self._output_file and self._output_file.exists():
            self._append_entry_to_file(entry)

    def _append_entry_to_file(self, entry: DiagnosticsEntry) -> None:
        """Append a single entry to the JSONL file."""
        if not self._output_file:
            return

        try:
            # Create entry dict and append as single line
            entry_dict = {
                "type": "entry",
                "correlation_id": entry.correlation_id,
                "timestamp": entry.timestamp,
                "level": entry.level,
                "category": entry.category,
                "message": entry.message,
                "data": entry.data,
            }

            # Append as new line to JSONL file
            with self._output_file.open("a") as f:
                f.write(json.dumps(entry_dict) + "\n")
        except Exception:
            # If append fails, fall back to recreating the file
            self._recreate_file_with_entries()

    def _recreate_file_with_entries(self) -> None:
        """Recreate the diagnostics file with all current entries in JSONL format."""
        if not self._output_file:
            return

        with self._output_file.open("w") as f:
            # Write session metadata first
            session_metadata = {
                "type": "session_start",
                "correlation_id": self.correlation_id,
                "timestamp": self.entries[0].timestamp
                if self.entries
                else datetime.now().isoformat(),
                "level": self.level,
            }
            f.write(json.dumps(session_metadata) + "\n")

            # Write all entries as individual lines
            for entry in self.entries:
                entry_dict = {
                    "type": "entry",
                    "correlation_id": entry.correlation_id,
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "category": entry.category,
                    "message": entry.message,
                    "data": entry.data,
                }
                f.write(json.dumps(entry_dict) + "\n")

    def log_ai_interaction(self, interaction: AIInteraction) -> None:
        """Log an AI interaction."""
        if not self._should_log("info"):
            return

        self.log(
            level="info",
            category="ai_interaction",
            message="Claude API interaction",
            data={
                "prompt_length": len(interaction.prompt),
                "response_length": len(interaction.response),
                "token_count": interaction.token_count,
                "tools_used": interaction.tools_used,
                "duration_ms": interaction.duration_ms,
            },
        )

    def log_context_gathering(self, context: ContextGathering) -> None:
        """Log context gathering operations."""
        if not self._should_log("debug"):
            return

        self.log(
            level="debug",
            category="context_gathering",
            message="Project context analysis",
            data={
                "files_count": len(context.files_analyzed),
                "files_analyzed": context.files_analyzed,
                "patterns_detected": context.patterns_detected,
                "decisions_made": context.decisions_made,
            },
        )

    def log_performance(self, metrics: PerformanceMetrics) -> None:
        """Log performance metrics."""
        if not self._should_log("debug"):
            return

        self.log(
            level="debug",
            category="performance",
            message=f"Operation timing: {metrics.operation}",
            data={
                "operation": metrics.operation,
                "phase": metrics.phase,
                "duration_ms": metrics.duration_ms,
            },
        )

    @contextmanager
    def time_operation(self, operation: str, phase: str = "default") -> Generator[None, None, None]:
        """Context manager for timing operations."""
        start_time = perf_counter()
        try:
            yield
        finally:
            duration_ms = (perf_counter() - start_time) * 1000
            metrics = PerformanceMetrics(
                correlation_id=self.correlation_id,
                timestamp=datetime.now().isoformat(),
                operation=operation,
                duration_ms=duration_ms,
                phase=phase,
            )
            self.log_performance(metrics)

    def flush(self) -> Optional[Path]:
        """Finalize the diagnostics file with session end timestamp."""
        if self.level == "off" or not self._output_file:
            return None

        # Return None if no entries to flush
        if not self.entries:
            return None

        # Add session_end timestamp as final line in JSONL file
        if self._output_file.exists():
            try:
                session_end = {
                    "type": "session_end",
                    "correlation_id": self.correlation_id,
                    "timestamp": datetime.now().isoformat(),
                }
                with self._output_file.open("a") as f:
                    f.write(json.dumps(session_end) + "\n")

                # Clear entries after successful flush
                self.entries.clear()
                return self._output_file
            except Exception:
                # If append fails, recreate file and add session_end
                self._recreate_file_with_entries()
                session_end = {
                    "type": "session_end",
                    "correlation_id": self.correlation_id,
                    "timestamp": datetime.now().isoformat(),
                }
                with self._output_file.open("a") as f:
                    f.write(json.dumps(session_end) + "\n")

                self.entries.clear()
                return self._output_file

        return self._output_file

    def error(self, category: str, message: str, data: Optional[dict[str, Any]] = None) -> None:
        """Log an error-level entry."""
        self.log("error", category, message, data)

    def info(self, category: str, message: str, data: Optional[dict[str, Any]] = None) -> None:
        """Log an info-level entry."""
        self.log("info", category, message, data)

    def debug(self, category: str, message: str, data: Optional[dict[str, Any]] = None) -> None:
        """Log a debug-level entry."""
        self.log("debug", category, message, data)


def create_claude_diagnostics_service(
    level: DiagnosticsLevel = "off",
    output_dir: Optional[Union[str, Path]] = None,
    correlation_id: Optional[str] = None,
) -> ClaudeDiagnosticsService:
    """Create a new Claude diagnostics service instance."""
    output_path = Path(output_dir) if output_dir else None
    return ClaudeDiagnosticsService(
        level=level,
        output_dir=output_path,
        correlation_id=correlation_id,
    )
