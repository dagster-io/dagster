import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, List, Mapping, Optional, TextIO

from rich.console import Console
from rich.table import Table
from typing_extensions import Self


@dataclass
class ProfilingEntry:
    name: str
    time: float


class ProfilingSession:
    def __init__(
        self,
        *,
        output: TextIO = sys.stdout,
        name: Optional[str] = None,
        experiment_settings: Optional[Mapping[str, Any]] = None,
    ):
        self.entries: list[ProfilingEntry] = []
        self.output = Console()
        self.name = name or "anonymous"
        self.experiment_settings = experiment_settings

    def start(self) -> Self:
        self.entries.append(ProfilingEntry("start", time.time()))
        return self

    def log_start_message(self) -> None:
        self.output.print(f"Profiling session started ({self.name})")
        self._log_blank_line()
        if self.experiment_settings:
            self._log_experiment_settings()
        self._log_blank_line()

    @contextmanager
    def logged_execution_time(self, name: str) -> Iterator[None]:
        yield
        self.entries.append(ProfilingEntry(name, time.time()))
        self._log_step(-1)

    def log_result_summary(self):
        self._log_divider()
        if self.experiment_settings:
            self._log_experiment_settings()
            self._log_blank_line()
        self._log_result_table()

    # ########################
    # ##### PRIVATE
    # ########################

    def _log_step(self, index: int) -> None:
        index = index if index >= 0 else len(self.entries) + index
        entry = self.entries[index]
        label = f"Execution time for step {index} ({entry.name}):"
        time_elapsed = entry.time - self.entries[index - 1].time
        message = f"{label} {time_elapsed:.4f} seconds"
        self.output.print(message)

    def _log_header(self, header: str) -> None:
        self.output.print(header)
        self.output.print("-" * len(header))

    def _log_divider(self) -> None:
        self.output.print("=" * 79)
        self.output.print()

    def _log_blank_line(self) -> None:
        self.output.print()

    def _log_experiment_settings(self) -> None:
        table = self._get_experiment_settings_table()
        self.output.print(table)

    def _log_result_table(self) -> None:
        table = self._get_result_table()
        self.output.print(table)

    def _get_experiment_settings_table(self) -> Table:
        table = Table(title="Experiment settings", title_justify="left")
        table.add_column("Key", justify="right")
        table.add_column("Value", justify="right")
        for key, value in (self.experiment_settings or {}).items():
            table.add_row(key, str(value))
        return table

    def _get_result_table(self) -> Table:
        table = Table(title="Execution times", title_justify="left")
        table.add_column("Index", justify="right")
        table.add_column("Step", justify="right")
        table.add_column("Time", justify="right")
        for i, entry in enumerate(self.entries[1:]):
            table.add_row(str(i), entry.name, f"{entry.time - self.entries[i].time:.4f}")
        return table
