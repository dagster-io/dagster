from abc import ABC
from typing import Any, Mapping, Sequence

from dagster import Failure, MetadataEntry
from dagster import _check as check


class DagsterDbtError(Failure, ABC):
    """The base exception of the ``dagster-dbt`` library."""


class DagsterDbtCliUnexpectedOutputError(DagsterDbtError):
    """Represents an error when parsing the output of a dbt CLI command."""

    invalid_line_nos: Sequence[int]

    def __init__(self, invalid_line_nos: Sequence[int]):
        check.list_param(invalid_line_nos, "invalid_line_nos", int)
        line_nos_str = ", ".join(map(str, invalid_line_nos))
        description = f"dbt CLI emitted unexpected output on lines {line_nos_str}"
        metadata_entries = [
            MetadataEntry("Invalid CLI Output Line Numbers", value={"line_nos": invalid_line_nos})
        ]
        super().__init__(description, metadata_entries)
        self.invalid_line_nos = invalid_line_nos


class DagsterDbtCliRuntimeError(DagsterDbtError, ABC):
    """Represents an error while executing a dbt CLI command."""

    def __init__(
        self,
        description: str,
        logs: Sequence[Mapping[str, Any]],
        raw_output: str,
        messages: Sequence[str],
    ):
        metadata_entries = [
            MetadataEntry(
                "Parsed CLI Output (JSON)",
                value={"logs": logs},
            ),
            MetadataEntry(
                "Parsed CLI Messages",
                value="\n".join(messages),
            ),
            MetadataEntry(
                "Raw CLI Output",
                value=raw_output,
            ),
        ]
        super().__init__(description, metadata_entries)


class DagsterDbtCliHandledRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a model error reported by the dbt CLI at runtime (return code 1)."""

    def __init__(self, logs: Sequence[Mapping[str, Any]], raw_output: str, messages: Sequence[str]):
        super().__init__("Handled error in the dbt CLI (return code 1)", logs, raw_output, messages)


class DagsterDbtCliFatalRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a fatal error in the dbt CLI (return code 2)."""

    def __init__(self, logs: Sequence[Mapping[str, Any]], raw_output: str, messages: Sequence[str]):
        super().__init__("Fatal error in the dbt CLI (return code 2)", logs, raw_output, messages)


class DagsterDbtRpcUnexpectedPollOutputError(DagsterDbtError):
    """Represents an unexpected response when polling the dbt RPC server."""


class DagsterDbtCliOutputsNotFoundError(DagsterDbtError):
    """Represents a problem in finding the ``target/run_results.json`` artifact when executing a dbt
    CLI command.

    For more details on ``target/run_results.json``, see
    https://docs.getdbt.com/reference/dbt-artifacts#run_resultsjson.
    """

    def __init__(self, path: str):
        super().__init__("Expected to find file at path {}".format(path))
