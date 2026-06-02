from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.get_logs_captured_events import (
    GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.compute_log import (
    DgApiComputeLogLinkList,
    DgApiComputeLogList,
    DgApiStepComputeLog,
    DgApiStepComputeLogLink,
)
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError

_MAX_PAGES = 100


@dataclass(frozen=True)
class DgApiComputeLogApi:
    _client: IGraphQLClient

    def get_logs(
        self,
        run_id: str,
        step_key: str | None = None,
        cursor: str | None = None,
        max_bytes: int | None = None,
    ) -> DgApiComputeLogList:
        events = self._get_logs_captured_events(run_id, step_key=step_key)

        items: list[DgApiStepComputeLog] = []
        for event in events:
            log_key = [run_id, "compute_logs", event.file_key]
            content = self._client.get_captured_logs(
                log_key=log_key,
                cursor=cursor,
                limit=max_bytes,
            ).captured_logs
            items.append(
                DgApiStepComputeLog(
                    file_key=event.file_key,
                    step_keys=event.step_keys or [],
                    stdout=content.stdout,
                    stderr=content.stderr,
                    cursor=content.cursor,
                )
            )

        return DgApiComputeLogList(items=items, run_id=run_id)

    def get_log_links(
        self,
        run_id: str,
        step_key: str | None = None,
    ) -> DgApiComputeLogLinkList:
        events = self._get_logs_captured_events(run_id, step_key=step_key)

        items: list[DgApiStepComputeLogLink] = []
        for event in events:
            step_keys = event.step_keys or []

            if event.external_stdout_url or event.external_stderr_url:
                items.append(
                    DgApiStepComputeLogLink(
                        file_key=event.file_key,
                        step_keys=step_keys,
                        stdout_download_url=event.external_stdout_url,
                        stderr_download_url=event.external_stderr_url,
                    )
                )
            else:
                log_key = [run_id, "compute_logs", event.file_key]
                metadata = self._client.get_captured_logs_metadata(
                    log_key=log_key
                ).captured_logs_metadata
                items.append(
                    DgApiStepComputeLogLink(
                        file_key=event.file_key,
                        step_keys=step_keys,
                        stdout_download_url=metadata.stdout_download_url,
                        stderr_download_url=metadata.stderr_download_url,
                    )
                )

        return DgApiComputeLogLinkList(items=items, run_id=run_id)

    def _get_logs_captured_events(
        self,
        run_id: str,
        step_key: str | None = None,
    ) -> list[GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent]:
        collected: list[GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent] = []
        after_cursor: str | None = None
        server_has_more = True

        for _ in range(_MAX_PAGES):
            if not server_has_more:
                break

            result = self._client.get_logs_captured_events(
                run_id=run_id,
                limit=100,
                after_cursor=after_cursor,
            ).logs_for_run

            match result.typename__:
                case "EventConnection":
                    for event in result.events:  # ty: ignore[unresolved-attribute]
                        if not isinstance(
                            event,
                            GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent,
                        ):
                            continue
                        if step_key and step_key not in (event.step_keys or []):
                            continue
                        collected.append(event)

                    server_has_more = result.has_more  # ty: ignore[unresolved-attribute]
                    new_cursor = result.cursor  # ty: ignore[unresolved-attribute]

                    if server_has_more and not new_cursor:
                        break

                    after_cursor = new_cursor

                case "RunNotFoundError":
                    raise DagsterPlusGraphqlError(f"Error fetching logs for run: {result.message}")  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error fetching logs for run: {result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)

        return collected
