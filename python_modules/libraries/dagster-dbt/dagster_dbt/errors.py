from abc import ABCMeta
from typing import List

from dagster import EventMetadataEntry, Failure, check


class DagsterDbtError(Failure, metaclass=ABCMeta):
    """An exception in the Dagster dbt intergration."""


class DagsterDbtUnexpectedCliOutputError(DagsterDbtError):
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


class DagsterDbtCliRuntimeError(DagsterDbtError, metaclass=ABCMeta):
    """A runtime exception from dbt."""

    def __init__(self, description: str, parsed_output: List[dict], raw_output: str):
        metadata_entries = [
            EventMetadataEntry.json({"logs": parsed_output}, label="Parsed CLI Output (JSON)",),
            EventMetadataEntry.text(
                DagsterDbtCliRuntimeError.stitch_messages(parsed_output),
                label="Parsed CLI Output (JSON) Message Attributes",
            ),
            EventMetadataEntry.text(raw_output, label="Raw CLI Output",),
        ]
        super().__init__(description, metadata_entries)

    @staticmethod
    def stitch_messages(parsed_output: List[dict]) -> str:
        return "\n".join(
            log["message"].strip("\n")
            for log in parsed_output
            if isinstance(log.get("message"), str)  # defensive
        )


class DagsterDbtHandledCliRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a model error reported by the dbt CLI at runtime (return code 1)."""

    def __init__(self, parsed_output: List[dict], raw_output: str):
        super().__init__("Handled error in the dbt CLI (return code 1)", parsed_output, raw_output)


class DagsterDbtFatalCliRuntimeError(DagsterDbtCliRuntimeError):
    """Represents a fatal error in the dbt CLI (return code 2)."""

    def __init__(self, parsed_output: List[dict], raw_output: str):
        super().__init__("Fatal error in the dbt CLI (return code 2)", parsed_output, raw_output)


class DagsterDbtUnexpectedRpcPollOutput(DagsterDbtError):
    pass
