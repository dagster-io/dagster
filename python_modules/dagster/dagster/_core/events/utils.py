import json
from json import JSONDecodeError

from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.errors import DeserializationError

import dagster._check as check
from dagster._core.events import DagsterEvent


def filter_dagster_events_from_cli_logs(log_lines):
    """Filters the raw log lines from a dagster-cli invocation to return only the lines containing json.

    - Log lines don't necessarily come back in order
    - Something else might log JSON
    - Docker appears to silently split very long log lines -- this is undocumented behavior

    TODO: replace with reading event logs from the DB

    """
    check.list_param(log_lines, "log_lines", str)

    events = []
    decoder = json.JSONDecoder()
    buffer = ""
    for raw_line in log_lines:
        buffer += raw_line.rstrip("\r\n")

        while buffer:
            trimmed = buffer.lstrip()
            if not trimmed:
                buffer = ""
                break

            start_idx = trimmed.find("{")
            if start_idx == -1:
                buffer = ""
                break

            if start_idx:
                trimmed = trimmed[start_idx:]

            try:
                _, end_idx = decoder.raw_decode(trimmed)
            except JSONDecodeError:
                buffer = trimmed
                break

            candidate = trimmed[:end_idx]
            buffer = trimmed[end_idx:]
            try:
                events.append(deserialize_value(candidate, DagsterEvent))
            except (JSONDecodeError, check.CheckError, DeserializationError):
                pass

    return events
