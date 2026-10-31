import json
import logging
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import UUID

import dagster._check as check
from dagster._annotations import preview
from dagster._core.pipes.client import PipesLaunchedData, PipesParams
from dagster._core.pipes.utils import PipesThreadedMessageReader
from dagster_pipes import PIPES_PROTOCOL_VERSION_FIELD, PipesPrefectLogsMessageWriter
from dagster_shared.record import record
from prefect.client.schemas.filters import (
    LogFilter,
    LogFilterFlowRunId,
    LogFilterTaskRunId,
    LogFilterTimestamp,
)
from prefect.client.schemas.objects import Log
from prefect.client.schemas.sorting import LogSort

from dagster_prefect.resource import PrefectResource

# Keys of the `report_launched` extras the Prefect clients send once the run exists.
PREFECT_RUN_KIND_EXTRA = "prefect_run_kind"
PREFECT_RUN_ID_EXTRA = "prefect_run_id"

# `read_logs` can only sort by the writer's own timestamp, so a log can land after one that
# was written later. Re-reading this far back, deduped by log id, picks those up.
LOOKBACK = timedelta(seconds=10)

# Prefect servers reject pages above `PREFECT_SERVER_API_DEFAULT_LIMIT`, 200 by default.
PAGE_SIZE = 200


@record
class _LogsCursor:
    after: datetime
    # Ids of logs already handled, with their timestamps so ids older than the lookback can
    # be dropped.
    seen: Mapping[UUID, datetime]


@preview
class PipesPrefectLogsMessageReader(PipesThreadedMessageReader):
    """Message reader that reads Pipes messages from a Prefect run's logs, through the Prefect API.

    Pairs with :py:class:`~dagster_pipes.PipesPrefectLogsMessageWriter` on the flow or task side,
    so nothing beyond the Prefect API is needed to get messages back. Every other log line of
    the run is forwarded to the Dagster step's stdout.

    Args:
        prefect (PrefectResource): The Prefect API the run's logs are read from.
        interval (float): How long to wait between reads, in seconds. Defaults to 5.
    """

    def __init__(self, prefect: PrefectResource, interval: float = 5):
        self.prefect = check.inst_param(prefect, "prefect", PrefectResource)
        self._run_kind: str | None = None
        self._run_id: UUID | None = None
        super().__init__(interval=interval)

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        yield {
            PipesPrefectLogsMessageWriter.PREFECT_LOGS_KEY: True,
            PipesPrefectLogsMessageWriter.MAX_MESSAGE_BYTES_KEY: (
                PipesPrefectLogsMessageWriter.DEFAULT_MAX_MESSAGE_BYTES
            ),
        }

    def on_launched(self, launched_payload: PipesLaunchedData) -> None:
        extras = launched_payload["extras"]
        if PREFECT_RUN_ID_EXTRA in extras:
            self._run_kind = extras[PREFECT_RUN_KIND_EXTRA]
            self._run_id = UUID(extras[PREFECT_RUN_ID_EXTRA])
        super().on_launched(launched_payload)

    def messages_are_readable(self, params: PipesParams) -> bool:
        return self._run_id is not None

    def download_messages(
        self, cursor: _LogsCursor | None, params: PipesParams
    ) -> tuple[_LogsCursor, str] | None:
        seen = dict(cursor.seen) if cursor else {}
        since = cursor.after - LOOKBACK if cursor else None
        new_logs = [log for log in self._read_logs(since) if log.id not in seen]
        if not new_logs:
            return None

        messages = []
        for log in new_logs:
            seen[log.id] = log.timestamp
            if _is_pipes_message(log.message):
                messages.append(log.message)
            else:
                sys.stdout.write(_format_log(log))

        after = max(log.timestamp for log in new_logs)
        if cursor:
            after = max(after, cursor.after)
        seen = {log_id: ts for log_id, ts in seen.items() if ts >= after - LOOKBACK}
        return _LogsCursor(after=after, seen=seen), "\n".join(messages)

    def no_messages_debug_text(self) -> str:
        return (
            f"Attempted to read messages from the logs of Prefect {self._run_kind} {self._run_id}."
            " This is expected if the flow or task doesn't open a Pipes session. Otherwise, check"
            " that it passes `message_writer=PipesPrefectLogsMessageWriter()` to"
            " `open_dagster_pipes`, that `PREFECT_LOGGING_TO_API_ENABLED` is not turned off, and"
            " that `PREFECT_LOGGING_LEVEL` is INFO or lower."
        )

    def _read_logs(self, since: datetime | None) -> list[Log]:
        run_id = check.not_none(self._run_id)
        timestamp = LogFilterTimestamp(after_=since)
        if self._run_kind == "task-run":
            log_filter = LogFilter(
                task_run_id=LogFilterTaskRunId(any_=[run_id]), timestamp=timestamp
            )
        else:
            log_filter = LogFilter(
                flow_run_id=LogFilterFlowRunId(any_=[run_id]), timestamp=timestamp
            )

        logs: list[Log] = []
        with self.prefect.get_client() as client:
            while True:
                page = client.read_logs(
                    log_filter=log_filter,
                    limit=PAGE_SIZE,
                    offset=len(logs),
                    sort=LogSort.TIMESTAMP_ASC,
                )
                logs.extend(page)
                if len(page) < PAGE_SIZE:
                    return logs


def _is_pipes_message(line: str) -> bool:
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        return False
    return isinstance(message, dict) and PIPES_PROTOCOL_VERSION_FIELD in message


def _format_log(log: Log) -> str:
    # Same shape as Prefect's own console output.
    return (
        f"{log.timestamp:%H:%M:%S.%f}"[:-3]
        + f" | {logging.getLevelName(log.level):<7} | {log.name} - {log.message}\n"
    )
