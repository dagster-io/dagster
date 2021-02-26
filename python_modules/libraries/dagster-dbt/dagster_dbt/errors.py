from abc import ABC
from typing import Any, Dict, List

from dagster import EventMetadataEntry, Failure, check


class DagsterDbtError(Failure, ABC):
    """The base exception of the ``dagster-dbt`` library."""


class DagsterDbtCliUnexpectedOutputError(DagsterDbtError):
    """Represents an error when parsing the output of a dbt CLI command."""

    invalid_line_nos: List[int]

    def __init__(self, invalid_line_nos: List[int]):
        check.list_param(invalid_line_nos, "invalid_line_nos", int)
        line_nos_str = ", ".join(map(str, invalid_line_nos))
        description = f"dbt CLI emitted unexpected output on lines {line_nos_str}"
        metadata_entries = [
            EventMetadataEntry.json(
                {"line_nos": invalid_line_nos}, "Invalid CLI Output Line Numbers"
            )
        ]
        super().__init__(description, metadata_entries)
        self.invalid_line_nos = invalid_line_nos


class DagsterDbtCliRuntimeError(DagsterDbtError, ABC):
    """Represents an error while executing a dbt CLI command."""

    def __init__(self, description: str, logs: List[Dict[str, Any]], raw_output: str):
        metadata_entries = [
            EventMetadataEntry.json(
                {"logs": logs},
                label="Parsed CLI Output (JSON)",
            ),
            EventMetadataEntry.text(
                DagsterDbtCliRuntimeError.stitch_messages(logs),
                label="Parsed CLI Output (JSON) Message Attributes",
            ),
            EventMetadataEntry.text(
                raw_output,
                label="Raw CLI Output",
            ),
        ]
        super().__init__(description, metadata_entries)

    @staticmethod
    def stitch_messages(logs: List[dict]) -> str:
        return "\n".join(
            log["message"].strip("\n")
            for log in logs
            if isinstance(log.get("message"), str)  # defensive
        )


class DagsterDbtCliHandledRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a model error reported by the dbt CLI at runtime (return code 1)."""

    def __init__(self, logs: List[Dict[str, Any]], raw_output: str):
        super().__init__("Handled error in the dbt CLI (return code 1)", logs, raw_output)


class DagsterDbtCliFatalRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a fatal error in the dbt CLI (return code 2)."""

    def __init__(self, logs: List[Dict[str, Any]], raw_output: str):
        super().__init__("Fatal error in the dbt CLI (return code 2)", logs, raw_output)


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
